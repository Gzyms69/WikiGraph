#!/usr/bin/env python3
"""
Load Multi-Language Data into Database

Two-pass database population:
1. Load articles and build title-to-ID mapping
2. Load links with source resolution and batch_num for debugging

INPUT: processed_batches_pl/ (articles and links with language fields)
OUTPUT: wikigraph_multilang.db populated with Polish Wikipedia data
"""

import sqlite3
import json
import gzip
import csv
import sys
import glob
from pathlib import Path

# Add config directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))


def setup_database_optimizations(cursor):
    """Apply SQLite performance optimizations for bulk loading."""
    # HIGH-PERFORMANCE BULK LOAD SETTINGS (temporarily unsafe)
    cursor.execute("PRAGMA journal_mode = OFF;")      # Disable journaling for speed
    cursor.execute("PRAGMA synchronous = OFF;")       # OS handles sync timing
    cursor.execute("PRAGMA cache_size = -2000000;")   # Use 2GB RAM for cache
    cursor.execute("PRAGMA temp_store = MEMORY;")     # Temp tables in RAM
    cursor.execute("PRAGMA locking_mode = EXCLUSIVE;") # Exclusive lock for process


def drop_indexes_for_bulk_load(cursor):
    """Drop indexes before bulk loading for maximum speed."""
    print("Dropping indexes for faster bulk loading...")

    # Get all user-created indexes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_autoindex%';")
    indexes = cursor.fetchall()

    dropped_count = 0
    for (index_name,) in indexes:
        try:
            cursor.execute(f"DROP INDEX IF EXISTS {index_name};")
            dropped_count += 1
        except sqlite3.Error as e:
            print(f"  Warning: Could not drop index {index_name}: {e}")

    cursor.connection.commit()
    print(f"✓ Dropped {dropped_count} indexes for faster loading")


def recreate_indexes_and_safety(cursor):
    """Recreate indexes and re-enable database safety after bulk loading."""
    print("Recreating indexes...")

    # Recreate the indexes from our schema
    indexes_to_create = [
        "CREATE INDEX IF NOT EXISTS idx_articles_lang_title ON articles(language, title);",
        "CREATE INDEX IF NOT EXISTS idx_articles_title ON articles(title);",
        "CREATE INDEX IF NOT EXISTS idx_links_lang_target ON links(language, target_title);",
        "CREATE INDEX IF NOT EXISTS idx_links_source ON links(source_id, language);"
    ]

    for index_sql in indexes_to_create:
        try:
            cursor.execute(index_sql)
        except sqlite3.Error as e:
            print(f"  Warning: Could not create index: {e}")

    print("✓ Indexes recreated")

    # Re-enable database safety
    print("Re-enabling database safety settings...")
    cursor.execute("PRAGMA journal_mode = WAL;")
    cursor.execute("PRAGMA synchronous = NORMAL;")
    cursor.execute("PRAGMA cache_size = -10000;")  # Reset to reasonable default

    cursor.connection.commit()
    print("✓ Database safety restored")


def load_articles(cursor, data_dir: Path, title_to_id: dict):
    """
    Load articles and build title-to-ID mapping.

    Args:
        cursor: Database cursor
        data_dir: Directory containing processed_batches_pl
        title_to_id: Dictionary to populate with title -> id mappings

    Returns:
        Number of articles loaded
    """
    print("Loading articles and building title mapping...")

    article_files = sorted(glob.glob(str(data_dir / 'articles_batch_*.jsonl.gz')))
    if not article_files:
        raise FileNotFoundError(f"No article files found in {data_dir}")

    article_count = 0

    for file_path in article_files:
        print(f"  Processing {Path(file_path).name}...")

        with gzip.open(file_path, 'rt', encoding='utf-8') as f:
            batch_articles = []

            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    article = json.loads(line)

                    # Build mapping BEFORE any potential normalization
                    title_to_id[article['title']] = article['id']

                    # Prepare data for batch insert (match our 9-column schema)
                    # Convert complex types to JSON strings for SQLite
                    categories_json = json.dumps(article.get('categories', []), ensure_ascii=False)
                    infobox_json = json.dumps(article.get('infobox'), ensure_ascii=False) if article.get('infobox') else None

                    batch_articles.append((
                        article['id'],
                        article['language'],  # Should be 'pl'
                        article['title'],
                        article.get('revision_id'),
                        article.get('timestamp'),
                        infobox_json,  # Convert dict to JSON string
                        categories_json,  # Convert list to JSON string
                        article.get('word_count'),
                        article.get('text_length')
                    ))

                except json.JSONDecodeError as e:
                    print(f"    WARNING: Skipping corrupted JSON: {e}")
                    continue

            # Batch insert articles
            if batch_articles:
                cursor.executemany('''
                    INSERT INTO articles
                    (id, language, title, revision_id, timestamp, infobox, categories, word_count, text_length)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', batch_articles)

                article_count += len(batch_articles)

                # Commit periodically for large datasets
                if article_count % 50000 == 0:
                    cursor.connection.commit()
                    print(f"    Committed {article_count:,} articles...")

    # Final commit for articles
    cursor.connection.commit()
    print(f"✓ Loaded {article_count:,} articles")
    print(f"✓ Title mapping built ({len(title_to_id):,} entries, ~{len(title_to_id) * 0.5 / 1024 / 1024:.1f}MB)")

    return article_count


def load_links(cursor, data_dir: Path, title_to_id: dict, lang_code: str):
    """
    Load links with source resolution and batch debugging info.

    Args:
        cursor: Database cursor
        data_dir: Directory containing processed_batches_pl
        title_to_id: Pre-built title to ID mapping

    Returns:
        Tuple of (links_loaded, unresolved_sources)
    """
    print("Loading links with source resolution...")

    links_files = sorted(glob.glob(str(data_dir / 'links_batch_*.csv.gz')))
    if not links_files:
        raise FileNotFoundError(f"No links files found in {data_dir}")

    links_count = 0
    unresolved_sources = 0

    for file_path in links_files:
        file_path_obj = Path(file_path)
        print(f"  Processing {file_path_obj.name}...")

        # Extract batch number from filename for debugging
        try:
            batch_num = int(file_path_obj.stem.split('_')[-1])
        except (ValueError, IndexError):
            batch_num = 0  # Fallback

        with gzip.open(file_path, 'rt', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            batch_links = []

            for row in reader:
                if len(row) != 2:
                    continue  # Skip malformed rows

                source_title, target_title = row

                # Resolve source title to ID
                source_id = title_to_id.get(source_title)
                if source_id is None:
                    unresolved_sources += 1
                    continue  # Skip links from non-existent articles

                # Add to batch: (source_id, target_title, lang_code, batch_num)
                batch_links.append((source_id, target_title, lang_code, batch_num))

                # Commit in batches for performance
                if len(batch_links) >= 50000:
                    cursor.executemany('''
                        INSERT INTO links (source_id, target_title, language, batch_num)
                        VALUES (?, ?, ?, ?)
                    ''', batch_links)
                    links_count += len(batch_links)
                    batch_links = []

            # Insert remaining links from this file
            if batch_links:
                cursor.executemany('''
                    INSERT INTO links (source_id, target_title, language, batch_num)
                    VALUES (?, ?, ?, ?)
                ''', batch_links)
                links_count += len(batch_links)

        # Commit after each file
        cursor.connection.commit()
        print(f"    {links_count:,} total links processed")

    print(f"✓ Loaded {links_count:,} links")
    if unresolved_sources > 0:
        print(f"⚠️  Skipped {unresolved_sources:,} links (source article not found)")

    return links_count, unresolved_sources


def update_metadata(cursor, article_count: int, links_count: int, lang_code: str):
    """Update metadata table with final counts."""
    print("Updating metadata...")

    cursor.execute('''
        INSERT OR REPLACE INTO metadata (key, value)
        VALUES (?, ?), (?, ?)
    ''', (f'{lang_code}_article_count', article_count, f'{lang_code}_link_count', links_count))

    cursor.connection.commit()
    print("✓ Metadata updated")


def verify_database(cursor, lang_code: str):
    """Run verification queries on loaded data."""
    print("\n" + "=" * 60)
    print("DATABASE VERIFICATION")
    print("=" * 60)

    # Count articles
    cursor.execute("SELECT COUNT(*) FROM articles WHERE language=?", (lang_code,))
    final_articles = cursor.fetchone()[0]
    print(f"Articles in database: {final_articles:,}")

    # Count links
    cursor.execute("SELECT COUNT(*) FROM links WHERE language=?", (lang_code,))
    final_links = cursor.fetchone()[0]
    print(f"Links in database: {final_links:,}")

    # Sample connections
    cursor.execute('''
        SELECT a.title, l.target_title
        FROM articles a
        JOIN links l ON a.id = l.source_id
        WHERE a.language=?
        LIMIT 5
    ''', (lang_code,))
    samples = cursor.fetchall()

    print("Sample connections:")
    for i, (src, tgt) in enumerate(samples, 1):
        print(f"  {i}. {src} → {tgt}")

    return final_articles, final_links


def main():
    """Main data loading execution."""
    import argparse

    parser = argparse.ArgumentParser(description='Load Multi-Language Wikipedia Data')
    parser.add_argument('--lang', type=str, default='pl',
                       help='Language code (e.g., pl, en) (default: pl)')

    args = parser.parse_args()

    # Get language configuration
    try:
        from config.language_manager import LanguageManager
        lang_config = LanguageManager.get_language_info(args.lang)
    except Exception as e:
        print(f"❌ ERROR: Failed to load configuration for language '{args.lang}': {e}")
        return

    print("=" * 70)
    print(f"LOADING {lang_config['name'].upper()} WIKIPEDIA INTO MULTI-LANGUAGE DATABASE")
    print("=" * 70)

    # Setup paths
    base_dir = Path('/mnt/c/Users/PC/WikiGraph')
    db_path = base_dir / 'databases' / 'wikigraph_multilang.db'
    data_dir = base_dir / f'processed_batches_{args.lang}'

    print(f"Database: {db_path}")
    print(f"Data directory: {data_dir}")
    print()

    # Verify inputs exist
    if not db_path.exists():
        print(f"❌ ERROR: Database not found: {db_path}")
        sys.exit(1)

    if not data_dir.exists():
        print(f"❌ ERROR: Data directory not found: {data_dir}")
        sys.exit(1)

    # Connect to database
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Apply performance optimizations
        setup_database_optimizations(cursor)

        # Drop indexes for faster bulk loading
        drop_indexes_for_bulk_load(cursor)

        # Initialize title mapping (will use ~300-500MB for 2.26M articles)
        title_to_id = {}

        # Phase 1: Load articles
        article_count = load_articles(cursor, data_dir, title_to_id)

        # Phase 2: Load links
        links_count, unresolved = load_links(cursor, data_dir, title_to_id, args.lang)

        # Recreate indexes and restore safety settings
        recreate_indexes_and_safety(cursor)

        # Update metadata
        update_metadata(cursor, article_count, links_count, args.lang)

        # Verification
        final_articles, final_links = verify_database(cursor, args.lang)

        print("\n" + "=" * 70)
        print(f"SUCCESS: {lang_config['name']} Wikipedia loaded into multi-language database!")
        print("=" * 70)
        print(f"Articles: {final_articles:,}")
        print(f"Links: {final_links:,}")
        print(f"Database size: ~{db_path.stat().st_size / 1024 / 1024 / 1024:.1f}GB")
        print("\nReady for Phase 3: API development and multi-language expansion")

    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        if 'conn' in locals():
            conn.rollback()
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    main()
