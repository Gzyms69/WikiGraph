from neo4j import GraphDatabase
import os
import logging
import time
from neo4j.exceptions import ServiceUnavailable, TransientError

logger = logging.getLogger("uvicorn.error")

class Neo4jClient:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "wikigraph")
        self.driver = None
        self.max_retries = 5

    def connect(self):
        if not self.driver:
            logger.info(f"Connecting to Neo4j at {self.uri}...")
            try:
                self.driver = GraphDatabase.driver(
                    self.uri, 
                    auth=(self.user, self.password),
                    max_connection_lifetime=30 * 60,  # 30 minutes
                    max_connection_pool_size=20,      # Conservative pool size
                    connection_acquisition_timeout=30.0,
                    connection_timeout=10.0,
                    keep_alive=True
                )
                
                # Robust connectivity verification with retry
                connected = False
                for attempt in range(self.max_retries):
                    try:
                        self.driver.verify_connectivity()
                        connected = True
                        break
                    except (ServiceUnavailable, TransientError) as e:
                        if attempt == self.max_retries - 1:
                            raise
                        wait_time = 2 ** attempt
                        logger.warning(f"Neo4j not ready (attempt {attempt+1}/{self.max_retries}). Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                
                if connected:
                    logger.info("Neo4j driver connected successfully.")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j after retries: {e}")
                self.driver = None
                raise

    def close(self):
        if self.driver:
            self.driver.close()

    def get_session(self, **kwargs):
        if not self.driver:
            self.connect()
        return self.driver.session(**kwargs)

db = Neo4jClient()