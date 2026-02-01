import asyncio
import sys
from app.services.neo4j_manager import Neo4jManager

async def find_dense_neo4j():
    manager = Neo4jManager()
    
    query = """
    MATCH (n:Concept)-[:LINKS_TO]->()
    WITH n, COUNT(*) as degree
    ORDER BY degree DESC
    LIMIT 5
    RETURN n.qid as qid, degree
    """
    
    for lang in manager.drivers.keys():
        print(f"--- {lang.upper()} Dense Nodes (Neo4j) ---")
        try:
            results = await manager.query(lang, query)
            for r in results:
                print(f"{r['qid']}: {r['degree']}")
        except Exception as e:
            print(f"Error {lang}: {e}")
            
    await manager.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(find_dense_neo4j())
