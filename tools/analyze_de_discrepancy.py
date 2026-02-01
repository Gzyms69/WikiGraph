import asyncio
import sqlite3
import sys
import os

# Ensure we can import from app
sys.path.append(os.getcwd())

from app.services.neo4j_manager import Neo4jManager

async def analyze():
    print("=== DATA DISCREPANCY ANALYSIS (DE) ===")
    manager = Neo4jManager()
    
    # 1. Fetch Neo4j QIDs
    print("Fetching Neo4j QIDs...")
    driver = manager.get_driver("de")
    if not driver:
        print("Error: Could not get DE driver")
        return

    try:
        with driver.session() as session:
            result = session.run("MATCH (n:Concept) RETURN n.qid")
            neo4j_qids = set(record["n.qid"] for record in result)
        print(f"Neo4j QIDs count: {len(neo4j_qids)}")
    except Exception as e:
        print(f"Error fetching from Neo4j: {e}")
        return

    # 2. Fetch SQLite QIDs (Articles only)
    print("Fetching SQLite QIDs (NS=0, Non-Redirect)...")
    conn = sqlite3.connect('data/db/de.db')
    cursor = conn.cursor()
    try:
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
    
    print(f"\nQIDs in Neo4j but NOT in SQLite Articles: {len(in_neo4j_only)}")

    # 4. Analyze Sample
    if in_neo4j_only:
        print("\n--- Inspecting Sample of Discrepancies ---")
        sample = in_neo4j_only[:20]
        for qid in sample:
            cursor.execute("""
                SELECT p.title, p.namespace, p.is_redirect
                FROM pages p
                JOIN id_mapping m ON p.page_id = m.page_id
                WHERE m.qid = ?
            """, (qid,))
            row = cursor.fetchone()
            
            if row:
                title, ns, is_red = row
                status = f"Found in SQLite: NS={ns}, Redir={is_red}, Title='{title}'"
            else:
                status = "MISSING from SQLite completely"
            
            print(f"  [{qid}] -> {status}")

    conn.close()
    manager.close()

if __name__ == "__main__":
    asyncio.run(analyze())
