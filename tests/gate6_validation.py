import requests
import time
import concurrent.futures
import statistics

BASE_URL = "http://localhost:8000"
LANGS = ["pl", "de", "es"]

def check(name, condition, details=""):
    status = "✅ PASS" if condition else "❌ FAIL"
    print(f"[{status}] {name} {details}")
    return condition

def test_integrity():
    print("\n=== PHASE 1: INTEGRITY CHECKS ===")
    # Jaccard Bounds
    r = requests.get(f"{BASE_URL}/api/v1/graph/neighbors/scored/pl/Q42?metric=jaccard&limit=5")
    if r.ok:
        scores = [x['score'] for x in r.json()]
        valid = all(0.0 <= s <= 1.0 for s in scores)
        check("Jaccard Bounds (0-1)", valid, f"Max: {max(scores) if scores else 0}")
    
    # Path connectivity
    r = requests.get(f"{BASE_URL}/api/v1/graph/path/shortest/pl?from_qid=Q42&to_qid=Q64")
    if r.ok:
        path = r.json()
        check("Shortest Path Connectivity", len(path) > 1, f"Length: {len(path)}")

def test_hub_safety():
    print("\n=== PHASE 2: HUB SAFETY (Earth Q2) ===")
    for lang in LANGS:
        t0 = time.time()
        # RA is the heaviest query
        r = requests.get(f"{BASE_URL}/api/v1/graph/neighbors/scored/{lang}/Q2?metric=resource_allocation&limit=5", timeout=20)
        dt = time.time() - t0
        check(f"Hub Safety ({lang.upper()})", r.ok and dt < 15, f"Time: {dt:.2f}s")

def test_cross_lang():
    print("\n=== PHASE 3: CROSS-LANGUAGE PARITY ===")
    results = {}
    for lang in LANGS:
        r = requests.get(f"{BASE_URL}/api/v1/entity/{lang}/Q42")
        if r.ok:
            data = r.json()
            results[lang] = len(data.get("neighbors", []))
            print(f"  {lang.upper()} Neighbors: {results[lang]}")
    
    check("Data Consistency", all(v > 0 for v in results.values()), "All langs have data")

def stress_task(i):
    try:
        r = requests.get(f"{BASE_URL}/api/v1/search/pl?q=Douglas")
        return r.status_code
    except:
        return 0

def test_concurrency():
    print("\n=== PHASE 4: CONCURRENCY SMOKE (20 Req) ===")
    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(stress_task, i) for i in range(20)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    dt = time.time() - t0
    success_rate = results.count(200) / len(results) * 100
    check("Concurrency Flood", success_rate == 100, f"Rate: {success_rate}% in {dt:.2f}s")

if __name__ == "__main__":
    try:
        # Ensure GDS projections exist (Lazy init via endpoints might fail if not projected)
        # We assume previous tests or dev.sh hook handled it, or we rely on the service to handle it?
        # Actually, Jaccard REQUIRES projection. Let's trigger one via exec just in case.
        import subprocess
        for lang in LANGS:
            subprocess.run(f"docker exec wikigraph-neo4j-{lang} cypher-shell -u neo4j -p wikigraph \"CALL gds.graph.exists('similarity-graph') YIELD exists; CALL gds.graph.drop('similarity-graph', false); CALL gds.graph.project('similarity-graph', 'Concept', 'LINKS_TO')\"", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        test_integrity()
        test_hub_safety()
        test_cross_lang()
        test_concurrency()
    except Exception as e:
        print(f"FATAL ERROR: {e}")
