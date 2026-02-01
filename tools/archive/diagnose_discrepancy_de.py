import sqlite3
import os
import sys
from pathlib import Path

def run_diagnostics(lang="de"):
    print(f"=== Gate 5B.4.7 Diagnostics ({lang.upper()}) ===")
    
    db_path = f"data/db/{lang}.db"
    if not os.path.exists(db_path):
        print(f"❌ Error: {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 1. Pipeline Simulation
    print(f"\n--- 1. Pipeline Simulation (SQLite {lang.upper()}) ---")
    query_simulation = """
        SELECT COUNT(*)
        FROM pages p 
        JOIN id_mapping m ON p.page_id = m.page_id
        WHERE p.namespace = 0 AND p.is_redirect = 0
    """
    cur.execute(query_simulation)
    simulated_count = cur.fetchone()[0]
    print(f"Simulated Neo4j Node Count (via JOIN): {simulated_count:,}")

    cur.execute("SELECT COUNT(*) FROM pages WHERE namespace = 0 AND is_redirect = 0")
    canonical_count = cur.fetchone()[0]
    print(f"SQLite Canonical Article Count (pages table only): {canonical_count:,}")
    
    discrepancy = canonical_count - simulated_count
    print(f"Discrepancy (Canonical - Simulated): {discrepancy:,}")

    # 2. Deep Sample of "Missing" Nodes
    print("\n--- 2. Missing Node Sample (Articles without QIDs) ---")
    query_missing = """
        SELECT p.page_id, p.title, p.is_redirect
        FROM pages p
        LEFT JOIN id_mapping m ON p.page_id = m.page_id
        WHERE p.namespace = 0
          AND p.is_redirect = 0
          AND m.qid IS NULL
        LIMIT 5
    """
    cur.execute(query_missing)
    rows = cur.fetchall()
    if rows:
        for i, row in enumerate(rows, 1):
            print(f"  {i}. ID: {row[0]}, Title: '{row[1]}', Redirect: {row[2]}")

    # 3. Infobox Verification
    print("\n--- 3. Infobox Verification ---")
    cur.execute("PRAGMA table_info(pages)")
    columns = cur.fetchall()
    infobox_col = next((col for col in columns if col[1] == 'infobox'), None)
    if infobox_col:
        print(f"Column 'infobox' found. Type: {infobox_col[2]}")
    cur.execute("SELECT COUNT(*) FROM pages WHERE infobox IS NOT NULL")
    print(f"Non-NULL Infobox Count: {cur.fetchone()[0]}")

    conn.close()

if __name__ == "__main__":
    run_diagnostics("de")
