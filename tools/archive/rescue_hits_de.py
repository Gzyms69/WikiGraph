import sqlite3
from neo4j import GraphDatabase
import time

URI = "bolt://localhost:7688"
AUTH = ("neo4j", "wikigraph")
DB_PATH = "data/db/de.db"
BATCH_SIZE = 10000

def rescue_hits():
    print("🚀 Starting HITS Data Rescue (DE)...")
    
    # Connect
    driver = GraphDatabase.driver(URI, auth=AUTH)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    count = 0
    buffer = []
    start_time = time.time()
    
    try:
        with driver.session() as session:
            # 1. Fetch using the discovered property name
            query = """
            MATCH (n:Concept)
            WHERE n.authtemp_auth_score IS NOT NULL
            RETURN n.qid as qid, n.authtemp_auth_score as score
            """
            result = session.run(query)
            
            print("   Streaming data from Neo4j...")
            for record in result:
                buffer.append((record['qid'], 'auth_score', record['score']))
                count += 1
                
                if len(buffer) >= BATCH_SIZE:
                    cursor.executemany(
                        "INSERT OR REPLACE INTO node_metrics (qid, metric_key, metric_value) VALUES (?, ?, ?)",
                        buffer
                    )
                    conn.commit()
                    buffer = []
                    if count % 100000 == 0:
                        print(f"   Saved {count} records...")
            
            # Final flush
            if buffer:
                cursor.executemany(
                    "INSERT OR REPLACE INTO node_metrics (qid, metric_key, metric_value) VALUES (?, ?, ?)",
                    buffer
                )
                conn.commit()
                
        print(f"✅ HITS Rescue Complete. Saved {count} scores in {time.time() - start_time:.1f}s.")
        
        # 2. Cleanup
        print("🧹 Cleaning up Neo4j properties...")
        with driver.session() as session:
            session.run("MATCH (n:Concept) REMOVE n.authtemp_auth_score, n.hubtemp_auth_score")
        print("✅ Cleanup complete.")
        
    finally:
        driver.close()
        conn.close()

if __name__ == "__main__":
    rescue_hits()
