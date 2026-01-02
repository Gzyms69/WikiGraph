#!/usr/bin/env python3
"""
CORE: SQLITE LOADER
Two-pass database population using zero-RAM SQL JOIN approach.
"""

import sqlite3
import json
import gzip
import csv
import sys
import glob
import time
import argparse
from pathlib import Path
from multiprocessing import Pool, cpu_count
from typing import List, Tuple, Dict
from functools import partial

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from tqdm import tqdm
except ImportError:
    print("Warning: tqdm not found. Progress bar will be disabled.")
    tqdm = None

def setup_database_optimizations(cursor):
    """Apply SQLite performance optimizations for bulk loading."""
    cursor.execute("PRAGMA journal_mode = WAL;")
    cursor.execute("PRAGMA synchronous = NORMAL;")
    cursor.execute("PRAGMA cache_size = -1000000;")
    cursor.execute("PRAGMA temp_store = MEMORY;")
    cursor.execute("PRAGMA locking_mode = EXCLUSIVE;")

def drop_indexes_for_bulk_load(cursor):
    print("Dropping indexes for faster bulk loading...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_autoindex%';")
    indexes = cursor.fetchall()
    for (index_name,) in indexes:
        try:
            cursor.execute(f"DROP INDEX IF EXISTS {index_name};")
        except sqlite3.Error: pass
    cursor.connection.commit()

def recreate_indexes_and_safety(cursor):
    print("Recreating indexes...")
    indexes_to_create = [
        "CREATE INDEX IF NOT EXISTS idx_articles_lang_title ON articles(language, title);",
        "CREATE INDEX IF NOT EXISTS idx_articles_title ON articles(title);",
        "CREATE INDEX IF NOT EXISTS idx_links_lang_target ON links(language, target_title);",
        "CREATE INDEX IF NOT EXISTS idx_links_source ON links(source_id, language);"
    ]
    for index_sql in indexes_to_create:
        try: cursor.execute(index_sql)
        except sqlite3.Error: pass
    cursor.execute("PRAGMA journal_mode = WAL;")
    cursor.execute("PRAGMA synchronous = NORMAL;")
    cursor.connection.commit()

def load_articles(cursor, data_dir: Path):
    print(f"Loading articles from {data_dir} with I/O smoothing...")
    article_files = sorted(data_dir.glob('articles_batch_*.jsonl.gz'))
    if not article_files: raise FileNotFoundError(f"No articles in {data_dir}")

    article_count = 0
    for file_path in article_files:
        print(f"  Processing {file_path.name}...")
        with gzip.open(file_path, 'rt', encoding='utf-8') as f:
            batch_articles = []
            for line in f:
                if not line.strip(): continue
                article = json.loads(line)
                batch_articles.append((
                    article['id'], article['language'], article['title'],
                    article.get('revision_id'), article.get('timestamp'),
                    json.dumps(article.get('infobox'), ensure_ascii=False) if article.get('infobox') else None,
                    json.dumps(article.get('categories', []), ensure_ascii=False),
                    article.get('word_count'), article.get('text_length')
                ))

                if len(batch_articles) >= 10000:
                    cursor.executemany('''
                        INSERT OR IGNORE INTO articles
                        (id, language, title, revision_id, timestamp, infobox, categories, word_count, text_length)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', batch_articles)
                    cursor.connection.commit()
                    article_count += len(batch_articles)
                    batch_articles = []
                    time.sleep(0.1)

            if batch_articles:
                cursor.executemany('''
                    INSERT OR IGNORE INTO articles
                    (id, language, title, revision_id, timestamp, infobox, categories, word_count, text_length)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', batch_articles)
                cursor.connection.commit()
                article_count += len(batch_articles)
    return article_count

def process_link_file_worker(file_path: str, lang_code: str):
    raw_links = []
    with gzip.open(file_path, 'rt', encoding='utf-8', newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 2: continue
            raw_links.append((row[0], row[1], lang_code))
    return raw_links

def load_links_parallel(cursor, data_dir: Path, lang_code: str):
    print("Loading links with Zero-RAM SQL JOIN approach...")
    links_files = sorted(data_dir.glob('links_batch_*.csv.gz'))
    if not links_files: raise FileNotFoundError(f"No links in {data_dir}")

    cursor.execute("CREATE TEMP TABLE temp_links (source_title TEXT, target_title TEXT, language TEXT)")
    cursor.execute("CREATE INDEX idx_temp_links_source ON temp_links(source_title, language)")

    cores = 2 # Stability Mode
    process_func = partial(process_link_file_worker, lang_code=lang_code)
    
    pbar = None
    if tqdm: pbar = tqdm(total=len(links_files), desc="Processing link batches")

    with Pool(processes=cores) as pool:
        results = pool.imap_unordered(process_func, [str(f) for f in links_files])
        for i, raw_links in enumerate(results):
            if raw_links:
                cursor.executemany("INSERT INTO temp_links (source_title, target_title, language) VALUES (?, ?, ?)", raw_links)
                if i % 10 == 0:
                    cursor.connection.commit()
                    time.sleep(0.5)
            if pbar: pbar.update(1)
    
    cursor.connection.commit()
    if pbar: pbar.close()

    print("Resolving IDs via SQL JOIN...")
    cursor.execute('''
        INSERT INTO links (source_id, target_title, language)
        SELECT a.id, t.target_title, t.language
        FROM temp_links t
        JOIN articles a ON t.source_title = a.title AND t.language = a.language
    ''')
    resolved = cursor.rowcount
    cursor.connection.commit()
    cursor.execute("DROP TABLE IF EXISTS temp_links")
    print(f"✓ Resolved {resolved:,} links.")
    return resolved

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--lang', default='pl')
    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent
    db_path = base_dir / 'data' / 'db' / 'wikigraph_multilang.db'
    data_dir = base_dir / 'data' / 'processed' / args.lang

    conn = None
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        setup_database_optimizations(cursor)
        drop_indexes_for_bulk_load(cursor)

        a_count = load_articles(cursor, data_dir)
        l_count = load_links_parallel(cursor, data_dir, args.lang)
        
        recreate_indexes_and_safety(cursor)
        print(f"\n✅ SUCCESS [{args.lang.upper()}]: Articles={a_count:,}, Links={l_count:,}")
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    main()