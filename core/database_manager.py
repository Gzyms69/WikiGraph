#!/usr/bin/env python3
"""
CORE: DATABASE MANAGER
Unified utility for DB initialization, FTS search indexing, and stats.
"""

import argparse
import sys
import logging
import sqlite3
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.models import create_base_schema, initialize_fts_tables, get_db_connection
from config.language_manager import LanguageManager

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def cmd_init(args):
    db_path = args.db_path or (Path(__file__).parent.parent / "data" / "db" / "wikigraph_multilang.db")
    logger.info(f"Initializing database at: {db_path}")
    create_base_schema(db_path)
    print("✅ Base schema initialized.")

def cmd_fts(args):
    db_path = args.db_path or (Path(__file__).parent.parent / "data" / "db" / "wikigraph_multilang.db")
    logger.info(f"Initializing FTS tables...")
    initialize_fts_tables(db_path)
    print("✅ FTS tables initialized.")

def cmd_stats(args):
    db_path = args.db_path or (Path(__file__).parent.parent / "data" / "db" / "wikigraph_multilang.db")
    if not db_path.exists():
        print(f"❌ ERROR: Database not found at {db_path}")
        return

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        print("\n" + "="*40)
        print("WIKIGRAPH DATABASE STATISTICS")
        print("="*40)
        
        try: cursor.execute("SELECT value FROM metadata WHERE key='schema_version'")
        except: print("Schema Version: Unknown")
        else: print(f"Schema Version: {cursor.fetchone()[0]}")
        
        langs = LanguageManager.list_available_languages()
        print(f"Configured Languages: {', '.join(langs)}")
        print("\nContent Breakdown:")
        print(f"{'Language':<10} | {'Articles':<12} | {'Links':<12}")
        print("-" * 40)
        
        for lang in langs:
            try:
                a = cursor.execute("SELECT COUNT(*) FROM articles WHERE language=?", (lang,)).fetchone()[0]
                l = cursor.execute("SELECT COUNT(*) FROM links WHERE language=?", (lang,)).fetchone()[0]
                print(f"{lang:<10} | {a:<12,} | {l:<12,}")
            except: print(f"{lang:<10} | {'Error':<12} | {'Error':<12}")
        print("="*40 + "\n")

def main():
    parser = argparse.ArgumentParser(description="WikiGraph Database Management")
    parser.add_argument("--db-path", type=Path, help="Override DB path")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("init")
    subparsers.add_parser("init-fts")
    subparsers.add_parser("stats")
    
    args = parser.parse_args()
    if args.command == "init": cmd_init(args)
    elif args.command == "init-fts": cmd_fts(args)
    elif args.command == "stats": cmd_stats(args)
    else: parser.print_help()

if __name__ == "__main__":
    main()