from neo4j import GraphDatabase
import sys

uri = "bolt://localhost:7687"
auth = ("neo4j", "wikigraph")

def check_node(qid):
    driver = GraphDatabase.driver(uri, auth=auth)
    with driver.session() as session:
        # Check Concept
        res = session.run("MATCH (c:Concept {qid: $qid}) RETURN c", qid=qid).single()
        if not res:
            print(f"❌ Concept {qid} NOT FOUND.")
            return

        print(f"✅ Concept {qid} found.")
        
        # Check Articles
        res = session.run("MATCH (c:Concept {qid: $qid})<-[:REPRESENTS]-(a:Article) RETURN a.title, a.lang, a.id", qid=qid)
        articles = [r.data() for r in res]
        
        if not articles:
            print(f"⚠️  No Articles connected to {qid}!")
        else:
            print(f"📚 Connected Articles ({len(articles)}):")
            for a in articles:
                print(f"   - [{a['a.lang']}] {a['a.title']} (ID: {a['a.id']})")

    driver.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 debug_node.py <QID>")
    else:
        check_node(sys.argv[1])
