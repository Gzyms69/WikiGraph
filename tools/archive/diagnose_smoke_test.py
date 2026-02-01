import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def diagnose():
    conn = sqlite3.connect("data/db/de.db")
    cursor = conn.cursor()
    
    # 1. Inspect Berlin specifically
    logger.info("--- Inspecting 'Berlin' (Q64) ---")
    
    # Get all pages with title 'Berlin'
    cursor.execute("SELECT page_id, title, namespace, infobox FROM pages WHERE title = 'Berlin'")
    pages = cursor.fetchall()
    for p in pages:
        has_data = "YES" if p[3] else "NO"
        logger.info(f"Page ID: {p[0]}, Title: {p[1]}, Namespace: {p[2]}, Has Infobox: {has_data}")
        
    # Check where Q64 points
    cursor.execute("SELECT page_id FROM id_mapping WHERE qid = 'Q64'")
    mapping = cursor.fetchone()
    if mapping:
        mapped_id = mapping[0]
        logger.info(f"Q64 maps to Page ID: {mapped_id}")
    else:
        logger.info("Q64 not found in id_mapping")

    # 2. Find a Golden QID (One that definitely has data)
    logger.info("\n--- Finding Golden QID ---")
    query = """
        SELECT m.qid, p.title 
        FROM pages p 
        JOIN id_mapping m ON p.page_id = m.page_id 
        WHERE p.infobox IS NOT NULL AND length(p.infobox) > 10
        LIMIT 1
    """
    cursor.execute(query)
    golden = cursor.fetchone()
    if golden:
        logger.info(f"Golden Candidate: QID={golden[0]}, Title={golden[1]}")
    else:
        logger.error("No pages with infoboxes found linked to QIDs!")

    conn.close()

if __name__ == "__main__":
    diagnose()
