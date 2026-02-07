import sqlite3
import json
import asyncio
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from app.services.language_service import LanguageService
from app.services.sqlite_pool import SQLitePool
from app.models import Infobox

logger = logging.getLogger(__name__)

class SQLiteService:
    """
    Async Service for SQLite metadata access.
    Uses run_in_executor to avoid blocking the Event Loop.
    Uses SQLitePool for connection management.
    """
    
    def _sync_get_concept_metadata(self, db_path: str, qid: str) -> Dict[str, Any]:
        """
        Synchronous fetch of Title + Infobox.
        """
        try:
            with SQLitePool.get_connection(db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT p.title, p.infobox
                    FROM pages p
                    JOIN id_mapping m ON p.page_id = m.page_id
                    WHERE m.qid = ?
                """
                cursor.execute(query, (qid,))
                row = cursor.fetchone()
                
                if not row:
                    return {"title": None, "infobox": None}
                
                title = row[0]
                infobox_raw = row[1]
                infobox_parsed = []
                
                if infobox_raw:
                    try:
                        infobox_parsed = json.loads(infobox_raw)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to decode JSON for {qid}")
                
                return {"title": title, "infobox": infobox_parsed}
            
        except Exception as e:
            logger.error(f"SQLite error for {qid} in {db_path}: {e}")
            return {"title": None, "infobox": None}

    async def get_concept_metadata(self, lang: str, qid: str) -> Dict[str, Any]:
        """
        Async fetch of concept metadata.
        """
        config = LanguageService.get_config(lang)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, 
            self._sync_get_concept_metadata, 
            config.db_path, 
            qid
        )

    def _sync_get_titles_batch(self, db_path: str, qids: List[str]) -> Dict[str, str]:
        if not qids: return {}
        try:
            with SQLitePool.get_connection(db_path) as conn:
                cursor = conn.cursor()
                
                placeholders = ','.join(['?'] * len(qids))
                query = f"""
                    SELECT m.qid, p.title 
                    FROM pages p 
                    JOIN id_mapping m ON p.page_id = m.page_id 
                    WHERE m.qid IN ({placeholders})
                """
                cursor.execute(query, qids)
                return {row[0]: row[1] for row in cursor.fetchall()}
        except Exception as e:
            logger.error(f"Batch title error in {db_path}: {e}")
            return {}

    async def get_titles_batch(self, lang: str, qids: List[str]) -> Dict[str, str]:
        """
        Async batch title fetch.
        """
        config = LanguageService.get_config(lang)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self._sync_get_titles_batch,
            config.db_path,
            qids
        )

    def _sync_search_articles(self, db_path: str, query: str, limit: int = 50) -> List[Dict[str, str]]:
        results = []
        try:
            with SQLitePool.get_connection(db_path) as conn:
                cursor = conn.cursor()
                # Use FTS5 match query
                # We order by rank to get best matches first
                sql = """
                    SELECT title, qid 
                    FROM articles_fts 
                    WHERE articles_fts MATCH ? 
                    ORDER BY rank 
                    LIMIT ?
                """
                # Sanitize query for FTS5 (basic)
                # FTS5 syntax can be complex. We'll wrap in quotes for phrase search or leave raw?
                # For now, let's treat it as a phrase or simple tokens. 
                # To make it robust against syntax errors, we might want to sanitize.
                # But for V1, passing raw query allows power users to use AND/OR/NEAR.
                cursor.execute(sql, (query, limit))
                for row in cursor.fetchall():
                    results.append({"title": row[0], "qid": row[1]})
        except Exception as e:
            logger.error(f"Search failed in {db_path}: {e}")
        return results

    async def search_articles(self, lang: str, query: str, limit: int = 50) -> List[Dict[str, str]]:
        """
        Async FTS5 search.
        """
        config = LanguageService.get_config(lang)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self._sync_search_articles,
            config.db_path,
            query,
            limit
        )

    async def get_compare_metadata(self, qid: str, langs: List[str]) -> Dict[str, Any]:
        """
        Fetches metadata for a QID across multiple languages in parallel.
        """
        tasks = [self.get_concept_metadata(lang, qid) for lang in langs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        comparison = {}
        for lang, res in zip(langs, results):
            if isinstance(res, Exception):
                logger.error(f"Comparison fetch failed for {lang}/{qid}: {res}")
                comparison[lang] = None
            else:
                comparison[lang] = res
        return comparison
