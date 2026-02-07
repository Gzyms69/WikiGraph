import asyncio
import sys
import os
from pprint import pprint

# Ensure project root is in path
sys.path.append(os.getcwd())

from app.services.bridge_service import BridgeService
from config.language_manager import LanguageManager

async def test_bridge():
    print("=== Testing BridgeService ===")
    service = BridgeService()
    
    test_cases = [
        ('pl', 'Q36'),   # Poland
        ('de', 'Q64'),   # Berlin
        ('es', 'Q29')    # Spain
    ]

    for lang, qid in test_cases:
        print(f"\n--- Testing {lang} / {qid} ---")
        try:
            # Check if language is active first to avoid "Language disabled" confusion
            config = LanguageManager.get_processing_config(lang)
            # Actually, LanguageService.get_config doesn't strict check 'enabled' for the service itself, 
            # but Neo4jManager might not have initialized the driver if 'enabled' was false in settings.
            # Let's see what happens.
            
            concept = await service.get_concept(lang, qid)
            
            if concept:
                print(f"✅ FOUND: {concept.title} ({concept.qid})")
                print(f"   Infobox: {bool(concept.infobox)} (Raw count: {len(concept.infobox) if concept.infobox else 0})")
                print(f"   Neighbors: {len(concept.neighbors) if concept.neighbors else 0}")
                if concept.neighbors:
                    print(f"   Sample Neighbor: {concept.neighbors[0].title} ({concept.neighbors[0].qid})")
            else:
                print(f"❌ NOT FOUND")
                
        except Exception as e:
            print(f"💥 ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bridge())
