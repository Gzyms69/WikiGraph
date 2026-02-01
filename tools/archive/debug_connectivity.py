import sqlite3
import sys
from pathlib import Path
from mwsql import Dump
from tqdm import tqdm

def get_db_path(lang):
    return Path(f"data/db/{lang}.db")

def fix_encoding(text):
    if isinstance(text, str):
        try:
            return text.encode('latin1').decode('utf-8')
        except:
            return text
    return text

def load_mappings(db_path):
    print("🧠 Loading metadata into memory...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    id_map = {} # id -> (qid, ns)
    title_map = {} # (ns, title) -> qid
    
    cursor.execute("""
        SELECT p.page_id, p.namespace, p.title, m.qid 
        FROM pages p 
        JOIN id_mapping m ON p.page_id = m.page_id
    """)
    
    for pid, ns, title, qid in tqdm(cursor, desc="Loading Maps"):
        id_map[pid] = (qid, ns)
        clean_title = title.replace(" ", "_")
        title_map[(ns, clean_title)] = qid
        
    conn.close()
    print(f"   Mapped {len(id_map)} entities.")
    return id_map, title_map

def debug_connectivity(lang="pl", limit=1000):
    db_path = get_db_path(lang)
    id_map, title_map = load_mappings(db_path)
    
    # Load Redirects
    print("Loading Redirect Map...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT namespace, title FROM pages WHERE is_redirect=1")
    redirect_set = set()
    for ns, title in cursor:
        redirect_set.add((ns, title.replace(" ", "_")))
    conn.close()
    print(f"   Loaded {len(redirect_set)} redirects.")
    
    # Open Dump
    pl_dump = Path(f"data/raw/{lang}wiki-latest-pagelinks.sql.gz")
    print(f"🔍 Scanning sample (1/10000) from {pl_dump.name}...")
    
    dump = Dump.from_file(str(pl_dump), encoding='latin1')
    
    stats = {
        "total_scanned": 0,
        "sampled": 0,
        "ok": 0,
        "src_missing_qid": 0,
        "tgt_missing_qid": 0,
        "tgt_is_redirect": 0,
        "tgt_is_redlink": 0
    }
    
    detailed_log = []
    
    for row in dump.rows():
        stats["total_scanned"] += 1
        # Sample 1/10000
        if stats["total_scanned"] % 10000 != 0:
            continue
            
        try:
            if len(row) < 3: continue
            stats["sampled"] += 1
            
            src_id = int(row[0])
            tgt_ns = int(row[1])
            tgt_title = fix_encoding(row[2])
            
            # Check Source
            if src_id not in id_map:
                stats["src_missing_qid"] += 1
                # detailed_log.append(f"FAIL: SourceID {src_id} missing QID")
                continue
                
            # Check Target
            tgt_key = (tgt_ns, tgt_title)
            if tgt_key in title_map:
                stats["ok"] += 1
            else:
                stats["tgt_missing_qid"] += 1
                if tgt_key in redirect_set:
                    stats["tgt_is_redirect"] += 1
                    detailed_log.append(f"FAIL: Target '{tgt_title}' (NS={tgt_ns}) is REDIRECT")
                else:
                    stats["tgt_is_redlink"] += 1
                    detailed_log.append(f"FAIL: Target '{tgt_title}' (NS={tgt_ns}) is REDLINK/UNKNOWN")
                    
        except Exception as e:
            print(f"Error parsing row: {e}")
            continue

    print("\n=== DIAGNOSTIC REPORT ===")
    print(f"Total Scanned: {stats['total_scanned']}")
    print(f"Total Sampled: {stats['sampled']}")
    if stats['sampled'] > 0:
        print(f"✅ OK (Valid Edges): {stats['ok']} ({stats['ok']/stats['sampled']*100:.1f}%)")
        print(f"❌ Source Missing QID: {stats['src_missing_qid']} ({stats['src_missing_qid']/stats['sampled']*100:.1f}%)")
        print(f"❌ Target Missing QID: {stats['tgt_missing_qid']} ({stats['tgt_missing_qid']/stats['sampled']*100:.1f}%)")
        print(f"   ↳ Of which Redirects: {stats['tgt_is_redirect']}")
        print(f"   ↳ Of which Redlinks:  {stats['tgt_is_redlink']}")
    
    print("\n--- Sample Failures (First 20) ---")
    for log in detailed_log[:20]:
        print(log)

if __name__ == "__main__":
    debug_connectivity()
