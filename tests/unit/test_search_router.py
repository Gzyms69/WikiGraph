import unittest
import asyncio
from app.api.v1.routers.search import search_entities
from app.services.sqlite_service import SQLiteService

class MockSQLiteService:
    async def search_articles(self, lang, q, limit):
        if q == "Warszawa":
            return [{"title": "ORP_Warszawa", "qid": "Q3880233"}]
        return []

class TestSearchRouter(unittest.TestCase):
    def test_search_direct(self):
        service = MockSQLiteService()
        result = asyncio.run(search_entities(lang="pl", q="Warszawa", limit=10, sqlite=service))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['title'], "ORP_Warszawa")
        print("✅ Router logic verified via mock.")

if __name__ == "__main__":
    unittest.main()
