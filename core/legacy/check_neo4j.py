
from neo4j import GraphDatabase
import time
import sys

def check_neo4j():
    print("Connecting to Neo4j...")
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "wikigraph"
    
    for i in range(10):
        try:
            driver = GraphDatabase.driver(uri, auth=(user, password))
            driver.verify_connectivity()
            print("SUCCESS: Neo4j is ready!")
            driver.close()
            return True
        except Exception as e:
            print(f"Attempt {i+1}: Waiting for Neo4j... ({e})")
            time.sleep(5)
    return False

if __name__ == "__main__":
    if not check_neo4j():
        sys.exit(1)
