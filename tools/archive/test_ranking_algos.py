import requests
import sys
import json

API_URL = "http://127.0.0.1:8000/graph/neighbors"
QID = "Q102317" # Kielce

def test_algo(algo_name):
    print(f"\n--- Testing Algorithm: {algo_name.upper()} ---")
    params = {
        "qid": QID,
        "lang": "pl",
        "limit": 10,
        "algorithm": algo_name
    }
    
    try:
        response = requests.get(API_URL, params=params, timeout=60) # Increased timeout
        response.raise_for_status()
        data = response.json()
        
        neighbors = data.get("neighbors", [])
        if not neighbors:
            print("❌ No neighbors found!")
            return

        for i, n in enumerate(neighbors):
            score = n.get('score', 0)
            print(f" {i+1}. [{score:.4f}] {n['title']} ({n['qid']})")
            
    except Exception as e:
        print(f"❌ Failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(e.response.text)

if __name__ == "__main__":
    print(f"🔍 Comparing Ranking Algorithms for {QID} (Kielce)...")
    test_algo("jaccard")
    test_algo("adamic_adar")
    test_algo("ppr")
