import asyncio
import time
import random
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict

# Add project root to path
import os
sys.path.append(os.getcwd())

from app.core.config import settings
from app.services.neo4j_manager import Neo4jManager
from app.services.metadata_manager import MetadataManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Gate6_StressTest")

async def get_random_qids_from_neo4j(neo4j: Neo4jManager, lang: str, limit: int) -> List[Dict]:
    """
    Fetches random QIDs and their properties from Neo4j.
    Using rand() is slow on large datasets, so we'll use a sampling approach 
    if the count is massive, or just LIMIT if acceptable.
    For stress testing, we want ANY valid QIDs.
    """
    logger.info(f"[{lang}] Fetching {limit} random nodes from Neo4j...")
    
    # Efficient sampling is hard in Neo4j without IDs, but for validation
    # we can just take the first N or skip random amount.
    # To be "Big Scale", let's just grab a large chunk.
    query = """
    MATCH (n:Concept)
    RETURN n.qid as qid, keys(n) as properties
    LIMIT $limit
    """
    
    # We might want to use SKIP to get different segments if we ran this multiple times
    # but for a single pass, simple LIMIT is fine.
    
    t0 = time.time()
    results = await neo4j.query(lang, query, {"limit": limit})
    t1 = time.time()
    
    logger.info(f"[{lang}] Fetched {len(results or [])} nodes in {t1-t0:.2f}s")
    return results

def verify_sqlite_batch(meta: MetadataManager, lang: str, qids: List[str], batch_size: int = 1000):
    """
    Verifies that titles exist in SQLite for the given QIDs.
    Uses get_titles_batch for efficiency.
    """
    total = len(qids)
    found = 0
    start_time = time.time()
    
    # Process in batches
    for i in range(0, total, batch_size):
        batch = qids[i:i+batch_size]
        results = meta.get_titles_batch(lang, batch)
        found += len(results)
        
    end_time = time.time()
    duration = end_time - start_time
    return found, duration

def verify_sqlite_infobox_random_sample(meta: MetadataManager, lang: str, qids: List[str], sample_size: int = 100):
    """
    Deep check: Fetch full infobox JSON for a random sample of QIDs.
    """
    subset = random.sample(qids, min(len(qids), sample_size))
    found = 0
    valid_json = 0
    start_time = time.time()
    
    for qid in subset:
        ib = meta.get_infobox(lang, qid)
        if ib is not None:
            found += 1
            if isinstance(ib, list): # It parses to a list of dicts
                valid_json += 1
                
    end_time = time.time()
    return found, valid_json, (end_time - start_time), len(subset)

async def stress_test_lang(lang: str, limit: int = 50000):
    neo4j = Neo4jManager()
    meta = MetadataManager()
    
    logger.info(f"--- STARTING STRESS TEST FOR LANGUAGE: {lang.upper()} ---")
    
    # 1. Neo4j Fetch & Purity Check
    nodes = await get_random_qids_from_neo4j(neo4j, lang, limit)
    if not nodes:
        logger.error(f"[{lang}] FAILED: No nodes returned from Neo4j.")
        return False
        
    qids = []
    impure_nodes = 0
    for node in nodes:
        props = node['properties']
        if 'title' in props: # STRICT CHECK: No titles in Neo4j
            impure_nodes += 1
        qids.append(node['qid'])
        
    if impure_nodes > 0:
        logger.error(f"[{lang}] FAILED: {impure_nodes} nodes contain forbidden 'title' property in Neo4j.")
    else:
        logger.info(f"[{lang}] PASSED: Neo4j Purity Check (0 nodes with 'title').")

    # 2. SQLite Bridge Stress Test (Titles)
    logger.info(f"[{lang}] Stressing SQLite Bridge (Titles) with {len(qids)} QIDs...")
    found_count, duration = verify_sqlite_batch(meta, lang, qids)
    
    throughput = len(qids) / duration if duration > 0 else 0
    success_rate = (found_count / len(qids)) * 100
    
    logger.info(f"[{lang}] SQLite Bridge Results:")
    logger.info(f"  - Duration: {duration:.2f}s")
    logger.info(f"  - Throughput: {throughput:.0f} lookups/sec")
    logger.info(f"  - Success Rate: {success_rate:.2f}% ({found_count}/{len(qids)})")
    
    if success_rate < 90.0:
        logger.warning(f"[{lang}] WARNING: Bridge success rate is low (<90%). Mismatched QIDs?")
    
    # 3. SQLite Deep Infobox Check
    logger.info(f"[{lang}] Verifying Infobox Integrity (Sample)...")
    ib_found, ib_valid, ib_dur, ib_total = verify_sqlite_infobox_random_sample(meta, lang, qids, sample_size=500)
    
    logger.info(f"[{lang}] Infobox Results (Sample N={ib_total}):")
    logger.info(f"  - Found: {ib_found}")
    logger.info(f"  - Valid JSON: {ib_valid}")
    logger.info(f"  - Avg Latency: {(ib_dur/ib_total)*1000:.2f}ms")
    
    logger.info(f"--- COMPLETED {lang.upper()} ---\n")
    return True

async def main():
    logger.info("Initializing Neo4j Manager...")
    neo4j = Neo4jManager()
    
    # Wait for connections
    status = neo4j.check_health()
    logger.info(f"Neo4j Status: {status}")
    
    langs = [l for l, c in settings['languages'].items() if c.get('enabled', False)]
    logger.info(f"Target Languages: {langs}")
    
    # Run tests sequentially to simulate realistic per-lang load, 
    # or gather() for total system stress. Let's do sequential for clearer logs first.
    for lang in langs:
        if status.get(lang, {}).get('connected'):
            await stress_test_lang(lang, limit=100000) # Big Scale: 100k rows
        else:
            logger.error(f"Skipping {lang} - Neo4j not connected.")

    neo4j.close()

if __name__ == "__main__":
    asyncio.run(main())
