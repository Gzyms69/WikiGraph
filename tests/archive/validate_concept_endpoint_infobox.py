import sys
import os
import time
import sqlite3
import concurrent.futures
import statistics
import logging
import asyncio
from typing import Dict, Any
from pathlib import Path
import nest_asyncio

# Apply nested asyncio to allow re-entrant event loops
nest_asyncio.apply()

# Add project root to path
sys.path.insert(0, os.getcwd())

# Mock Neo4jManager to avoid needing a live Neo4j instance for this integration test
# We want to test the MetadataManager integration within the router logic, not Neo4j itself.
from unittest.mock import MagicMock, patch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the router function directly to test it
# Note: We need to handle the async nature of the router
from app.api.routers.concept import get_concept
from app.services.metadata_manager import MetadataManager

def get_random_qids(lang, limit=10000):
    """Fetch TRULY RANDOM QIDs from the DB (no filters)."""
    db_path = Path(f"data/db/{lang}.db")
    if not db_path.exists():
        logger.error(f"Database for {lang} not found at {db_path}")
        return []
    
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        query = "SELECT qid FROM id_mapping ORDER BY RANDOM() LIMIT ?"
        cursor.execute(query, (limit,))
        qids = [row[0] for row in cursor.fetchall()]
        conn.close()
        return qids
    except Exception as e:
        logger.error(f"Failed to fetch random QIDs for {lang}: {e}")
        return []

async def run_router_test(lang, qid):
    """
    Simulates a call to get_concept for a specific QID.
    Mocks Neo4j response to return the QID as present in the target language.
    """
    # Mock Neo4jManager to return a hit for this language
    mock_neo_response = {
        lang: [{"qid": qid, "neighbor_qids": []}] # Simplified: no neighbors needed for this test
    }
    
    with patch('app.api.routers.concept.Neo4jManager') as MockNeo:
        instance = MockNeo.return_value
        instance.query_all.return_value = mock_neo_response
        
        try:
            result = await get_concept(qid=qid)
            return result
        except Exception as e:
            # handle 404s or other errors gracefully for the test
            return None

def test_integration(lang, num_requests=2000, max_workers=10): # Scaled down slightly for full integration test speed
    logger.info(f"--- Starting Router Integration Test for {lang.upper()} ---")
    
    qids = get_random_qids(lang, num_requests)
    if not qids: return 0.0
    
    logger.info(f"Testing {len(qids)} QIDs...")
    
    results = []
    start_time = time.perf_counter()
    
    # We need a helper to run async code in threads
    def worker(qid):
        return asyncio.run(run_router_test(lang, qid))

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(worker, qid): qid for qid in qids}
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    end_time = time.perf_counter()
    total_time = end_time - start_time
    
    # Validation
    valid_responses = 0
    has_infobox = 0
    is_null = 0
    structure_errors = 0
    
    for r in results:
        if r:
            valid_responses += 1
            # Check Structure
            if "infoboxes" not in r:
                structure_errors += 1
                continue
                
            ib_data = r["infoboxes"].get(lang)
            
            if ib_data is None:
                is_null += 1
            elif isinstance(ib_data, list):
                has_infobox += 1
            else:
                structure_errors += 1
                logger.error(f"Invalid infobox type: {type(ib_data)}")

    success_rate = (valid_responses / len(qids)) * 100
    infobox_yield = (has_infobox / valid_responses * 100) if valid_responses else 0
    throughput = len(qids) / total_time
    
    logger.info(f"Results for {lang.upper()}:")
    logger.info(f"  Valid Responses: {valid_responses}/{len(qids)}")
    logger.info(f"  Structure Errors: {structure_errors}")
    logger.info(f"  Infobox Present: {has_infobox} ({infobox_yield:.2f}%)")
    logger.info(f"  Infobox Null:    {is_null}")
    logger.info(f"  Throughput:      {throughput:.2f} req/sec")
    
    return infobox_yield

if __name__ == "__main__":
    # Test DE
    yield_de = test_integration('de')
    # Test PL
    yield_pl = test_integration('pl')
    
    # Final Sanity Check
    if yield_de > 0 and yield_pl > 0:
        logger.info("INTEGRATION TEST PASSED: Router correctly serves infoboxes.")
        sys.exit(0)
    else:
        logger.error("INTEGRATION TEST FAILED: No infoboxes found or errors occurred.")
        sys.exit(1)
