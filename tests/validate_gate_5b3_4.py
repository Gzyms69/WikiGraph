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

class StressValidator:
    def __init__(self, gate_name):
        self.gate_name = gate_name
        self.start_time = time.time()

    def report(self, metrics):
        print("\n" + "="*50)
        print(f"{self.gate_name} STRESS TEST REPORT")
        print("="*50)
        for k, v in metrics.items():
            print(f"{k:<35}: {v}")
        print("="*50 + "\n")

def run_gate_5b3_4():
    validator = StressValidator("GATE 5B.3.4 (PROPER STRESS)")
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
        
        # 1. Stress Traversal (D=5, L=200) -> Target ~1000 nodes
        print(f"   🔥 1. Stress Traversal ({DENSE_QID}, D=5, L=200)...")
        t0 = time.time()
        try:
            r1 = requests.get(f"http://localhost:9999/api/stress/concept/{DENSE_QID}/traverse?max_depth=5&limit_per_depth=200&total_node_limit=2000", timeout=30)
            dur1 = time.time() - t0
            
            if r1.status_code == 200:
                d1 = r1.json()
                nodes1 = len(d1["graph"]["nodes"])
                metrics["1. Time"] = f"{dur1:.2f}s"
                metrics["1. Nodes Returned"] = f"{nodes1}"
                
                # Check memory immediately
                mem_peak = backend_proc.memory_info().rss / 1024 / 1024
                metrics["1. Peak Memory"] = f"{mem_peak:.1f}MB (Δ {mem_peak-mem_start:.1f}MB)"
                
                # Verify we actually got > 150 nodes
                if nodes1 > 200:
                    metrics["1. Saturation"] = "✅ High (>200)"
                else:
                    metrics["1. Saturation"] = f"⚠️ Low ({nodes1})"
            else:
                metrics["1. Result"] = f"❌ Failed {r1.status_code}"
        except Exception as e:
            metrics["1. Result"] = f"❌ Exception {e}"

        # 2. Hard Limit Check (Cap at 1000?)
        # Let's see if we can hit 1000.
        # If D=5, L=200, we theoretically can reach 1+200*5 = 1001.
        # So we expect ~1000 nodes.
        
        # 3. Concurrent Stress (3x Dense, D=3, L=100)
        print("   🔥 3. Concurrent Stress (3x Dense, D=3, L=100)...")
        targets = ["Q15828079", "Q1515114", "Q9392633"] 
        
        def fetch(qid):
            t_start = time.time()
            try:
                res = requests.get(f"http://localhost:9999/api/stress/concept/{qid}/traverse?max_depth=3&limit_per_depth=100&total_node_limit=1000", timeout=20)
                return time.time() - t_start, res.status_code
            except Exception:
                return 0, 500

        t0 = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(fetch, targets))
        total_dur = time.time() - t0
        
        metrics["3. Concurrent Time"] = f"{total_dur:.2f}s"
        metrics["3. Success"] = f"{sum(1 for r in results if r[1]==200)}/3"

        # Final Memory
        mem_end = backend_proc.memory_info().rss / 1024 / 1024
        metrics["Total Memory Delta"] = f"+{mem_end - mem_start:.1f}MB"
        
        validator.report(metrics)

    finally:
        os.kill(proc.pid, signal.SIGTERM)

if __name__ == "__main__":
    run_gate_5b3_4()
