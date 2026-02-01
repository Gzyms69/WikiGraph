import sys
import os
import sqlite3
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.getcwd())

from core.pipeline.prepare_neo4j_csv import load_mappings

def verify_logic(lang):
    print(f"Verifying CSV Generation Logic for {lang.upper()}...")
    db_path = Path(f"data/db/{lang}.db")
    
    # 1. Get expected count from SQLite (Must have QID)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) 
        FROM pages p 
        JOIN id_mapping m ON p.page_id = m.page_id
        WHERE p.namespace = 0 AND p.is_redirect = 0
    """)
    expected_count = cur.fetchone()[0]
    conn.close()
    print(f"Expected Canonical Articles: {expected_count}")
    
    # 2. Run load_mappings
    id_map, _ = load_mappings(db_path)
    actual_count = len(id_map)
    print(f"Actual Mapped Nodes: {actual_count}")
    
    if expected_count == actual_count:
        print("✅ SUCCESS: Counts match perfectly.")
    else:
        print(f"❌ FAILURE: Mismatch (Diff: {actual_count - expected_count})")
        sys.exit(1)

if __name__ == "__main__":
    verify_logic("pl")
