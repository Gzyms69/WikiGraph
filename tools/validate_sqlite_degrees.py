import asyncio
import sqlite3
import argparse
from app.services.neo4j_manager import Neo4jManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Validation")

async def validate(lang: str):
    manager = Neo4jManager()
    sqlite_path = f"data/db/{lang}.db"
    conn = sqlite3.connect(f"file:{sqlite_path}?mode=ro", uri=True)
    cur = conn.cursor()
    
    try:
        print(f"Validating {lang}...")
        
        # 1. Check if ANY rows updated
        cur.execute("SELECT count(*) FROM pages WHERE out_degree > 0 OR in_degree > 0")
        updated_count = cur.fetchone()[0]
        print(f"Rows with non-zero degree in SQLite: {updated_count}")
        
        if updated_count == 0:
            print("⚠️ No degrees found. Did the update run?")
            return

        # 2. Sample Validation
        cur.execute("""
            SELECT m.qid, p.out_degree, p.in_degree 
            FROM pages p JOIN id_mapping m ON p.page_id = m.page_id 
            WHERE p.out_degree > 0 OR p.in_degree > 0 
            LIMIT 5
        """)
        samples = cur.fetchall()
        
        matches = 0
        for row in samples:
            qid, sql_out, sql_in = row
            query = f"MATCH (n:Concept {{qid: '{qid}'}}) RETURN count{{(n)-[:LINKS_TO]->()}} as out_d, count{{(n)<-[:LINKS_TO]-()}} as in_d"
            res = await manager.query(lang, query)
            
            if res:
                neo_out = res[0]['out_d']
                neo_in = res[0]['in_d']
                
                if sql_out == neo_out and sql_in == neo_in:
                    matches += 1
                    print(f"  ✅ {qid}: Match (Out: {sql_out}, In: {sql_in})")
                else:
                    print(f"  ❌ {qid}: Mismatch! SQLite({sql_out},{sql_in}) vs Neo4j({neo_out},{neo_in})")
            else:
                print(f"  ❌ {qid}: Not found in Neo4j")
                
    finally:
        conn.close()
        manager.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", required=True)
    args = parser.parse_args()
    asyncio.run(validate(args.lang))
