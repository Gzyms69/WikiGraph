from fastapi import APIRouter
from app.database import db
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/keyword")
def search_by_keyword(q: str, lang: str = None, limit: int = 10):
    """
    Searches for articles using a full-text Lucene index.
    Returns matched articles and their associated Concepts.
    Optimized for speed by joining with Concept AFTER limit.
    """
    # Build Lucene query with language filter if provided
    lucene_q = q
    if lang:
        # Search specifically within language-prefixed titles if we had them,
        # but since we only index 'title', we filter by lang property in WITH.
        pass

    query = """
    CALL db.index.fulltext.queryNodes('article_titles', $q) 
    YIELD node, score
    """
    
    if lang:
        query += " WHERE node.lang = $lang "
        
    query += """
    WITH node, score LIMIT $limit
    MATCH (node)-[:REPRESENTS]->(c:Concept)
    RETURN node.title as title, node.lang as lang, c.qid as qid, score
    """
    
    try:
        with db.get_session() as session:
            results = session.run(query, q=q, lang=lang, limit=limit).data()
        return {"query": q, "results": results}
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return {"query": q, "results": [], "error": str(e)}
