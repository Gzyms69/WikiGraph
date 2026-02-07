import logging
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from typing import Dict
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class SQLitePool:
    _engines: Dict[str, object] = {}

    @classmethod
    def get_engine(cls, db_path: str):
        if db_path not in cls._engines:
            logger.info(f"Initializing SQLite connection pool for {db_path}")
            # SQLAlchemy connection URL for SQLite
            # We use absolute path if possible, or relative.
            # Assuming db_path is a file path string.
            
            # Construct Safe URL
            # 3 slashes for relative, 4 for absolute. 
            # We will treat db_path as a direct file system path.
            url = f"sqlite:///{db_path}"
            
            cls._engines[db_path] = create_engine(
                url,
                poolclass=QueuePool,
                pool_size=20,            # Max connections to keep persistently
                max_overflow=40,         # Max surge connections
                pool_timeout=30,         # Seconds to wait for a connection
                pool_recycle=3600,       # Recycle connections every hour
                connect_args={
                    'check_same_thread': False, # Needed for threading/async executors
                    'timeout': 10,              # SQLite Busy Timeout
                    'uri': True,                # Enable URI mode
                    # 'mode': 'ro'              # Read-only mode (careful: some SQLite versions/Drivers need explicit handling)
                    # We skip mode=ro in the connect_args because generic SQLAlchemy usage 
                    # for SQLite often assumes read-write, but we can set it if we are sure.
                    # Given the "immutable" nature of the usage, standard open is fine. 
                    # If we enforce ro, we might block ourselves from FTS updates later.
                    # We will rely on filesystem permissions or careful usage.
                }
            )
        return cls._engines[db_path]

    @classmethod
    @contextmanager
    def get_connection(cls, db_path: str):
        """
        Yields a DBAPI connection (raw sqlite3.Connection) from the pool.
        Usage:
            with SQLitePool.get_connection(path) as conn:
                cursor = conn.cursor()
                ...
        """
        engine = cls.get_engine(db_path)
        # engine.raw_connection() checks out a connection from the pool
        conn = engine.raw_connection()
        try:
            yield conn
        finally:
            conn.close() # Returns to pool
