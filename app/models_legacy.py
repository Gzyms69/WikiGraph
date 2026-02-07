"""
Database models and connection management for WikiGraph API
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from config.language_manager import LanguageManager

logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection(db_path: Optional[Path] = None):
    """
    Context manager for SQLite database connections.

    Args:
        db_path: Path to the SQLite database file. If None, uses default from project root.

    Yields:
        sqlite3.Connection: Database connection
    """
    if db_path is None:
        # Default path relative to project root
        db_path = Path(__file__).parent.parent / "databases" / "wikigraph_multilang.db"
    
    conn = None
    try:
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def create_base_schema(db_path: Optional[Path] = None):
    """
    Create the core multi-language database schema.

    Args:
        db_path: Path to the SQLite database file
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Articles table with language support
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER NOT NULL,
                language TEXT NOT NULL,
                title TEXT NOT NULL,
                revision_id INTEGER,
                timestamp TEXT,
                infobox TEXT,
                categories TEXT,
                word_count INTEGER,
                text_length INTEGER,
                PRIMARY KEY (id, language)
            )
        ''')

        # Links table with language support
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS links (
                source_id INTEGER NOT NULL,
                target_title TEXT NOT NULL,
                language TEXT NOT NULL,
                batch_num INTEGER,
                FOREIGN KEY (source_id, language)
                REFERENCES articles(id, language)
            )
        ''')

        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_lang_title ON articles(language, title)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_title ON articles(title)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_links_lang_target ON links(language, target_title)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_links_source ON links(source_id, language)')

        # Metadata table
        cursor.execute('CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT)')
        
        # Versioning
        cursor.execute("INSERT OR IGNORE INTO metadata (key, value) VALUES ('schema_version', '1.0-multilang')")
        cursor.execute("INSERT OR IGNORE INTO metadata (key, value) VALUES ('created_at', datetime('now'))")
        
        conn.commit()
        logger.info("Base database schema created/verified")

def initialize_fts_tables(db_path: Optional[Path] = None):
    """
    Create FTS5 virtual tables for full-text search if they don't exist.

    Args:
        db_path: Path to the SQLite database file
    """
    available_langs = LanguageManager.list_available_languages()

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        for lang in available_langs:
            fts_table = f"articles_fts_{lang}"

            # Check if FTS table already exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (fts_table,))
            if cursor.fetchone():
                logger.info(f"FTS table {fts_table} already exists")
                continue

            # Create FTS5 virtual table for title search
            # Use ascii tokenizer to preserve diacritics (no unicode normalization)
            cursor.execute(f"""
                CREATE VIRTUAL TABLE {fts_table} USING fts5(
                    title,
                    tokenize="ascii"
                )
            """)

            # Populate FTS table with title data from articles table
            cursor.execute(f"""
                INSERT INTO {fts_table}(rowid, title)
                SELECT rowid, title
                FROM articles
                WHERE language = ?
            """, (lang,))

            logger.info(f"Created and populated FTS table {fts_table}")

        conn.commit()

def search_articles(db_path: Path, query: str, lang: str,
                   limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """
    Perform full-text search on articles.

    Args:
        db_path: Path to the SQLite database file
        query: Search query string
        lang: Language code
        limit: Maximum number of results
        offset: Offset for pagination

    Returns:
        Dict containing results, total count, and language
    """
    fts_table = f"articles_fts_{lang}"

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # Get total count
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM {fts_table}
            WHERE {fts_table} MATCH ?
        """, (query,))

        total = cursor.fetchone()[0]

        # Get results with snippets
        cursor.execute(f"""
            SELECT a.id, fts.title, snippet({fts_table}, 0, '<mark>', '</mark>', '...', 50)
            FROM {fts_table} fts
            JOIN articles a ON a.rowid = fts.rowid
            WHERE {fts_table} MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
        """, (query, limit, offset))

        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'title': row[1],
                'snippet': row[2]
            })

    return {
        'results': results,
        'total': total,
        'lang': lang
    }
