from neo4j import GraphDatabase
import time

URI = "bolt://localhost:7688"
AUTH = ("neo4j", "wikigraph")

def debug_hits():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        print("1. Estimating Memory...")
        try:
            est = session.run("""
                CALL gds.hits.write.estimate('proj_de', {writeProperty: 'debug_score'})
                YIELD requiredMemory, nodeCount, relationshipCount
            """).single()
            print(f"   Required Memory: {est['requiredMemory']}")
            print(f"   Nodes: {est['nodeCount']}, Rels: {est['relationshipCount']}")
        except Exception as e:
            print(f"   Estimate Failed: {e}")

        print("\n2. Checking if Projection Exists...")
        exists = session.run("CALL gds.graph.exists('proj_de') YIELD exists").single()['exists']
        if not exists:
            print("   Projecting Graph (NATURAL)...")
            session.run("CALL gds.graph.project('proj_de', 'Concept', 'LINKS_TO')")
        else:
            print("   Projection 'proj_de' already exists.")

        print("\n3. Running HITS (STATS ONLY)...")
        print("   This runs the full algo but returns summary stats, avoiding write/stream overhead.")
        start = time.time()
        try:
            res = session.run("""
                CALL gds.hits.stats('proj_de', {concurrency: 4})
                YIELD computeMillis, ranIterations, didConverge
            """).single()
            print(f"   SUCCESS! Time: {res['computeMillis']}ms, Iterations: {res['ranIterations']}, Converged: {res['didConverge']}")
        except Exception as e:
            print(f"   FAILURE during STATS mode: {e}")
            return

        print("\n4. Running HITS (MUTATE mode - In-Memory Write)...")
        print("   This writes to the projected graph (RAM), not the database (Disk).")
        try:
            res = session.run("""
                CALL gds.hits.mutate('proj_de', {mutateProperty: 'debug_score', concurrency: 4})
                YIELD mutateMillis, nodePropertiesWritten
            """).single()
            print(f"   SUCCESS! Time: {res['mutateMillis']}ms, Props Written: {res['nodePropertiesWritten']}")
        except Exception as e:
            print(f"   FAILURE during MUTATE mode: {e}")
            return

    driver.close()

if __name__ == "__main__":
    debug_hits()