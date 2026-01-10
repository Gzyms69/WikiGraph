from fastapi import APIRouter, HTTPException
from app.database import db

router = APIRouter()

@router.post("/embeddings")
def get_node_embeddings(limit: int = 5, dimensions: int = 16):
    """
    Generates node embeddings using the FastRP algorithm.
    Returns vector representations for Concepts.
    """
    # Note: Using an anonymous projection or existing 'wikigraph'
    query = """
    CALL gds.fastRP.stream('wikigraph', {
        embeddingDimension: $dim,
        randomSeed: 42
    })
    YIELD nodeId, embedding
    RETURN gds.util.asNode(nodeId).qid AS qid, embedding
    LIMIT $limit
    """
    
    with db.get_session() as session:
        # Check if projected graph exists
        exists = session.run("CALL gds.graph.exists('wikigraph') YIELD exists").single()["exists"]
        if not exists:
            raise HTTPException(status_code=400, detail="Analytics not initialized. Call /analytics/initialize first.")
            
        try:
            results = session.run(query, limit=limit, dim=dimensions).data()
            return {"algorithm": "FastRP", "dimensions": dimensions, "embeddings": results}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")
