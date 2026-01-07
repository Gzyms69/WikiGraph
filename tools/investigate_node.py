from neo4j import GraphDatabase
import sys

uri = "bolt://localhost:7687"
auth = ("neo4j", "wikigraph")

def check_problematic_node(qid):
    driver = GraphDatabase.driver(uri, auth=auth)
    with driver.session() as session:
        print(f"🔍 Investigating {qid}...")
        
        # 1. Check Concept
        c = session.run("MATCH (c:Concept {qid: $qid}) RETURN c", qid=qid).single()
        if not c:
            print("❌ Concept not found.")
            return
        print("✅ Concept found.")

        # 2. Check Linked Articles
        res = session.run("""
            MATCH (c:Concept {qid: $qid})<-[:REPRESENTS]-(a:Article)
            RETURN a.id, a.title, a.lang
        """, qid=qid).data()
        
        if not res:
            print("❌ No Articles connected!")
        else:
            for r in res:
                print(f"📄 Article: ID={r['a.id']}, Lang={r['a.lang']}, Title='{r['a.title']}'")

    driver.close()

if __name__ == "__main__":
    check_problematic_node("Q131824731")
    # Also check a local one if user provided it, but Q13... is a good sample
