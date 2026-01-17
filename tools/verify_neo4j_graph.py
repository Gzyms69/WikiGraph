#!/usr/bin/env python3
import time
import sys
import random
import os
import csv
import argparse
from neo4j import GraphDatabase

# Gate 5 Criteria (Polish)
EXPECTED_NODES_PL = 1675749
EXPECTED_EDGES_PL = 99903827

# Gate 5 Criteria (German)
EXPECTED_NODES_DE = 3106093
EXPECTED_EDGES_DE = 149412870

TOLERANCE = 0.01 
DEGREE_THRESHOLD = 200000

AUTH = ("neo4j", "wikigraph")

def get_random_csv_samples(filepath, n=100):
    """Samples n random rows from the CSV file efficiently."""
    samples = []
    if not os.path.exists(filepath):
        print(f"❌ FAIL: CSV file not found: {filepath}")
        sys.exit(1)
        
    filesize = os.stat(filepath).st_size
    with open(filepath, 'r', encoding='utf-8') as f: 
        # Read header to know structure (skip it) 
        f.readline() 
        
        for _ in range(n):
            pos = random.randint(0, filesize - 100)
            f.seek(pos)
            f.readline() # Discard partial line
            line = f.readline() # Read valid line
            if not line: break # EOF
            
            try:
                # Basic CSV parsing
                parts = list(csv.reader([line.strip()]))[0]
                if len(parts) >= 2:
                    samples.append((parts[0], parts[1]))
            except:
                continue
    return samples

def verify_graph(lang, port):
    csv_path = f"data/neo4j_bulk/{lang}/edges.csv"
    uri = f"bolt://localhost:{port}"
    
    print(f"🔍 Starting Gate 5 Validation ({lang.upper()}) on {uri}...")
    
    # 0. Sample Source Data FIRST
    print(f"   🎲 Sampling 100 random edges from {csv_path}...")
    source_samples = get_random_csv_samples(csv_path, 100)
    if len(source_samples) < 50:
        print("   ❌ FAIL: Could not extract enough samples from CSV.")
        sys.exit(1)
    print(f"   ✅ Got {len(source_samples)} source samples.")

    driver = GraphDatabase.driver(uri, auth=AUTH)
    try:
        with driver.session() as session:
            # 1. Connectivity
            start_time = time.time()
            session.run("RETURN 1").single()
            print(f"   ✅ Connection OK ({time.time() - start_time:.3f}s)")

            # 2. Node Count
            n_count = session.run("MATCH (n:Concept) RETURN count(n) as c").single()["c"]
            print(f"   📊 Nodes: {n_count:,}")
            
            expected_nodes = EXPECTED_NODES_PL if lang == 'pl' else EXPECTED_NODES_DE
            delta_n = abs(n_count - expected_nodes) / expected_nodes
            if delta_n > TOLERANCE:
                print(f"   ❌ FAIL: Node count mismatch > 1% (Expected {expected_nodes})")
                sys.exit(1)
            
            # 3. Edge Count
            e_count = session.run("MATCH ()-[r:LINKS_TO]->() RETURN count(r) as c").single()["c"]
            print(f"   📊 Edges: {e_count:,}")
            
            expected_edges = EXPECTED_EDGES_PL if lang == 'pl' else EXPECTED_EDGES_DE
            delta_e = abs(e_count - expected_edges) / expected_edges
            if delta_e > TOLERANCE:
                print(f"   ❌ FAIL: Edge count mismatch > 1% (Expected {expected_edges})")
                sys.exit(1)

            # 4. Topology Check
            if lang == 'pl':
                print("   🌍 Verifying Topology (Q36 -> Q270)...")
                res = session.run("MATCH (a:Concept {qid: 'Q36'})-[r:LINKS_TO]->(b:Concept {qid: 'Q270'}) RETURN count(r) as c").single()["c"]
                if res == 0:
                    print("   ❌ FAIL: Critical path Q36 -> Q270 missing!")
                    sys.exit(1)
                print("   ✅ Critical path verified.")
            elif lang == 'de':
                # Germany (Q183) -> Berlin (Q64)
                print("   🌍 Verifying Topology (Q183 -> Q64)...")
                res = session.run("MATCH (a:Concept {qid: 'Q183'})-[r:LINKS_TO]->(b:Concept {qid: 'Q64'}) RETURN count(r) as c").single()["c"]
                if res == 0:
                    print("   ❌ FAIL: Critical path Q183 -> Q64 missing!")
                    sys.exit(1)
                print("   ✅ Critical path verified.")

            # 5. TRUE Random Verification (Source -> DB)
            print("   🧪 Verifying Source Integrity (CSV -> Graph)...")
            found = 0
            for src, tgt in source_samples:
                exists = session.run("""
                    MATCH (a:Concept {qid: $src})-[r:LINKS_TO]->(b:Concept {qid: $tgt}) 
                    RETURN count(r) as c
                """, src=src, tgt=tgt).single()["c"]
                if exists > 0:
                    found += 1
            
            print(f"   📊 Verified {found}/{len(source_samples)} samples.")
            if found < len(source_samples): # Should be 100% match if import was clean
                print(f"   ❌ FAIL: Data integrity error. Missing edges in graph.")
                sys.exit(1)
            print("   ✅ Source integrity confirmed (100% match).")

            # 6. Degree Distribution Sanity
            print("   📈 Checking Max Degree...")
            max_degree = session.run("""
                MATCH (n)-[r]->()
                WITH n, count(r) as degree
                RETURN max(degree) as m
            """).single()["m"]
            print(f"   ℹ️  Max Out-Degree: {max_degree:,}")
            if max_degree > DEGREE_THRESHOLD:
                 print(f"   ⚠️  Warning: Max degree > {DEGREE_THRESHOLD}")

            # 7. Performance Test (3-hop)
            print("   ⏱️  Performance Benchmark (3-hop expansion)...")
            t0 = time.time()
            seed = 'Q36' if lang == 'pl' else 'Q183'
            session.run(f"MATCH p=(n:Concept {{qid: '{seed}'}})-[*3]->(m) RETURN count(p) LIMIT 1")
            t1 = time.time()
            duration = (t1 - t0) * 1000
            if duration > 2000:
                print(f"   ⚠️  Path query slow: {duration:.1f}ms (Target: <2000ms)")
            else:
                print(f"   ✅ Path query fast: {duration:.1f}ms")

            # 8. Constraint Check
            print("   🔒 Checking Constraints...")
            indexes = list(session.run("SHOW CONSTRAINTS"))
            has_constraint = any(
                idx["labelsOrTypes"] == ["Concept"] and 
                idx["properties"] == ["qid"] and 
                idx["type"] == "UNIQUENESS"
                for idx in indexes
            )
            if has_constraint:
                print("   ✅ Uniqueness Constraint ONLINE.")
            else:
                print("   ❌ FAIL: Uniqueness Constraint MISSING.")
                sys.exit(1)

    except Exception as e:
        print(f"❌ ERROR: Validation failed: {e}")
        sys.exit(1)
    finally:
        driver.close()

    print(f"\n🏁 Gate 5 ({lang.upper()}) PASSED: Graph is fully consistent.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", default="pl", help="Language code (pl, de)")
    parser.add_argument("--port", type=int, default=7687, help="Bolt port")
    args = parser.parse_args()
    
    verify_graph(args.lang, args.port)