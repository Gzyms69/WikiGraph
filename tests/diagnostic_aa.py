import requests
import time
import subprocess
import json

BASE_URL = "http://localhost:8000"
NODES = [
    {"qid": "Q42", "name": "Douglas Adams"},
    {"qid": "Q1744", "name": "Madonna"},
    {"qid": "Q64", "name": "Berlin"}
]

def log_resources():
    subprocess.run("docker stats --no-stream --format '{{.Name}}: {{.MemUsage}} / {{.CPUPerc}}'", shell=True)

print("--- Adamic Adar Diagnostic ---")
log_resources()

for node in NODES:
    qid = node["qid"]
    name = node["name"]
    print(f"\nTesting {name} ({qid})...")
    
    t0 = time.time()
    try:
        r = requests.get(f"{BASE_URL}/api/v1/graph/neighbors/scored/pl/{qid}?limit=5&metric=adamic_adar", timeout=30)
        dt = time.time() - t0
        
        if r.ok:
            data = r.json()
            count = len(data)
            print(f"✅ SUCCESS ({dt:.2f}s) - {count} results")
            if count > 0:
                print(f"   Top: {data[0]['title']} ({data[0]['score']:.2f})")
        else:
            print(f"❌ FAILED ({dt:.2f}s) - Status: {r.status_code}")
            print(f"   Error: {r.text[:100]}...")
    except Exception as e:
        print(f"❌ TIMEOUT/ERROR ({time.time() - t0:.2f}s) - {e}")

    log_resources()
