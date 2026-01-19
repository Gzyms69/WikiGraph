import sqlite3
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class MetadataManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MetadataManager, cls).__new__(cls)
        return cls._instance

    def get_title(self, lang: str, qid: str) -> str:
        """
        Fetches the article title for a QID from the local SQLite database.
        """
        db_path = Path(f"data/db/{lang}.db")
        if not db_path.exists():
            return None
            
        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cursor = conn.cursor()
            query = """
                SELECT p.title 
                FROM pages p 
                JOIN id_mapping m ON p.page_id = m.page_id 
                WHERE m.qid = ?
            """
            cursor.execute(query, (qid,))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"Metadata fetch failed for {lang}/{qid}: {e}")
            return None

    def get_titles_batch(self, lang: str, qids: list) -> dict:
        """
        Fetches titles for a list of QIDs.
        Returns: { 'Q1': 'Title1', 'Q2': 'Title2' }
        """
        if not qids: return {}
        
        db_path = Path(f"data/db/{lang}.db")
        if not db_path.exists(): return {}

        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cursor = conn.cursor()
            
            # SQLite limit is usually 999 vars, but we paginate to 10-50 neighbors so it's safe.
            placeholders = ','.join(['?'] * len(qids))
            query = f"""
                SELECT m.qid, p.title 
                FROM pages p 
                JOIN id_mapping m ON p.page_id = m.page_id 
                WHERE m.qid IN ({placeholders})
            """
            cursor.execute(query, qids)
            result = {row[0]: row[1] for row in cursor.fetchall()}
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Batch metadata fetch failed for {lang}: {e}")
            return {}