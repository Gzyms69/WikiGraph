from app.services.bridge_service import BridgeService
from app.services.sqlite_service import SQLiteService
from app.services.neo4j_service import Neo4jService

# Singleton instances for dependency injection
_bridge_service = None
_sqlite_service = None
_neo4j_service = None

def get_bridge_service() -> BridgeService:
    global _bridge_service
    if _bridge_service is None:
        _bridge_service = BridgeService()
    return _bridge_service

def get_sqlite_service() -> SQLiteService:
    global _sqlite_service
    if _sqlite_service is None:
        _sqlite_service = SQLiteService()
    return _sqlite_service

def get_neo4j_service() -> Neo4jService:
    global _neo4j_service
    if _neo4j_service is None:
        _neo4j_service = Neo4jService()
    return _neo4j_service
