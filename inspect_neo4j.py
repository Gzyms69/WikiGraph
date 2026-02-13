from neo4j import GraphDatabase
import json

def inspect_lang(lang, bolt_port):
    uri = f"bolt://localhost:{bolt_port}"
    auth = ("neo4j", "wikigraph")
    report = {"language": lang, "nodes": {}, "relationships": {}}
    
    try:
        driver = GraphDatabase.driver(uri, auth=auth)
        with driver.session() as session:
            # Node labels and counts
            res = session.run("CALL db.labels()")
            labels = [r[0] for r in res]
            
            for label in labels:
                count_res = session.run(f"MATCH (n:{label}) RETURN count(n) as count").single()
                count = count_res["count"]
                
                # Check for properties completeness
                # Get some sample keys from first 1000 nodes
                prop_res = session.run(f"MATCH (n:{label}) WITH n LIMIT 1000 UNWIND keys(n) as key RETURN DISTINCT key")
                props = [r["key"] for r in prop_res]
                
                prop_stats = {}
                for prop in props:
                    prop_count_res = session.run(f"MATCH (n:{label}) WHERE n.{prop} IS NOT NULL RETURN count(n) as count").single()
                    prop_stats[prop] = {
                        "count": prop_count_res["count"],
                        "completeness_pct": round(prop_count_res["count"] / count * 100, 2) if count > 0 else 0
                    }
                
                report["nodes"][label] = {
                    "count": count,
                    "properties": prop_stats
                }
            
            # Relationships
            res = session.run("CALL db.relationshipTypes()")
            rel_types = [r[0] for r in res]
            
            for rel_type in rel_types:
                count_res = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count").single()
                count = count_res["count"]
                
                # Relationship properties
                prop_res = session.run(f"MATCH ()-[r:{rel_type}]->() WITH r LIMIT 1000 UNWIND keys(r) as key RETURN DISTINCT key")
                props = [r["key"] for r in prop_res]
                
                prop_stats = {}
                for prop in props:
                    prop_count_res = session.run(f"MATCH ()-[r:{rel_type}]->() WHERE r.{prop} IS NOT NULL RETURN count(r) as count").single()
                    prop_stats[prop] = {
                        "count": prop_count_res["count"],
                        "completeness_pct": round(prop_count_res["count"] / count * 100, 2) if count > 0 else 0
                    }
                
                report["relationships"][rel_type] = {
                    "count": count,
                    "properties": prop_stats
                }
                
        driver.close()
    except Exception as e:
        report["error"] = str(e)
    
    return report

if __name__ == "__main__":
    configs = [
        ("pl", 7687),
        ("de", 7688),
        ("es", 7757)
    ]
    
    results = []
    for lang, port in configs:
        print(f"Inspecting {lang} on port {port}...")
        results.append(inspect_lang(lang, port))
    
    with open("neo4j_audit.json", "w") as f:
        json.dump(results, f, indent=2)
