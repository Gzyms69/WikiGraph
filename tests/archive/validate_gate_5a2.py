import sys
import os
import time
import subprocess
import psutil

# Fix path
sys.path.append(os.getcwd())

from app.services.neo4j_manager import Neo4jManager

def run_gate_5a2():
    print("🔒 Running Gate 5A.2: Connection Manager Validation...")
    
    # Metrics
    mem_before = psutil.Process().memory_info().rss / 1024 / 1024
    
    # 1. Initialization
    start_time = time.time()
    manager = Neo4jManager()
    init_time = time.time() - start_time
    print(f"   ✅ Manager initialized in {init_time:.4f}s")
    
    # 2. Health Check (Baseline)
    print("   🏥 Checking initial health...")
    status = manager.check_health()
    print(f"      Status: {status}")
    
    if not status['pl']['connected'] or not status['de']['connected']:
        print("   ❌ FAIL: Initial connection failed.")
        return False
    
    if status['pl']['latency_ms'] > 500 or status['de']['latency_ms'] > 500:
        print("   ❌ FAIL: Latency too high (>500ms).")
        return False
    print("   ✅ Baseline health OK.")

    # 3. Graceful Degradation Test
    print("   📉 Simulating German DB Failure (Stopping neo4j-de)...")
    subprocess.run(["docker", "stop", "neo4j-de"], check=True, stdout=subprocess.DEVNULL)
    
    try:
        # Give it a moment to fully stop/close sockets
        time.sleep(2)
        
        status_fail = manager.check_health()
        print(f"      Status during failure: {status_fail}")
        
        if status_fail['pl']['connected'] is not True:
            print("   ❌ FAIL: Polish DB should still be connected!")
            return False
            
        if status_fail['de']['connected'] is not False:
            print("   ❌ FAIL: German DB should be disconnected!")
            return False
            
        print("   ✅ Graceful degradation verified.")
        
    finally:
        print("   🔄 Recovery: Restarting neo4j-de...")
        subprocess.run(["docker", "start", "neo4j-de"], check=True, stdout=subprocess.DEVNULL)
        # Wait for Neo4j to be ready (dumb wait, but script will retry health check)
        print("      Waiting for readiness...")
        time.sleep(10) 

    # 4. Recovery Check
    print("   🏥 Checking recovery...")
    status_recovered = manager.check_health()
    if not status_recovered['de']['connected']:
        print("   ⚠️  Warning: German DB not yet ready (might take longer). Retrying...")
        time.sleep(10)
        status_recovered = manager.check_health()
        
    if status_recovered['de']['connected']:
        print("   ✅ Recovery successful.")
    else:
        print("   ❌ FAIL: German DB did not recover.")
        return False

    # 5. Memory Check
    mem_after = psutil.Process().memory_info().rss / 1024 / 1024
    print(f"   📊 Memory: {mem_before:.1f}MB -> {mem_after:.1f}MB (Delta: {mem_after - mem_before:.1f}MB)")
    
    manager.close()
    return True

if __name__ == "__main__":
    if run_gate_5a2():
        print("\n🎉 Gate 5A.2 PASSED")
    else:
        print("\n❌ Gate 5A.2 FAILED")
        sys.exit(1)
