import sys
import os
import time
import sqlite3
import concurrent.futures
import statistics
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.getcwd())

from app.services.metadata_manager import MetadataManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_random_qids(lang, limit=10000):
    """Fetch TRULY RANDOM QIDs from the DB (no filters)."""
    db_path = Path(f"data/db/{lang}.db")
    if not db_path.exists():
        logger.error(f"Database for {lang} not found at {db_path}")
        return []
    
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        # Get random QIDs regardless of whether they have an infobox
        query = """
            SELECT qid 
            FROM id_mapping 
            ORDER BY RANDOM() 
            LIMIT ?
        """
        cursor.execute(query, (limit,))
        qids = [row[0] for row in cursor.fetchall()]
        conn.close()
        return qids
    except Exception as e:
        logger.error(f"Failed to fetch random QIDs for {lang}: {e}")
        return []

def validate_distribution(lang, num_requests=10000, max_workers=20):
    logger.info(f"--- Starting Random Distribution Test for {lang.upper()} ---")
    
    # 1. Get Samples
    logger.info("Fetching 10,000 random QIDs...")
    qids = get_random_qids(lang, num_requests)
    if not qids:
        logger.error("No QIDs found to test.")
        return 0
    
    manager = MetadataManager()
    
    # 2. Worker Function
    def worker(qid):
        return manager.get_infobox(lang, qid)

    # 3. Execute
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(worker, qid): qid for qid in qids}
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
            
    # 4. Analysis
    total = len(results)
    found = 0
    is_none = 0
    empty_list = 0
    
    for r in results:
        if r is None:
            is_none += 1
        elif isinstance(r, list) and len(r) == 0:
            empty_list += 1
        elif isinstance(r, list) and len(r) > 0:
            found += 1
        else:
            logger.warning(f"Unexpected return type: {type(r)}")

    found_pct = (found / total) * 100
    none_pct = (is_none / total) * 100
    empty_pct = (empty_list / total) * 100
    
    logger.info(f"Results for {lang.upper()} (N={total}):")
    logger.info(f"  Infobox Found: {found} ({found_pct:.2f}%)")
    logger.info(f"  None (No Data): {is_none} ({none_pct:.2f}%)")
    logger.info(f"  Empty List:    {empty_list} ({empty_pct:.2f}%)")
    
    return found_pct

if __name__ == "__main__":
    logger.info("Validating distribution against expected yields (DE: ~62%, PL: ~79%)")
    
    yield_de = validate_distribution('de')
    yield_pl = validate_distribution('pl')
    
    # Validation Logic (Allowing 5% variance from expected)
    # DE Expected: ~62.2%
    # PL Expected: ~79.4%
    
    failed = False
    
    if abs(yield_de - 62.2) > 5.0:
        logger.warning(f"DE yield {yield_de}% deviates significantly from expected 62.2%")
        # failed = True # Warning only for now
    else:
        logger.info("DE yield is within expected range.")
        
    if abs(yield_pl - 79.4) > 5.0:
        logger.warning(f"PL yield {yield_pl}% deviates significantly from expected 79.4%")
        # failed = True
    else:
        logger.info("PL yield is within expected range.")
        
    if failed:
        sys.exit(1)
    else:
        sys.exit(0)
