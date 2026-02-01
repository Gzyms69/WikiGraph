import sqlite3
import json
import logging
import re
from pathlib import Path
from collections import Counter, defaultdict
import statistics

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Heuristic lists for critical fields
GEO_KEYS = [
    'breitengrad', 'längengrad', 'lat', 'long', 'latitude', 'longitude', 
    'szerokość', 'długość', 'współrzędne', 'koordinaten'
]
IMAGE_KEYS = ['bild', 'image', 'zdjęcie', 'grafika', 'foto', 'file']
NAME_KEYS = ['name', 'nazwa', 'titel', 'imię i nazwisko']

def is_populated(value):
    """Check if a value is meaningfully populated."""
    if value is None: return False
    s = str(value).strip()
    if not s: return False
    if s.lower() in ['?', '-', '–', '—', 'unknown', 'n/a', 'keine', 'brak', 'nie']: return False
    return True

def analyze_population(lang: str, sample_size: int = 10000):
    db_path = Path(f"data/db/{lang}.db")
    if not db_path.exists():
        logger.error(f"DB not found: {db_path}")
        return

    logger.info(f"\n=== DEEP AUDIT: {lang.upper()} (Sample: {sample_size}) ===")
    
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cursor = conn.cursor()
    
    # Get random sample of items WITH infoboxes
    query = """
        SELECT infobox 
        FROM pages 
        WHERE infobox IS NOT NULL 
        ORDER BY RANDOM() 
        LIMIT ?
    """
    cursor.execute(query, (sample_size,))
    rows = cursor.fetchall()
    conn.close()

    # Stats containers
    template_counts = Counter()
    # Store field stats per template: { "TemplateName": { "field": {"present": 0, "populated": 0} } }
    schema_stats = defaultdict(lambda: defaultdict(lambda: {"present": 0, "populated": 0}))
    
    # Special Category Stats
    geo_stats = {"total_places": 0, "with_coords": 0}
    
    for (ib_json,) in rows:
        try:
            data = json.loads(ib_json)
        except: continue
        
        if not isinstance(data, list) or not data: continue
        
        # Analyze main template
        main_tmpl = data[0]
        t_name = main_tmpl.get("template", "Unknown").strip()
        params = main_tmpl.get("params", {})
        
        template_counts[t_name] += 1
        
        # Field Analysis
        has_geo = False
        
        for key, val in params.items():
            k_lower = key.lower()
            
            # Update Schema Stats
            stats = schema_stats[t_name][key]
            stats["present"] += 1
            if is_populated(val):
                stats["populated"] += 1
                
                # Check Special Types
                if any(g in k_lower for g in GEO_KEYS):
                    has_geo = True
                    
        # Heuristic: Is this a "Place"?
        # If template name contains "Stadt", "Ort", "Miejscowość", "Gemeinde"
        t_lower = t_name.lower()
        if any(x in t_lower for x in ['stadt', 'ort', 'gemeinde', 'miejscowość', 'miasto', 'wieś']):
            geo_stats["total_places"] += 1
            if has_geo:
                geo_stats["with_coords"] += 1

    # Reporting
    report = []
    
    # 1. Geo Coverage
    if geo_stats["total_places"] > 0:
        geo_pct = (geo_stats["with_coords"] / geo_stats["total_places"]) * 100
        report.append(f"## 🌍 Geographic Readiness")
        report.append(f"- **Total 'Place' Templates:** {geo_stats['total_places']}")
        report.append(f"- **With Coordinates:** {geo_stats['with_coords']} ({geo_pct:.1f}%)")
        if geo_pct < 50:
            report.append("  ⚠️ CRITICAL: Low coordinate availability. Check field mapping!")
    
    # 2. Template Deep Dive (Top 20)
    report.append(f"\n## 📊 Template Deep Dive (Top 20)")
    
    for t_name, count in template_counts.most_common(20):
        report.append(f"\n### `{t_name}` (N={count})")
        
        # Get all fields for this template
        fields = schema_stats[t_name]
        
        # Sort fields by presence frequency
        sorted_fields = sorted(fields.items(), key=lambda x: x[1]['present'], reverse=True)
        
        # Show top 15 fields
        report.append(f"| Field | Presence % | Population % |")
        report.append(f"|---|---|---|")
        
        for field, stats in sorted_fields[:15]:
            present_pct = (stats['present'] / count) * 100
            pop_pct = (stats['populated'] / count) * 100
            gap = present_pct - pop_pct
            
            # Highlight anomalies
            gap_str = f"{gap:.1f}%"
            if gap > 20: gap_str = f"**{gap:.1f}%** ⚠️" # High 'Empty String' rate
            
            report.append(f"| {field} | {present_pct:.1f}% | {pop_pct:.1f}% | {gap_str} |")
            
    print("\n".join(report))
    return "\n".join(report)

if __name__ == "__main__":
    report_de = analyze_population("de", 10000)
    report_pl = analyze_population("pl", 10000)
    
    with open("docs/PHASE_A_DEEP_AUDIT_REPORT.md", "w") as f:
        f.write("# Phase A: Deep Data Audit Report\n\n")
        f.write(report_de + "\n\n")
        f.write(report_pl + "\n\n")
        
    print("\n✅ Report saved to docs/PHASE_A_DEEP_AUDIT_REPORT.md")
