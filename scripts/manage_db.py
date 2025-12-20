#!/usr/bin/env python3
"""
WikiGraph Database Management Utility

Provides a unified interface for database initialization, maintenance,
and statistics.
"""

import argparse
import sys
import logging
from pathlib import Path

# Add project root to path so we can import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.models import create_base_schema, initialize_fts_tables, get_db_connection
from config.language_manager import LanguageManager

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def cmd_init(args):
    """Initialize the base database schema."""
    logger.info(f"Initializing database at: {args.db_path or 'default'}")
    create_base_schema(args.db_path)
    print("✅ Base schema initialized.")

def cmd_fts(args):
    """Initialize or update FTS tables."""
    logger.info(f"Initializing FTS tables for: {args.lang or 'all languages'}")
    initialize_fts_tables(args.db_path)
    print("✅ FTS tables initialized.")

def cmd_stats(args):
    """Show database statistics."""
    with get_db_connection(args.db_path) as conn:
        cursor = conn.cursor()
        
        print("\n" + "="*40)
        print("WIKIGRAPH DATABASE STATISTICS")
        print("="*40)
        
        # Schema version
        cursor.execute("SELECT value FROM metadata WHERE key='schema_version'")
        version = cursor.fetchone()
        print(f"Schema Version: {version[0] if version else 'Unknown'}")
        
        # Available languages
        langs = LanguageManager.list_available_languages()
        print(f"Configured Languages: {', '.join(langs)}")
        
        print("\nContent Breakdown:")
        print(f"{'Language':<10} | {'Articles':<12} | {'Links':<12}")
        print("-" * 40)
        
        for lang in langs:
            try:
                cursor.execute("SELECT COUNT(*) FROM articles WHERE language=?", (lang,))
                article_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM links WHERE language=?", (lang,))
                link_count = cursor.fetchone()[0]
                
                print(f"{lang:<10} | {article_count:<12,} | {link_count:<12,}")
            except sqlite3.OperationalError:
                print(f"{lang:<10} | {'Table Error':<12} | {'Table Error':<12}")
        
        try:
            cursor.execute("SELECT COUNT(*) FROM articles")
            total_articles = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM links")
            total_links = cursor.fetchone()[0]
            
            print("-" * 40)
            print(f"{'TOTAL':<10} | {total_articles:<12,} | {total_links:<12,}")
        except sqlite3.OperationalError:
            print("-" * 40)
            print(f"{'TOTAL':<10} | {'N/A':<12} | {'N/A':<12}")
            
        print("="*40 + "\n")

def main():
    parser = argparse.ArgumentParser(description="WikiGraph Database Management")
    parser.add_argument("--db-path", type=Path, help="Path to SQLite database")
    
    subparsers = parser.add_subparsers(dest="command", help="Management commands")
    
    # Init command
    subparsers.add_parser("init", help="Initialize base schema")
    
    # FTS command
    fts_parser = subparsers.add_parser("init-fts", help="Initialize/update FTS tables")
    fts_parser.add_argument("--lang", help="Specific language to index")
    
    # Stats command
    subparsers.add_parser("stats", help="Show database statistics")
    
    args = parser.parse_args()
    
    if args.command == "init":
        cmd_init(args)
    elif args.command == "init-fts":
        cmd_fts(args)
    elif args.command == "stats":
        cmd_stats(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
