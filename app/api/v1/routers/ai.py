from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from app.api import deps
from app.services.bridge_service import BridgeService
from app.services.ai_service import AIService
from app.services.language_service import LanguageService
from app.core.config import settings

router = APIRouter()

class InsightResponse(BaseModel):
    qid: str
    lang: str
    insight: str
    provider: str
    model: str

@router.post("/analyze/{lang}/{qid}", response_model=InsightResponse)
async def analyze_node(
    lang: str = Path(..., description="Language code"),
    qid: str = Path(..., description="Wikidata QID"),
    bridge: BridgeService = Depends(deps.get_bridge_service)
):
    """
    Generate an AI-powered insight for a graph node.
    """
    # 1. Validate Language
    if lang not in LanguageService.get_active_languages():
        raise HTTPException(status_code=404, detail=f"Language '{lang}' not supported")

    # 2. Fetch Concept Data (Graph + Metadata)
    # We use get_concept to ensure we have neighbors and titles for context
    concept = await bridge.get_concept(lang, qid)
    if not concept:
        raise HTTPException(status_code=404, detail="Entity not found")

    # 3. Generate Insight
    insight = await AIService.analyze_node(concept)
    
    # 4. Get Dynamic Metadata
    provider = settings.get("ai", {}).get("provider", "mock")
    model_name = await AIService.get_model_name()

    return InsightResponse(
        qid=qid,
        lang=lang,
        insight=insight,
        provider=provider,
        model=model_name
    )
