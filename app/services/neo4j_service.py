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

    async def find_shortest_path(self, lang: str, from_qid: str, to_qid: str, max_depth: int = 6) -> List[str]:
        """
        Find shortest path between two QIDs using BFS.
        Returns ordered list of QIDs.
        """
        driver = self.manager.get_driver(lang)
        if not driver:
            return []

        # Cypher shortestPath uses BFS
        query = """
        MATCH p = shortestPath((start:Concept {qid: $start})-[*..%d]->(end:Concept {qid: $end}))
        RETURN [n in nodes(p) | n.qid] as path
        """ % max_depth

        # Progressive Timeout Calculation
        # Base: 2.0s
        # Scale: max(1.5 * depth, 5.0)
        # Depth 6 -> 9s
        # Depth 24 -> 36s
        timeout = max(5.0, max_depth * 1.5)

        try:
            # FIX: Use query() instead of query_all() as this is language-specific
            results = await self.manager.query(lang, query, {"start": from_qid, "end": to_qid}, timeout=timeout)
            if results and results[0].get("path"):
                return results[0]["path"]
            return []
        except Exception as e:
            # logger.error(f"Shortest path failed: {e}") # Add logger import if needed or print
            print(f"Shortest path failed: {e}")
            return []
