from fastapi import APIRouter
from app.database import db

router = APIRouter()

@router.get("/keyword")
def search_by_keyword(q: str, limit: int = 10):
    """
    Searches for articles using a full-text Lucene index.
    Returns matched articles and their associated Concepts.
    """
    # Neo4j Full-Text syntax uses Lucene query format
    query = """
    CALL db.index.fulltext.queryNodes('article_titles', $q) 
    YIELD node, score
    MATCH (node)-[:REPRESENTS]->(c:Concept)
    RETURN node.title as title, node.lang as lang, c.qid as qid, score
    LIMIT $limit
    """
    
    with db.get_session() as session:
        results = session.run(query, q=q, limit=limit).data()
        
    return {"query": q, "results": results}
