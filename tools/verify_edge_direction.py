import asyncio
from app.services.neo4j_manager import Neo4jManager

async def verify_direction():
    manager = Neo4jManager()
    qid = "Q15828079"
    
    queries = {
        "outgoing": f"MATCH (n:Concept {{qid: '{qid}'}})-[r:LINKS_TO]->(m) RETURN count(r) as cnt",
        "incoming": f"MATCH (n:Concept {{qid: '{qid}'}})<-[r:LINKS_TO]-(m) RETURN count(r) as cnt"
    }
    
    for lang in ["de", "pl"]:
        print(f"--- {lang.upper()} Direction Check ---")
        for direction, q in queries.items():
            try:
                res = await manager.query(lang, q)
                if res:
                    print(f"{direction}: {res[0]['cnt']}")
                else:
                    print(f"{direction}: 0 (No result)")
            except Exception as e:
                print(f"{direction} error: {e}")
                
    await manager.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(verify_direction())
