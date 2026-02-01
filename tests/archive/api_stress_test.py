import requests
import time
import sys
import json
import random

BASE_URL = "http://localhost:8000"

def log_test(name, success, data=None):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"[{status}] {name}")
    if not success and data:
        print(f"      Detail: {data}")

def run_suite():
    print("🧪 WIKIGRAPH API AGNOSTIC TEST SUITE")
    print("="*40)

    # 1. Health Check
    try:
        r = requests.get(f"{BASE_URL}/")
        log_test("API Health Check", r.status_code == 200)
    except Exception as e:
        print(f"❌ Critical Error: Could not connect to API. {e}")
        return

    # 2. Dynamic Language Discovery (The Agnostic Fix)
    try:
        r = requests.get(f"{BASE_URL}/graph/languages")
        log_test("Language Discovery", r.status_code == 200)
        langs = r.json().get("languages", [])
        
        if not langs:
            print("⚠️ No languages found in DB. Ingest data first!")
            return
            
        print(f"   ℹ️  Detected Languages: {langs}")
        primary_lang = langs[0] # Use the first one found
        
        # Determine secondary language for gap analysis (if exists)
        secondary_lang = langs[1] if len(langs) > 1 else primary_lang
        
    except Exception as e:
        log_test("Language Discovery", False, str(e))
        return

    # 3. GDS Init
    try:
        r = requests.post(f"{BASE_URL}/analytics/initialize")
        log_test("GDS Initialization", r.status_code == 200)
    except:
        pass # Might already be initialized

    # 4. Search (Explicit Language Required now)
    # We query for a common letter 'a' just to verify the endpoint works for the lang
    r = requests.get(f"{BASE_URL}/search/keyword?q=a&lang={primary_lang}")
    log_test(f"Search ({primary_lang}): Basic Query", r.status_code == 200)
    
    if r.status_code == 200 and len(r.json()['results']) > 0:
        # Get a real title to use for subsequent tests
        test_node_title = r.json()['results'][0]['title']
        print(f"   ℹ️  Using test node: '{test_node_title}'")
    else:
        test_node_title = "Physics" # Fallback, might fail if not exists
        print("   ⚠️  Search returned empty, using fallback title.")

    # 5. Interlingual Traversal (Only if we have 2 langs or just test logic)
    # We'll just test the endpoint structure. Finding a valid path randomly is hard.
    # We assume 'start' exists.
    r = requests.get(f"{BASE_URL}/graph/shortest-path?start={test_node_title}&end={test_node_title}&lang={primary_lang}")
    # 404 is acceptable if path not found, but 422/500 is not.
    # Actually, path to self should be 0 hops or handled.
    log_test(f"Traversal Endpoint ({primary_lang})", r.status_code in [200, 404], f"Status: {r.status_code} | Body: {r.text}")

    # 6. Advanced Analytics
    r = requests.post(f"{BASE_URL}/analytics/pagerank?limit=1")
    log_test("Analytics: PageRank", r.status_code == 200, r.text)

    r = requests.post(f"{BASE_URL}/analytics/bridges?limit=1")
    log_test("Analytics: Bridge Detection", r.status_code == 200, r.text)

    # 7. Gap Analysis (Dynamic Params)
    r = requests.get(f"{BASE_URL}/analytics/gaps?source_lang={primary_lang}&target_lang={secondary_lang}&limit=1")
    log_test(f"Gap Analysis ({primary_lang} -> {secondary_lang})", r.status_code == 200, r.text)

    # 8. AI/ML Readiness
    r = requests.post(f"{BASE_URL}/ml/embeddings?limit=1&dimensions=32")
    log_test("ML: FastRP Embeddings", r.status_code == 200, r.text)

    # 9. Recommendations (Personalization)
    # Requires explicit lang now
    r = requests.get(f"{BASE_URL}/graph/recommendations?title={test_node_title}&lang={primary_lang}&limit=3")
    log_test(f"Recommendations ({primary_lang})", r.status_code == 200)

    print("="*40)
    print("🏁 TEST SUITE COMPLETE")

if __name__ == "__main__":
    run_suite()