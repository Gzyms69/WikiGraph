import asyncio
import os
import sys
from pathlib import Path

# Setup Path
sys.path.append(str(Path.cwd()))

from app.services.neo4j_service import Neo4jService

async def main():
    service = Neo4jService()
    print("Testing Resource Allocation (RA) on PL...")
    
    # Test on Q42 (Douglas Adams) - Manageable node size
    qid = "Q42" 
    try:
        results = await asyncio.wait_for(
            service.get_scored_neighbors("pl", qid, limit=5, metric="resource_allocation"),
            timeout=10.0
        )
    except asyncio.TimeoutError:
        print(f"❌ Query timed out for {qid}.")
        results = []
    
    if results:
        print(f"✅ Success! Found {len(results)} neighbors for {qid}.")
        for r in results:
            print(f"   - {r['qid']}: {r['score']:.4f}")
    else:
        print("❌ Failed to get results or timed out.")

    service.manager.close()

if __name__ == "__main__":
    asyncio.run(main())
