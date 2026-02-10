import requests
import sys

BASE_URL = "http://localhost:8000"
LANGS = ["pl", "de", "es"]
TEST_NODES = ["Q42", "Q64", "Q2"]

def test_metrics_exhaustively():
    print("=== MASTER METRICS VALIDATOR ===")
    
    for lang in LANGS:
        print(f"\n🌍 Testing Language: {lang.upper()}")
        for qid in TEST_NODES:
            print(f"  Node: {qid}")
            
            # 1. Fetch Baseline (Discovery)
            url = f"{BASE_URL}/api/v1/graph/metrics/{lang}/{qid}"
            try:
                r = requests.get(url)
                if not r.ok:
                    print(f"    ❌ FAILED baseline fetch ({r.status_code})")
                    continue
                
                full_metrics = r.json().get("metrics", {})
                if not full_metrics:
                    print("    ⚠️ No metrics found for this node")
                    continue
                
                all_keys = list(full_metrics.keys())
                print(f"    Keys discovered: {all_keys}")
                
                # 2. Test every single key
                for key in all_keys:
                    filter_url = f"{url}?key={key}"
                    rf = requests.get(filter_url)
                    
                    if not rf.ok:
                        print(f"    ❌ FAILED filter test for {key} ({rf.status_code})")
                        continue
                    
                    filtered_metrics = rf.json().get("metrics", {})
                    
                    # Assertions
                    is_correct_count = len(filtered_metrics) == 1
                    is_correct_key = key in filtered_metrics
                    is_correct_value = filtered_metrics.get(key) == full_metrics[key]
                    
                    if is_correct_count and is_correct_key and is_correct_value:
                        print(f"    ✅ {key}: {filtered_metrics[key]}")
                    else:
                        print(f"    ❌ {key} FAILED (Count={len(filtered_metrics)}, Match={is_correct_value})")
                        
            except Exception as e:
                print(f"    ❌ EXCEPTION: {e}")

if __name__ == "__main__":
    test_metrics_exhaustively()
