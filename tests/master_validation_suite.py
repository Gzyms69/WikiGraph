import requests
import time
import sys
import json
import subprocess

BASE_URL = "http://localhost:8000"

# --- UTILS ---
def log(msg, status="INFO"):
    print(f"[{status}] {msg}")

def check(name, condition, details=""):
    status = "✅ PASS" if condition else "❌ FAIL"
    log(f"{name}: {details}", status)
    return condition

def run_gds_projection(lang):
    log(f"Projecting GDS for {lang}...", "SETUP")
    # Use triple quotes for the python string to handle inner quotes easily
    cmd = f"""docker exec wikigraph-neo4j-{lang} cypher-shell -u neo4j -p wikigraph "CALL gds.graph.exists('similarity-graph') YIELD exists; CALL gds.graph.drop('similarity-graph', false); CALL gds.graph.project('similarity-graph', 'Concept', 'LINKS_TO')" """
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# --- PHASE 1: ENDPOINT MATRIX ---
def test_endpoints(lang, qid):
    log(f"Testing Endpoints for {lang}...", "PHASE 1")
    
    endpoints = [
        (f"/api/health", "Health"),
        (f"/api/v1/search/{lang}?q=Douglas", "Search"),
        (f"/api/v1/entity/{lang}/{qid}", "Entity"),
        (f"/api/v1/graph/metrics/{lang}/{qid}", "Metrics"),
        (f"/api/v1/graph/path/shortest/{lang}?from_qid={qid}&to_qid=Q64", "Path"),
        (f"/api/v1/graph/neighbors/scored/{lang}/{qid}?metric=jaccard", "Neighbors (Jaccard)"),
        (f"/api/v1/graph/neighbors/scored/{lang}/{qid}?metric=resource_allocation", "Neighbors (RA)"),
        (f"/api/v1/graph/neighbors/scored/{lang}/{qid}?metric=adamic_adar", "Neighbors (AA)")
    ]

    for path, name in endpoints:
        t0 = time.time()
        try:
            r = requests.get(f"{BASE_URL}{path}", timeout=20)
            dt = time.time() - t0
            
            # Validation Logic
            valid = r.ok
            if "Neighbors" in name and valid:
                try:
                    data = r.json()
                    valid = isinstance(data, list)
                except: valid = False
            elif "Metrics" in name and valid:
                try:
                    data = r.json()
                    valid = "metrics" in data and "pagerank" in data["metrics"]
                except: valid = False
            elif "Path" in name and valid:
                try:
                    data = r.json()
                    valid = len(data) > 0
                except: valid = False
            
            check(f"{name} ({lang})", valid, f"{dt:.2f}s | Status: {r.status_code}")
        except Exception as e:
            check(f"{name} ({lang})", False, f"Exception: {e}")

# --- PHASE 2: ALGORITHM VERIFICATION ---
def test_algorithms(lang, qid):
    log(f"Verifying Algorithms for {lang}...", "PHASE 2")
    
    # 1. Jaccard (GDS) - Check Bounds
    try:
        r = requests.get(f"{BASE_URL}/api/v1/graph/neighbors/scored/{lang}/{qid}?metric=jaccard")
        if r.ok:
            scores = [x['score'] for x in r.json()]
            valid_bounds = all(0.0 <= s <= 1.0 for s in scores)
            check("Jaccard Bounds", valid_bounds, f"Max: {max(scores) if scores else 0}")
    except: pass
    
    # 2. Metrics - Check Values
    try:
        r = requests.get(f"{BASE_URL}/api/v1/graph/metrics/{lang}/{qid}")
        if r.ok:
            m = r.json().get("metrics", {})
            check("PageRank > 0", m.get("pagerank", 0) > 0, str(m.get("pagerank")))
            check("Triangle Count >= 0", m.get("triangle_count", -1) >= 0, str(m.get("triangle_count")))
    except: pass

# --- PHASE 3: ERROR HANDLING ---
def test_errors(lang):
    log(f"Testing Error Handling for {lang}...", "PHASE 3")
    
    # Invalid QID
    try:
        r = requests.get(f"{BASE_URL}/api/v1/entity/{lang}/INVALID_QID")
        check("Invalid QID -> 422/404", r.status_code in [404, 422], f"Got {r.status_code}")
    except: pass
    
    # Missing Param
    try:
        r = requests.get(f"{BASE_URL}/api/v1/search/{lang}")
        check("Missing Param -> 422", r.status_code == 422, f"Got {r.status_code}")
    except: pass

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 master_validation_suite.py <lang> <qid>")
        sys.exit(1)
        
    lang = sys.argv[1]
    qid = sys.argv[2]
    
    # Ensure GDS Project
    run_gds_projection(lang)
    
    test_endpoints(lang, qid)
    test_algorithms(lang, qid)
    test_errors(lang)