import argparse
import asyncio
import sqlite3
import logging
import time
from app.services.neo4j_manager import Neo4jManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RedirectCleanup")

async def get_redirect_qids(lang):
    """Fetch QIDs of redirects from SQLite"""
    logger.info(f"Fetching redirect QIDs from SQLite ({lang.upper()})...")
    conn = sqlite3.connect(f"data/db/{lang}.db")
    cur = conn.cursor()
    
    # Select QIDs where page is a redirect in main namespace (0)
    query = """
        SELECT m.qid 
        FROM pages p 
        JOIN id_mapping m ON p.page_id = m.page_id 
        WHERE p.namespace = 0 AND p.is_redirect = 1
    """
    try:
        cur.execute(query)
        qids = set(row[0] for row in cur.fetchall())
        logger.info(f"Found {len(qids)} redirect QIDs in SQLite.")
        return qids
    finally:
        conn.close()

async def cleanup(lang, batch_size=1000, dry_run=True):
    manager = Neo4jManager()
    
    try:
        # 1. Get Initial Count
        count_res = await manager.query(lang, "MATCH (n:Concept) RETURN count(n) as total")
        initial_count = count_res[0]["total"]
        logger.info(f"Initial Neo4j Node Count: {initial_count}")
        
        # 2. Get Redirect Candidates
        redirect_qids = await get_redirect_qids(lang)
        
        candidates = list(redirect_qids)
        logger.info(f"Processing {len(candidates)} candidates for deletion...")
        
        if dry_run:
            logger.info("--- DRY RUN MODE ---")
            # Verify a sample exist in Neo4j
            sample = candidates[:10]
            query = "MATCH (n:Concept) WHERE n.qid IN $qids RETURN n.qid"
            res = await manager.query(lang, query, {"qids": sample})
            found = [r["n.qid"] for r in res]
            logger.info(f"Sample Check: {len(found)}/{len(sample)} of sample candidates found in Neo4j.")
            logger.info(f"Would delete ~{len(candidates)} nodes (if they all exist in graph).")
            return

        # 4. Execute Deletion
        logger.info("--- EXECUTION MODE ---")
        total_deleted = 0
        
        for i in range(0, len(candidates), batch_size):
            batch = candidates[i:i + batch_size]
            
            # Query to delete nodes in this batch
            query = """
            UNWIND $qids as qid
            MATCH (n:Concept {qid: qid})
            DETACH DELETE n
            RETURN count(*) as deleted
            """
            
            res = await manager.query(lang, query, {"qids": batch})
            deleted = res[0]["deleted"] if res else 0
            total_deleted += deleted
            
            if (i // batch_size) % 5 == 0:
                logger.info(f"Batch {(i // batch_size) + 1}: Deleted {deleted} nodes (Total: {total_deleted})")
        
        logger.info(f"Cleanup Complete. Total Deleted: {total_deleted}")
        
        # 5. Final Verification
        count_res = await manager.query(lang, "MATCH (n:Concept) RETURN count(n) as total")
        final_count = count_res[0]["total"]
        logger.info(f"Final Neo4j Node Count: {final_count}")
        logger.info(f"Delta: {initial_count - final_count}")

    finally:
        manager.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch-size", type=int, default=1000)
    
    args = parser.parse_args()
    asyncio.run(cleanup(args.lang, args.batch_size, args.dry_run))
