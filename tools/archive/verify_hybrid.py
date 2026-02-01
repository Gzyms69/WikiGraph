import requests
import json

API_BASE = "http://localhost:8000"
TEST_QID = "Q102317" # Kielce

def test_hybrid():
    print("Testing /graph/weighted-neighbors...")
    payload = {
        "qid": TEST_QID,
        "lang": "pl",
        "limit": 15,
        "weights": {"jaccard": 1.0, "adamic_adar": 1.0, "ppr": 0.5},
        "algorithms": ["jaccard", "adamic_adar", "ppr"]
    }
    
    try:
        resp = requests.post(f"{API_BASE}/graph/weighted-neighbors", json=payload)
        if resp.status_code == 200:
            print("✅ Success!")
            data = resp.json()
            print(f"Found {len(data['neighbors'])} neighbors.")
            for n in data['neighbors'][:5]:
                print(f" - {n['title']} (Score: {n['score']:.4f})")
        else:
            print(f"❌ Failed: {resp.status_code}")
            print(resp.text)
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_hybrid()
