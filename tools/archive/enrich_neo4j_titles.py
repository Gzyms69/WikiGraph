import asyncio
import sqlite3
from app.services.neo4j_manager import Neo4jManager
from typing import List, Tuple
import time

async def enrich_neo4j_with_titles(lang: str, manager: Neo4jManager):
    print(f"\n{'='*60}")
    print(f"ENRICHING NEO4J {lang.upper()} WITH TITLES")
    print(f"{'='*60}")
    
    db_path = f"data/db/{'pl' if lang == 'pl' else 'de'}.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Create Index for performance
    await manager.query(lang, "CREATE INDEX concept_qid IF NOT EXISTS FOR (n:Concept) ON (n.qid)")
    
    batch_size = 10000
    offset = 0
    total_updated = 0
    start_time = time.time()
    
    while True:
        # Join with id_mapping to get QID
        cur.execute("""
            SELECT m.qid, p.title 
            FROM pages p
            JOIN id_mapping m ON p.page_id = m.page_id
            WHERE p.title IS NOT NULL AND p.title != ''
            LIMIT ? OFFSET ?
        """, (batch_size, offset))
        
        batch = cur.fetchall()
        if not batch:
            break
            
        qid_title_pairs = [{"qid": row['qid'], "title": row['title']} for row in batch]
        
        # Neo4j sub-batches
        for i in range(0, len(qid_title_pairs), 2000):
            sub_batch = qid_title_pairs[i:i+2000]
            
            query = """
            UNWIND $pairs AS pair
            MATCH (n:Concept {qid: pair.qid})
            SET n.title = pair.title
            RETURN count(n) as updated
            """
            
            try:
                result = await manager.query(lang, query, {"pairs": sub_batch})
                updated = result[0]["updated"] if result else 0
                total_updated += updated
            except Exception as e:
                print(f"  ❌ Error in batch {offset}: {e}")
        
        if offset > 0 and offset % 100000 == 0:
            print(f"  Processed {offset} rows... (Total Updated: {total_updated:,})")
            
        offset += batch_size
    
    conn.close()
    
    duration = time.time() - start_time
    print(f"\n✅ COMPLETED {lang.upper()}: Updated {total_updated:,} nodes in {duration:.2f} seconds")

async def main():
    print("NEO4J TITLE ENRICHMENT")
    manager = Neo4jManager()
    try:
        for lang in ["pl", "de"]:
            await enrich_neo4j_with_titles(lang, manager)
    finally:
        manager.close()

if __name__ == "__main__":
    asyncio.run(main())