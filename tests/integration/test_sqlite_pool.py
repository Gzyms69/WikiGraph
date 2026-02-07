import unittest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from app.services.sqlite_service import SQLiteService

# Assume we have a valid database for testing (PL or DE)
# If not, the test will skip or fail gracefully.
DB_LANG = 'pl' 

class TestSQLitePool(unittest.TestCase):
    def setUp(self):
        self.service = SQLiteService()

    def test_concurrent_access(self):
        """
        Simulate 20 concurrent readers to verify pool stability.
        """
        qids = ["Q1", "Q2", "Q3", "Q4", "Q5"] * 4 # 20 requests
        
        async def run_test():
            tasks = []
            for qid in qids:
                tasks.append(self.service.get_concept_metadata(DB_LANG, qid))
            
            results = await asyncio.gather(*tasks)
            return results

        start = time.time()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(run_test())
        end = time.time()
        
        print(f"Pool Stress Test: Processed {len(results)} requests in {end - start:.4f}s")
        self.assertEqual(len(results), 20)
        # Check if we got results (assuming Q1 etc might not exist, but we shouldn't crash)
        for res in results:
            self.assertIn("title", res)

if __name__ == "__main__":
    unittest.main()
