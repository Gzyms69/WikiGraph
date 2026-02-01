import os
import sys
import time
import requests
import subprocess
import signal
import psutil
import json

# Fix path
sys.path.append(os.getcwd())

# Expected Counts (approximate is fine for health check, but we know exacts)
EXPECTED = {
    'pl': {'nodes': 1675749, 'edges': 99903827},
    'de': {'nodes': 3106093, 'edges': 149412870}
}

def run_gate_5a3():
    print("🔒 Running Gate 5A.3: Health Endpoint Validation...")
    
    # 1. Start Server
    print("   🚀 Starting server on port 9999...")
    proc = subprocess.Popen(
        ["./venv_gate5/bin/uvicorn", "app.main:app", "--port", "9999"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    pid = proc.pid
    
    try:
        # Wait for readiness
        time.sleep(2)
        if proc.poll() is not None:
            print("   ❌ FAIL: Server died immediately.")
            return False

        # 2. Check Full Health (Both DBs Up)
        print("   🏥 Checking full system health...")
        try:
            start_t = time.time()
            resp = requests.get("http://localhost:9999/health", timeout=2)
            latency = (time.time() - start_t) * 1000
            
            if resp.status_code != 200:
                print(f"   ❌ FAIL: Status code {resp.status_code}")
                return False
                
            data = resp.json()
            
            # Verify Structure and Counts
            for lang in ['pl', 'de']:
                if not data[lang]['connected']:
                    print(f"   ❌ FAIL: {lang} should be connected.")
                    return False
                
                # Check Counts (Allow 1% variance just in case, but usually exact)
                nodes = data[lang].get('nodes', 0)
                edges = data[lang].get('edges', 0)
                
                if abs(nodes - EXPECTED[lang]['nodes']) > 100:
                    print(f"   ❌ FAIL: {lang} Node count mismatch. Got {nodes}, expected {EXPECTED[lang]['nodes']}")
                    return False
                    
                if abs(edges - EXPECTED[lang]['edges']) > 100:
                    print(f"   ❌ FAIL: {lang} Edge count mismatch. Got {edges}, expected {EXPECTED[lang]['edges']}")
                    return False
            
            print(f"   ✅ Full Health OK (Latency: {latency:.1f}ms)")
            
        except Exception as e:
            print(f"   ❌ FAIL: Request error: {e}")
            return False

        # 3. Partial Failure Test
        print("   📉 Simulating Partial Failure (Stopping neo4j-de)...")
        subprocess.run(["docker", "stop", "neo4j-de"], check=True, stdout=subprocess.DEVNULL)
        time.sleep(2) # Allow connections to drop
        
        try:
            resp = requests.get("http://localhost:9999/health", timeout=2)
            data = resp.json()
            
            if not data['pl']['connected']:
                print("   ❌ FAIL: Polish DB should still be UP.")
                return False
                
            if data['de']['connected']:
                print("   ❌ FAIL: German DB should be DOWN.")
                return False
                
            print("   ✅ Partial failure correctly reported.")
            
        except Exception as e:
            print(f"   ❌ FAIL: API crashed on partial failure: {e}")
            return False
            
        # 4. Recovery
        print("   🔄 Recovering neo4j-de...")
        subprocess.run(["docker", "start", "neo4j-de"], check=True, stdout=subprocess.DEVNULL)
        time.sleep(10) # Wait for startup
        
        # 5. Memory Check
        mem = psutil.Process(pid).memory_info().rss / 1024 / 1024
        print(f"   📊 Server Memory: {mem:.1f}MB")
        if mem > 100:
            print("   ❌ FAIL: Memory usage too high (>100MB)")
            return False

        return True

    finally:
        os.kill(pid, signal.SIGTERM)
        # Ensure Docker container is back up if we crashed mid-test
        subprocess.run(["docker", "start", "neo4j-de"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    if run_gate_5a3():
        print("\n🎉 Gate 5A.3 PASSED")
    else:
        print("\n❌ Gate 5A.3 FAILED")
        sys.exit(1)
