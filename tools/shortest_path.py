#!/usr/bin/env python3
from neo4j import GraphDatabase

def find_shortest_path_advanced(start_title, end_title, lang='pl'):
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "wikigraph"
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    # This query allows for LINKS_TO or REDIRECTS_TO at each step
    query = """
    MATCH (start:Article {title: $start_title, lang: $lang}), 
          (end:Article {title: $end_title, lang: $lang})
    MATCH p = shortestPath((start)-[:LINKS_TO|REDIRECTS_TO*..10]->(end))
    RETURN p
    """
    
    print(f"Searching for advanced path (including redirects): {start_title} -> {end_title} ({lang})...")
    
    try:
        with driver.session() as session:
            result = session.run(query, start_title=start_title, end_title=end_title, lang=lang).single() 
            
            if result:
                path = result['p']
                # Collect titles from both Articles and Aliases in the path
                steps = []
                for node in path.nodes:
                    steps.append(f"{node['title']} ({list(node.labels)[0]})")
                print(f"✅ Found Path ({len(steps)-1} steps): {' -> '.join(steps)}")
            else:
                print("❌ Still no path found. Checking outgoing links from Kraków...")
                links = session.run("""
                    MATCH (n:Article {title: $start_title, lang: $lang})-[r:LINKS_TO]->(m) 
                    RETURN m.title as target LIMIT 5
                """, start_title=start_title, lang=lang).data()
                print(f"Sample links from {start_title}: {[l['target'] for l in links]}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    find_shortest_path_advanced("Kraków", "Kielce")