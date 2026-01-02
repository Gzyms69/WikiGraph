#!/usr/bin/env python3
import time
from neo4j import GraphDatabase

def test_graph():
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "wikigraph"
    
    print(f"Connecting to Neo4j at {uri}...")
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    try:
        with driver.session() as session:
            print("\n--- Basic Statistics ---")
            
            # Count Nodes
            nodes = session.run("MATCH (n) RETURN labels(n)[0] as label, count(*) as count").data()
            for row in nodes:
                print(f"Label: {row['label']:<10} | Count: {row['count']:,}")
            
            # Count Relationships
            rels = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(*) as count").data()
            for row in rels:
                print(f"Type:  {row['type']:<10} | Count: {row['count']:,}")

            print("\n--- Connectivity Test ---")
            # Sample Path Discovery (German context)
            # Find a path between 'Berlin' and 'München'
            query = """
            MATCH (a:Article {title: 'Berlin', lang: 'de'}), (b:Article {title: 'München', lang: 'de'})
            MATCH p = shortestPath((a)-[:LINKS_TO*..3]->(b))
            RETURN p
            """
            print("Searching for shortest path: Berlin (DE) -> München (DE)...")
            result = session.run(query).single() 
            
            if result:
                path = result['p']
                nodes = [n['title'] for n in path.nodes]
                print(f"✅ Found Path: {' -> '.join(nodes)}")
            else:
                # Try finding just the nodes first to confirm title indexing
                print("Checking if nodes exist...")
                a_exists = session.run("MATCH (a:Article {title: 'Berlin', lang: 'de'}) RETURN a.title").single()
                b_exists = session.run("MATCH (a:Article {title: 'München', lang: 'de'}) RETURN a.title").single()
                print(f"Berlin exists: {bool(a_exists)}")
                print(f"München exists: {bool(b_exists)}")

    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        print("Note: The import might still be running in the background.")
    finally:
        driver.close()

if __name__ == "__main__":
    test_graph()
