#!/usr/bin/env python3
import sqlite3
import shutil
import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.core.config import settings

def setup_fts(lang: str, revert: bool = False):
    db_path = Path(f"data/db/{lang}.db")
    if not db_path.exists():
        print(f"⚠️  Skipping {lang}: Database file not found at {db_path}")
        return

    if revert:
        print(f"🔄 Reverting FTS for {lang}...")
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("DROP TABLE IF EXISTS articles_fts")
            conn.commit()
            conn.close()
            print(f"✅ Dropped articles_fts table for {lang}.")
            
            # Optional: Restore backup? 
            # The prompt implies "backup before running", likely to restore state if FTS corrupts DB.
            # But "Reversible" usually means "Undo the change". 
            # Dropping the table undoes the change effectively without losing other data updates (if any happened).
            # Restoring the file rolls back EVERYTHING. 
            # I will just drop the table for 'revert' action, but keep the backup file.
        except Exception as e:
            print(f"❌ Failed to revert {lang}: {e}")
        return

    # Backup logic
    backup_path = db_path.with_suffix(".db.bak_fts")
    if not backup_path.exists():
        print(f"💾 Creating backup for {lang} at {backup_path}...")
        try:
            shutil.copy2(db_path, backup_path)
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return
    else:
        print(f"ℹ️  Backup already exists for {lang}, skipping backup.")

    print(f"🚀 Setting up FTS5 for {lang}...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if FTS5 is available
        try:
            cursor.execute("CREATE VIRTUAL TABLE IF NOT EXISTS test_fts USING fts5(x)")
            cursor.execute("DROP TABLE test_fts")
        except sqlite3.OperationalError:
            print(f"❌ FTS5 not supported by this SQLite version. Aborting.")
            return

        # Transactional Setup
        cursor.execute("BEGIN TRANSACTION")
        
        # Clean slate
        cursor.execute("DROP TABLE IF EXISTS articles_fts")
        
        # Create FTS Table
        # We index 'title' for search. 'qid' is stored but unindexed to save space/time (we retrieve it).
        cursor.execute("CREATE VIRTUAL TABLE articles_fts USING fts5(title, qid UNINDEXED)")
        
        # Populate
        print(f"   Populating index (this may take a while)...")
        cursor.execute("""
            INSERT INTO articles_fts(title, qid)
            SELECT p.title, m.qid 
            FROM pages p 
            JOIN id_mapping m ON p.page_id = m.page_id 
            WHERE p.namespace = 0
        """)
        
        rows = cursor.rowcount
        cursor.execute("COMMIT")
        conn.close()
        print(f"✅ FTS setup complete for {lang}. Indexed {rows} articles.")
        
    except Exception as e:
        print(f"❌ FTS setup failed for {lang}: {e}")
        # Try to rollback? SQLite does it on close/error usually if transaction active.

def main():
    parser = argparse.ArgumentParser(description="Setup SQLite FTS5 Search Index")
    parser.add_argument("--lang", help="Specific language code (e.g., pl, de)")
    parser.add_argument("--revert", action="store_true", help="Remove FTS table")
    args = parser.parse_args()

    if args.lang:
        langs = [args.lang]
    else:
        # Auto-detect from settings or file system
        langs = [f.stem for f in Path("data/db").glob("*.db") if not f.name.endswith(".bak_fts")]

    print(f"Targets: {langs}")
    for lang in langs:
        setup_fts(lang, args.revert)

if __name__ == "__main__":
    main()
