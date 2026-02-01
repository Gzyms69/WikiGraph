from fastapi import APIRouter, HTTPException, Query
from app.services.neo4j_manager import Neo4jManager
from app.services.metadata_manager import MetadataManager
from typing import Dict, List, Set, Any, Optional
import asyncio
import psutil
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# HARD LIMITS
HARD_MAX_DEPTH = 3
HARD_LIMIT_PER_DEPTH = 200
HARD_TOTAL_NODE_LIMIT = 1000
MIN_FREE_MEMORY_BYTES = 1 * 1024 * 1024 * 1024 # 1GB

@router.get("/concept/{qid}/traverse")
async def traverse_concept(
    qid: str,
    max_depth: int = Query(1, ge=1, le=HARD_MAX_DEPTH),
    limit_per_depth: int = Query(10, ge=1, le=HARD_LIMIT_PER_DEPTH),
    total_node_limit: int = Query(100, ge=1, le=HARD_TOTAL_NODE_LIMIT)
):
    mem = psutil.virtual_memory()
    if mem.available < MIN_FREE_MEMORY_BYTES:
        raise HTTPException(status_code=503, detail="Server busy (Low Memory)")

    manager = Neo4jManager()
    meta_manager = MetadataManager()

    visited: Set[str] = {qid}
    frontier: Set[str] = {qid}
    nodes_map: Dict[str, Dict] = {qid: {"titles": {}}} 
    edges_list: List[Dict] = []
    
    depth = 0

    try:
        while frontier and depth < max_depth:
            if len(nodes_map) >= total_node_limit:
                break

            query = """
            UNWIND $ids AS qid
            CALL {
                WITH qid
                MATCH (n:Concept {qid: qid})-[:LINKS_TO]->(m:Concept)
                RETURN n.qid as src, m.qid as tgt
                LIMIT $limit_per_node
            }
            RETURN src, tgt
            """
            
            async def fetch_layer(lang, ids):
                try:
                    return lang, await manager.query(lang, query, {"ids": ids, "limit_per_node": limit_per_depth})
                except Exception as e:
                    return lang, None

            tasks = []
            active_langs = list(manager.drivers.keys())
            frontier_list = list(frontier)
            for lang in active_langs:
                tasks.append(asyncio.wait_for(fetch_layer(lang, frontier_list), timeout=3.0))

            results_raw = await asyncio.gather(*tasks, return_exceptions=True)

            level_discovered_frontier = set()
            edge_accumulator = {} # (src, tgt) -> set(langs)

            for res in results_raw:
                if isinstance(res, Exception): continue
                lang, rows = res
                if rows is None: continue

                for row in rows:
                    src, tgt = row["src"], row["tgt"]
                    
                    if tgt not in visited:
                        level_discovered_frontier.add(tgt)
                    
                    # Accumulate edges temporarily
                    edge_key = (src, tgt)
                    if edge_key not in edge_accumulator:
                        edge_accumulator[edge_key] = set()
                    edge_accumulator[edge_key].add(lang)

            # Apply Width Limit to the candidates
            next_frontier_list = sorted(list(level_discovered_frontier))
            if len(next_frontier_list) > limit_per_depth:
                next_frontier_list = next_frontier_list[:limit_per_depth]
            
            allowed_new_nodes = set(next_frontier_list)
            
            # Now finalize nodes and edges for this level
            for (src, tgt), langs in edge_accumulator.items():
                # Only include edge if target is an allowed new node OR already visited
                if tgt in allowed_new_nodes or tgt in visited:
                    if src not in nodes_map: nodes_map[src] = {"titles": {}}
                    if tgt not in nodes_map: nodes_map[tgt] = {"titles": {}}
                    
                    edges_list.append({
                        "from": src,
                        "to": tgt,
                        "languages": list(langs)
                    })

            visited.update(allowed_new_nodes)
            frontier = allowed_new_nodes
            depth += 1

    except Exception as e:
        logger.error(f"Traversal Error: {e}")

    # Enrichment
    all_qids = list(nodes_map.keys())
    for lang in manager.drivers.keys():
        try:
            titles = meta_manager.get_titles_batch(lang, all_qids)
            for q, t in titles.items():
                if q in nodes_map:
                    nodes_map[q]["titles"][lang] = t
        except Exception: pass

    return {
        "qid": qid,
        "max_depth": max_depth,
        "graph": {
            "nodes": nodes_map,
            "edges": edges_list
        }
    }