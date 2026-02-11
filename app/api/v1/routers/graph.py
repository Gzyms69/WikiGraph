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

@router.get("/nebula/{lang}")
async def get_nebula(
    lang: str = Path(..., description="Language code"),
    limit: int = Query(150, ge=10, le=500),
    neo4j: Neo4jService = Depends(deps.get_neo4j_service),
    sqlite: SQLiteService = Depends(deps.get_sqlite_service)
):
    """
    Get a global view of the graph (Nebula) for a specific language.
    Source: SQLite (Top PageRank) -> Neo4j (Links).
    """
    if lang not in LanguageService.get_active_languages():
        raise HTTPException(status_code=404, detail=f"Language '{lang}' not supported")

    # 1. Fetch Top Nodes from SQLite (PageRank)
    top_nodes = await sqlite.get_top_pagerank(lang, limit)
    if not top_nodes:
        return {"nodes": [], "links": []}

    qids = [n['qid'] for n in top_nodes]

    # 2. Fetch Titles for these nodes
    titles = await sqlite.get_titles_batch(lang, qids)

    # 3. Fetch Links between these nodes (Closed World)
    links = await neo4j.get_links_between(lang, qids)

    # 4. Format Response
    nodes_formatted = []
    for n in top_nodes:
        qid = n['qid']
        nodes_formatted.append({
            "id": f"{lang}:{qid}",
            "qid": qid,
            "name": titles.get(qid, qid),
            "val": n['val'],
            "lang": lang,
            "community": 0 # Placeholder for now
        })

    links_formatted = []
    for l in links:
        links_formatted.append({
            "source": f"{lang}:{l['source']}",
            "target": f"{lang}:{l['target']}"
        })

    return {"nodes": nodes_formatted, "links": links_formatted}

@router.get("/weighted-neighbors/{lang}/{qid}")
async def get_weighted_neighbors_bridge(
    lang: str = Path(..., description="Language code"),
    qid: str = Path(..., description="Wikidata QID"),
    neo4j: Neo4jService = Depends(deps.get_neo4j_service),
    sqlite: SQLiteService = Depends(deps.get_sqlite_service)
):
    """
    Bridge endpoint for frontend compatibility.
    Wraps get_scored_neighbors to return the specific format expected by WikiNebula.
    """
    if lang not in LanguageService.get_active_languages():
        raise HTTPException(status_code=404, detail=f"Language '{lang}' not supported")

    # Reuse existing logic
    scored = await get_scored_neighbors(lang, qid, metric="adamic_adar", limit=15, neo4j=neo4j, sqlite=sqlite)
    
    # Transform to Frontend Format
    neighbors = []
    for item in scored:
        neighbors.append({
            "qid": item.qid,
            "title": item.title,
            "lang": lang,
            "score": item.score
        })
        
    return {"center": qid, "neighbors": neighbors}

@router.get("/languages")
async def get_active_languages():
    """
    Returns a list of currently active and configured languages.
    """
    return {"languages": LanguageService.get_active_languages()}
