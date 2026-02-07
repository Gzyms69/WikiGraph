import httpx
import asyncio
import time
import argparse

# Configuration
BASE_URL = "http://localhost:8000/api/v1/graph/path/shortest"
LANG = "pl"
START_QID = "Q36" # Poland
END_QID = "Q64"   # Berlin

async def test_depth(depth: int):
    print(f"Testing depth {depth}...")
    start_time = time.time()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/{LANG}",
                params={"from_qid": START_QID, "to_qid": END_QID, "max_depth": depth},
                timeout=60.0 # Client side timeout
            )
            elapsed = time.time() - start_time
            if response.status_code == 200:
                path = response.json()
                print(f"✅ Depth {depth}: Found path length {len(path)} in {elapsed:.4f}s")
            else:
                print(f"❌ Depth {depth}: Error {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Depth {depth}: Exception - {e}")

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--depths", nargs="+", type=int, default=[6, 12, 24])
    args = parser.parse_args()
    
    print(f"🚀 Starting Pathfinding Stress Test on {LANG} ({START_QID} -> {END_QID})")
    
    for depth in args.depths:
        await test_depth(depth)

if __name__ == "__main__":
    asyncio.run(main())
