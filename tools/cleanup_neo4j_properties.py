import argparse
import asyncio
import time
import random
from app.services.neo4j_manager import Neo4jManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Neo4jCleanup")

class Neo4jCleaner:
    def __init__(self, lang):
        self.lang = lang
        self.manager = Neo4jManager()

    async def backup_properties(self):
        logger.info(f"Backing up properties for {self.lang.upper()}...")
        filename = f"backup_{self.lang}_properties_{int(time.time())}.csv"
        # APOC export query
        query = f"""
        CALL apoc.export.csv.query(
            "MATCH (n:Concept) RETURN n.qid as qid, n.title as title, n.out_degree as out_degree, n.in_degree as in_degree",
            "{filename}",
            {{}}
        )
        """
        try:
            await self.manager.query(self.lang, query)
            logger.info(f"Backup created: {filename} (in container import dir)")
            return True
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False

    async def dry_run(self, sample_size=100):
        logger.info(f"DRY RUN: Checking {sample_size} nodes in {self.lang.upper()}...")
        query = f"""
        MATCH (n:Concept)
        WHERE n.title IS NOT NULL OR n.out_degree IS NOT NULL
        RETURN n.qid, n.title, n.out_degree
        LIMIT {sample_size}
        """
        results = await self.manager.query(self.lang, query)
        logger.info(f"Found {len(results)} candidates for cleanup.")
        if results:
            logger.info(f"Sample: {results[0]}")
        return len(results)

    async def execute_cleanup(self, batch_size=10000):
        logger.info(f"STARTING CLEANUP: {self.lang.upper()} (Batch Size: {batch_size})")
        
        total_cleaned = 0
        start_time = time.time()
        
        while True:
            query = """
            MATCH (n:Concept)
            WHERE n.title IS NOT NULL OR n.out_degree IS NOT NULL
            WITH n LIMIT $limit
            REMOVE n.title, n.out_degree, n.in_degree
            RETURN count(n) as cleaned
            """
            
            try:
                res = await self.manager.query(self.lang, query, {"limit": batch_size})
                cleaned = res[0]["cleaned"]
                
                if cleaned == 0:
                    break
                
                total_cleaned += cleaned
                if total_cleaned % 100000 == 0:
                    logger.info(f"Cleaned {total_cleaned} nodes...")
                    
            except Exception as e:
                logger.error(f"Error in batch: {e}")
                break
        
        duration = time.time() - start_time
        logger.info(f"CLEANUP COMPLETE. Processed {total_cleaned} nodes in {duration:.2f}s.")
        return total_cleaned

    async def verify(self, sample_size=100):
        logger.info("VERIFYING CLEANUP...")
        
        # 1. Check Node Count
        count_query = "MATCH (n:Concept) RETURN count(n) as total"
        res = await self.manager.query(self.lang, count_query)
        total = res[0]["total"]
        logger.info(f"Total Nodes: {total} (Should be unchanged)")
        
        # 2. Check for leftover properties
        query = """
        MATCH (n:Concept)
        WHERE n.title IS NOT NULL OR n.out_degree IS NOT NULL
        RETURN count(n) as leftovers
        """
        res = await self.manager.query(self.lang, query)
        leftovers = res[0]["leftovers"]
        
        if leftovers == 0:
            logger.info("✅ VERIFICATION PASSED: No properties remaining.")
            return True
        else:
            logger.error(f"❌ VERIFICATION FAILED: {leftovers} nodes still have properties.")
            return False

    def close(self):
        self.manager.close()

async def main(args):
    cleaner = Neo4jCleaner(args.lang)
    
    try:
        if args.dry_run:
            await cleaner.dry_run(args.sample)
        elif args.verify:
            await cleaner.verify(args.sample)
        else:
            # Full Execution Flow
            if args.backup:
                if not await cleaner.backup_properties():
                    logger.error("Aborting due to backup failure.")
                    return
            
            await cleaner.execute_cleanup(args.batch_size)
            await cleaner.verify()
            
    finally:
        cleaner.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--backup", action="store_true", default=True)
    parser.add_argument("--batch-size", type=int, default=10000)
    parser.add_argument("--sample", type=int, default=100)
    
    args = parser.parse_args()
    asyncio.run(main(args))
