import os
import sys
import requests
import subprocess
import time
import signal
import json
import psutil
import sqlite3
from pathlib import Path

# --- Validation Template Logic ---
class GateValidator:
    def __init__(self):
        self.memory_before = self.measure_memory()
        self.start_time = time.time()
        
    def measure_memory(self):
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024

    def report(self, success, metrics):
        duration = time.time() - self.start_time
        mem_after = self.measure_memory()
        mem_delta = mem_after - self.memory_before
        
        print("\n" + "="*40)
        print(f"GATE 5B.3.2 VALIDATION REPORT")
        print("="*40)
        print(f"Status:       {'✅ PASSED' if success else '❌ FAILED'}")
        print(f"Time:         {duration:.2f}s")
        print(f"Memory:       {self.memory_before:.1f}MB -> {mem_after:.1f}MB (Δ: {mem_delta:.1f}MB)")
        print(f"Memory Limit: < 150MB Delta")
        print("-" * 40)
        for k, v in metrics.items():
            print(f"{k:<20}: {v}")
        print("="*40 + "\n")
        
        return success

def get_source_truth(qid, lang):
    db_path = Path(f"data/db/{lang}.db")
    if not db_path.exists(): return None
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cursor = conn.cursor()
    cursor.execute("SELECT p.title FROM pages p JOIN id_mapping m ON p.page_id = m.page_id WHERE m.qid = ?", (qid,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

def run_gate_5b3_2():
    validator = GateValidator()
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
            return validator.report(False, {"Error": "Server failed to start"})
        
        backend_proc = psutil.Process(proc.pid)
        mem_backend_start = backend_proc.memory_info().rss / 1024 / 1024
        
        # 1. Test Existence & Structure
        t0 = time.time()
        try:
            r = requests.get("http://localhost:9999/api/concept/Q36/traverse")
        except Exception as e:
            return validator.report(False, {"Error": f"Request failed: {e}"})
            
        metrics["Response Time"] = f"{(time.time()-t0)*1000:.1f}ms"

        if r.status_code != 200:
            return validator.report(False, {"Status": r.status_code, "Detail": r.text})
            
        data = r.json()
        
        # 2. Structural Validation
        if "qid" not in data or "graph" not in data:
            return validator.report(False, {"Error": "Missing keys"})
            
        nodes = data["graph"]["nodes"]
        if "Q36" not in nodes:
            return validator.report(False, {"Error": "Root Q36 missing"})
            
        # 3. Source Truth Validation
        pl_title = nodes["Q36"]["titles"].get("pl")
        expected_pl = get_source_truth("Q36", "pl")
        
        if pl_title != expected_pl:
             return validator.report(False, {"Title Error": f"Got {pl_title}, Expected {expected_pl}"})
        metrics["Source Truth"] = "✅ Verified (SQLite)"

        # 4. Limits
        r_limit = requests.get("http://localhost:9999/api/concept/Q36/traverse?max_depth=5")
        if r_limit.status_code != 422:
             return validator.report(False, {"Limit Check": f"Failed (Got {r_limit.status_code})"})
        metrics["Hard Limits"] = "✅ Enforced (422)"

        # 5. Rollback Verification (5B.1 and 5B.2)
        r_5b1 = requests.get("http://localhost:9999/api/concept/Q36")
        if r_5b1.status_code != 200:
             return validator.report(False, {"Rollback 5B.1": f"FAILED ({r_5b1.status_code})"})
        
        r_5b2 = requests.get("http://localhost:9999/api/pl/concept/Q36")
        if r_5b2.status_code != 200:
             return validator.report(False, {"Rollback 5B.2": f"FAILED ({r_5b2.status_code})"})
             
        metrics["Rollback Check"] = "✅ 5B.1 & 5B.2 OK"

        # Memory Delta (Backend Process)
        mem_backend_end = backend_proc.memory_info().rss / 1024 / 1024
        metrics["Backend Memory"] = f"{mem_backend_start:.1f}MB -> {mem_backend_end:.1f}MB (Δ: {mem_backend_end - mem_backend_start:.1f}MB)"

        return validator.report(True, metrics)

    finally:
        os.kill(proc.pid, signal.SIGTERM)

if __name__ == "__main__":
    if not run_gate_5b3_2():
        sys.exit(1)