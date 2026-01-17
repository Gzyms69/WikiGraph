#!/usr/bin/env python3
"""
WikiGraph SQLite Loader (Tier 2 Storage) - mwsql Edition
- Initializes the metadata database (per language).
- Parses raw SQL dumps using mwsql (Safe Parsing).
- Populates 'pages', 'link_targets', 'category_links', 'id_mapping'.
- Handles latin1 -> utf8 conversion for binary fields.
"""

import sqlite3
import sys
import os
from pathlib import Path
from mwsql import Dump

# Schema with link_targets
SCHEMA = """
CREATE TABLE IF NOT EXISTS pages (
    page_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    namespace INTEGER,
    is_redirect BOOLEAN,
    len INTEGER,
    touched TIMESTAMP
);

CREATE TABLE IF NOT EXISTS link_targets (
    lt_id INTEGER PRIMARY KEY,
    lt_namespace INTEGER,
    lt_title TEXT
);

CREATE TABLE IF NOT EXISTS id_mapping (
    page_id INTEGER PRIMARY KEY,
    qid TEXT,
    FOREIGN KEY(page_id) REFERENCES pages(page_id)
);

CREATE TABLE IF NOT EXISTS category_links (
    page_id INTEGER,
    lt_id INTEGER,
    category_name TEXT,
    FOREIGN KEY(page_id) REFERENCES pages(page_id)
);

CREATE INDEX IF NOT EXISTS idx_title ON pages(title);
CREATE INDEX IF NOT EXISTS idx_qid ON id_mapping(qid);
CREATE INDEX IF NOT EXISTS idx_cat_page ON category_links(page_id);
CREATE INDEX IF NOT EXISTS idx_cat_name ON category_links(category_name);
CREATE INDEX IF NOT EXISTS idx_lt_id ON link_targets(lt_id);
"""

def get_db_connection(db_path):
    conn = sqlite3.connect(db_path)
    # Speed Optimizations
    conn.execute("PRAGMA journal_mode = MEMORY;") 
    conn.execute("PRAGMA synchronous = OFF;") 
    conn.execute("PRAGMA cache_size = 200000;")
    conn.execute("PRAGMA temp_store = MEMORY;")
    conn.execute("PRAGMA locking_mode = EXCLUSIVE;")
    return conn

def init_db(db_path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f"✅ Database initialized at {db_path}")

def fix_encoding(text):
    """Fixes potential latin1 vs utf8 mismatch in strings."""
    if isinstance(text, str):
        # Try to re-encode as latin1 and decode as utf-8
        try:
            return text.encode('latin1').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            return text
    return text

def process_page_dump(file_path, db_path, limit=None):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    print(f"📄 Processing {file_path.name}...")
    
    # Load with latin1 to handle binary, then fix text
    dump = Dump.from_file(str(file_path), encoding='latin1')
    
    batch, batch_size = [], 100000
    count = 0
    cursor.execute("BEGIN TRANSACTION")
    
    for row in dump.rows():
        if limit and count >= limit: break
        
        # Schema: id(0), ns(1), title(2), is_redirect(3), ..., len(9)
        if len(row) < 10: continue
        
        try:
            p_id = int(row[0])
            ns = int(row[1])
            title = fix_encoding(row[2])
            is_redir = int(row[3])
            p_len = int(row[9])
            
            if ns in [0, 14]:
                batch.append((p_id, title, ns, is_redir, p_len))
                count += 1
        except (ValueError, IndexError): continue

        if len(batch) >= batch_size:
            cursor.executemany("INSERT OR IGNORE INTO pages (page_id, title, namespace, is_redirect, len) VALUES (?, ?, ?, ?, ?)", batch)
            batch = []

    if batch: cursor.executemany("INSERT OR IGNORE INTO pages (page_id, title, namespace, is_redirect, len) VALUES (?, ?, ?, ?, ?)", batch)
    cursor.execute("COMMIT")
    conn.close()

def process_linktarget_dump(file_path, db_path, limit=None):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    print(f"🎯 Processing {file_path.name}...")
    
    # Check if lt_namespace column exists, if not recreate table (Quick Migration)
    try:
        cursor.execute("SELECT lt_namespace FROM link_targets LIMIT 1")
    except sqlite3.OperationalError:
        print("⚠️  Schema outdated. Dropping and recreating link_targets...")
        cursor.execute("DROP TABLE IF EXISTS link_targets")
        cursor.execute("""
            CREATE TABLE link_targets (
                lt_id INTEGER PRIMARY KEY,
                lt_namespace INTEGER,
                lt_title TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lt_id ON link_targets(lt_id)")
        conn.commit()

    dump = Dump.from_file(str(file_path), encoding='latin1')
    batch, batch_size = [], 100000
    count = 0
    cursor.execute("BEGIN TRANSACTION")
    
    for row in dump.rows():
        if limit and count >= limit: break
        
        # Schema: lt_id(0), lt_namespace(1), lt_title(2)
        if len(row) < 3: continue
        try:
            lt_id = int(row[0])
            lt_ns = int(row[1])
            lt_title = fix_encoding(row[2])
            batch.append((lt_id, lt_ns, lt_title))
            count += 1
        except (ValueError, IndexError): continue

        if len(batch) >= batch_size:
            cursor.executemany("INSERT OR IGNORE INTO link_targets (lt_id, lt_namespace, lt_title) VALUES (?, ?, ?)", batch)
            batch = []

    if batch: cursor.executemany("INSERT OR IGNORE INTO link_targets (lt_id, lt_namespace, lt_title) VALUES (?, ?, ?)", batch)
    cursor.execute("COMMIT")
    conn.close()
    print(f"   Processed {count} link targets.")

def process_category_dump(file_path, db_path, limit=None):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    print(f"🏷️ Processing {file_path.name}...")
    
    print("   Loading link_targets into memory map...")
    # NOTE: This loads title, but for categories we might need NS too later. For now, name is enough.
    cursor.execute("SELECT lt_id, lt_title FROM link_targets")
    lt_map = dict(cursor.fetchall())
    print(f"   Mapped {len(lt_map)} link targets.")

    dump = Dump.from_file(str(file_path), encoding='latin1')
    batch, batch_size = [], 100000
    count = 0
    cursor.execute("BEGIN TRANSACTION")
    
    for row in dump.rows():
        if limit and count >= limit: break
        
        # Schema: cl_from(0), ..., cl_target_id(6)
        if len(row) < 7: continue
        try:
            p_id = int(row[0])
            cl_target_id = int(row[6])
            
            cat_name = lt_map.get(cl_target_id)
            if cat_name:
                batch.append((p_id, cl_target_id, cat_name))
                count += 1
        except (ValueError, IndexError): continue
        
        if len(batch) >= batch_size:
            cursor.executemany("INSERT OR IGNORE INTO category_links (page_id, lt_id, category_name) VALUES (?, ?, ?)", batch)
            batch = []

    if batch: cursor.executemany("INSERT OR IGNORE INTO category_links (page_id, lt_id, category_name) VALUES (?, ?, ?)", batch)
    cursor.execute("COMMIT")
    conn.close()

def process_props_dump(file_path, db_path, limit=None):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    print(f"🔗 Processing {file_path.name}...")
    
    dump = Dump.from_file(str(file_path), encoding='latin1')
    batch, batch_size = [], 100000
    count = 0
    cursor.execute("BEGIN TRANSACTION")
    
    for row in dump.rows():
        if limit and count >= limit: break
        
        # Schema: pp_page(0), pp_propname(1), pp_value(2)
        if len(row) < 3: continue
        try:
            if row[1] == 'wikibase_item':
                batch.append((int(row[0]), row[2]))
                count += 1
        except (ValueError, IndexError): continue
        
        if len(batch) >= batch_size:
            cursor.executemany("INSERT OR IGNORE INTO id_mapping (page_id, qid) VALUES (?, ?)", batch)
            batch = []

    if batch: cursor.executemany("INSERT OR IGNORE INTO id_mapping (page_id, qid) VALUES (?, ?)", batch)
    cursor.execute("COMMIT")
    conn.close()

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--lang", default="en")
    parser.add_argument("--db", default=None, help="Specific DB path (default: data/db/{lang}.db)")
    parser.add_argument("--limit", type=int, default=None, help="Limit rows per file for testing")
    parser.add_argument("--only-targets", action="store_true", help="Process only link_targets")
    args = parser.parse_args()
    
    if args.db:
        db_path = Path(args.db)
    else:
        db_path = Path(f"data/db/{args.lang}.db")
        
    if args.init: init_db(db_path)
        
    raw = Path("data/raw")
    
    if args.only_targets:
        process_linktarget_dump(raw / f"{args.lang}wiki-latest-linktarget.sql.gz", db_path, args.limit)
    else:
        files = [
            (raw / f"{args.lang}wiki-latest-page.sql.gz", process_page_dump),
            (raw / f"{args.lang}wiki-latest-linktarget.sql.gz", process_linktarget_dump),
            (raw / f"{args.lang}wiki-latest-categorylinks.sql.gz", process_category_dump),
            (raw / f"{args.lang}wiki-latest-page_props.sql.gz", process_props_dump)
        ]
        
        for p, func in files:
            if p.exists(): func(p, db_path, args.limit)
            else: print(f"⚠️ Missing {p}")

if __name__ == "__main__":
    main()