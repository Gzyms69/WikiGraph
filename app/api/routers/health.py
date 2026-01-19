from fastapi import APIRouter
from app.services.neo4j_manager import Neo4jManager
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
async def check_system_health():
    manager = Neo4jManager()
    
    # 1. Basic Connectivity
    health_status = manager.check_health()
    
    # 2. Enrich with Counts (if connected)
    for lang, status in health_status.items():
        if status.get("connected"):
            driver = manager.get_driver(lang)
            try:
                with driver.session() as session:
                    # Optimized count queries
                    nodes = session.run("MATCH (n) RETURN count(n) as c").single()["c"]
                    edges = session.run("MATCH ()-[r]->() RETURN count(r) as c").single()["c"]
                    status["nodes"] = nodes
                    status["edges"] = edges
            except Exception as e:
                logger.error(f"Failed to fetch counts for {lang}: {e}")
                status["metrics_error"] = str(e)
                
    return health_status
