from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import graph, analytics, search, ml

app = FastAPI(
    title="WikiGraph Research API",
    description="High-performance API for cross-lingual Wikipedia Knowledge Graph analysis.",
    version="1.0.0"
)

# CORS (Allow frontend to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(graph.router, prefix="/graph", tags=["Graph Traversal"])
app.include_router(analytics.router, prefix="/analytics", tags=["Graph Analytics"])
app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(ml.router, prefix="/ml", tags=["Machine Learning"])

@app.get("/")
def read_root():
    return {"status": "online", "system": "WikiGraph Lab"}
