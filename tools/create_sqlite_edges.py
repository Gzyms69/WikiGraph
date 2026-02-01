import sqlite3
import sys

def create_edges_table(lang):
    print(f"Creating edges table for {lang}...")
    conn = sqlite3.connect(f"data/db/{lang}.db")
    cur = conn.cursor()
    
    # Check if link_targets exists first
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='link_targets'")
    if not cur.fetchone():
        print(f"Skipping {lang}: link_targets table not found.")
        return

    cur.execute("DROP TABLE IF EXISTS edges") # Clean start
    
    print("   Executing Join Query (May take time)...")
    cur.execute("""
    CREATE TABLE edges AS
    SELECT m_src.qid as src_qid, m_tgt.qid as tgt_qid 
    FROM link_targets lt
    JOIN pages p_src ON lt.src_ns = p_src.ns AND lt.src_title = p_src.title
    JOIN id_mapping m_src ON p_src.page_id = m_src.page_id
    JOIN pages p_tgt ON lt.tgt_ns = p_tgt.ns AND lt.tgt_title = p_tgt.title
    JOIN id_mapping m_tgt ON p_tgt.page_id = m_tgt.page_id
    """)
    
    print("   Creating Indexes...")
    cur.execute("CREATE INDEX idx_edges_src ON edges(src_qid);")
    cur.execute("CREATE INDEX idx_edges_tgt ON edges(tgt_qid);")
    
    cur.execute("SELECT COUNT(*) FROM edges")
    count = cur.fetchone()[0]
    print(f"   Edges created: {count}")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_edges_table("pl")
    create_edges_table("de")
