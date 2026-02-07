import asyncio
from typing import Optional
from app.services.sqlite_service import SQLiteService
from app.services.neo4j_service import Neo4jService
from app.models import Concept, ConceptNeighbor, Infobox

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
        Fully hydrates a Concept object.
        """
        # 1. Parallel Fetch: Metadata (Title/Infobox) AND Neighbors (IDs)
        metadata_task = self.sqlite.get_concept_metadata(lang, qid)
        neighbors_task = self.neo4j.get_neighbors(lang, qid, limit=20) # Limit 20 for now
        
        metadata, neighbor_qids = await asyncio.gather(metadata_task, neighbors_task)
        
        # If no metadata (not in SQLite) AND no neighbors (not in Graph), it doesn't exist.
        # However, it might exist in Graph but not SQLite (if missing from dump), or vice versa.
        # We assume if it has neither, it's 404.
        if not metadata['title'] and not neighbor_qids:
            # Final check: Does it exist in Neo4j alone?
            exists = await self.neo4j.check_existence(lang, qid)
            if not exists:
                return None

        # 2. Resolve Neighbor Titles
        neighbor_titles = await self.sqlite.get_titles_batch(lang, neighbor_qids)
        
        # 3. Construct Neighbor Objects
        neighbors = []
        for n_qid in neighbor_qids:
            neighbors.append(ConceptNeighbor(
                qid=n_qid,
                title=neighbor_titles.get(n_qid) # Might be None if neighbor is redlink/missing
            ))

        # 4. Construct Final Concept
        return Concept(
            qid=qid,
            lang=lang,
            title=metadata['title'],
            infobox=metadata['infobox'],
            neighbors=neighbors
        )
