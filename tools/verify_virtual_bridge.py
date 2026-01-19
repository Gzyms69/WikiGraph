#!/usr/bin/env python3
import sys
from neo4j import GraphDatabase

# Configuration
LANGUAGES = {
    'pl': 'bolt://localhost:7687',
    'de': 'bolt://localhost:7688'
}
AUTH = ("neo4j", "wikigraph")

# Test Candidates (Universal Concepts)
TEST_QIDS = [
    ('Q36', 'Poland'),
    ('Q183', 'Germany'),
    ('Q5', 'Human'),
    ('Q2', 'Earth'),
    ('Q42', 'Douglas Adams')
]

def verify_virtual_bridge():
    print("🌉 Starting Virtual Bridge Validation (Gate 5.0)...")
    
    drivers = {}
    sessions = {}
    
    # 1. Connect to all DBs
    try:
        for lang, uri in LANGUAGES.items():
            print(f"   Connecting to {lang.upper()} ({uri})...")
            drivers[lang] = GraphDatabase.driver(uri, auth=AUTH)
            # Verify connection
            drivers[lang].verify_connectivity()
    except Exception as e:
        print(f"❌ FAIL: Could not connect to {lang}: {e}")
        sys.exit(1)

    print("   ✅ Connections established.")

    # 2. Check QID Consistency
    print("\n🔍 Checking QID Consistency across languages...")
    failures = 0
    
    for qid, desc in TEST_QIDS:
        results = {}
        for lang, driver in drivers.items():
            with driver.session() as session:
                # We assume title is stored on the node (it might not be if we optimized for space!)
                # Wait, REBUILDPLAN said "Schema: Minimal and QID-based". 
                # Let's check if we have 'title' property. 
                # In prepare_neo4j_csv.py we wrote: writer.writerow([qid, 0, "Concept"])
                # We did NOT write the title to Neo4j to save space!
                
                # However, the node EXISTENCE is what matters for the bridge.
                # Let's check existence.
                res = session.run("MATCH (n:Concept {qid: $qid}) RETURN n.qid", qid=qid).single()
                results[lang] = bool(res)
        
        # Output result
        status_str = " | ".join([f"{l}:{('✅' if r else '❌')}" for l, r in results.items()])
        print(f"   {qid} ({desc}): {status_str}")
        
        if not all(results.values()):
            # It's okay if Douglas Adams is missing in a small wiki, but DE/PL should have these.
            print(f"      ⚠️  Warning: {qid} missing in some languages.")
            failures += 1

    if failures > 2:
        print("❌ FAIL: Too many missing common QIDs. Alignment suspect.")
        sys.exit(1)

    # 3. Check Cross-Language Edge (Germany Q183 -> Berlin Q64)
    print("\n🔗 Checking Common Edge (Q183 -> Q64)...")
    edge_results = {}
    for lang, driver in drivers.items():
        with driver.session() as session:
            res = session.run("""
                MATCH (a:Concept {qid: 'Q183'})-[r:LINKS_TO]->(b:Concept {qid: 'Q64'})
                RETURN count(r) as c
            """).single()["c"]
            edge_results[lang] = res > 0
            
    status_str = " | ".join([f"{l}:{('✅' if r else '❌')}" for l, r in edge_results.items()])
    print(f"   Q183 -> Q64: {status_str}")
    
    if not any(edge_results.values()):
        print("❌ FAIL: Common edge missing in ALL languages.")
        sys.exit(1)

    print("\n🏁 Gate 5.0 PASSED: Virtual Bridge is viable.")
    
    # Cleanup
    for d in drivers.values(): d.close()

if __name__ == "__main__":
    verify_virtual_bridge()
