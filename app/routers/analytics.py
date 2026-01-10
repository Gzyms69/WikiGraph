from fastapi import APIRouter, HTTPException
from app.database import db

router = APIRouter()

@router.post("/initialize")
def initialize_analytics():
    """
    Projects the graph into memory for GDS. 
    This must be called once before running analytics.
    We project relationships as UNDIRECTED to support structural algorithms like K-Core.
    """
    check_query = "CALL gds.graph.exists('wikigraph') YIELD exists"
    drop_query = "CALL gds.graph.drop('wikigraph')"
    project_query = """
    CALL gds.graph.project(
      'wikigraph',
      ['Concept', 'Article'],
      {
        LINKS_TO: { orientation: 'UNDIRECTED' },
        REPRESENTS: { orientation: 'UNDIRECTED' }
      }
    )
    """
    
    with db.get_session() as session:
        exists = session.run(check_query).single()["exists"]
        if exists:
            session.run(drop_query)
        
        session.run(project_query)
        return {"status": "Graph projected successfully (Undirected)", "name": "wikigraph"}

@router.post("/pagerank")
def calculate_pagerank(limit: int = 10):
    """
    Runs PageRank on the 'wikigraph' projection.
    """
    query = """
    CALL gds.pageRank.stream('wikigraph')
    YIELD nodeId, score
    RETURN gds.util.asNode(nodeId).qid AS qid, score
    ORDER BY score DESC
    LIMIT $limit
    """
    
    with db.get_session() as session:
        # Check if projected graph exists
        exists = session.run("CALL gds.graph.exists('wikigraph') YIELD exists").single()["exists"]
        if not exists:
            raise HTTPException(status_code=400, detail="Analytics not initialized. Call /analytics/initialize first.")
            
        results = session.run(query, limit=limit).data()
        
    return {"top_concepts": results}

@router.post("/bridges")
def find_bridges(limit: int = 10):
    """
    Finds concepts that act as bridges between different clusters 
    using Betweenness Centrality.
    Uses concurrency to handle large graph scale.
    """
    query = """
    CALL gds.betweenness.stream('wikigraph', { concurrency: 4 })
    YIELD nodeId, score
    RETURN gds.util.asNode(nodeId).qid AS qid, score
    ORDER BY score DESC
    LIMIT $limit
    """
    try:
        with db.get_session() as session:
            results = session.run(query, limit=limit).data()
        return {"bridges": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bridge analysis failed: {str(e)}")

@router.post("/silos")
def find_silos(limit: int = 5):
    """
    Uses Louvain Community Detection to identify isolated information silos.
    Returns the largest identified communities and their sample concepts.
    """
    query = """
    CALL gds.louvain.stream('wikigraph')
    YIELD nodeId, communityId
    WITH communityId, collect(gds.util.asNode(nodeId).qid) as qids
    RETURN communityId, size(qids) as size, qids[0..5] as samples
    ORDER BY size DESC
    LIMIT $limit
    """
    with db.get_session() as session:
        results = session.run(query, limit=limit).data()
    return {"communities": results}

@router.post("/k-core")
def find_kcore(limit: int = 10):
    """
    Identifies the core structural component of the graph.
    Returns concepts with the highest coreness values.
    """
    query = """
    CALL gds.kcore.stream('wikigraph')
    YIELD nodeId, coreValue
    RETURN gds.util.asNode(nodeId).qid as qid, coreValue
    ORDER BY coreValue DESC
    LIMIT $limit
    """
    with db.get_session() as session:
        results = session.run(query, limit=limit).data()
    return {"k_core": results}

@router.get("/gaps")
def find_gaps(source_lang: str, target_lang: str, limit: int = 10):
    """
    Finds concepts that are influential (high degree) in the Source language
    but have no article in the Target language.
    """
    query = """
    MATCH (c:Concept)
    WHERE (c)<-[:REPRESENTS]-(:Article {lang: $source})
      AND NOT (c)<-[:REPRESENTS]-(:Article {lang: $target})
    WITH c, count{(c)-[:LINKS_TO]-()} as degree
    RETURN c.qid as qid, degree
    ORDER BY degree DESC
    LIMIT $limit
    """
    with db.get_session() as session:
        results = session.run(query, source=source_lang, target=target_lang, limit=limit).data()
    return {"source": source_lang, "missing_in": target_lang, "gaps": results}
