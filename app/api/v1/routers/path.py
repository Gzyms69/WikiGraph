from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Dict, Optional, Any
from app.api import deps
from app.services.neo4j_service import Neo4jService
from app.services.sqlite_service import SQLiteService
from app.services.language_service import LanguageService
from pydantic import BaseModel

router = APIRouter()

class PathNode(BaseModel):
    qid: str
    title: Optional[str]
    order: int

@router.get("/shortest/{lang}", response_model=List[PathNode])
async def get_shortest_path(
    lang: str = Path(..., description="Language code"),
    from_qid: str = Query(..., description="Start QID", pattern=r"^Q[0-9]+$"),
    to_qid: str = Query(..., description="End QID", pattern=r"^Q[0-9]+$"),
    max_depth: int = Query(6, ge=1, le=24, description="Maximum search depth (BFS). Higher values increase timeout."),
    neo4j: Neo4jService = Depends(deps.get_neo4j_service),
    sqlite: SQLiteService = Depends(deps.get_sqlite_service)
):
    """
    Find the shortest path (BFS) between two entities.
    Returns the full path enriched with titles.
    """
    if lang not in LanguageService.get_active_languages():
        raise HTTPException(status_code=404, detail=f"Language '{lang}' not supported")

    # 1. Topology Search (Neo4j)
    path_qids = await neo4j.find_shortest_path(lang, from_qid, to_qid, max_depth)
    
    if not path_qids:
        # Check if start/end exist to give better error? 
        # For now, empty list means no path found or disconnected.
        return []

    # 2. Metadata Enrichment (SQLite)
    titles = await sqlite.get_titles_batch(lang, path_qids)

    # 3. Format Response (Preserve Order)
    result = []
    for i, qid in enumerate(path_qids):
        result.append(PathNode(
            qid=qid,
            title=titles.get(qid),
            order=i
        ))
    
    return result
