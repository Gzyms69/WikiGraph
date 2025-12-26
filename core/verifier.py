import sys
from neo4j import GraphDatabase
from tqdm import tqdm

class RobustVerifier:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def run_query(self, query, **kwargs):
        with self.driver.session() as session:
            return list(session.run(query, **kwargs))

    def test_hubs(self, lang="pl"):
        print(f"\n--- Top 5 Most Connected Articles (Hubs) [{lang}] ---")
        query = """
        MATCH (a:Article {lang: $lang})
        RETURN a.title as title, COUNT { (a)--() } as degree
        ORDER BY degree DESC
        LIMIT 5
        """
        results = self.run_query(query, lang=lang)
        for r in results:
            print(f" {r['degree']:<8,} connections | {r['title']}")

    def find_fuzzy_path(self, start_fuzzy, end_fuzzy, lang="pl"):
        print(f"\n--- Pathfinding (Fuzzy): '{start_fuzzy}' -> '{end_fuzzy}' ---")
        # Find exact titles first using CONTAINS or STARTS WITH to be safe
        query_titles = """
        MATCH (a:Article {lang: $lang})
        WHERE a.title CONTAINS $fuzzy
        RETURN a.title as title LIMIT 1
        """
        start_title_res = self.run_query(query_titles, fuzzy=start_fuzzy, lang=lang)
        end_title_res = self.run_query(query_titles, fuzzy=end_fuzzy, lang=lang)
        
        if not start_title_res or not end_title_res:
            print(f" Could not resolve fuzzy titles. Found: Start={start_title_res}, End={end_title_res}")
            return

        start_title = start_title_res[0]['title']
        end_title = end_title_res[0]['title']
        print(f" Resolved to: '{start_title}' -> '{end_title}'")

        path_query = """
        MATCH (start:Article {title: $start, lang: $lang}), (end:Article {title: $end, lang: $lang})
        MATCH p = shortestPath((start)-[:LINKS_TO*..10]->(end))
        RETURN [n in nodes(p) | n.title] as path
        """
        res = self.run_query(path_query, start=start_title, end=end_title, lang=lang)
        if res:
            print(f" Path: {' -> '.join(res[0]['path'])}")
        else:
            print(" No path found within 10 hops.")

    def check_link_reciprocity(self, lang="pl"):
        print(f"\n--- Link Reciprocity (Mutual Links) ---")
        query = """
        MATCH (a:Article {lang: $lang})-[r1:LINKS_TO]->(b:Article {lang: $lang})
        WHERE (b)-[:LINKS_TO]->(a)
        RETURN a.title, b.title LIMIT 3
        """
        results = self.run_query(query, lang=lang)
        print(" Sample mutual links:")
        for r in results:
            print(f"  {r['a.title']} <--> {r['b.title']}")

def main():
    verifier = RobustVerifier("bolt://localhost:7687", "neo4j", "wikigraph")
    try:
        verifier.test_hubs("pl")
        verifier.check_link_reciprocity("pl")
        
        # Testing logical paths
        verifier.find_fuzzy_path("Fryderyk Chopin", "Maria Skłodowska", "pl")
        verifier.find_fuzzy_path("Python", "Informatyka", "pl")
        verifier.find_fuzzy_path("Warszawa", "Kraków", "pl")
        
    finally:
        verifier.close()

if __name__ == "__main__":
    main()
