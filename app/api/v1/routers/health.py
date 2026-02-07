from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.services.neo4j_manager import Neo4jManager
from app.services.language_service import LanguageService
from app.services.sqlite_pool import SQLitePool
from pathlib import Path
import os

router = APIRouter()

@router.get("/health", tags=["system"])
async def health_check() -> Dict[str, Any]:
    """
    System Health Check.
    Returns status of Neo4j drivers and SQLite databases.
    """
    status = {
        "status": "ok",
        "neo4j": {},
        "sqlite": {}
    }
    
    # 1. Neo4j Check
    neo4j_health = Neo4jManager().check_health()
    status["neo4j"] = neo4j_health
    
    # Check if any enabled language is down
    for lang, health in neo4j_health.items():
        if not health["connected"]:
            status["status"] = "degraded"

    # 2. SQLite Check
    active_langs = LanguageService.get_active_languages()
    for lang in active_langs:
        config = LanguageService.get_config(lang)
        db_path = config.db_path
        
        sqlite_status = {"connected": False, "path": db_path}
        if os.path.exists(db_path):
            try:
                # Use pool to verify connection
                with SQLitePool.get_connection(db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    sqlite_status["connected"] = True
            except Exception as e:
                sqlite_status["error"] = str(e)
                status["status"] = "degraded"
        else:
            sqlite_status["error"] = "File not found"
            status["status"] = "degraded"
            
        status["sqlite"][lang] = sqlite_status

    return status
