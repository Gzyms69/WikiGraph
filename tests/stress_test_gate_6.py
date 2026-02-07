import httpx
import asyncio
import time
import statistics
import logging
from collections import defaultdict

# Setup
BASE_URL = "http://localhost:8000/api/v1"
CONCURRENCY = 10
ITERATIONS = 50

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("StressTest")

# Test Data
CASES = [
    # 1. Health (Low cost)
    ("GET", "/health", {}, "Health"),
    
    # 2. Search (FTS5) - High performance
    ("GET", "/search/pl", {"q": "Warszawa"}, "Search (Hit)"),
    ("GET", "/search/de", {"q": "Berlin"}, "Search (Hit DE)"),
    ("GET", "/search/pl", {"q": "xyz_non_existent_string_123"}, "Search (Miss)"),
    
    # 3. Compare (Parallel SQLite)
    ("GET", "/compare/Q36", {"langs": "pl,de,es"}, "Compare (Poland)"),
    ("GET", "/compare/Q64", {"langs": "pl,de"}, "Compare (Berlin)"),
    
    # 4. Graph Neighbors (Adamic-Adar) - Neo4j Compute
    ("GET", "/graph/neighbors/scored/pl/Q36", {"metric": "adamic_adar", "limit": 10}, "Graph (Poland AA)"),
    ("GET", "/graph/neighbors/scored/de/Q64", {"metric": "jaccard", "limit": 10}, "Graph (Berlin Jaccard)"),
    
    # 5. Pathfinding (BFS) - Variable Depth
    ("GET", "/graph/path/shortest/pl", {"from_qid": "Q36", "to_qid": "Q64", "max_depth": 6}, "Path (Short 6)"),
    ("GET", "/graph/path/shortest/pl", {"from_qid": "Q36", "to_qid": "Q64", "max_depth": 12}, "Path (Medium 12)"),
    # Note: Very deep paths might timeout, we test robustness here.
]

async def run_request(client, method, endpoint, params, name):
    start = time.time()
    try:
        if method == "GET":
            response = await client.get(f"{BASE_URL}{endpoint}", params=params, timeout=30.0)
        
        duration = (time.time() - start) * 1000
        return {
            "name": name,
            "status": response.status_code,
            "duration": duration,
            "success": response.status_code == 200,
            "size": len(response.content)
        }
    except Exception as e:
        return {
            "name": name,
            "status": 0,
            "duration": (time.time() - start) * 1000,
            "success": False,
            "error": str(e),
            "size": 0
        }

async def stress_test():
    logger.info(f"🚀 Starting Stress Test: {CONCURRENCY} concurrent workers, {ITERATIONS} iterations per worker.")
    
    stats = defaultdict(list)
    
    async with httpx.AsyncClient(limits=httpx.Limits(max_connections=CONCURRENCY)) as client:
        tasks = []
        for _ in range(ITERATIONS):
            for method, endpoint, params, name in CASES:
                tasks.append(run_request(client, method, endpoint, params, name))
        
        # Shuffle tasks? No, let's hammer it sequentially per iteration to simulate load
        # Actually asyncio.gather runs them concurrently.
        
        # We will split into batches to avoid OS file limit
        batch_size = 50
        results = []
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i+batch_size]
            results.extend(await asyncio.gather(*batch))
            print(f"Processed {len(results)}/{len(tasks)} requests...", end="\r")

    print("\n✅ Test Complete. Analyzing...")
    
    # Analysis
    report = {}
    for r in results:
        name = r["name"]
        stats[name].append(r)

    print(f"\n{'NAME':<25} | {'REQ':<5} | {'SUCC':<5} | {'P95 (ms)':<8} | {'AVG (ms)':<8} | {'ERRORS'}")
    print("-" * 80)
    
    for name, data in stats.items():
        durations = [d['duration'] for d in data]
        successes = [d for d in data if d['success']]
        errors = [d for d in data if not d['success']]
        
        avg = statistics.mean(durations)
        p95 = statistics.quantiles(durations, n=20)[18] if len(durations) > 20 else sorted(durations)[int(len(durations)*0.95)]
        
        print(f"{name:<25} | {len(data):<5} | {len(successes):<5} | {p95:<8.2f} | {avg:<8.2f} | {len(errors)}")
        if errors:
            print(f"   ⚠️ Last Error: {errors[-1].get('error') or errors[-1].get('status')}")

if __name__ == "__main__":
    asyncio.run(stress_test())