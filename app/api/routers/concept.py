from fastapi import APIRouter, HTTPException, Query
from app.services.neo4j_manager import Neo4jManager
from app.services.metadata_manager import MetadataManager
from typing import Dict, List, Optional, Any
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/concept/{qid}")
async def get_concept(
    qid: str, 
    limit: int = Query(10, ge=1, le=100), 
    offset: int = Query(0, ge=0)
):
    neo_manager = Neo4jManager()
    meta_manager = MetadataManager()
    
    # 1. Query Neo4j for Node + Neighbors using proper SKIP/LIMIT
    query = """
    MATCH (n:Concept {qid: $qid})
    OPTIONAL MATCH (n)-[:LINKS_TO]->(m:Concept)
    WITH n, m
    ORDER BY m.qid ASC
    SKIP $offset
    LIMIT $limit
    RETURN n.qid as qid, collect(m.qid) as neighbor_qids
    """
    
    params = {"qid": qid, "offset": offset, "limit": limit}
    graph_results = await neo_manager.query_all(query, params)
    
    if not graph_results:
        raise HTTPException(status_code=503, detail="No active database connections")

    merged = {
        "qid": qid,
        "titles": {},
        "infoboxes": {},
        "neighbors": {},
        "found_in": []
    }
    
    found_any = False
    
    for lang, rows in graph_results.items():
        if rows:
            found_any = True
            merged["found_in"].append(lang)
            row = rows[0]
            
            merged["titles"][lang] = meta_manager.get_title(lang, qid)
            merged["infoboxes"][lang] = meta_manager.get_infobox(lang, qid)
            
            neighbor_qids = row.get("neighbor_qids", [])
            merged["neighbors"][lang] = []
            
            if neighbor_qids:
                neighbor_titles = meta_manager.get_titles_batch(lang, neighbor_qids)
                for n_qid in neighbor_qids:
                    if n_qid:
                        merged["neighbors"][lang].append({
                            "qid": n_qid,
                            "title": neighbor_titles.get(n_qid)
                        })
            
    if not found_any:
        raise HTTPException(status_code=404, detail=f"Concept {qid} not found")
        
    return merged