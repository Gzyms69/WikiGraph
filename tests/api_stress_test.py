import requests
import time
import sys
import json

BASE_URL = "http://localhost:8000"

def log_test(name, success, data=None):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"[{status}] {name}")
    if not success and data:
        print(f"      Detail: {data}")

def run_suite():
    print("🧪 WIKIGRAPH API ULTIMATE TEST SUITE")
    print("="*40)

    # 1. Health & Init
    try:
        r = requests.get(f"{BASE_URL}/")
        log_test("API Health Check", r.status_code == 200)
        
        r = requests.post(f"{BASE_URL}/analytics/initialize")
        log_test("GDS Initialization", r.status_code == 200)
    except Exception as e:
        print(f"❌ Critical Error: Could not connect to API. {e}")
        return

    # 2. Search & UTF-8
    # Testing Polish special chars and case insensitivity
    r = requests.get(f"{BASE_URL}/search/keyword?q=Kraków")
    log_test("Search: Polish UTF-8 (Kraków)", r.status_code == 200 and len(r.json()['results']) > 0)
    
    r = requests.get(f"{BASE_URL}/search/keyword?q=berlin")
    log_test("Search: Case Insensitivity (berlin)", r.status_code == 200 and len(r.json()['results']) > 0)

    # 3. Interlingual Traversal
    start, end = "Warszawa", "München"
    r = requests.get(f"{BASE_URL}/graph/shortest-path?start={start}&end={end}&lang=pl")
    if r.status_code == 200:
        hops = r.json().get('hops', 0)
        log_test(f"Traversal: {start}(PL) -> {end}(DE)", hops > 0, f"Found in {hops} hops")
    else:
        log_test(f"Traversal: {start} -> {end}", False, r.text)

    # 4. Advanced Analytics
    r = requests.post(f"{BASE_URL}/analytics/pagerank?limit=1")
    log_test("Analytics: PageRank", r.status_code == 200)

    r = requests.post(f"{BASE_URL}/analytics/bridges?limit=1")
    log_test("Analytics: Bridge Detection (Betweenness)", r.status_code == 200)

    r = requests.post(f"{BASE_URL}/analytics/k-core?limit=1")
    log_test("Analytics: K-Core Backbone", r.status_code == 200)

    # 5. Gap Analysis
    r = requests.get(f"{BASE_URL}/analytics/gaps?source_lang=de&target_lang=pl&limit=1")
    log_test("Research: Cross-Lingual Gap Analysis", r.status_code == 200)

    # 6. AI/ML Readiness
    r = requests.post(f"{BASE_URL}/ml/embeddings?limit=1&dimensions=32")
    if r.status_code == 200:
        dim = len(r.json()['embeddings'][0]['embedding'])
        log_test("ML: FastRP Embeddings (32-dim)", dim == 32)
    else:
        log_test("ML: Embeddings", False, r.text)

    r = requests.get(f"{BASE_URL}/graph/recommendations?title=Polska&lang=pl&limit=3")
    log_test("Personalization: PPR Recommendations", r.status_code == 200)

    print("="*40)
    print("🏁 TEST SUITE COMPLETE")

if __name__ == "__main__":
    run_suite()
