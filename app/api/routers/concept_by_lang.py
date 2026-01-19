from fastapi import APIRouter, HTTPException, Query
from app.services.neo4j_manager import Neo4jManager
from app.services.metadata_manager import MetadataManager
from app.core.config import settings
from typing import List, Optional

router = APIRouter()

def validate_lang(lang: str):
    # Check against configured languages
    # settings['languages'] keys are valid codes
    if lang not in settings['languages']:
        raise HTTPException(status_code=400, detail=f"Invalid language code: {lang}")

@router.get("/{lang}/concept/{qid}")
async def get_concept_by_lang(
    lang: str, 
    qid: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    validate_lang(lang)
    manager = Neo4jManager()
    meta = MetadataManager()
    
    # 1. Fetch Node + Neighbors
    query = """
    MATCH (n:Concept {qid: $qid})
    OPTIONAL MATCH (n)-[:LINKS_TO]->(m:Concept)
    WITH n, m
    ORDER BY m.qid ASC
    SKIP $offset
    LIMIT $limit
    RETURN n.qid as qid, collect(m.qid) as neighbors
    """
    
    results = await manager.query(lang, query, {"qid": qid, "offset": offset, "limit": limit})
    
    if results is None:
        raise HTTPException(status_code=503, detail="Database connection failed")
        
    if not results:
        raise HTTPException(status_code=404, detail="Concept not found")
        
    row = results[0]
    
    # 2. Enrich
    resp = {
        "qid": row["qid"],
        "lang": lang,
        "title": meta.get_title(lang, qid),
        "neighbors": []
    }
    
    neighbor_qids = [x for x in row["neighbors"] if x]
    if neighbor_qids:
        titles = meta.get_titles_batch(lang, neighbor_qids)
        for nq in neighbor_qids:
            resp["neighbors"].append({
                "qid": nq,
                "title": titles.get(nq)
            })
            
    return resp

@router.get("/{lang}/concept/{qid}/path")
async def get_path(
    lang: str,
    qid: str,
    target_qid: str,
    max_depth: int = Query(3, ge=1, le=5)
):
    validate_lang(lang)
    manager = Neo4jManager()
    
    # Shortest Path Query
    # Uses Neo4j's built-in shortestPath function
    query = """
    MATCH path = shortestPath((start:Concept {qid: $start})-[*1..5]-(end:Concept {qid: $end}))
    WHERE length(path) <= $max_depth
    RETURN [node IN nodes(path) | node.qid] as qids
    LIMIT 1
    """
    
    # Note: Variable length relationship limit in Cypher [*1..5] needs to be literal integer usually?
    # Actually, parameterizing depth in the pattern `[*1..$depth]` is supported in newer Neo4j,
    # but `shortestPath` has specific requirements.
    # Safe way: use literal in query string (validated via Pydantic) or WHERE clause on length.
    # I used WHERE length(path) <= $max_depth.
    
    results = await manager.query(lang, query, {
        "start": qid, 
        "end": target_qid, 
        "max_depth": max_depth
    })
    
    if results is None:
        raise HTTPException(status_code=503, detail="Database connection failed")
        
    if not results:
        # Check if start node exists? Or just return 404 for path?
        # Standard: 404 if path not found? Or 200 with empty?
        # Let's check if nodes exist first? Expensive.
        # If empty, return 404 "Path not found"
        raise HTTPException(status_code=404, detail="Path not found")
        
    path_qids = results[0]["qids"]
    
    # Enrich path with titles
    meta = MetadataManager()
    titles = meta.get_titles_batch(lang, path_qids)
    
    enriched_path = []
    for q in path_qids:
        enriched_path.append({
            "qid": q,
            "title": titles.get(q)
        })
        
    return {
        "source": qid,
        "target": target_qid,
        "length": len(path_qids) - 1,
        "path": enriched_path
    }
