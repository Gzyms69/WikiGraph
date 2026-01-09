from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from app.database import db
import logging

# Configure router logging
logger = logging.getLogger(__name__)

router = APIRouter()

class WeightedNeighborsRequest(BaseModel):
    qid: str
    lang: str = "pl"
    limit: int = 15
    weights: Dict[str, float] = {"jaccard": 1.0, "adamic_adar": 1.0, "ppr": 1.0}
    algorithms: List[str] = ["jaccard", "adamic_adar", "ppr"]

class BulkNeighborsRequest(BaseModel):
    requests: List[WeightedNeighborsRequest]

@router.post("/bulk-weighted-neighbors")
def get_bulk_weighted_neighbors(request: BulkNeighborsRequest):
    """
    Batch process multiple neighbor requests.
    """
    results = {}
    for req in request.requests:
        try:
            res = get_weighted_neighbors(req)
            results[req.qid] = res["neighbors"]
        except Exception as e:
            logger.error(f"Bulk failed for {req.qid}: {str(e)}")
            results[req.qid] = []
    return {"results": results}

@router.get("/shortest-path")
def shortest_path(start: str, end: str, lang: str = "pl"):
    """
    Finds the shortest path between two articles (by title) across the graph.
    Returns path with standardized lang:qid IDs.
    """
    query = """
    MATCH (start:Article {title: $start, lang: $lang})
    MATCH (end:Article {title: $end})
    MATCH p = shortestPath((start)-[:REPRESENTS|LINKS_TO*]-(end))
    RETURN [n in nodes(p) | {
        label: labels(n)[0], 
        title: n.title, 
        qid: n.qid, 
        lang: n.lang,
        id: CASE 
            WHEN 'Article' IN labels(n) THEN n.lang + ':' + n.qid 
            ELSE n.qid 
        END
    }] as path, length(p) as hops
    """
    
    with db.get_session() as session:
        result = session.run(query, start=start, end=end, lang=lang).single() 
        
    if not result:
        raise HTTPException(status_code=404, detail="Path not found or nodes do not exist")
        
    return result.data()

@router.get("/nebula")
def get_nebula_sample(langs: str = None, limit: int = 150):
    """
    Returns a sample of high-importance nodes using precomputed PageRank and Community IDs.
    Fast read-only endpoint. Requires `tools/precompute_metrics.py` to have been run.
    """
    lang_list = langs.split(",") if langs else []
    
    query = """
    MATCH (n:Concept)
    WHERE n.pagerank IS NOT NULL
    WITH n
    ORDER BY n.pagerank DESC
    LIMIT $limit
    
    // Get primary article for display
    MATCH (n)<-[:REPRESENTS]-(a:Article)
    """
    
    if lang_list:
        query += " WHERE a.lang IN $langs "
    
    query += """
    WITH n, head(collect(a)) as a
    
    RETURN n.qid as qid, 
           coalesce(a.lang, 'unknown') + ':' + n.qid as id,
           coalesce(a.title, n.qid) as name, 
           n.pagerank as val,
           coalesce(a.lang, 'unknown') as lang,
           coalesce(n.community, -1) as community
    """
    
    try:
        with db.get_session() as session:
            # 1. Fetch Top Nodes
            logger.info(f"Fetching top {limit} precomputed nodes...")
            nodes = session.run(query, limit=limit, langs=lang_list).data()
            
            if not nodes:
                logger.warning("No precomputed nodes found. Run 'tools/precompute_metrics.py'!")
                # Fallback? Or just return empty. Better to fail fast and prompt admin action.
                return {"nodes": [], "links": []}

            logger.info(f"Found {len(nodes)} nodes.")
            
            # 2. Fetch links between these nodes
            qids = [n['qid'] for n in nodes]
            links = []
            
            if qids:
                link_query = """
                MATCH (c1:Concept)-[:LINKS_TO]-(c2:Concept)
                WHERE c1.qid IN $qids AND c2.qid IN $qids
                RETURN c1.qid as source_qid, c2.qid as target_qid
                """
                raw_links = session.run(link_query, qids=qids).data()
                logger.info(f"Found {len(raw_links)} links.")
                
                qid_to_id = {n['qid']: n['id'] for n in nodes}
                seen = set()
                for rl in raw_links:
                    s = qid_to_id.get(rl['source_qid'])
                    t = qid_to_id.get(rl['target_qid'])
                    if s and t:
                        pair = tuple(sorted([s, t]))
                        if pair not in seen:
                            links.append({"source": s, "target": t})
                            seen.add(pair)
            
            return {"nodes": nodes, "links": links}

    except Exception as e:
        logger.error(f"Nebula Error: {str(e)}")
        return {"nodes": [], "links": []}

@router.post("/weighted-neighbors")
def get_weighted_neighbors(request: WeightedNeighborsRequest):
    """
    Multi-algorithm neighbor scoring with user-defined weights.
    Normalization: Min-Max normalization within the candidate set.
    """
    qid = request.qid
    weights = request.weights
    limit = request.limit
    lang = request.lang
    
    # 1. Candidate Generation: Union of direct neighbors
    # We fetch scores for all selected algorithms in one pass
    query = """
    MATCH (c:Concept {qid: $qid})
    MATCH (c)-[:LINKS_TO]-(neighbor:Concept)
    WHERE neighbor.qid <> $qid
    
    // Calculate raw scores
    WITH c, neighbor,
         (1.0 * COUNT { (c)-[:LINKS_TO]-(common)-[:LINKS_TO]-(neighbor) } / 
          (coalesce(c.degree, 1) + coalesce(neighbor.degree, 1) - 
           COUNT { (c)-[:LINKS_TO]-(common)-[:LINKS_TO]-(neighbor) })) AS s_jaccard,
         sum(CASE 
           WHEN coalesce(common.degree, 100) > 1 
           THEN 1.0 / log(coalesce(common.degree, 100)) 
           ELSE 0 
         END) AS s_aa,
         coalesce(neighbor.pagerank, 0) as s_ppr
    
    // Normalization Step (Z-Score or Min-Max)
    // Here we use Min-Max relative to the current candidate set
    WITH collect({n: neighbor, sj: s_jaccard, saa: s_aa, sp: s_ppr}) as candidates
    UNWIND candidates as can
    WITH can,
         max([c in candidates | c.sj]) as max_j, min([c in candidates | c.sj]) as min_j,
         max([c in candidates | c.saa]) as max_aa, min([c in candidates | c.saa]) as min_aa,
         max([c in candidates | c.sp]) as max_ppr, min([c in candidates | c.sp]) as min_ppr
    
    WITH can.n as neighbor,
         (CASE WHEN max_j > min_j THEN (can.sj - min_j) / (max_j - min_j) ELSE 0 END) as norm_j,
         (CASE WHEN max_aa > min_aa THEN (can.saa - min_aa) / (max_aa - min_aa) ELSE 0 END) as norm_aa,
         (CASE WHEN max_ppr > min_ppr THEN (can.sp - min_ppr) / (max_ppr - min_ppr) ELSE 0 END) as norm_ppr
         
    // Weighted Sum
    WITH neighbor,
         ($w_j * norm_j + $w_aa * norm_aa + $w_ppr * norm_ppr) as final_score
    
    // Filter noise and get primary article
    MATCH (neighbor)<-[:REPRESENTS]-(a:Article)
    WHERE NOT a.title =~ '^\\d+$' 
      AND NOT a.title =~ '^\\d+ .*'
      AND NOT a.title STARTS WITH 'List of'
      AND NOT a.title STARTS WITH 'Lista '
      AND NOT a.title STARTS WITH 'Kategoria:'
      AND NOT a.title STARTS WITH 'Category:'
      AND NOT a.title CONTAINS 'Biografien'
    
    ORDER BY final_score DESC
    WITH neighbor, final_score, collect(a) as articles
    WITH neighbor, final_score, articles[0] as article
    RETURN neighbor.qid as qid, 
           article.title as title, 
           article.lang as lang,
           'HYBRID' as type,
           final_score as score
    LIMIT $limit
    """
    
    try:
        with db.get_session() as session:
            results = session.run(query, 
                                 qid=qid, 
                                 w_j=weights.get("jaccard", 0), 
                                 w_aa=weights.get("adamic_adar", 0), 
                                 w_ppr=weights.get("pagerank", 0), # PPR fallback to pagerank key
                                 limit=limit).data()
            return {"center": qid, "neighbors": results}
    except Exception as e:
        logger.error(f"Weighted neighbors failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations")
def get_recommendations(title: str, lang: str = "pl", limit: int = 5):
    """
    Personalized PageRank recommendations.
    """
    find_id_query = """
    MATCH (a:Article {title: $title, lang: $lang})-[:REPRESENTS]->(c:Concept)
    RETURN id(c) as nodeId
    """
    ppr_query = """
    CALL gds.pageRank.stream('wikigraph', { sourceNodes: [$sourceNodeId] })
    YIELD nodeId, score
    RETURN gds.util.asNode(nodeId).qid as qid, score
    ORDER BY score DESC
    LIMIT $limit
    """
    with db.get_session() as session:
        node_record = session.run(find_id_query, title=title, lang=lang).single()
        if not node_record:
            raise HTTPException(status_code=404, detail="Article not found")
        source_id = node_record["nodeId"]
        results = session.run(ppr_query, sourceNodeId=source_id, limit=limit + 1).data()
    recommendations = [r for r in results if r["qid"] != results[0]["qid"]]
    return {"seed": title, "recommendations": recommendations[:limit]}