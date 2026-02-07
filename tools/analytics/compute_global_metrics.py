import argparse
import time
import psutil
import sqlite3
from neo4j import GraphDatabase
import sys
import os

# Configuration
BUFFER_SIZE = 50000

class PerformanceMonitor:
    def __init__(self, total_nodes):
        self.total_nodes = total_nodes
        self.start_time = time.time()
        self.start_memory = psutil.virtual_memory().used
        self.last_update = time.time()
        self.processed = 0

    def log_progress(self, count):
        self.processed = count
        now = time.time()
        if now - self.last_update < 1.0 and count < self.total_nodes:
            return
        
        self.last_update = now
        elapsed = now - self.start_time
        nodes_per_sec = count / elapsed if elapsed > 0 else 0
        memory_used = (psutil.virtual_memory().used) / (1024**3)
        progress = (count / self.total_nodes) * 100
        
        print(f"[{count}/{self.total_nodes}] {progress:.1f}% | {nodes_per_sec:.0f} nodes/sec | RAM: {memory_used:.2f}GB | Time: {elapsed:.0f}s")

class MetricsComputeTool:
    def __init__(self, lang, neo4j_uri, db_path):
        self.lang = lang
        self.driver = GraphDatabase.driver(neo4j_uri, auth=("neo4j", "wikigraph"))
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.projected = False

    def check_memory(self):
        available = psutil.virtual_memory().available / (1024**3)
        print(f"System Available RAM: {available:.2f} GB")
        if available < 1.0:
            print("CRITICAL: Less than 1GB RAM available. Aborting.")
            sys.exit(1)

    def estimate_projection(self, orientation="NATURAL"):
        query = f"""
        CALL gds.graph.project.estimate('Concept', {{ LINKS_TO: {{ orientation: '{orientation}' }} }})
        YIELD requiredMemory, nodeCount, relationshipCount
        """
        with self.driver.session() as session:
            result = session.run(query).single()
            req_mem = result['requiredMemory']
            print(f"GDS Projection Estimate ({orientation}): {req_mem} for {result['nodeCount']} nodes.")
            return req_mem

    def run_algorithm(self, algo_name, gds_proc, key_name, limit=None):
        print(f"\n--- Running {algo_name} ---")
        
        # Determine yield field based on procedure
        yield_field = "score"
        if "louvain" in gds_proc or "leiden" in gds_proc:
            yield_field = "communityId"
        elif "localClusteringCoefficient" in gds_proc:
            yield_field = "localClusteringCoefficient"

        # Stream results
        stream_query = f"CALL {gds_proc}('proj_{self.lang}') YIELD nodeId, {yield_field} AS val"

        # We need to map internal nodeId to QID
        full_query = f"""
        {stream_query}
        WITH gds.util.asNode(nodeId).qid AS qid, val
        RETURN qid, val
        """

        monitor = PerformanceMonitor(self.get_node_count())
        buffer = []
        count = 0

        with self.driver.session() as session:
            result = session.run(full_query)
            for record in result:
                buffer.append((record['qid'], key_name, record['val']))
                count += 1
                
                if len(buffer) >= BUFFER_SIZE:
                    self.flush_buffer(buffer)
                    buffer = []
                    monitor.log_progress(count)
            
            if buffer:
                self.flush_buffer(buffer)
                monitor.log_progress(count)
        
        print(f"Finished {algo_name}. Total processed: {count}")

    def flush_buffer(self, buffer):
        self.cursor.executemany(
            "INSERT OR REPLACE INTO node_metrics (qid, metric_key, metric_value) VALUES (?, ?, ?)",
            buffer
        )
        self.conn.commit()

    def get_node_count(self):
        with self.driver.session() as session:
            return session.run("MATCH (n:Concept) RETURN count(n) as count").single()['count']

    def project_graph(self, orientation="NATURAL"):
        print(f"Projecting graph for {self.lang} (Orientation: {orientation})...")
        query = f"CALL gds.graph.project('proj_{self.lang}', 'Concept', {{ LINKS_TO: {{ orientation: '{orientation}' }} }})"
        with self.driver.session() as session:
            session.run(query)
            self.projected = True

    def drop_projection(self):
        if not self.projected:
            return
        print("Dropping projection...")
        query = f"CALL gds.graph.drop('proj_{self.lang}', false)"
        with self.driver.session() as session:
            session.run(query)
            self.projected = False

    def close(self):
        self.driver.close()
        self.conn.close()

def main():
    parser = argparse.ArgumentParser(description="WikiGraph Global Metrics Compute Tool")
    parser.add_argument("--lang", required=True, help="Language code (pl, de, es)")
    parser.add_argument("--algorithms", default="pagerank", help="Comma-separated algorithms: pagerank,harmonic,louvain,leiden")
    parser.add_argument("--dry-run", action="store_true", help="Estimate memory only")
    parser.add_argument("--limit", type=int, help="Limit records for canary test")
    args = parser.parse_args()

    # Map ports (Logic from infrastructure.yaml)
    ports = {"pl": 7687, "de": 7688, "es": 7757}
    if args.lang not in ports:
        print(f"Unknown language: {args.lang}")
        sys.exit(1)

    uri = f"bolt://localhost:{ports[args.lang]}"
    db_path = f"data/db/{args.lang}.db"

    tool = MetricsComputeTool(args.lang, uri, db_path)
    
    try:
        tool.check_memory()
        
        algos = args.algorithms.split(",")
        algo_map = {
            "pagerank": ("PageRank", "gds.pageRank.stream", "pagerank", "NATURAL"),
            "harmonic": ("Harmonic Centrality", "gds.closeness.harmonic.stream", "harmonic_centrality", "NATURAL"),
            "louvain": ("Louvain Communities", "gds.louvain.stream", "louvain_id", "UNDIRECTED"),
            "leiden": ("Leiden Communities", "gds.leiden.stream", "leiden_id", "UNDIRECTED"),
            "lcc": ("Local Clustering Coefficient", "gds.localClusteringCoefficient.stream", "lcc", "UNDIRECTED")
        }

        # We need to group algorithms by orientation to minimize projections
        by_orientation = {}
        for a in algos:
            if a in algo_map:
                orient = algo_map[a][3]
                if orient not in by_orientation:
                    by_orientation[orient] = []
                by_orientation[orient].append(algo_map[a])

        for orient, algorithms in by_orientation.items():
            tool.estimate_projection(orient)
            if args.dry_run:
                continue
                
            tool.project_graph(orient)
            for algo in algorithms:
                tool.run_algorithm(algo[0], algo[1], algo[2], limit=args.limit)
            tool.drop_projection()

    finally:
        tool.close()

if __name__ == "__main__":
    main()
