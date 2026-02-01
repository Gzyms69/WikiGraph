import sqlite3
import os

def analyze_sqlite(db_path, lang):
    print(f"\n{'='*60}")
    print(f"SQLITE ANALYSIS: {lang.upper()} ({db_path})")
    print(f"{'='*60}")
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # List all tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = cur.fetchall()
    
    print(f"\n📋 TABLES ({len(tables)} total):")
    for (table_name,) in tables:
        try:
            # Get row count
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cur.fetchone()[0]
            
            # Get schema
            cur.execute(f"PRAGMA table_info({table_name})")
            columns = cur.fetchall()
            
            print(f"  └─ {table_name} ({row_count:,} rows)")
            for col in columns:
                col_id, col_name, col_type, notnull, default, pk = col
                print(f"     ├─ {col_name}: {col_type} {'PRIMARY' if pk else ''}")
        except Exception as e:
            print(f"  └─ {table_name}: Error analyzing - {e}")
    
    # Check for edges-like tables
    print(f"\n🔍 EDGE-RELATED TABLES:")
    edge_tables = []
    for (table_name,) in tables:
        if any(keyword in table_name.lower() for keyword in ['edge', 'link', 'pagelink', 'pl_']):
            edge_tables.append(table_name)
    
    if edge_tables:
        for table in edge_tables:
            print(f"  └─ {table}")
            try:
                cur.execute(f"SELECT * FROM {table} LIMIT 3")
                sample = cur.fetchall()
                print(f"     Sample rows: {sample}")
            except Exception as e:
                print(f"     Error reading sample: {e}")
    else:
        print("  └─ NO edge-related tables found")
    
    conn.close()

if __name__ == "__main__":
    analyze_sqlite("data/db/pl.db", "Polish")
    analyze_sqlite("data/db/de.db", "German")
