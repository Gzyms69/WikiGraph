import sqlite3
from pathlib import Path

def add_column(db_path):
    name = Path(db_path).name
    print(f"Checking {name}...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    try:
        # We use JSON affinity for SQLite
        cur.execute("ALTER TABLE pages ADD COLUMN infobox JSON")
        conn.commit()
        print(f"✅ [{name}] Added 'infobox' column.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"ℹ️  [{name}] Column 'infobox' already exists.")
        else:
            print(f"❌ [{name}] Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    dbs = ["data/db/pl.db", "data/db/de.db"]
    for db in dbs:
        if Path(db).exists():
            add_column(db)
        else:
            print(f"⚠️  Database not found: {db}")
