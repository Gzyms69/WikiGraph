import requests
import sys

BASE_URL = "http://localhost:8000"
LANGS = ["pl", "de", "es"]
QID = "Q42"

def check(name, condition, msg=""):
    print(f"[{'PASS' if condition else 'FAIL'}] {name} {msg}")

def test_lang(lang):
    print(f"
--- Testing {lang.upper()} ---")
    
    # 1. Fetch All
    r = requests.get(f"{BASE_URL}/api/v1/graph/metrics/{lang}/{QID}")
    if not r.ok:
        print(f"FAIL: Baseline fetch failed {r.status_code}")
        return
        
    full_data = r.json().get("metrics", {})
    if not full_data:
        print("WARN: No metrics found for this node")
        return

    # 2. Test Individual Keys
    keys = ["pagerank", "triangle_count"] # Common keys
    for k in keys:
        if k not in full_data: continue
        
        r_single = requests.get(f"{BASE_URL}/api/v1/graph/metrics/{lang}/{QID}?key={k}")
        single_data = r_single.json().get("metrics", {})
        
        # Verify only 1 key
        is_single = len(single_data) == 1 and k in single_data
        # Verify value match
        is_match = single_data[k] == full_data[k]
        
        check(f"Filter {k}", is_single and is_match, f"Value: {single_data[k]}")

    # 3. Test Invalid Key
    r_inv = requests.get(f"{BASE_URL}/api/v1/graph/metrics/{lang}/{QID}?key=INVALID_METRIC")
    inv_data = r_inv.json().get("metrics", {})
    check("Invalid Key", len(inv_data) == 0, "Should be empty")

if __name__ == "__main__":
    try:
        # Check if backend is up
        requests.get(f"{BASE_URL}/api/health")
        for l in LANGS:
            test_lang(l)
    except Exception as e:
        print(f"Test Aborted: {e}")
