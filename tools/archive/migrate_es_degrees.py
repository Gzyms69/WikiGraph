import sqlite3
from neo4j import GraphDatabase
import time

URI = "bolt://localhost:7757"
AUTH = ("neo4j", "wikigraph")
DB_PATH = "data/db/es.db"
BATCH_SIZE = 50000

def migrate_degrees():
    print("🚀 Migrating Spanish Degrees (Neo4j -> SQLite)...")
    driver = GraphDatabase.driver(URI, auth=AUTH)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    count = 0
    buffer = []
    
    with driver.session() as session:
        # We compute both in and out degree
        query = """
        MATCH (n:Concept)
        RETURN n.qid as qid, 
               COUNT { (n)-->() } as out_d,
               COUNT { (n)<--() } as in_d
        """
        result = session.run(query)
        
        for record in result:
            buffer.append((record['out_d'], record['in_d'], record['qid']))
            count += 1
            
            if len(buffer) >= BATCH_SIZE:
                cursor.executemany(
                    "UPDATE pages SET out_degree = ?, in_degree = ? WHERE page_id = (SELECT page_id FROM id_mapping WHERE qid = ?)",
                    buffer
                )
                conn.commit()
                buffer = []
                print(f"   Processed {count} nodes...")

        if buffer:
            cursor.executemany(
                "UPDATE pages SET out_degree = ?, in_degree = ? WHERE page_id = (SELECT page_id FROM id_mapping WHERE qid = ?)",
                buffer
            )
            conn.commit()

    print(f"✅ Migration Complete. Updated {count} nodes.")
    driver.close()
    conn.close()

if __name__ == "__main__":
    migrate_degrees()
