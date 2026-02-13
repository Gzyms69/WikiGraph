import argparse
from neo4j import GraphDatabase
import sys

def warmup_gds(lang, uri):
    print(f"🚀 Warming up GDS for [{lang.upper()}]...")
    driver = GraphDatabase.driver(uri, auth=("neo4j", "wikigraph"))
    
    try:
        with driver.session() as session:
            # Check if projection exists
            exists = session.run("CALL gds.graph.exists('similarity-graph') YIELD exists").single()['exists']
            
            if exists:
                print("✅ 'similarity-graph' projection already exists. Ready for Jaccard.")
                return

            print("⏳ 'similarity-graph' not found. Creating projection (this may take memory)...")
            session.run("CALL gds.graph.project('similarity-graph', 'Concept', 'LINKS_TO')")
            print("✅ Projection created successfully.")
            
    except Exception as e:
        print(f"❌ Failed to warmup GDS: {e}")
        sys.exit(1)
    finally:
        driver.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WikiGraph GDS Warmup Tool")
    parser.add_argument("--lang", required=True, help="Language code (pl, de, es)")
    args = parser.parse_args()

    ports = {"pl": 7687, "de": 7688, "es": 7757}
    if args.lang not in ports:
        print(f"Unknown language: {args.lang}")
        sys.exit(1)

    uri = f"bolt://localhost:{ports[args.lang]}"
    warmup_gds(args.lang, uri)
