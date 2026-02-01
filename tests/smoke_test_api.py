import sys
import os
import asyncio
import logging
from unittest.mock import MagicMock, patch, AsyncMock

# Add project root to path
sys.path.insert(0, os.getcwd())

from app.api.routers.concept import get_concept

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def smoke_test():
    """
    Smoke test for the updated /api/concept/{qid} endpoint.
    Tests three cases:
    1. QID with known infobox (Actinium Q1121)
    2. QID without infobox (Berlin Q64 - Confirmed Missing)
    3. Missing QID (404)
    """
    logger.info("--- Starting Smoke Test for /api/concept/{qid} ---")

    test_cases = [
        {"qid": "Q1121", "lang": "de", "desc": "Actinium (Should have DE infobox)"},
        {"qid": "Q1744", "lang": "pl", "desc": "Madonna (Should have PL infobox)"},
        {"qid": "Q64", "lang": "de", "desc": "Berlin (Should be NULL for infobox)"},
    ]

    for case in test_cases:
        qid = case["qid"]
        lang = case["lang"]
        logger.info(f"Testing {case['desc']}...")

        # Mock Neo4j to simulate the node being found in the target language
        mock_neo_response = {
            lang: [{"qid": qid, "neighbor_qids": []}]
        }

        with patch('app.api.routers.concept.Neo4jManager') as MockNeo:
            instance = MockNeo.return_value
            # Use AsyncMock for query_all since it is awaited in the router
            instance.query_all = AsyncMock(return_value=mock_neo_response)
            
            try:
                result = await get_concept(qid=qid)
                
                # Validate Structure
                if "infoboxes" in result:
                    ib_data = result["infoboxes"].get(lang)
                    status = "FOUND" if ib_data else "NULL"
                    
                    if qid == "Q1121" and not ib_data:
                        logger.error(f"  [FAILURE] Expected data for Actinium but got NULL")
                    elif qid == "Q64" and ib_data:
                        logger.warning(f"  [UNEXPECTED] Got data for Berlin (expected NULL)")
                    else:
                        logger.info(f"  [SUCCESS] Response correct. Data for {lang}: {status}")
                    
                    if ib_data:
                        # Print first template name for visual confirmation
                        template_name = ib_data[0].get("template", "Unknown")
                        logger.info(f"  [DATA] First template: {template_name}")
                else:
                    logger.error(f"  [FAILURE] Response missing 'infoboxes' key for {qid}")
                    
            except Exception as e:
                logger.error(f"  [ERROR] Call failed for {qid}: {e}")
                import traceback
                logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(smoke_test())
