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
    lang: Optional[str] = None
    limit: int = 15
    weights: Dict[str, float] = {"jaccard": 1.0, "adamic_adar": 1.0, "ppr": 1.0}
    algorithms: List[str] = ["jaccard", "adamic_adar", "ppr"]

class BulkNeighborsRequest(BaseModel):
    requests: List[WeightedNeighborsRequest]

@router.get("/languages")
def get_available_languages():
    """
    Dynamically discovers all languages present in the graph.
    """
    query = "MATCH (a:Article) RETURN distinct a.lang as lang ORDER BY lang"
    try:
        with db.get_session() as session:
            result = session.run(query).data()
            langs = [r['lang'] for r in result]
            return {"languages": langs}
    except Exception as e:
        logger.error(f"Failed to fetch languages: {str(e)}")
        return {"languages": []}

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
def shortest_path(start: str, end: str, lang: str):
    """
    Finds the shortest path between two articles (by title) across the graph.
    Returns path with standardized lang:qid IDs.
    User MUST provide lang.
    """
    # Edge Case: Start == End
    if start == end:
        # We need to fetch the node details to return a valid path structure
        # But for pathfinding logic, the distance is 0.
        fetch_query = "MATCH (n:Article {title: $title, lang: $lang}) RETURN n.qid as qid, labels(n) as labels"
        with db.get_session() as session:
            node = session.run(fetch_query, title=start, lang=lang).single()
            if not node:
                raise HTTPException(status_code=404, detail="Node not found")
            
            # Construct a single-node path
            return {
                "path": [{
                    "label": node['labels'][0],
                    "title": start,
                    "qid": node['qid'],
                    "lang": lang,
                    "id": lang + ':' + node['qid'] if 'Article' in node['labels'] else node['qid']
                }],
                "hops": 0
            }

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
    
    try:
        with db.get_session() as session:
            result = session.run(query, start=start, end=end, lang=lang).single() 
            
        if not result:
            # Check if nodes exist to give better error
            check = "MATCH (a:Article {title: $title, lang: $lang}) RETURN count(a) as c"
            with db.get_session() as session:
                s_exists = session.run(check, title=start, lang=lang).single()['c'] > 0
                e_exists = session.run(check, title=end, lang=lang).single()['c'] > 0 # Assumes end is same lang for now? No, end is ANY article.
                # Actually query above didn't specify end lang.
            
            if not s_exists:
                raise HTTPException(status_code=404, detail=f"Start article '{start}' ({lang}) not found")
            
            # If nodes exist but no path
            raise HTTPException(status_code=404, detail="No path found between these articles")
            
        return result.data()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Shortest path failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/nebula")
def get_nebula_sample(langs: str = None, limit: int = 150):
    """
    Returns a balanced sample of high-importance nodes for each requested language.
    If no langs provided, dynamically fetches ALL available languages.
    """
    # 1. Determine target languages
    if langs:
        lang_list = langs.split(",")
    else:
        # Dynamic Default: Fetch all available langs from DB
        avail = get_available_languages()["languages"]
        lang_list = avail if avail else ["en"] # Fallback only if DB empty

    per_lang_limit = max(10, limit // len(lang_list)) if lang_list else limit
    
    combined_nodes = []
    
    with db.get_session() as session:
        for lang in lang_list:
            # Fetch top concepts specifically for this language
            query = """
            MATCH (a:Article {lang: $lang})-[:REPRESENTS]->(n:Concept)
            WHERE n.pagerank IS NOT NULL
            WITH n, a
            ORDER BY n.pagerank DESC
            LIMIT $limit
            
            RETURN n.qid as qid, 
                   $lang + ':' + n.qid as id,
                   a.title as name, 
                   n.pagerank as val,
                   $lang as lang,
                   coalesce(n.community, -1) as community
            """
            result = session.run(query, lang=lang, limit=per_lang_limit).data()
            combined_nodes.extend(result)
            
    # Fetch links between these specific nodes
    node_ids = [n['qid'] for n in combined_nodes]
    links = []
    
    if node_ids:
        with db.get_session() as session:
            # We want links between Concepts, but mapped to our Lang:QID IDs
            link_query = """
            MATCH (c1:Concept)-[:LINKS_TO]-(c2:Concept)
            WHERE c1.qid IN $qids AND c2.qid IN $qids
            RETURN c1.qid as source_qid, c2.qid as target_qid
            """
            raw_links = session.run(link_query, qids=node_ids).data()
            
            # Map back to the specific lang:qid IDs we generated
            qid_map = {}
            for n in combined_nodes:
                if n['qid'] not in qid_map: qid_map[n['qid']] = []
                qid_map[n['qid']].append(n['id'])
            
            seen = set()
            for rl in raw_links:
                sources = qid_map.get(rl['source_qid'], [])
                targets = qid_map.get(rl['target_qid'], [])
                
                for s in sources:
                    for t in targets:
                        pair = tuple(sorted([s, t]))
                        if pair not in seen:
                            links.append({"source": s, "target": t})
                            seen.add(pair)

    return {"nodes": combined_nodes, "links": links}

@router.post("/weighted-neighbors")
def get_weighted_neighbors(request: WeightedNeighborsRequest):
    """
    Multi-algorithm neighbor scoring with user-defined weights.
    Normalization: Min-Max normalization within the candidate set.
    """
    qid = request.qid
    weights = request.weights
    limit = request.limit
    
    lang_filter = ""
    params = {
        "qid": qid,
        "w_j": weights.get("jaccard", 0), 
        "w_aa": weights.get("adamic_adar", 0), 
        "w_ppr": weights.get("pagerank", 0),
        "limit": limit
    }
    
    if request.lang:
        lang_filter = "AND a.lang = $lang"
        params["lang"] = request.lang

    
    # 1. Candidate Generation: Union of direct neighbors
    # We fetch scores for all selected algorithms in one pass
    query = f"""
    MATCH (c:Concept {{qid: $qid}})
    MATCH (c)-[:LINKS_TO]-(neighbor:Concept)
    WHERE neighbor.qid <> $qid
    
    // Calculate raw scores using CALL subqueries to isolate scope
    CALL {{
        WITH c, neighbor
        MATCH (c)-[:LINKS_TO]-(common)-[:LINKS_TO]-(neighbor)
        RETURN sum(1.0 / log(coalesce(common.degree, 100) + 1)) as s_aa, 
               count(common) as intersection
    }}
    
    WITH c, neighbor, s_aa, intersection,
         (1.0 * intersection / 
          (coalesce(c.degree, 1) + coalesce(neighbor.degree, 1) - intersection)) AS s_jaccard,
         coalesce(neighbor.pagerank, 0) as s_ppr
    
    // Normalization Step: Collect all candidates first
    WITH collect({{n: neighbor, sj: s_jaccard, saa: s_aa, sp: s_ppr}}) as candidates
    
    // Calculate Global Min/Max for the set (Unwind -> Aggregate)
    WITH candidates
    UNWIND candidates as c
    WITH candidates,
         max(c.sj) as max_j, min(c.sj) as min_j,
         max(c.saa) as max_aa, min(c.saa) as min_aa,
         max(c.sp) as max_ppr, min(c.sp) as min_ppr
    
    // Process each candidate with the global stats
    UNWIND candidates as can
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
      {lang_filter}
    
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
            results = session.run(query, **params).data()
            return {"center": qid, "neighbors": results}
    except Exception as e:
        logger.error(f"Weighted neighbors failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations")
def get_recommendations(title: str, lang: str, limit: int = 5):
    """
    Personalized PageRank recommendations.
    User MUST provide lang.
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