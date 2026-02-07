from app.services.neo4j_manager import Neo4jManager
from typing import List, Dict, Any

class Neo4jService:
    """
    Async Wrapper/Service for Neo4j Operations.
    Currently delegates to the Singleton Neo4jManager but standardizes the interface.
    """
    
    def __init__(self):
        self.manager = Neo4jManager()

    async def get_neighbors(self, lang: str, qid: str, limit: int = 10) -> List[str]:
        """
        Fetches neighboring QIDs for a given QID.
        """
        query = """
        MATCH (n:Concept {qid: $qid})-[r]-(m:Concept)
        RETURN m.qid as qid
        LIMIT $limit
        """
        params = {"qid": qid, "limit": limit}
        
        results = await self.manager.query(lang, query, params)
        if not results:
            return []
            
        return [r['qid'] for r in results]

    async def check_existence(self, lang: str, qid: str) -> bool:
        query = "MATCH (n:Concept {qid: $qid}) RETURN 1"
        results = await self.manager.query(lang, query, {"qid": qid})
        return bool(results)

    async def get_scored_neighbors(self, lang: str, qid: str, limit: int = 20, metric: str = "adamic_adar") -> List[Dict[str, Any]]:
        """
        Computes local similarity metrics for the neighborhood of a QID.
        Supported metrics: adamic_adar, jaccard.
        """
        if metric == "adamic_adar":
            # undirected AA
            query = """
            MATCH (p:Concept {qid: $qid})-[:LINKS]-(common)-[:LINKS]-(neighbor:Concept)
            WHERE p <> neighbor
            WITH neighbor, common
            RETURN neighbor.qid as qid, sum(1.0 / log(size((common)-[:LINKS]-()) + 1.1)) as score
            ORDER BY score DESC
            LIMIT $limit
            """
        elif metric == "jaccard":
            # undirected Jaccard
            query = """
            MATCH (p:Concept {qid: $qid})-[:LINKS]-(common)-[:LINKS]-(neighbor:Concept)
            WHERE p <> neighbor
            WITH p, neighbor, count(common) as intersection
            MATCH (p)-[:LINKS]-(p_neighbor)
            WITH p, neighbor, intersection, count(p_neighbor) as p_degree
            MATCH (neighbor)-[:LINKS]-(n_neighbor)
            WITH neighbor, intersection, p_degree, count(n_neighbor) as n_degree
            RETURN neighbor.qid as qid, float(intersection) / (p_degree + n_degree - intersection) as score
            ORDER BY score DESC
            LIMIT $limit
            """
        else:
            return []

        params = {"qid": qid, "limit": limit}
        results = await self.manager.query(lang, query, params)
        return results if results else []
