import sqlite3
import os
import sys
from pathlib import Path

def run_diagnostics():
    print("=== Gate 5B.4.6a Diagnostics ===")
    
    db_path = "data/db/pl.db"
    if not os.path.exists(db_path):
        print(f"❌ Error: {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 1. Pipeline Simulation (Replicating prepare_neo4j_csv.py logic)
    print("\n--- 1. Pipeline Simulation (SQLite) ---")
    # Exact logic from prepare_neo4j_csv.py: JOIN pages and id_mapping, filter NS=0 and is_redirect=0
    # Note: prepare_neo4j_csv.py filters NS=0. It does NOT explicitly include NS=14 (Categories) in the nodes CSV loop seen earlier.
    # The loop was: "for pid, qid in id_map.items(): writer.writerow([qid, 0, "Concept"])"
    # And id_map was populated with "WHERE p.namespace = 0 AND p.is_redirect = 0".
    # So we simulate strict NS=0.
    
    query_simulation = """
        SELECT COUNT(*)
        FROM pages p 
        JOIN id_mapping m ON p.page_id = m.page_id
        WHERE p.namespace = 0 AND p.is_redirect = 0
    """
    cur.execute(query_simulation)
    simulated_count = cur.fetchone()[0]
    print(f"Simulated Neo4j Node Count (via JOIN): {simulated_count:,}")

    # Canonical Count (What we *think* we should have)
    cur.execute("SELECT COUNT(*) FROM pages WHERE namespace = 0 AND is_redirect = 0")
    canonical_count = cur.fetchone()[0]
    print(f"SQLite Canonical Article Count (pages table only): {canonical_count:,}")
    
    discrepancy = canonical_count - simulated_count
    print(f"Discrepancy (Canonical - Simulated): {discrepancy:,}")

    # 2. Deep Sample of "Missing" Nodes
    print("\n--- 2. Missing Node Sample (Articles without QIDs) ---")
    # Finding articles that are in 'pages' but dropped by the JOIN
    query_missing = """
        SELECT p.page_id, p.title, p.is_redirect
        FROM pages p
        LEFT JOIN id_mapping m ON p.page_id = m.page_id
        WHERE p.namespace = 0
          AND p.is_redirect = 0
          AND m.qid IS NULL
        LIMIT 15
    """
    cur.execute(query_missing)
    rows = cur.fetchall()
    if rows:
        for i, row in enumerate(rows, 1):
            print(f"  {i}. ID: {row[0]}, Title: '{row[1]}', Redirect: {row[2]}")
    else:
        print("  No missing nodes found (Sample is empty).")

    # 3. Infobox Verification
    print("\n--- 3. Infobox Verification ---")
    cur.execute("PRAGMA table_info(pages)")
    columns = cur.fetchall()
    infobox_col = next((col for col in columns if col[1] == 'infobox'), None)
    
    if infobox_col:
        print(f"Column 'infobox' found. Type: {infobox_col[2]}")
    else:
        print("❌ Column 'infobox' NOT FOUND.")

    cur.execute("SELECT COUNT(*) FROM pages WHERE infobox IS NOT NULL")
    non_null_count = cur.fetchone()[0]
    print(f"Non-NULL Infobox Count: {non_null_count}")

    conn.close()

    # 4. File Checks
    print("\n--- 4. File Checks ---")
    csv_path = "data/neo4j_bulk/pl/nodes.csv"
    if os.path.exists(csv_path):
        with open(csv_path, 'rb') as f:
            lines = sum(1 for _ in f)
        print(f"Line count of {csv_path}: {lines:,} (Header + Data)")
    else:
        print(f"❌ CSV not found at {csv_path}")

    code_path = "core/tools/prepare_neo4j_csv.py"
    if os.path.exists(code_path):
        print(f"Checking SQL in {code_path}:")
        with open(code_path, 'r') as f:
            for line in f:
                if "SELECT" in line and "FROM" in line:
                    print(f"  Code: {line.strip()}")
                if "WHERE" in line and "namespace" in line:
                    print(f"  Code: {line.strip()}")
    else:
        print(f"❌ Code file not found: {code_path}")

if __name__ == "__main__":
    run_diagnostics()
