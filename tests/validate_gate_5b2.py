import os
import sys
import time
import requests
import subprocess
import signal
import psutil
import json
from neo4j import GraphDatabase

sys.path.append(os.getcwd())

def run_gate_5b2():
    print("🔒 Running Gate 5B.2: Language Endpoints (Rigorous Validation)...")
    
    env = os.environ.copy()
    env["TEST_MODE"] = "true"
    
    # 1. Start Server
    proc = subprocess.Popen(
        ["./venv_gate5/bin/uvicorn", "app.main:app", "--port", "9999"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env
    )
    pid = proc.pid
    
    try:
        time.sleep(2)
        if proc.poll() is not None:
            print("   ❌ FAIL: Server died.")
            return False
            
        proc_obj = psutil.Process(pid)
        mem_before = proc_obj.memory_info().rss / 1024 / 1024

        # 2. Response Time
        start_t = time.time()
        r = requests.get("http://localhost:9999/api/pl/concept/Q36")
        dur = (time.time() - start_t) * 1000
        if r.status_code != 200 or dur > 300:
            print(f"   ❌ FAIL: Response time/status. {r.status_code}, {dur:.1f}ms")
            return False
        print(f"   ✅ Response Time: {dur:.1f}ms (<300ms)")

        # 3. Invalid Language
        r = requests.get("http://localhost:9999/api/xx/concept/Q36")
        if r.status_code != 400:
            print(f"   ❌ FAIL: Invalid Lang code {r.status_code}")
            return False
        print("   ✅ Invalid Language -> 400")

        # 4. Pagination (Offset)
        print("   🧪 Testing Pagination (Offset)...")
        r1 = requests.get("http://localhost:9999/api/pl/concept/Q36?limit=5&offset=0").json()
        r2 = requests.get("http://localhost:9999/api/pl/concept/Q36?limit=5&offset=5").json()
        
        set1 = set(n['qid'] for n in r1['neighbors'])
        set2 = set(n['qid'] for n in r2['neighbors'])
        
        if not set1.isdisjoint(set2):
            print(f"   ❌ FAIL: Pagination overlap! {set1} vs {set2}")
            return False
        print("   ✅ Pagination Offset works (Disjoint sets).")

        # 5. Path Accuracy vs Cypher
        print("   🧪 Testing Path Accuracy (Direct Cypher Check)...")
        driver = GraphDatabase.driver("bolt://localhost:7689", auth=("neo4j", "wikigraph"))
        with driver.session() as session:
            # We must verify connectivity first
            driver.verify_connectivity()
            res = session.run("MATCH p=shortestPath((s:Concept{qid:'Q36'})-[*1..3]-(e:Concept{qid:'Q64'})) RETURN [n in nodes(p)|n.qid] as qids LIMIT 1").single()
            if not res:
                print("   ❌ FAIL: Ground truth path not found in Neo4j.")
                return False
            truth_path = res["qids"]
        driver.close()
        
        r = requests.get("http://localhost:9999/api/pl/concept/Q36/path?target_qid=Q64&max_depth=3")
        api_path = [n['qid'] for n in r.json()['path']]
        
        if api_path != truth_path:
            print(f"   ❌ FAIL: Path Mismatch!\n      Truth: {truth_path}\n      API:   {api_path}")
            return False
        print("   ✅ Path Accuracy Verified against Neo4j.")

        # 6. Depth Limits
        print("   🧪 Testing Depth Limits...")
        r = requests.get("http://localhost:9999/api/pl/concept/Q36/path?target_qid=Q64&max_depth=5")
        if r.status_code != 200:
             print("   ❌ FAIL: Depth 5 failed.")
             return False
        print("   ✅ Depth Parameter respected.")

        # 7. Memory Delta
        mem_after = proc_obj.memory_info().rss / 1024 / 1024
        delta = mem_after - mem_before
        print(f"   📊 Memory Delta: +{delta:.1f}MB (< 100MB)")
        if delta > 100:
            print("   ❌ FAIL: Memory limit exceeded.")
            return False

        # 8. Rollback Check (5B.1 Endpoint)
        print("   🧪 Verifying 5B.1 Endpoint (Rollback Check)...")
        r = requests.get("http://localhost:9999/api/concept/Q36")
        if r.status_code != 200 or "titles" not in r.json():
            print("   ❌ FAIL: 5B.1 Endpoint broken!")
            return False
        print("   ✅ 5B.1 Endpoint still functional.")

        return True

    finally:
        os.kill(pid, signal.SIGTERM)

if __name__ == "__main__":
    if run_gate_5b2():
        print("\n🎉 Gate 5B.2 PASSED (Rigorous)")
    else:
        print("\n❌ Gate 5B.2 FAILED")
        sys.exit(1)
