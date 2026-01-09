import requests
import time

API_BASE = "http://localhost:8000"
TEST_QID = "Q170715" # Kielce
ALGORITHMS = ["jaccard", "adamic_adar", "ppr"]

def test_algo(algo):
    print(f"--- Testing Algorithm: {algo} ---")
    start = time.time()
    try:
        resp = requests.get(f"{API_BASE}/graph/neighbors", params={
            "qid": TEST_QID,
            "algorithm": algo,
            "limit": 15,
            "lang": "pl"
        }, timeout=30)
        duration = time.time() - start
        if resp.status_code == 200:
            data = resp.json()
            print(f"Success! Found {len(data.get('neighbors', []))} neighbors in {duration:.2f}s")
            for nb in data.get('neighbors', [])[:3]:
                print(f"  - {nb['title']} (Score: {nb.get('score', 0):.4f})")
        else:
            print(f"Failed! Status: {resp.status_code}, Error: {resp.text}")
    except Exception as e:
        print(f"Error: {str(e)}")
    print("\n")

if __name__ == "__main__":
    for algo in ALGORITHMS:
        test_algo(algo)
