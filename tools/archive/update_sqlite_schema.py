import sqlite3
import argparse
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SQLiteUpdate")

def update_schema(db_path: str):
    path = Path(db_path)
    if not path.exists():
        logger.error(f"Database not found: {db_path}")
        return False

    logger.info(f"Updating schema for {db_path}...")
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    
    try:
        # Check if columns exist
        cur.execute("PRAGMA table_info(pages)")
        columns = [row[1] for row in cur.fetchall()]
        
        updated = False
        if "out_degree" not in columns:
            logger.info("Adding out_degree column...")
            cur.execute("ALTER TABLE pages ADD COLUMN out_degree INTEGER DEFAULT 0")
            updated = True
        else:
            logger.info("out_degree column already exists.")

        if "in_degree" not in columns:
            logger.info("Adding in_degree column...")
            cur.execute("ALTER TABLE pages ADD COLUMN in_degree INTEGER DEFAULT 0")
            updated = True
        else:
            logger.info("in_degree column already exists.")
            
        if updated:
            conn.commit()
            logger.info("Schema update committed.")
        else:
            logger.info("Schema already up to date.")
            
        return True
    except Exception as e:
        logger.error(f"Failed to update schema: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", help="Language code (pl/de) or 'all'", default="all")
    args = parser.parse_args()
    
    langs = ["pl", "de"] if args.lang == "all" else [args.lang]
    for lang in langs:
        update_schema(f"data/db/{lang}.db")
