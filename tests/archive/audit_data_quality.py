import sqlite3
import json
import logging
from pathlib import Path
from collections import Counter, defaultdict
import statistics

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def analyze_db(lang: str, sample_size: int = 10000):
    db_path = Path(f"data/db/{lang}.db")
    if not db_path.exists():
        logger.error(f"Database {db_path} not found.")
        return

    logger.info(f"\n=== STARTING AUDIT FOR: {lang.upper()} (Sample: {sample_size}) ===")
    
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cursor = conn.cursor()

    # 1. Fetch Random Sample with Infobox Content
    # We want to analyze what IS there, so we filter for infobox IS NOT NULL first for the schema part,
    # but for coverage we need random.
    # Hybrid approach: Get random sample, classify coverage, then analyze schema of found ones.
    
    query = "SELECT qid, p.infobox FROM id_mapping m JOIN pages p ON m.page_id = p.page_id ORDER BY RANDOM() LIMIT ?"
    cursor.execute(query, (sample_size,))
    rows = cursor.fetchall()
    
    conn.close()

    # Metrics
    total_checked = len(rows)
    found_count = 0
    null_count = 0
    empty_list_count = 0
    
    template_counts = Counter()
    param_counts = []
    
    # Schema Analysis (Template -> Field Frequency)
    template_schema = defaultdict(Counter) # { "Infobox Person": { "birth_date": 50, "name": 100 } }
    
    for qid, ib_json in rows:
        if not ib_json:
            null_count += 1
            continue
            
        try:
            data = json.loads(ib_json)
        except:
            null_count += 1 # Treat parse error as missing for stats
            continue
            
        if not isinstance(data, list):
            null_count += 1
            continue
            
        if len(data) == 0:
            empty_list_count += 1
            continue
            
        found_count += 1
        
        # Analyze first template (usually the main one)
        main_tmpl = data[0]
        t_name = main_tmpl.get("template", "Unknown").strip()
        params = main_tmpl.get("params", {})
        
        template_counts[t_name] += 1
        param_counts.append(len(params))
        
        # Schema tracking
        for k in params.keys():
            template_schema[t_name][k] += 1

    # Report Generation
    coverage_pct = (found_count / total_checked) * 100
    avg_params = statistics.mean(param_counts) if param_counts else 0
    
    report = []
    report.append(f"## Data Coverage: {lang.upper()}")
    report.append(f"- **Total Sampled:** {total_checked}")
    report.append(f"- **Infobox Found:** {found_count} ({coverage_pct:.2f}%)")
    report.append(f"- **NULL/Missing:** {null_count}")
    report.append(f"- **Empty Arrays:** {empty_list_count}")
    report.append(f"- **Richness Score:** Avg {avg_params:.1f} params per infobox")
    
    report.append(f"\n### Top 10 Templates")
    for t, count in template_counts.most_common(10):
        report.append(f"- `{t}`: {count} instances")

    report.append(f"\n### Schema Consistency (Top 5 Templates)")
    for t, _ in template_counts.most_common(5):
        total_instances = template_counts[t]
        report.append(f"\n**Template:** `{t}` (N={total_instances})")
        
        # Get top 5 fields for this template
        fields = template_schema[t]
        for f, f_count in fields.most_common(5):
            f_pct = (f_count / total_instances) * 100
            report.append(f"- `{f}`: {f_pct:.1f}%")

    # Print to console and return text
    print("\n".join(report))
    return "\n".join(report)

if __name__ == "__main__":
    report_de = analyze_db("de", 10000)
    report_pl = analyze_db("pl", 10000)
    
    # Save to file
    with open("docs/API_DATA_QUALITY_REPORT_2026-01-29.md", "w") as f:
        f.write("# API Data Quality Report (2026-01-29)\n\n")
        if report_de: f.write(report_de + "\n\n")
        if report_pl: f.write(report_pl + "\n\n")
        
    print(f"\n✅ Report saved to docs/API_DATA_QUALITY_REPORT_2026-01-29.md")
