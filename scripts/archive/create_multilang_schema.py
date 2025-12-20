#!/usr/bin/env python3
"""
Multi-Language Database Schema Creation

Creates SQLite tables with language support for the WikiGraph knowledge base.
Supports multiple languages in a single database with proper indexing.
"""

import sqlite3
import sys
from pathlib import Path


def create_multilang_schema(db_path: Path):
    """
    Create multi-language database schema.

    Args:
        db_path: Path to SQLite database file
    """
    print(f"Creating multi-language database schema at: {db_path}")

    # Ensure database directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        # Articles table with language support
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER NOT NULL,
                language TEXT NOT NULL DEFAULT 'pl',
                title TEXT NOT NULL,
                revision_id INTEGER,
                timestamp TEXT,
                infobox TEXT,
                categories TEXT,
                word_count INTEGER,
                text_length INTEGER,
                PRIMARY KEY (id, language)
            )
        ''')

        # Links table with language support
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS links (
                source_id INTEGER NOT NULL,
                target_title TEXT NOT NULL,
                language TEXT NOT NULL DEFAULT 'pl',
                batch_num INTEGER,
                FOREIGN KEY (source_id, language)
                REFERENCES articles(id, language)
            )
        ''')

        # Create indexes for performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_articles_lang_title
            ON articles(language, title)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_articles_title
            ON articles(title)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_links_lang_target
            ON links(language, target_title)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_links_source
            ON links(source_id, language)
        ''')

        # Create metadata table for tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        # Insert schema version
        cursor.execute('''
            INSERT OR REPLACE INTO metadata (key, value)
            VALUES ('schema_version', '1.0-multilang')
        ''')

        cursor.execute('''
            INSERT OR REPLACE INTO metadata (key, value)
            VALUES ('created_at', datetime('now'))
        ''')

        conn.commit()
        print("✅ Database schema created successfully")
        print("✅ Multi-language support enabled")
        print("✅ Indexes created for performance")

        # Verify schema
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"✅ Created tables: {[t[0] for t in tables]}")

        cursor.execute("SELECT COUNT(*) FROM metadata")
        meta_count = cursor.fetchone()[0]
        print(f"✅ Metadata records: {meta_count}")

    except Exception as e:
        print(f"❌ Error creating schema: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def verify_schema(db_path: Path):
    """Verify the database schema is correct."""
    print(f"\nVerifying schema at: {db_path}")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        required_tables = ['articles', 'links', 'metadata']

        for table in required_tables:
            if table not in tables:
                print(f"❌ Missing table: {table}")
                return False
            else:
                print(f"✅ Table exists: {table}")

        # Check indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [i[0] for i in cursor.fetchall()]
        required_indexes = ['idx_articles_lang_title', 'idx_articles_title',
                          'idx_links_lang_target', 'idx_links_source']

        for index in required_indexes:
            if index not in indexes:
                print(f"❌ Missing index: {index}")
                return False
            else:
                print(f"✅ Index exists: {index}")

        # Check metadata
        cursor.execute("SELECT value FROM metadata WHERE key='schema_version'")
        version = cursor.fetchone()
        if version and version[0] == '1.0-multilang':
            print("✅ Schema version: 1.0-multilang")
        else:
            print("❌ Incorrect schema version")
            return False

        print("✅ Schema verification complete")
        return True

    except Exception as e:
        print(f"❌ Error verifying schema: {e}")
        return False
    finally:
        conn.close()


def main():
    """Main execution."""
    print("=" * 60)
    print("WIKIGRAPH MULTI-LANGUAGE DATABASE SCHEMA CREATION")
    print("=" * 60)

    base_dir = Path('/mnt/c/Users/PC/WikiGraph')
    db_path = base_dir / 'databases' / 'wikigraph_multilang.db'

    print(f"Database path: {db_path}")
    print()

    try:
        # Create schema
        create_multilang_schema(db_path)

        # Verify schema
        if verify_schema(db_path):
            print("\n" + "=" * 60)
            print("SUCCESS: Multi-language database ready!")
            print("=" * 60)
            print(f"Database: {db_path}")
            print("Features:")
            print("  • Multi-language article storage")
            print("  • Composite primary keys (id, language)")
            print("  • Optimized indexes for queries")
            print("  • Metadata tracking")
            print("\nReady for Phase 2: Database loading")
        else:
            print("\n❌ Schema verification failed")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
