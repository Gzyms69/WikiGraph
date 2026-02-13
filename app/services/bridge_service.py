import asyncio
from typing import Optional
from app.services.sqlite_service import SQLiteService
from app.services.neo4j_service import Neo4jService
from app.models import Concept, ConceptNeighbor, Infobox, ScoredNeighbor

class BridgeService:
    """
    Orchestrates the resolution of Concepts by bridging:
    1. Graph Topology (Neo4j)
    2. Rich Metadata (SQLite)
    """
    
    def __init__(self):
        self.sqlite = SQLiteService()
        self.neo4j = Neo4jService()

    async def get_concept(self, lang: str, qid: str) -> Optional[Concept]:
        """
        Fully hydrates a Concept object with all available data.
        """
        # 1. Parallel Fetch: Metadata, Metrics, Neighbors, Sim(AA), Sim(Jaccard)
        metadata_task = self.sqlite.get_concept_metadata(lang, qid)
        metrics_task = self.sqlite.get_node_metrics(lang, qid)
        neighbors_task = self.neo4j.get_neighbors(lang, qid, limit=20)
        
        # New Context Tasks (Top 5 similar nodes)
        aa_task = self.neo4j.get_scored_neighbors(lang, qid, limit=5, metric="adamic_adar")
        jaccard_task = self.neo4j.get_scored_neighbors(lang, qid, limit=5, metric="jaccard")
        
        metadata, metrics, neighbor_qids, aa_raw, jaccard_raw = await asyncio.gather(
            metadata_task, metrics_task, neighbors_task, aa_task, jaccard_task
        )
        
        if not metadata['title'] and not neighbor_qids:
            exists = await self.neo4j.check_existence(lang, qid)
            if not exists:
                return None

        # 2. Batch Resolve Titles (Neighbors + Similarities)
        all_qids = set(neighbor_qids)
        all_qids.update(x['qid'] for x in aa_raw)
        all_qids.update(x['qid'] for x in jaccard_raw)
        
        titles_map = await self.sqlite.get_titles_batch(lang, list(all_qids))
        
        # 3. Construct Neighbor Objects
        neighbors = []
        for n_qid in neighbor_qids:
            neighbors.append(ConceptNeighbor(
                qid=n_qid,
                title=titles_map.get(n_qid)
            ))

        # 4. Construct Scored Neighbor Objects
        similarities = {
            "adamic_adar": [
                ScoredNeighbor(qid=x['qid'], title=titles_map.get(x['qid']), score=x['score']) 
                for x in aa_raw
            ],
            "jaccard": [
                ScoredNeighbor(qid=x['qid'], title=titles_map.get(x['qid']), score=x['score']) 
                for x in jaccard_raw
            ]
        }

        # 5. Construct Final Concept with all compiled data
        return Concept(
            qid=qid,
            lang=lang,
            title=metadata['title'],
            infobox=metadata['infobox'],
            neighbors=neighbors,
            # Degrees
            degree=int(metrics.get('degree', 0)),
            in_degree=int(metrics.get('in_degree', 0)),
            out_degree=int(metrics.get('out_degree', 0)),
            # Analytical Metrics
            pagerank=metrics.get('pagerank'),
            auth_score=metrics.get('auth_score'),
            triangle_count=int(metrics.get('triangle_count', 0)) if metrics.get('triangle_count') else None,
            louvain_id=int(metrics.get('louvain_id', 0)) if metrics.get('louvain_id') else None,
            leiden_id=int(metrics.get('leiden_id', 0)) if metrics.get('leiden_id') else None,
            # Similarities
            similarities=similarities
        )
