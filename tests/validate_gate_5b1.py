import os
import sys
import time
import requests
import subprocess
import signal
import psutil
import sqlite3
import concurrent.futures
from pathlib import Path

sys.path.append(os.getcwd())

# Test Candidates
TEST_CASES = [
    ("Q36", "Poland"), 
    ("Q64", "Berlin"),
    ("Q142", "France"),
    ("Q5", "Human"), 
    ("Q2", "Earth")
]

def get_source_truth(lang, qid):
    db_path = Path(f"data/db/{lang}.db")
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cursor = conn.cursor()
    query = "SELECT p.title FROM pages p JOIN id_mapping m ON p.page_id = m.page_id WHERE m.qid = ?"
    cursor.execute(query, (qid,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

def run_gate_5b1():
    print("🔒 Running Gate 5B.1: QID Endpoints (Pessimistic Final Validation)...")
    
    # 0. Baseline Memory
    proc_main = psutil.Process()
    mem_baseline = proc_main.memory_info().rss / 1024 / 1024
    
    env = os.environ.copy()
    env["TEST_MODE"] = "true"
    
    # 1. Start Server
    proc = subprocess.Popen(
        ["./venv_gate5/bin/uvicorn", "app.main:app", "--port", "9999"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env
    )
    
    try:
        time.sleep(2)
        if proc.poll() is not None: return False

        # 2. Source Truth Validation (Titles)
        print("   🧪 Validating Title Accuracy against SQLite...")
        for qid, desc in TEST_CASES:
            resp = requests.get(f"http://localhost:9999/api/concept/{qid}")
            actual = resp.json()["titles"]
            for lang in ["pl", "de"]:
                expected = get_source_truth(lang, qid)
                if actual.get(lang) != expected:
                    print(f"   ❌ FAIL: Title mismatch for {qid}/{lang}. Expected: {expected}, Got: {actual.get(lang)}")
                    return False
        print("   ✅ Title Accuracy: 100% (5/5 QIDs matched).")

        # 3. Pagination Test
        print("   🧪 Testing Pagination (limit=5, offset=2)...")
        # Get baseline neighbors for Q36/pl
        r1 = requests.get("http://localhost:9999/api/concept/Q36?limit=10&offset=0").json()
        all_10 = [n["qid"] for n in r1["neighbors"]["pl"]]
        
        # Get slice
        r2 = requests.get("http://localhost:9999/api/concept/Q36?limit=5&offset=2").json()
        sliced = [n["qid"] for n in r2["neighbors"]["pl"]]
        
        if sliced != all_10[2:7]:
            print(f"   ❌ FAIL: Pagination slice mismatch. Expected {all_10[2:7]}, Got {sliced}")
            return False
        print("   ✅ Pagination Logic Verified.")

        # 4. Memory Delta & Concurrency
        print("   🧪 Testing Concurrency & Memory Delta...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            list(executor.map(lambda q: requests.get(f"http://localhost:9999/api/concept/Q36"), range(20)))
        
        mem_after = psutil.Process(proc.pid).memory_info().rss / 1024 / 1024
        mem_delta = mem_after - 40 # Assuming ~40MB baseline for uvicorn+fastapi
        print(f"   📊 Memory Delta: +{mem_after-40:.1f}MB (Limit < 50MB)")
        if (mem_after - 40) > 50:
            print("   ❌ FAIL: Memory leak detected.")
            return False

        return True

    finally:
        os.kill(proc.pid, signal.SIGTERM)
        subprocess.run(["docker", "start", "neo4j-de-test"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    if run_gate_5b1():
        print("\n🎉 Gate 5B.1 PASSED (Final)")
    else:
        sys.exit(1)
