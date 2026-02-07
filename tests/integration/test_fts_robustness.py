import unittest
import asyncio
from app.services.sqlite_service import SQLiteService

class TestFTSRobustness(unittest.TestCase):
    def test_malformed_query(self):
        # We need a real DB for this to check if sqlite3 raises OperationalError
        # and if our service catches it.
        service = SQLiteService()
        try:
            # "OR" without operands is often a syntax error in FTS5 standard query syntax
            # or unmatched quotes: '"Warszawa'
            results = asyncio.run(service.search_articles('pl', '"Warszawa', 10))
            # It should return empty list, not raise
            print(f"Malformed query returned: {results}")
            self.assertIsInstance(results, list)
        except Exception as e:
            self.fail(f"Service raised exception on malformed query: {e}")

if __name__ == "__main__":
    unittest.main()
