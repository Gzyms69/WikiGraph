from fastapi import FastAPI
from app.core.config import settings
from app.api.routers import health, concept, concept_by_lang, traverse

app = FastAPI(title="WikiGraph API", version="0.1.0")

# Mount health under /api for consistency
app.include_router(health.router, prefix="/api")
app.include_router(concept.router, prefix="/api")
app.include_router(concept_by_lang.router, prefix="/api")
app.include_router(traverse.router, prefix="/api")

@app.get("/test")
def read_test():
    return {"status": "ok", "languages": list(settings["languages"].keys())}