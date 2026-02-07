import asyncio
import logging
import sys
import os
import json
from tabulate import tabulate

# Add project root to path
sys.path.append(os.getcwd())

from app.core.config import settings
from app.services.neo4j_manager import Neo4jManager
from app.services.metadata_manager import MetadataManager

# Configure logging
logging.basicConfig(level=logging.ERROR) # Minimal logging for clean output
logger = logging.getLogger("RosettaStone")

# ROSETTA STONE: Universal QIDs across diverse categories
ROSETTA_STONE = [
    {"qid": "Q2", "label": "Earth"},
    {"qid": "Q46", "label": "Europe"},
    {"qid": "Q64", "label": "Berlin"},
    {"qid": "Q413", "label": "Physics"},
    {"qid": "Q395", "label": "Mathematics"},
    {"qid": "Q937", "label": "Albert Einstein"},
    {"qid": "Q7186", "label": "Marie Curie"},
    {"qid": "Q362", "label": "World War II"},
    {"qid": "Q2736", "label": "Football"},
    {"qid": "Q75", "label": "Internet"},
    {"qid": "Q36", "label": "Poland"},
    {"qid": "Q183", "label": "Germany"},
    {"qid": "Q29", "label": "Spain"},
]

async def analyze_concept(neo4j: Neo4jManager, meta: MetadataManager, lang: str, qid: str):
    """
    Analyzes a single concept in a specific language.
    """
    # 1. Topology (Neo4j)
    # Using degree() function for efficiency
    query = "MATCH (n:Concept {qid: $qid}) RETURN count{(n)--()} as degree"
    topo_res = await neo4j.query(lang, query, {"qid": qid})
    degree = topo_res[0]['degree'] if topo_res else 0

    # 2. Metadata (SQLite)
    title = meta.get_title(lang, qid)
    infobox = meta.get_infobox(lang, qid)
    
    ib_count = 0
    ib_complexity = 0
    if infobox and isinstance(infobox, list):
        ib_count = len(infobox)
        # Sum of keys across all templates in the infobox array
        ib_complexity = sum(len(tpl) for tpl in infobox if isinstance(tpl, dict))

    return {
        "title": title or "MISSING",
        "degree": degree,
        "ib_count": ib_count,
        "ib_complexity": ib_complexity
    }

async def main():
    neo4j = Neo4jManager()
    meta = MetadataManager()
    
    # Check health first
    status = neo4j.check_health()
    active_langs = [l for l, s in status.items() if s.get('connected')]
    
    print(f"--- ROSETTA STONE: INTERLANGUAGE ANALYSIS ---")
    print(f"Active Languages: {active_langs}\n")

    table_data = []
    
    for entry in ROSETTA_STONE:
        qid = entry['qid']
        label = entry['label']
        
        row = [f"{label} ({qid})"]
        
        for lang in ['pl', 'de', 'es']: # Focus on the three main validated languages
            if lang not in active_langs:
                row.append("N/A")
                continue
                
            data = await analyze_concept(neo4j, meta, lang, qid)
            
            # Format: Title | Deg | Cpx
            display = f"{data['title']}\nDeg: {data['degree']}\nCpx: {data['ib_complexity']}"
            row.append(display)
            
        table_data.append(row)

    headers = ["Concept (QID)", "Polish (PL)", "German (DE)", "Spanish (ES)"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Analysis Metrics
    print("\n--- ARCHITECTURAL INSIGHTS ---")
    
    # Calculate averages
    stats = {l: {"degree": [], "cpx": []} for l in ['pl', 'de', 'es']}
    for entry in ROSETTA_STONE:
        for lang in ['pl', 'de', 'es']:
            if lang in active_langs:
                d = await analyze_concept(neo4j, meta, lang, entry['qid'])
                if d['title'] != "MISSING":
                    stats[lang]["degree"].append(d['degree'])
                    stats[lang]["cpx"].append(d['ib_complexity'])

    for lang, s in stats.items():
        if s["degree"]:
            avg_deg = sum(s["degree"]) / len(s["degree"])
            avg_cpx = sum(s["cpx"]) / len(s["cpx"])
            print(f"[{lang.upper()}] Avg Degree: {avg_deg:.1f} | Avg Metadata Complexity: {avg_cpx:.1f}")

    neo4j.close()

if __name__ == "__main__":
    asyncio.run(main())
