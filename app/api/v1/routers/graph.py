from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Dict, Optional, Any
from app.api import deps
from app.services.neo4j_service import Neo4jService
from app.services.sqlite_service import SQLiteService
from app.services.language_service import LanguageService
from pydantic import BaseModel

router = APIRouter()

class ScoredNeighbor(BaseModel):
    qid: str
    title: Optional[str]
    score: float

@router.get("/neighbors/scored/{lang}/{qid}", response_model=List[ScoredNeighbor])
async def get_scored_neighbors(
    lang: str = Path(..., description="Language code"),
    qid: str = Path(..., description="Wikidata QID", pattern=r"^Q[0-9]+$"),
    metric: str = Query("adamic_adar", description="Similarity metric: adamic_adar, jaccard"),
    limit: int = Query(20, ge=1, le=100),
    neo4j: Neo4jService = Depends(deps.get_neo4j_service),
    sqlite: SQLiteService = Depends(deps.get_sqlite_service)
):
    """
    Get neighboring entities scored by similarity metrics.
    """
    if lang not in LanguageService.get_active_languages():
        raise HTTPException(status_code=404, detail=f"Language '{lang}' not supported")

    # 1. Compute Scored QIDs in Neo4j
    scored_qids = await neo4j.get_scored_neighbors(lang, qid, limit, metric)
    if not scored_qids:
        return []

    # 2. Resolve Titles in SQLite
    qids = [item['qid'] for item in scored_qids]
    titles = await sqlite.get_titles_batch(lang, qids)

    # 3. Combine
    results = []
    for item in scored_qids:
        results.append(ScoredNeighbor(
            qid=item['qid'],
            title=titles.get(item['qid']),
            score=item['score']
        ))
    
    return results
