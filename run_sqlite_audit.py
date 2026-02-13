import sqlite3
import json
import logging
import time
from pathlib import Path
from multiprocessing import Pool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def audit_single_table(db_path, table_name):
    """Audits a single table in a single pass."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get columns
    cursor.execute(f'PRAGMA table_info("{table_name}")')
    cols = cursor.fetchall()
    
    # Build a single efficient query
    # We want: Total Rows, Count(col) [non-null], Sum(col == '') [empty]
    select_parts = ["COUNT(*) as _total"]
    for col in cols:
        name = col[1]
        type_ = col[2].upper()
        # count(name) returns number of non-null values
        select_parts.append(f'COUNT("{name}") as "null_{name}"')
        if "TEXT" in type_:
            select_parts.append(f'SUM(CASE WHEN "{name}" = "" THEN 1 ELSE 0 END) as "empty_{name}"')
        else:
            select_parts.append(f'0 as "empty_{name}"')

    query = f'SELECT {", ".join(select_parts)} FROM "{table_name}"'
    
    logger.info(f"  [{table_name}] Starting single-pass scan...")
    start_time = time.time()
    try:
        cursor.execute(query)
        res = cursor.fetchone()
        row_dict = dict(zip([d[0] for d in cursor.description], res))
        elapsed = time.time() - start_time
        logger.info(f"  [{table_name}] Scan complete in {elapsed:.2f}s")
        
        total_rows = row_dict["_total"]
        col_stats = {}
        for col in cols:
            name = col[1]
            non_null = row_dict[f"null_{name}"]
            null_count = total_rows - non_null
            empty_count = row_dict[f"empty_{name}"]
            
            col_stats[name] = {
                "type": col[2],
                "nulls": int(null_count),
                "empty_strings": int(empty_count or 0),
                "completeness_pct": round(((total_rows - null_count - empty_count) / total_rows * 100), 2) if total_rows > 0 else 100.0
            }
            
        metrics_summary = None
        if table_name == "node_metrics":
            logger.info("  [node_metrics] Calculating metrics summary...")
            cursor.execute("SELECT metric_key, COUNT(*), AVG(metric_value), MIN(metric_value), MAX(metric_value) FROM node_metrics GROUP BY metric_key")
            metrics_summary = {}
            for m_key, count, avg, min_v, max_v in cursor.fetchall():
                metrics_summary[m_key] = {
                    "count": count,
                    "avg": avg,
                    "min": min_v,
                    "max": max_v
                }

        return {
            "total_rows": total_rows,
            "columns": col_stats,
            "metrics_summary": metrics_summary,
            "scan_time_sec": elapsed
        }
    except Exception as e:
        logger.error(f"  [{table_name}] Error: {e}")
        return {"error": str(e)}
    finally:
        conn.close()

def audit_database(args):
    db_name, db_path = args
    logger.info(f"Auditing Database: {db_name} ({db_path})")
    if not Path(db_path).exists():
        return db_name, {"error": "File not found"}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall() if not t[0].startswith('articles_fts')]
    conn.close()
    
    db_report = {}
    for table in tables:
        db_report[table] = audit_single_table(db_path, table)
        
    return db_name, db_report

if __name__ == "__main__":
    dbs = [
        ("wikigraph_multilang", "data/db/wikigraph_multilang.db"),
        ("pl", "data/db/pl.db"),
        ("de", "data/db/de.db"),
        ("es", "data/db/es.db")
    ]
    
    start_all = time.time()
    # Use Pool to leverage multiple cores
    with Pool(processes=len(dbs)) as pool:
        results = pool.map(audit_database, dbs)
    
    full_report = dict(results)
    
    with open("sqlite_audit.json", "w") as f:
        json.dump(full_report, f, indent=2)
    
    logger.info(f"Full audit completed in {time.time() - start_all:.2f}s")
