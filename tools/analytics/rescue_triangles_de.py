import sqlite3
from neo4j import GraphDatabase
import time

URI = "bolt://localhost:7688"
AUTH = ("neo4j", "wikigraph")
DB_PATH = "data/db/de.db"
BATCH_SIZE = 10000

def rescue_triangles():
    print("🚀 Starting Triangle Count Rescue (DE)...")
    
    driver = GraphDatabase.driver(URI, auth=AUTH)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    count = 0
    buffer = []
    
    try:
        with driver.session() as session:
            # Check if property exists
            check = session.run("MATCH (n:Concept) WHERE n.temp_triangle_count IS NOT NULL RETURN count(n) as c").single()['c']
            print(f"   Found {check} nodes with Triangle Count.")
            
            if check == 0:
                print("   No data found. Computation likely failed or is still running.")
                return

            query = """
            MATCH (n:Concept)
            WHERE n.temp_triangle_count IS NOT NULL
            RETURN n.qid as qid, n.temp_triangle_count as val
            """
            result = session.run(query)
            
            print("   Streaming...")
            for record in result:
                buffer.append((record['qid'], 'triangle_count', record['val']))
                count += 1
                
                if len(buffer) >= BATCH_SIZE:
                    cursor.executemany(
                        "INSERT OR REPLACE INTO node_metrics (qid, metric_key, metric_value) VALUES (?, ?, ?)",
                        buffer
                    )
                    conn.commit()
                    buffer = []
                    if count % 100000 == 0:
                        print(f"   Saved {count}...")
            
            if buffer:
                cursor.executemany(
                    "INSERT OR REPLACE INTO node_metrics (qid, metric_key, metric_value) VALUES (?, ?, ?)",
                    buffer
                )
                conn.commit()
                
        print(f"✅ Rescue Complete. Saved {count} records.")
        
        # Cleanup
        print("🧹 Cleaning up...")
        with driver.session() as session:
            session.run("MATCH (n:Concept) REMOVE n.temp_triangle_count")
            
    finally:
        driver.close()
        conn.close()

if __name__ == "__main__":
    rescue_triangles()
