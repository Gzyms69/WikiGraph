import unittest
import asyncio
from app.api.v1.routers.health import health_check

class TestHealthRouter(unittest.TestCase):
    def test_health_check(self):
        # This will try to connect to real Neo4j/SQLite.
        # If they are running, it should return 'ok'.
        # If not, it should return 'degraded', but not crash.
        try:
            result = asyncio.run(health_check())
            print(f"Health Check Result: {result}")
            self.assertIn("status", result)
            self.assertIn("neo4j", result)
            self.assertIn("sqlite", result)
        except Exception as e:
            self.fail(f"Health check crashed: {e}")

if __name__ == "__main__":
    unittest.main()
