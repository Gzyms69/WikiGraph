import sqlite3
import logging
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Representative QIDs for diverse categories
# We use major entities that SHOULD have infoboxes
GOLDEN_ENTITIES = {
    "Cities": {
        "Q64": "Berlin",
        "Q1055": "Hamburg",
        "Q1726": "München",
        "Q270": "Warszawa", # PL capital
        "Q31487": "Kraków"
    },
    "Countries": {
        "Q183": "Deutschland",
        "Q36": "Polen",
        "Q30": "USA"
    },
    "People (Politicians)": {
        "Q1601": "Angela Merkel", # DE Chancellor
        "Q2764": "Donald Tusk"    # PL PM
    },
    "People (Scientists)": {
        "Q937": "Albert Einstein",
        "Q76": "Barack Obama" # Testing Personendaten vs Infobox
    },
    "Chemicals": {
        "Q1121": "Actinium", # Confirmed working
        "Q627": "Stickstoff"
    },
    "Movies": {
        "Q44578": "Titanic"
    },
    "Companies": {
        "Q312": "Apple"
    }
}

def check_db(lang: str, entities: Dict[str, Dict[str, str]]):
    db_path = f"data/db/{lang}.db"
    logger.info(f"\n=== AUDIT RESULTS: {lang.upper()} ===")
    
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        
        headers = f"{'Category':<20} | {'QID':<6} | {'Entity':<15} | {'Infobox Status':<15} | Template (Sample)"
        logger.info(headers)
        logger.info("-" * len(headers))
        
        for category, items in entities.items():
            for qid, name in items.items():
                # 1. Check if linked in ID Mapping
                cursor.execute("SELECT page_id FROM id_mapping WHERE qid = ?", (qid,))
                mapping = cursor.fetchone()
                
                status = "MISSING ID"
                template_sample = ""
                
                if mapping:
                    page_id = mapping[0]
                    # 2. Check Infobox in Pages
                    cursor.execute("SELECT infobox FROM pages WHERE page_id = ?", (page_id,))
                    row = cursor.fetchone()
                    
                    if row:
                        ib_data = row[0]
                        if ib_data:
                            status = "✅ FOUND"
                            # Try to extract template name
                            try:
                                # Simple string search to avoid heavy json parse for log
                                start = ib_data.find('"template": "') + 13
                                end = ib_data.find('"', start)
                                template_sample = ib_data[start:end][:30] # Truncate
                            except:
                                template_sample = "Parse Error"
                        else:
                            status = "❌ NULL"
                    else:
                        status = "❌ NO PAGE ROW"
                
                logger.info(f"{category:<20} | {qid:<6} | {name:<15} | {status:<15} | {template_sample}")
                
        conn.close()
    except Exception as e:
        logger.info(f"DB Error for {lang}: {e}")

if __name__ == "__main__":
    check_db("de", GOLDEN_ENTITIES)
    check_db("pl", GOLDEN_ENTITIES)
