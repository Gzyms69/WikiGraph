import subprocess
import requests
import time
import json
import sys
import os
import signal

def run_gate_5b3_0():
    print("🔒 Running Gate 5B.3.0: Production Safety Baseline...")
    
    # 1. Container Memory Baseline
    print("\n[1] Container Memory Baseline:")
    try:
        cmd = ["docker", "stats", "--no-stream", "--format", "{{.Name}}: {{.MemUsage}}"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        output = res.stdout.strip()
        print(output)
        
        if "neo4j-pl" not in output:
            print("❌ FAIL: neo4j-pl not running.")
            return False
        if "neo4j-de" not in output:
            print("❌ FAIL: neo4j-de not running.")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Docker stats error: {e}")
        return False
        
    # 2. Query Performance Baseline (Using Isolated Port 8001)
    print("\n[2] Query Performance Baseline (Port 8001):")
    
    # Ensure Prod Environment
    env = os.environ.copy()
    if "TEST_MODE" in env: del env["TEST_MODE"]
    
    proc = subprocess.Popen(
        ["./venv_gate5/bin/uvicorn", "app.main:app", "--port", "8001"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env
    )
    
    try:
        time.sleep(3)
        if proc.poll() is not None:
            print("❌ FAIL: Backend failed to start on 8001.")
            return False

        # Measure 5B.1 (QID)
        t0 = time.time()
        try:
            r = requests.get("http://localhost:8001/api/concept/Q36")
            lat1 = (time.time() - t0) * 1000
            if r.status_code != 200:
                print(f"❌ FAIL: 5B.1 Endpoint Error {r.status_code}")
                return False
            print(f"   ✅ 5B.1 (QID): {lat1:.1f}ms")
        except Exception as e:
            print(f"❌ FAIL: Connection error: {e}")
            return False

        # Measure 5B.2 (Lang)
        t0 = time.time()
        r = requests.get("http://localhost:8001/api/pl/concept/Q36")
        lat2 = (time.time() - t0) * 1000
        if r.status_code != 200:
            print(f"❌ FAIL: 5B.2 Endpoint Error {r.status_code}")
            return False
        print(f"   ✅ 5B.2 (Lang): {lat2:.1f}ms")
        
        # 3. Log Review
        print("\n[3] Neo4j Log Review:")
        for c in ["neo4j-pl", "neo4j-de"]:
            res = subprocess.run(["docker", "logs", "--tail", "20", c], capture_output=True, text=True)
            logs = res.stdout + res.stderr
            # Filter for actual errors, ignore standard info
            if "ERROR" in logs:
                print(f"   ⚠️  Warning: ERROR found in {c} logs.")
            else:
                print(f"   ✅ {c} Logs clean.")

    finally:
        # 4. Emergency Stop
        print("\n[4] Emergency Stop Test:")
        os.kill(proc.pid, signal.SIGTERM)
        proc.wait()
        
        try:
            requests.get("http://localhost:8001/api/health", timeout=0.5)
            print("❌ FAIL: Backend still reachable after SIGTERM.")
            return False
        except:
            print("   ✅ Backend successfully stopped.")

    return True

if __name__ == "__main__":
    if run_gate_5b3_0():
        print("\n🎉 Gate 5B.3.0 PASSED")
    else:
        sys.exit(1)
