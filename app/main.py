from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.routers import health, concept, concept_by_lang, traverse
from app.api.v1.routers import entity as entity_v1
from app.api.v1.routers import search as search_v1
from app.api.v1.routers import compare as compare_v1
from app.api.v1.routers import graph as graph_v1
from app.api.v1.routers import path as path_v1
from app.api.v1.routers import health as health_v1
from app.services.sqlite_pool import SQLitePool
from app.services.neo4j_manager import Neo4jManager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup (if needed)
    yield
    # Shutdown
    SQLitePool.close_all()
    Neo4jManager().close()

app = FastAPI(title="WikiGraph API", version="0.1.0", lifespan=lifespan)

# Mount V1 API
app.include_router(health_v1.router, prefix="/api/v1", tags=["v1", "system"])
app.include_router(entity_v1.router, prefix="/api/v1/entity", tags=["v1"])
app.include_router(search_v1.router, prefix="/api/v1/search", tags=["v1", "search"])
app.include_router(compare_v1.router, prefix="/api/v1/compare", tags=["v1", "compare"])
app.include_router(graph_v1.router, prefix="/api/v1/graph", tags=["v1", "graph"])
app.include_router(path_v1.router, prefix="/api/v1/graph/path", tags=["v1", "graph"])

# Mount Legacy API (v0)
app.include_router(health.router, prefix="/api")
app.include_router(concept.router, prefix="/api")
app.include_router(concept_by_lang.router, prefix="/api")
app.include_router(traverse.router, prefix="/api")

@app.get("/test")
def read_test():
    return {"status": "ok", "languages": list(settings["languages"].keys())}