"""
GATE 5B.3.5: ROLLBACK VALIDATION WITH ENRICHED DATA
"""
import time
import psutil
import requests
from datetime import datetime
import json
import os
import signal
import subprocess

def validate_rollback():
    print("\n" + "="*60)
    print("GATE 5B.3.5: ROLLBACK VALIDATION")
    print(f"TIME: {datetime.now().isoformat()}")
    print("="*60)
    
    # Start Backend
    env = os.environ.copy()
    env["TEST_MODE"] = "false"
    proc = subprocess.Popen(
        ["./venv_gate5/bin/uvicorn", "app.main:app", "--port", "9999"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env
    )
    time.sleep(3)
    
    try:
        # 1. Basic Endpoints
        print("\n1️⃣ BASIC ENDPOINT VALIDATION")
        endpoints = [
            ("/api/health", dict()),
            ("/api/concept/Q36", dict()),  # Poland (PL/DE) 
            ("/api/de/concept/Q15828079", dict()), # German Reich (DE only)
        ]
        
        for endpoint, params in endpoints:
            try:
                start = time.time()
                response = requests.get(f"http://localhost:9999{endpoint}", params=params, timeout=5)
                duration = time.time() - start
                
                status = "✅" if response.status_code == 200 else "❌"
                print(f"  {status} {endpoint}: {response.status_code} ({duration:.3f}s)")
                
                if response.status_code == 200 and "concept" in endpoint:
                    data = response.json()
                    title = data.get('titles', {}).get('de') or data.get('title')
                    print(f"     Title: {title}")
            except Exception as e:
                print(f"  ❌ {endpoint}: Error - {e}")
        
        # 2. Traversal with Titles (Using Q15828079)
        print("\n2️⃣ TRAVERSAL VALIDATION (Dense Node)")
        test_qid = "Q15828079"
        try:
            start_time = time.time()
            response = requests.get(
                f"http://localhost:9999/api/concept/{test_qid}/traverse",
                params={'max_depth': 2, 'limit_per_depth': 100, 'total_node_limit': 1000},
                timeout=10
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                nodes = data["graph"]["nodes"]
                print(f"  ✅ Traversal: {len(nodes)} nodes in {duration:.3f}s")
                
                # Verify Titles exist in Graph
                sample_node = next(iter(nodes.values()))
                if "titles" in sample_node and sample_node["titles"]:
                    print("     ✅ Titles present in graph nodes")
                else:
                    print("     ⚠️ Titles MISSING in graph nodes")
            else:
                print(f"  ❌ Traversal failed: {response.status_code}")
        except Exception as e:
            print(f"  ❌ Traversal error: {e}")

        # 3. Stress Endpoint Gone
        print("\n3️⃣ STRESS ENDPOINT CHECK")
        r = requests.get(f"http://localhost:9999/api/stress/concept/{test_qid}/traverse")
        if r.status_code == 404:
            print("  ✅ Stress endpoint removed (404)")
        else:
            print(f"  ⚠️ Stress endpoint accessible: {r.status_code}")

    finally:
        os.kill(proc.pid, signal.SIGTERM)

if __name__ == "__main__":
    validate_rollback()