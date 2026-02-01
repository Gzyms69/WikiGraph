import asyncio
import sqlite3
import argparse
from app.services.neo4j_manager import Neo4jManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DegreeCompute")

async def compute_degrees_to_sqlite(lang: str, limit: int = None):
    logger.info(f"Computing degrees for {lang.upper()} (Limit: {limit})...")
    
    manager = Neo4jManager()
    sqlite_path = f"data/db/{lang}.db"
    conn = sqlite3.connect(sqlite_path)
    cur = conn.cursor()
    
    # We fetch degree from Neo4j and UPDATE SQLite
    limit_clause = f"LIMIT {limit}" if limit else ""
    
    # Using simple MATCH for the test batch. For full migration, we'd use apoc.periodic.iterate logic or batching.
    query = f"""
    MATCH (n:Concept)
    WITH n, count{{(n)-[:LINKS_TO]->()}} as out_d, count{{(n)<-[:LINKS_TO]-()}} as in_d
    RETURN n.qid as qid, out_d, in_d
    {limit_clause}
    """
    
    try:
        results = await manager.query(lang, query)
        if not results:
            logger.warning("No results from Neo4j.")
            return 0
            
        logger.info(f"Fetched {len(results)} rows from Neo4j. Updating SQLite...")
        
        updated_count = 0
        batch = []
        for row in results:
            batch.append((row['out_d'], row['in_d'], row['qid']))
            
            if len(batch) >= 1000:
                cur.executemany("""
                    UPDATE pages 
                    SET out_degree = ?, in_degree = ? 
                    WHERE page_id = (SELECT page_id FROM id_mapping WHERE qid = ?)
                """, batch)
                updated_count += len(batch)
                batch = []
                
        if batch:
            cur.executemany("""
                UPDATE pages 
                SET out_degree = ?, in_degree = ? 
                WHERE page_id = (SELECT page_id FROM id_mapping WHERE qid = ?)
            """, batch)
            updated_count += len(batch)
            
        conn.commit()
        logger.info(f"Updated {updated_count} rows in SQLite.")
        return updated_count

    except Exception as e:
        logger.error(f"Error: {e}")
        return 0
    finally:
        conn.close()
        manager.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", required=True)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    
    asyncio.run(compute_degrees_to_sqlite(args.lang, args.limit))
