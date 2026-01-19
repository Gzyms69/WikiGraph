import os
import sys
import time
import requests
import subprocess
import signal
import psutil
from pathlib import Path

# Fix path to allow importing app
sys.path.append(os.getcwd())

def test_directories():
    print("   📂 Checking directories...")
    required = ["app/api/routers", "app/core"]
    for d in required:
        if not os.path.exists(d):
            print(f"   ❌ FAIL: Missing {d}")
            return False
    print("   ✅ Directories exist.")
    return True

def test_config():
    print("   ⚙️ Checking config loader...")
    try:
        from app.core.config import settings
        if "languages" not in settings:
            print("   ❌ FAIL: 'languages' key missing in settings")
            return False
        if "pl" not in settings["languages"]:
            print("   ❌ FAIL: 'pl' config missing")
            return False
        print("   ✅ Config loaded successfully.")
        return True
    except Exception as e:
        print(f"   ❌ FAIL: Config load error: {e}")
        return False

def test_server_with_metrics():
    print("   🚀 Checking server startup with metrics...")
    
    start_time = time.time()
    proc = subprocess.Popen(
        ["./venv_gate5/bin/uvicorn", "app.main:app", "--port", "9999"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    pid = proc.pid
    process_obj = psutil.Process(pid)
    
    ready = False
    startup_time = 0
    response_time = 0
    memory_usage = 0
    
    try:
        # Poll for readiness (max 10s)
        for i in range(20):
            if proc.poll() is not None:
                print("   ❌ FAIL: Server process died immediately.")
                return False
            
            try:
                req_start = time.time()
                resp = requests.get("http://localhost:9999/test", timeout=0.5)
                req_end = time.time()
                
                if resp.status_code == 200:
                    startup_time = time.time() - start_time
                    response_time = (req_end - req_start) * 1000
                    ready = True
                    break
            except requests.exceptions.RequestException:
                time.sleep(0.5)
                continue
        
        if not ready:
            print("   ❌ FAIL: Server timed out (did not start in 10s).")
            return False

        # Measure Memory
        try:
            memory_usage = process_obj.memory_info().rss / 1024 / 1024 # MB
        except psutil.NoSuchProcess:
            print("   ⚠️  Warning: Process died before memory check.")
            
        print(f"   ✅ Server started in {startup_time:.2f}s")
        print(f"   ✅ Response time: {response_time:.1f}ms")
        print(f"   ✅ Memory usage: {memory_usage:.1f}MB (Target < 50MB)")
        
        if memory_usage > 50:
             print("   ❌ FAIL: Memory usage exceeded 50MB limit.")
             return False

        return True

    finally:
        # Rollback / Cleanup Test
        print("   🔄 Testing rollback (shutdown)...")
        os.kill(pid, signal.SIGTERM)
        proc.wait(timeout=5)
        if proc.poll() is None:
             print("   ❌ FAIL: Server did not shut down cleanly.")
             os.kill(pid, signal.SIGKILL)
             return False
        print("   ✅ Server shut down cleanly.")

def run_gate():
    print("🔒 Running Gate 5A.1 Validation (Pessimistic Mode)...")
    if not test_directories(): sys.exit(1)
    if not test_config(): sys.exit(1)
    if not test_server_with_metrics(): sys.exit(1)
    print("\n🎉 Gate 5A.1 PASSED with Metrics")

if __name__ == "__main__":
    run_gate()