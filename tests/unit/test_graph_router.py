import unittest
import asyncio
from app.api.v1.routers.graph import get_scored_neighbors

class MockNeo4jService:
    async def get_scored_neighbors(self, lang, qid, limit, metric):
        return [{"qid": "Q2", "score": 0.5}, {"qid": "Q3", "score": 0.3}]

class MockSQLiteService:
    async def get_titles_batch(self, lang, qids):
        return {"Q2": "Title_2", "Q3": "Title_3"}

class TestGraphRouter(unittest.TestCase):
    def test_scored_neighbors_direct(self):
        neo4j = MockNeo4jService()
        sqlite = MockSQLiteService()
        result = asyncio.run(get_scored_neighbors(
            lang="pl", qid="Q1", metric="adamic_adar", limit=10, 
            neo4j=neo4j, sqlite=sqlite
        ))
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].qid, "Q2")
        self.assertEqual(result[0].title, "Title_2")
        self.assertEqual(result[0].score, 0.5)
        print("✅ Graph scoring logic verified via mock.")

if __name__ == "__main__":
    unittest.main()
