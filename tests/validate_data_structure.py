"""
COMPREHENSIVE DATA STRUCTURE VALIDATION
Validates the enriched Neo4j structure and consistency with SQLite
"""
import asyncio
import sqlite3
from app.services.neo4j_manager import Neo4jManager
import time
import random

async def validate_neo4j_structure(lang: str):
    """Validate Neo4j node properties and data consistency"""
    print(f"\n{'='*60}")
    print(f"NEO4J STRUCTURE VALIDATION: {lang.upper()}")
    print(f"{'='*60}")
    
    manager = Neo4jManager()
    results = {
        "language": lang,
        "total_nodes": 0,
        "nodes_with_title": 0,
        "nodes_with_out_degree": 0,
        "nodes_with_in_degree": 0,
        "sample_checks": []
    }
    
    try:
        # 1. Get overall statistics
        stats_query = """
        MATCH (n:Concept)
        RETURN 
            count(n) as total,
            sum(CASE WHEN n.title IS NOT NULL THEN 1 ELSE 0 END) as with_title,
            sum(CASE WHEN n.out_degree IS NOT NULL THEN 1 ELSE 0 END) as with_out_degree,
            sum(CASE WHEN n.in_degree IS NOT NULL THEN 1 ELSE 0 END) as with_in_degree,
            avg(n.out_degree) as avg_out_degree,
            max(n.out_degree) as max_out_degree
        """
        stats = await manager.query(lang, stats_query)
        if stats:
            row = stats[0]
            results["total_nodes"] = row["total"]
            results["nodes_with_title"] = row["with_title"]
            results["nodes_with_out_degree"] = row["with_out_degree"]
            results["nodes_with_in_degree"] = row["with_in_degree"]
            
            print(f"📊 PROPERTY COVERAGE:")
            print(f"  ├─ Total Nodes: {row['total']:,}")
            if row['total'] > 0:
                print(f"  ├─ With Title: {row['with_title']:,} ({row['with_title']/row['total']*100:.1f}%)")
                print(f"  ├─ With Out Degree: {row['with_out_degree']:,} ({row['with_out_degree']/row['total']*100:.1f}%)")
                print(f"  ├─ With In Degree: {row['with_in_degree']:,} ({row['with_in_degree']/row['total']*100:.1f}%)")
            print(f"  ├─ Avg Out Degree: {row['avg_out_degree']:.2f}")
            print(f"  └─ Max Out Degree: {row['max_out_degree']:,}")
        
        # 2. Sample validation: Check 100 random nodes
        print(f"\n🔍 SAMPLE VALIDATION (100 random nodes):")
        # Neo4j 5.x doesn't have rand() directly in ORDER BY for all editions efficiently, 
        # but we'll use it if supported or fallback to a sample of recently updated.
        sample_query = """
        MATCH (n:Concept)
        WHERE n.title IS NOT NULL AND n.out_degree IS NOT NULL
        RETURN n.qid as qid, n.title as neo4j_title, n.out_degree as neo4j_out_degree
        LIMIT 500
        """
        all_samples = await manager.query(lang, sample_query)
        if not all_samples:
            print("  ⚠️ No nodes with titles and degrees found for sampling.")
            return results

        sample_nodes = random.sample(all_samples, min(len(all_samples), 100))
        
        # Connect to SQLite for comparison
        db_path = f"data/db/{lang}.db"
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        title_matches = 0
        degree_matches = 0
        
        for i, node in enumerate(sample_nodes, 1):
            qid = node["qid"]
            
            # Check SQLite for title
            cur.execute("SELECT p.title FROM pages p JOIN id_mapping m ON p.page_id = m.page_id WHERE m.qid = ?", (qid,))
            sqlite_row = cur.fetchone()
            sqlite_title = sqlite_row["title"] if sqlite_row else None
            
            # Check actual edge count in Neo4j
            edge_count_query = """
            MATCH (n:Concept {qid: $qid})-[r:LINKS_TO]->()
            RETURN count(r) as actual_edges
            """
            edge_result = await manager.query(lang, edge_count_query, {"qid": qid})
            actual_edges = edge_result[0]["actual_edges"] if edge_result else 0
            
            # Record results
            check_result = {
                "qid": qid,
                "neo4j_title": node["neo4j_title"],
                "sqlite_title": sqlite_title,
                "neo4j_out_degree": node["neo4j_out_degree"],
                "actual_edges": actual_edges,
                "titles_match": node["neo4j_title"] == sqlite_title if sqlite_title else False,
                "degree_matches": node["neo4j_out_degree"] == actual_edges
            }
            
            results["sample_checks"].append(check_result)
            
            if check_result["titles_match"]:
                title_matches += 1
            if check_result["degree_matches"]:
                degree_matches += 1
            
            # Print first 5 for inspection
            if i <= 5:
                status = "✅" if check_result["titles_match"] else "⚠️"
                degree_status = "✅" if check_result["degree_matches"] else "⚠️"
                print(f"  {i}. {qid}: {status} Title, {degree_status} Degree")
                if not check_result["titles_match"]:
                    print(f"     Neo4j: '{node['neo4j_title']}'")
                    print(f"     SQLite: '{sqlite_title}'")
        
        conn.close()
        
        print(f"\n📈 SAMPLE RESULTS:")
        print(f"  ├─ Title Matches: {title_matches}/100")
        print(f"  └─ Degree Matches: {degree_matches}/100")
        
        # 3. Check specific known nodes
        print(f"\n🎯 KNOWN NODE VALIDATION:")
        known_nodes = [
            ("Q15828079", "Deutsches Reich"),  # German Reich
            ("Q36", "Polen"),  # Poland
            ("Q42", "Douglas Adams"),  # Douglas Adams
        ]
        
        for qid, expected_title in known_nodes:
            query = """
            MATCH (n:Concept {qid: $qid})
            RETURN n.qid as qid, n.title as title, n.out_degree as out_degree
            """
            result = await manager.query(lang, query, {"qid": qid})
            
            if result:
                node = result[0]
                actual_title = node.get("title", "NO TITLE")
                # Case insensitive check
                match = expected_title.lower() in actual_title.lower() if actual_title else False
                status = "✅" if match else "❌"
                print(f"  {status} {qid}: Expected contains '{expected_title}', Got '{actual_title}'")
            else:
                if lang == 'de' or qid == "Q36": # Q36 is in both
                    print(f"  ❌ {qid}: Not found in Neo4j {lang.upper()}")
        
    except Exception as e:
        print(f"  ❌ Validation error: {e}")
    
    return results

async def main():
    start_time = time.time()
    
    # Validate both databases
    all_results = []
    for lang in ["pl", "de"]:
        results = await validate_neo4j_structure(lang)
        all_results.append(results)
    
    duration = time.time() - start_time
    print(f"\n⏱️ Total validation time: {duration:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())
