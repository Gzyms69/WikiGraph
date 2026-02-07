import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from app.api.v1.routers.path import get_shortest_path

class TestPathRouter(unittest.IsolatedAsyncioTestCase):
    async def test_get_shortest_path_found(self):
        # Mock Services
        mock_neo4j = MagicMock()
        mock_neo4j.find_shortest_path = AsyncMock(return_value=["Q1", "Q2", "Q3"])
        
        mock_sqlite = MagicMock()
        mock_sqlite.get_titles_batch = AsyncMock(return_value={"Q1": "Start", "Q2": "Mid", "Q3": "End"})
        
        # Call Endpoint
        result = await get_shortest_path(
            lang="pl", from_qid="Q1", to_qid="Q3", max_depth=10,
            neo4j=mock_neo4j, sqlite=mock_sqlite
        )
        
        # Verify
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].qid, "Q1")
        self.assertEqual(result[0].title, "Start")
        self.assertEqual(result[0].order, 0)
        self.assertEqual(result[2].qid, "Q3")
        self.assertEqual(result[2].title, "End")
        
        # Verify calls
        mock_neo4j.find_shortest_path.assert_called_with("pl", "Q1", "Q3", 10)
        mock_sqlite.get_titles_batch.assert_called_with("pl", ["Q1", "Q2", "Q3"])

    async def test_get_shortest_path_not_found(self):
        mock_neo4j = MagicMock()
        mock_neo4j.find_shortest_path = AsyncMock(return_value=[])
        
        mock_sqlite = MagicMock()
        
        result = await get_shortest_path(
            lang="pl", from_qid="Q1", to_qid="Q99", max_depth=6,
            neo4j=mock_neo4j, sqlite=mock_sqlite
        )
        
        self.assertEqual(result, [])

if __name__ == "__main__":
    unittest.main()
