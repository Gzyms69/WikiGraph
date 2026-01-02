#!/usr/bin/env python3
from neo4j import GraphDatabase

def setup_schema():
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "wikigraph"
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    print("🚀 Initializing Concept-Centric Schema...")
    
    with driver.session() as session:
        # Constraints
        session.run("CREATE CONSTRAINT concept_qid IF NOT EXISTS FOR (c:Concept) REQUIRE c.qid IS UNIQUE")
        session.run("CREATE CONSTRAINT article_id IF NOT EXISTS FOR (a:Article) REQUIRE a.id IS UNIQUE")
        
        # Indexes for fast search
        session.run("CREATE INDEX article_title_lang IF NOT EXISTS FOR (a:Article) ON (a.title, a.lang)")
        session.run("CREATE INDEX article_lang IF NOT EXISTS FOR (a:Article) ON (a.lang)")
        
        print("✅ Constraints and Indexes created.")
        
    driver.close()

if __name__ == "__main__":
    setup_schema()
