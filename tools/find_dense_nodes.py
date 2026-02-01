import sqlite3
import sys

def find_dense(lang):
    try:
        conn = sqlite3.connect(f"data/db/{lang}.db")
        cur = conn.cursor()
        # Note: edges table stores src as QID string in 'src' column? 
        # Or page_id?
        # Let's check schema first.
        # Based on project context, edges usually link QIDs or page_ids.
        # core/sqlite_loader.py suggests edges table has (src, tgt)
        # and src/tgt are QIDs (TEXT).
        
        cur.execute("SELECT src, COUNT(*) as cnt FROM edges GROUP BY src ORDER BY cnt DESC LIMIT 5")
        rows = cur.fetchall()
        print(f"--- {lang.upper()} Dense Nodes ---")
        for r in rows:
            print(f"{r[0]}: {r[1]}")
        conn.close()
    except Exception as e:
        print(f"Error querying {lang}: {e}")

if __name__ == "__main__":
    find_dense("pl")
    find_dense("de")
