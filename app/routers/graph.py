from fastapi import APIRouter, HTTPException
from app.database import db

router = APIRouter()

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
    Returns a sample of high-importance nodes.
    Uses 'lang:qid' as the standardized ID for Articles.
    """
    lang_list = langs.split(",") if langs else []
    
    query = """
    CALL gds.pageRank.stream('wikigraph')
    YIELD nodeId, score
    WITH gds.util.asNode(nodeId) as n, score
    ORDER BY score DESC
    LIMIT $limit
    MATCH (n)<-[:REPRESENTS]-(a:Article)
    """
    
    if lang_list:
        query += " WHERE a.lang IN $langs "
        
    query += """
    RETURN n.qid as qid, 
           a.lang + ':' + n.qid as id,
           a.title as name, 
           score as val,
           a.lang as lang
    """
    
    with db.get_session() as session:
        exists = session.run("CALL gds.graph.exists('wikigraph') YIELD exists").single()["exists"]
        if not exists:
            session.run("CALL gds.graph.project('wikigraph', ['Concept', 'Article'], {LINKS_TO: {orientation:'UNDIRECTED'}, REPRESENTS: {orientation:'UNDIRECTED'}})")
            
        results = session.run(query, limit=limit, langs=lang_list).data()
        
    return {"nodes": results, "links": []}

@router.get("/neighbors")
def get_neighbors(qid: str, limit: int = 15):
    """
    Get 1-hop neighbors of a Concept.
    """
    query = """
    MATCH (c:Concept {qid: $qid})-[r:LINKS_TO]-(neighbor:Concept)
    RETURN neighbor.qid as qid, type(r) as type
    LIMIT $limit
    """
    with db.get_session() as session:
        results = session.run(query, qid=qid, limit=limit).data()
    return {"center": qid, "neighbors": results}

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