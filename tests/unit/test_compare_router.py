import unittest
import asyncio
from app.api.v1.routers.compare import compare_entities

class MockSQLiteService:
    async def get_compare_metadata(self, qid, langs):
        results = {}
        for lang in langs:
            results[lang] = {"title": f"Title_{lang}", "infobox": []}
        return results

class TestCompareRouter(unittest.TestCase):
    def test_compare_direct(self):
        service = MockSQLiteService()
        result = asyncio.run(compare_entities(qid="Q1", langs="pl,de", sqlite=service))
        self.assertEqual(len(result), 2)
        self.assertEqual(result['pl']['title'], "Title_pl")
        self.assertEqual(result['de']['title'], "Title_de")
        print("✅ Comparison logic verified via mock.")

if __name__ == "__main__":
    unittest.main()
