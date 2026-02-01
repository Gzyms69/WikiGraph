import os
import sys
import requests
import subprocess
import time
import signal
import json
import psutil
import concurrent.futures
from statistics import mean

class RealStressValidator:
    def __init__(self, gate_name):
        self.gate_name = gate_name
        self.start_time = time.time()

    def report(self, metrics):
        print("\n" + "="*60)
        print(f"{self.gate_name} REAL METRICS REPORT")
        print("="*60)
        for k, v in metrics.items():
            print(f"{k:<40}: {v}")
        print("="*60 + "\n")

def run_real_stress():
    validator = RealStressValidator("GATE 5B.3.4 (EDGE STRESS)")
    metrics = {}
    
    env = os.environ.copy()
    env["TEST_MODE"] = "false"
    
    proc = subprocess.Popen(
        ["./venv_gate5/bin/uvicorn", "app.main:app", "--port", "9999"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env
    )
    
    try:
        time.sleep(3)
        if proc.poll() is not None: 
            print("❌ Server failed to start")
            return
        
        backend_proc = psutil.Process(proc.pid)
        mem_start = backend_proc.memory_info().rss / 1024 / 1024
        
        DENSE_QID = "Q15828079" # 12k edges
        
        # Test A: Single Node, Many Edges (Edge Processing)
        print(f"   🔥 Test A: Single Dense Node ({DENSE_QID}, Limit=500)...")
        t0 = time.time()
        try:
            r_a = requests.get(f"http://localhost:9999/api/stress/concept/{DENSE_QID}/traverse?max_depth=1&limit_per_depth=500&total_node_limit=2000", timeout=10)
            dur_a = time.time() - t0
            
            if r_a.status_code == 200:
                d_a = r_a.json()
                edges_a = len(d_a["graph"]["edges"])
                metrics["A. Neo4j+Process Time (500 edges)"] = f"{dur_a:.3f}s"
                metrics["A. Edge Count"] = edges_a
                metrics["A. Edges/Sec"] = f"{edges_a/dur_a:.1f}"
            else:
                metrics["A. Result"] = f"❌ Failed {r_a.status_code}"
        except Exception as e:
            metrics["A. Result"] = f"❌ Exception {e}"

        # Test B: Many Nodes, Moderate Edges (Concurrent)
        print("   🔥 Test B: 3 Dense Nodes Concurrent...")
        targets = ["Q15828079", "Q1515114", "Q9392633"]
        def fetch_b(qid):
            t_s = time.time()
            try:
                res = requests.get(f"http://localhost:9999/api/stress/concept/{qid}/traverse?max_depth=2&limit_per_depth=100&total_node_limit=2000", timeout=10)
                return time.time() - t_s, len(res.json().get("graph", {}).get("edges", []))
            except:
                return 0, 0

        t0 = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            results_b = list(executor.map(fetch_b, targets))
        dur_b = time.time() - t0
        
        total_edges_b = sum(r[1] for r in results_b)
        metrics["B. Concurrent Time"] = f"{dur_b:.3f}s"
        metrics["B. Total Edges Fetched"] = total_edges_b
        if dur_b > 0:
            metrics["B. Aggregated Throughput"] = f"{total_edges_b/dur_b:.1f} edges/s"

        # Test C: Title Lookup Stress (1000+ nodes)
        print("   🔥 Test C: Title Lookup Stress (1000 nodes)...")
        t0 = time.time()
        try:
            r_c = requests.get(f"http://localhost:9999/api/stress/concept/{DENSE_QID}/traverse?max_depth=5&limit_per_depth=200&total_node_limit=2000", timeout=30)
            dur_c = time.time() - t0
            
            if r_c.status_code == 200:
                d_c = r_c.json()
                nodes_c = len(d_c["graph"]["nodes"])
                metrics["C. Full Request Time (1000 nodes)"] = f"{dur_c:.3f}s"
                metrics["C. Node Count"] = nodes_c
            else:
                metrics["C. Result"] = f"❌ Failed {r_c.status_code}"
        except Exception as e:
            metrics["C. Result"] = f"❌ Exception {e}"

        # Test D: Memory Overhead
        mem_peak = backend_proc.memory_info().rss / 1024 / 1024
        metrics["D. Peak Memory Delta"] = f"+{mem_peak - mem_start:.1f}MB"
        
        validator.report(metrics)

    finally:
        os.kill(proc.pid, signal.SIGTERM)

if __name__ == "__main__":
    run_real_stress()
