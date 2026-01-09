#!/usr/bin/env python3
from neo4j import GraphDatabase
import os
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("precompute")

uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "wikigraph")

def precompute():
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    with driver.session() as session:
        logger.info("🚀 Starting Batched Precomputation Pipeline...")
        
        # 1. Cleanup old state
        logger.info("🧹 Cleaning up old projections and labels...")
        session.run("CALL gds.graph.exists('wikigraph_precompute') YIELD exists WHERE exists CALL gds.graph.drop('wikigraph_precompute') YIELD graphName RETURN count(*)")
        session.run("MATCH (n:NodeCache) DETACH DELETE n")
        session.run("MATCH (n:HighRank) REMOVE n:HighRank")
        
        # 2. Precompute Degrees (BATCHED with APOC)
        logger.info("📐 Precomputing node degrees (Batched)...")
        session.run("""
            CALL apoc.periodic.iterate(
                "MATCH (c:Concept) RETURN c",
                "SET c.degree = COUNT { (c)-[:LINKS_TO]-() }",
                {batchSize: 1000, parallel: true}
            )
        """)
        
        # 3. Create Basic Indexes
        logger.info("🔍 Creating primary indexes...")
        session.run("CREATE CONSTRAINT concept_qid_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.qid IS UNIQUE")
        session.run("CREATE INDEX concept_degree IF NOT EXISTS FOR (c:Concept) ON (c.degree)")
        session.run("CREATE INDEX article_title_lang IF NOT EXISTS FOR (a:Article) ON (a.title, a.lang)")
        
        # 4. Project ONLY Concepts (Memory Optimized)
        logger.info("📦 Projecting Concept graph into GDS...")
        session.run("""
            CALL gds.graph.project(
                'wikigraph_precompute',
                'Concept',
                {
                    LINKS_TO: {orientation: 'UNDIRECTED'}
                }
            )
        """)
        
        # 5. Compute PageRank
        logger.info("✍️  Writing PageRank scores...")
        session.run("""
            CALL gds.pageRank.write('wikigraph_precompute', {
                writeProperty: 'pagerank',
                maxIterations: 30,
                dampingFactor: 0.85
            })
        """)
        
        # 6. Compute Louvain Communities
        logger.info("✍️  Writing Louvain Communities...")
        session.run("""
            CALL gds.louvain.write('wikigraph_precompute', {
                writeProperty: 'community'
            })
        """)
        
        # 7. Drop Projection
        logger.info("🧹 Dropping projection...")
        session.run("CALL gds.graph.drop('wikigraph_precompute')")
        
        # 8. Label Top Nodes
        logger.info("🏷️  Labeling Top 1000 nodes as HighRank...")
        session.run("""
            MATCH (c:Concept)
            WHERE c.pagerank IS NOT NULL
            WITH c ORDER BY c.pagerank DESC LIMIT 1000
            SET c:HighRank
        """)
        
        # 9. Create Materialized Cache (NodeCache)
        logger.info("💎 Creating Materialized Cache (NodeCache)...")
        # Step 1: Base Metadata
        session.run("""
            MATCH (c:HighRank)
            WITH c LIMIT 500
            MATCH (c)<-[:REPRESENTS]-(a:Article)
            WITH c, a ORDER BY CASE WHEN a.lang = 'pl' THEN 1 WHEN a.lang = 'en' THEN 2 ELSE 3 END, size(a.title) DESC
            WITH c, head(collect(a)) as main_article
            MERGE (nc:NodeCache {qid: c.qid})
            SET nc.name = main_article.title,
                nc.lang = main_article.lang,
                nc.val = c.pagerank,
                nc.community = coalesce(c.community, -1)
        """)
        
        logger.info("🔗 Pre-linking HighRank nodes in cache...")
        session.run("""
            MATCH (nc:NodeCache)
            MATCH (c:Concept {qid: nc.qid})
            OPTIONAL MATCH (c)-[:LINKS_TO]-(neighbor:HighRank)
            WITH nc, collect(DISTINCT neighbor.qid)[0..10] as neighbors
            SET nc.neighbors = neighbors
        """)
        
        # 10. Create Cache Index
        session.run("CREATE INDEX node_cache_qid IF NOT EXISTS FOR (n:NodeCache) ON (n.qid)")
        
        logger.info("✅ Precomputation and Caching Complete!")

    driver.close()

if __name__ == "__main__":
    precompute()