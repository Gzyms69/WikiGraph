from app.services.bridge_service import BridgeService
from app.services.sqlite_service import SQLiteService

# Singleton instances for dependency injection
_bridge_service = None
_sqlite_service = None

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
