import asyncio
from app.services.neo4j_manager import Neo4jManager

async def analyze_neo4j():
    print(f"\n{'='*60}")
    print(f"NEO4J ANALYSIS")
    print(f"{'='*60}")
    
    manager = Neo4jManager()
    
    for lang in ["pl", "de"]:
        print(f"\n🌐 LANGUAGE: {lang.upper()}")
        
        try:
            # 1. Total nodes
            query = "MATCH (n) RETURN count(n) as total_nodes"
            res = await manager.query(lang, query)
            if res:
                print(f"  ├─ Total Nodes: {res[0]['total_nodes']:,}")
            else:
                print("  ├─ Total Nodes: 0 (No result)")
            
            # 3. Relationship Types
            query = "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType"
            res = await manager.query(lang, query)
            if res:
                rel_types = [row["relationshipType"] for row in res]
                print(f"  ├─ Relationship Types: {', '.join(rel_types)}")
            else:
                print("  ├─ Relationship Types: None")
            
            # 4. Total relationships
            query = "MATCH ()-[r]->() RETURN count(r) as total_rels"
            res = await manager.query(lang, query)
            if res:
                print(f"  ├─ Total Relationships: {res[0]['total_rels']:,}")
            
            # 5. Check Properties
            query = "MATCH (n:Concept) WITH n LIMIT 1 RETURN keys(n) as properties"
            res = await manager.query(lang, query)
            if res:
                print(f"  ├─ Concept Properties: {res[0]['properties']}")
            
        except Exception as e:
            print(f"  ├─ ERROR: {e}")
            
    await manager.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(analyze_neo4j())
