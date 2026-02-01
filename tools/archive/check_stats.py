from app.database import db

def check_stats():
    query = """
    MATCH (a:Article)
    RETURN a.lang as lang, count(a) as count
    ORDER BY count DESC
    """
    with db.get_session() as session:
        res = session.run(query).data()
        for r in res:
            print(f"{r['lang']}: {r['count']}")

if __name__ == "__main__":
    check_stats()
