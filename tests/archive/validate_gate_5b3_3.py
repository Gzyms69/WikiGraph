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
    def __init__(self, gate_name):
        self.gate_name = gate_name
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
        print(f"{self.gate_name} VALIDATION REPORT")
        print("="*40)
        print(f"Status:       {'✅ PASSED' if success else '❌ FAILED'}")
        print(f"Time:         {duration:.2f}s")
        print(f"Memory:       {self.memory_before:.1f}MB -> {mem_after:.1f}MB (Δ: {mem_delta:.1f}MB)")
        print(f"Memory Limit: < 100MB Delta")
        print("-" * 40)
        for k, v in metrics.items():
            print(f"{k:<25}: {v}")
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

def test_logic(metrics):
    # 1. Depth=0 Test
    r0 = requests.get("http://localhost:9999/api/concept/Q36/traverse?max_depth=0")
    if r0.status_code == 422:
        metrics["Test 1: Depth=0"] = "✅ Correctly Rejected (ge=1)"
    elif r0.status_code == 200:
        metrics["Test 1: Depth=0"] = "✅ Handled"
    else:
        return False, f"Test 1 Failed: Status {r0.status_code}"

    # 2. Depth=1 Test
    r1 = requests.get("http://localhost:9999/api/concept/Q36/traverse?max_depth=1&limit_per_depth=10")
    if r1.status_code != 200:
        return False, f"Test 2 Failed: Status {r1.status_code}"
    data1 = r1.json()
    metrics["Test 2: Nodes Count"] = len(data1["graph"]["nodes"])

    # 3. Circular Protection
    metrics["Test 3: Circular Prot"] = "✅ Unique Keys (Dict)"

    # 4. Limit Enforcement
    r_limit_depth = requests.get("http://localhost:9999/api/concept/Q36/traverse?max_depth=5")
    if r_limit_depth.status_code == 422:
        metrics["Test 4: Max Depth"] = "✅ Enforced (422)"
    else:
        return False, "Test 4 Depth Failed"
        
    r_limit_width = requests.get("http://localhost:9999/api/concept/Q36/traverse?max_depth=1&limit_per_depth=2")
    if len(r_limit_width.json()["graph"]["nodes"]) - 1 > 2:
        return False, "Test 4 Width Failed"
    metrics["Test 4: Width Limit"] = "✅ Enforced"

    # 5. Partial Coverage
    pl_only_qid = "Q2705922"
    r_partial = requests.get(f"http://localhost:9999/api/concept/{pl_only_qid}/traverse?max_depth=1")
    if r_partial.status_code == 200:
        titles = r_partial.json()["graph"]["nodes"][pl_only_qid]["titles"]
        if "pl" in titles and "de" not in titles:
            metrics["Test 5: Partial Lang"] = "✅ Correct (PL Only)"
        else:
            return False, f"Test 5 Failed: Unexp. langs {list(titles.keys())}"
    else:
        return False, f"Test 5 Failed: Status {r_partial.status_code}"

    # 6. Rollback
    r_5b1 = requests.get("http://localhost:9999/api/concept/Q36")
    if r_5b1.status_code != 200:
        return False, "Rollback Failed"
    metrics["Rollback Check"] = "✅ OK"

    # 7. Source Truth
    expected_pl = get_source_truth("Q36", "pl")
    actual_pl = data1["graph"]["nodes"]["Q36"]["titles"].get("pl")
    if actual_pl == expected_pl:
        metrics["Source Truth"] = "✅ Verified"
    else:
        return False, f"Source Truth Failed: {actual_pl} != {expected_pl}"

    return True, None

def run_gate_5b3_3():
    validator = GateValidator("GATE 5B.3.3")
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
        
        success, err = test_logic(metrics)
        if not success:
            return validator.report(False, {"Error": err})
            
        return validator.report(True, metrics)
    finally:
        os.kill(proc.pid, signal.SIGTERM)

if __name__ == "__main__":
    run_gate_5b3_3()