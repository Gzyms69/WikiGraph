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

def get_real_qids(lang, limit=10000):
    """Fetch real QIDs that have infoboxes from the DB."""
    db_path = Path(f"data/db/{lang}.db")
    if not db_path.exists():
        logger.error(f"Database for {lang} not found at {db_path}")
        return []
    
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        # Get QIDs that actually have data to test parsing/retrieval
        query = """
            SELECT m.qid 
            FROM id_mapping m 
            JOIN pages p ON m.page_id = p.page_id 
            WHERE p.infobox IS NOT NULL 
            ORDER BY RANDOM() 
            LIMIT ?
        """
        cursor.execute(query, (limit,))
        qids = [row[0] for row in cursor.fetchall()]
        conn.close()
        return qids
    except Exception as e:
        logger.error(f"Failed to fetch sample QIDs for {lang}: {e}")
        return []

def benchmark_lang(lang, num_requests=10000, max_workers=20):
    logger.info(f"--- Starting Benchmark for {lang.upper()} ---")
    
    # 1. Get Samples
    logger.info("Fetching sample QIDs...")
    qids = get_real_qids(lang, num_requests)
    if not qids:
        logger.error("No QIDs found to test.")
        return
    
    logger.info(f"Loaded {len(qids)} QIDs. Starting concurrent requests with {max_workers} workers...")
    
    manager = MetadataManager()
    
    # 2. Worker Function
    def worker(qid):
        start = time.perf_counter()
        result = manager.get_infobox(lang, qid)
        end = time.perf_counter()
        return (result is not None, (end - start) * 1000) # Duration in ms

    # 3. Execute
    results = []
    start_total = time.perf_counter()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(worker, qid): qid for qid in qids}
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
            
    end_total = time.perf_counter()
    total_time = end_total - start_total
    
    # 4. Metrics
    successes = [r for r in results if r[0]]
    failures = [r for r in results if not r[0]]
    latencies = [r[1] for r in results]
    
    success_rate = (len(successes) / len(results)) * 100
    p50 = statistics.median(latencies)
    p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else 0
    p99 = statistics.quantiles(latencies, n=100)[98] if len(latencies) > 100 else 0
    throughput = len(results) / total_time
    
    logger.info(f"Results for {lang.upper()}:")
    logger.info(f"  Total Requests: {len(results)}")
    logger.info(f"  Success Rate:   {success_rate:.2f}%")
    logger.info(f"  Throughput:     {throughput:.2f} req/sec")
    logger.info(f"  Latency P50:    {p50:.3f} ms")
    logger.info(f"  Latency P95:    {p95:.3f} ms")
    logger.info(f"  Latency P99:    {p99:.3f} ms")
    
    return success_rate

if __name__ == "__main__":
    success_de = benchmark_lang('de')
    success_pl = benchmark_lang('pl')
    
    if success_de > 95 and success_pl > 95:
        logger.info("TEST PASSED: High availability confirmed.")
        sys.exit(0)
    else:
        logger.error("TEST FAILED: Success rate below threshold.")
        # We don't exit 1 strictly because the DB might just have NULLs even if we filtered, 
        # but since we filtered for IS NOT NULL, we expect near 100% success.
        sys.exit(1)
