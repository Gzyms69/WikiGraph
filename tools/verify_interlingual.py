#!/usr/bin/env python3
"""
WikiGraph: Interlingual Verification
Tests the graph's ability to unify and traverse across languages.
"""

from neo4j import GraphDatabase
import sys

# Configuration
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "wikigraph")

def run_query(tx, query, **params):
    result = tx.run(query, **params)
    return [record for record in result]

def verify_graph():
    print("🌍 WIKIGRAPH INTERLINGUAL VERIFICATION")
    print("=======================================")
    
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        with driver.session() as session:
            
            # TEST 1: Unified Concepts
            # Find concepts that are represented in BOTH Polish and German
            print("\n🧪 TEST 1: Unified Concepts (PL + DE)")
            query_1 = """
            MATCH (c:Concept)
            WHERE size([(c)<-[:REPRESENTS]-(a) WHERE a.lang = 'pl' | 1]) > 0 
              AND size([(c)<-[:REPRESENTS]-(a) WHERE a.lang = 'de' | 1]) > 0
            RETURN c.qid as qid, 
                   [(c)<-[:REPRESENTS]-(a) WHERE a.lang = 'pl' | a.title][0] as pl_title,
                   [(c)<-[:REPRESENTS]-(a) WHERE a.lang = 'de' | a.title][0] as de_title
            LIMIT 5
            """
            results_1 = session.execute_read(run_query, query_1)
            for r in results_1:
                print(f"   ✅ [{r['qid']}] PL: {r['pl_title']} <---> DE: {r['de_title']}")
            if not results_1:
                print("   ❌ No unified concepts found!")

            # TEST 2: Cross-Lingual Traversal
            # Start at 'Polska' (PL), follow links to Concepts, find German Articles representing those concepts
            print("\n🧪 TEST 2: Cross-Lingual Neighbors of 'Polska' (PL)")
            query_2 = """
            MATCH (start:Article {lang: 'pl', title: 'Polska'})-[:REPRESENTS]->(c_start:Concept)
            MATCH (c_start)-[:LINKS_TO]->(c_end:Concept)
            MATCH (c_end)<-[:REPRESENTS]-(end:Article {lang: 'de'})
            RETURN end.title as de_neighbor, c_end.qid as qid
            LIMIT 5
            """
            results_2 = session.execute_read(run_query, query_2)
            for r in results_2:
                print(f"   ✅ 'Polska' (PL) --links--> [{r['qid']}] --> '{r['de_neighbor']}' (DE)")

            # TEST 3: Interlingual Shortest Path
            # Path from Warszawa (PL) to Berlin (DE)
            # The path goes: Article(PL) -> Concept -> [LINKS_TO*] -> Concept <- Article(DE)
            print("\n🧪 TEST 3: Shortest Path: Warszawa (PL) -> Berlin (DE)")
            query_3 = """
            MATCH (start:Article {lang: 'pl', title: 'Warszawa'})
            MATCH (end:Article {lang: 'de', title: 'Berlin'})
            MATCH p = shortestPath((start)-[:REPRESENTS|LINKS_TO*]-(end))
            RETURN [n in nodes(p) | CASE 
                WHEN 'Article' IN labels(n) THEN n.title + ' (' + n.lang + ')'
                WHEN 'Concept' IN labels(n) THEN 'Concept ' + n.qid
                ELSE 'Unknown'
            END] as path, length(p) as hops
            """
            results_3 = session.execute_read(run_query, query_3)
            if results_3:
                path = results_3[0]['path']
                hops = results_3[0]['hops']
                print(f"   ✅ Path found ({hops} hops):")
                print("      " + " -> ".join(path))
            else:
                print("   ❌ No path found between Warszawa (PL) and Berlin (DE)")

if __name__ == "__main__":
    try:
        verify_graph()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
