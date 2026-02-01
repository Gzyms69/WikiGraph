import time
import psutil
import subprocess
import sys

def run_performance_test():
    """Run extraction with profiling"""
    
    print("🚀 PERFORMANCE SPRINT: Target 500 articles/second")
    print("=" * 60)
    
    # Test 1: 10000 articles baseline (using 10000 as requested in Phase 3)
    print("\nTest 1: Validation (10000 articles)")
    start = time.time()
    result = subprocess.run(
        [sys.executable, "core/tools/extract_infoboxes.py", "--lang", "de", "--limit", "10000"],
        capture_output=True,
        text=True
    )
    elapsed = time.time() - start
    
    # Check for failure
    if result.returncode != 0:
        print(f"❌ Script failed with error:\n{result.stderr}")
        return False
        
    print(result.stdout)
    
    # Extract speed from stdout manually if needed, or just calculate
    # The script prints "Average speed: X articles/second"
    speed = 0
    for line in result.stdout.split('\n'):
        if "Average speed:" in line:
            try:
                speed = float(line.split('Speed:')[-1].split('articles')[0].strip().split(' ')[-2]) # Parse from line
            except:
                pass
            # Actually easier to just parse the specific line: "Average speed: 123.4 articles/second"
            try:
                parts = line.split()
                # parts might be ["Average", "speed:", "123.4", "articles/second"]
                for i, part in enumerate(parts):
                    if part == "speed:":
                        speed = float(parts[i+1])
            except:
                pass

    # If parsing failed, calculate manually
    if speed == 0:
        speed = 10000 / elapsed
    
    print(f"\nMeasured Speed: {speed:.1f} articles/second")
    print(f"Time: {elapsed:.1f}s")
    
    if speed < 500:
        print(f"❌ FAIL: {speed:.1f} < 500 articles/second target")
        return False
    
    print("✅ PASS: Performance meets target")
    return True

if __name__ == "__main__":
    success = run_performance_test()
    sys.exit(0 if success else 1)
