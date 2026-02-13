import requests
import time
import subprocess
import json

BASE_URL = "http://localhost:8000"
LANGS = ["pl", "de", "es"]
NODES = {"pl": "Q42", "de": "Q42", "es": "Q42"} # Douglas Adams exists in all

def log_resources(tag):
    print(f"\n--- {tag} ---")
    subprocess.run("free -h | grep Mem", shell=True)
    subprocess.run("docker stats --no-stream --format '{{.Name}}: {{.MemUsage}}'", shell=True)

def gds_project(lang):
    container = f"wikigraph-neo4j-{lang}"
    print(f"[{lang}] Projecting 'similarity-graph'...")
    cmd = [
        "docker", "exec", container, "cypher-shell", "-u", "neo4j", "-p", "wikigraph",
        "CALL gds.graph.exists('similarity-graph') YIELD exists; "
        "CALL gds.graph.drop('similarity-graph', false); "
        "CALL gds.graph.project('similarity-graph', 'Concept', 'LINKS_TO')"
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def test_endpoints():
    # 1. Health
    try:
        r = requests.get(f"{BASE_URL}/api/health")
        print(f"Health: {r.status_code}")
    except Exception as e:
        print(f"Health Check Failed: {e}")
        return

    # 2. Per-Language Tests
    for lang in LANGS:
        qid = NODES[lang]
        print(f"\nTesting {lang.upper()} ({qid})...")
        
        # Project GDS (Required for Jaccard)
        gds_project(lang)
        
        # Jaccard
        t0 = time.time()
        r = requests.get(f"{BASE_URL}/api/v1/graph/neighbors/scored/{lang}/{qid}?limit=5&metric=jaccard")
        dt = time.time() - t0
        print(f"  Jaccard: {r.status_code} ({dt:.2f}s) - Found: {len(r.json()) if r.ok else 'ERR'}")

        # RA
        t0 = time.time()
        r = requests.get(f"{BASE_URL}/api/v1/graph/neighbors/scored/{lang}/{qid}?limit=5&metric=resource_allocation")
        dt = time.time() - t0
        print(f"  RA:      {r.status_code} ({dt:.2f}s) - Found: {len(r.json()) if r.ok else 'ERR'}")
        
        log_resources(f"After {lang} Load")

if __name__ == "__main__":
    print("Waiting for startup stability (5s)...")
    time.sleep(5)
    log_resources("Baseline")
    test_endpoints()