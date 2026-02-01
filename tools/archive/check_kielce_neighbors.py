import requests
import sys
import json

API_URL = "http://localhost:8000/graph/neighbors"

def check_neighbors_api(qid):
    params = {
        "qid": qid,
        "lang": "pl",
        "limit": 20
    }
    
    print(f"🔍 Calling API for {qid} (Kielce)...")
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        neighbors = data.get("neighbors", [])
        
        if not neighbors:
            print("❌ No neighbors found!")
        else:
            print(f"✅ Found {len(neighbors)} neighbors (via API):")
            for n in neighbors:
                # API returns 'score' if updated, let's check
                score_str = f"[{n.get('score', 0):.4f}] " if 'score' in n else ""
                print(f"   {score_str}{n['title']} ({n['qid']}) - Lang: {n['lang']}")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ API Request Failed: {e}")
        if e.response:
            print(f"Response: {e.response.text}")

if __name__ == "__main__":
    check_neighbors_api("Q102317") # Correct QID for Kielce