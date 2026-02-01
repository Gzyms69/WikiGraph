import asyncio
import sqlite3
import sys
import os

# Ensure we can import from app
sys.path.append(os.getcwd())

from app.services.neo4j_manager import Neo4jManager

async def analyze():
    print("=== DATA DISCREPANCY ANALYSIS (PL) ===")
    manager = Neo4jManager()
    
    # 1. Fetch Neo4j QIDs
    print("Fetching Neo4j QIDs...")
    driver = manager.get_driver("pl")
    if not driver:
        print("Error: Could not get PL driver")
        return

    try:
        with driver.session() as session:
            # Using simple query, fetching all QIDs
            result = session.run("MATCH (n:Concept) RETURN n.qid")
            # Consume all records
            neo4j_qids = set(record["n.qid"] for record in result)
        print(f"Neo4j QIDs count: {len(neo4j_qids)}")
    except Exception as e:
        print(f"Error fetching from Neo4j: {e}")
        return

    # 2. Fetch SQLite QIDs (Articles only)
    print("Fetching SQLite QIDs (NS=0, Non-Redirect)...")
    conn = sqlite3.connect('data/db/pl.db')
    cursor = conn.cursor()
    try:
        # Need to join with id_mapping as pages doesn't have qid
        cursor.execute("""
            SELECT m.qid 
            FROM pages p 
            JOIN id_mapping m ON p.page_id = m.page_id 
            WHERE p.namespace = 0 AND p.is_redirect = 0
        """)
        rows = cursor.fetchall()
        sqlite_qids = set(row[0] for row in rows)
        print(f"SQLite Article QIDs count: {len(sqlite_qids)}")
    except Exception as e:
        print(f"Error fetching from SQLite: {e}")
        conn.close()
        return

    # 3. Compare
    in_neo4j_only = list(neo4j_qids - sqlite_qids)
    in_sqlite_only = list(sqlite_qids - neo4j_qids)
    
    print(f"\nQIDs in Neo4j but NOT in SQLite Articles: {len(in_neo4j_only)}")
    print(f"QIDs in SQLite Articles but NOT in Neo4j: {len(in_sqlite_only)}")

    # 4. Analyze Sample
    if in_neo4j_only:
        print("\n--- Inspecting QIDs present in Neo4j but missing from SQLite 'Articles' ---")
        sample = in_neo4j_only[:10]
        for qid in sample:
            # Check what they actually are in SQLite
            cursor.execute("""
                SELECT p.title, p.namespace, p.is_redirect
                FROM pages p
                JOIN id_mapping m ON p.page_id = m.page_id
                WHERE m.qid = ?
            """, (qid,))
            row = cursor.fetchone()
            
            status = "UNKNOWN"
            if row:
                title, ns, is_red = row
                status = f"Found: NS={ns}, Redir={is_red}, Title='{title}'"
            else:
                status = "Not in SQLite id_mapping/pages"
            
            print(f"  [{qid}] -> {status}")

    conn.close()
    manager.close()

if __name__ == "__main__":
    asyncio.run(analyze())
