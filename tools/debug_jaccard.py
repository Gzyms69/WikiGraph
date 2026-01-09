from neo4j import GraphDatabase
import time

uri = "bolt://localhost:7687"
auth = ("neo4j", "wikigraph")
qid = "Q102317" # Kielce

query = """
    MATCH (c:Concept {qid: $qid})
    MATCH (c)-[:LINKS_TO]-(neighbor:Concept)
    MATCH (neighbor)<-[:REPRESENTS]-(a:Article)
    WHERE NOT a.title =~ '^\\d+$' 
      AND NOT a.title =~ '^\\d+ .*'
      AND NOT a.title STARTS WITH 'List of'
      AND NOT a.title STARTS WITH 'Lista '
      AND NOT a.title STARTS WITH 'Kategoria:'
      AND NOT a.title STARTS WITH 'Category:'
      AND NOT a.title CONTAINS 'Biografien'
    
    WITH c, neighbor, a, COUNT { (c)-[:LINKS_TO]-() } as c_degree
    MATCH (c)-[:LINKS_TO]-(common)-[:LINKS_TO]-(neighbor)
    WITH c, c_degree, neighbor, a, count(common) as intersection
    
    WITH neighbor, a, intersection, c_degree, COUNT { (neighbor)-[:LINKS_TO]-() } as n_degree
    WITH neighbor, a, intersection, (c_degree + n_degree - intersection) as union_size
    
    WITH neighbor, a, 
         CASE WHEN union_size > 0 
              THEN (1.0 * intersection / union_size) 
              ELSE 0.0 
         END as score
    
    ORDER BY score DESC
    RETURN neighbor.qid, a.title, score LIMIT 10
"""

print(f"Connecting to {uri}...")
driver = GraphDatabase.driver(uri, auth=auth)
with driver.session() as session:
    print("Running Jaccard Query...")
    start = time.time()
    results = session.run(query, qid=qid).data()
    end = time.time()
    print(f"Query took {end - start:.4f} seconds")
    for r in results:
        print(r)
driver.close()
