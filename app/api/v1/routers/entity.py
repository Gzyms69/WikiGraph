from fastapi import APIRouter, Depends, HTTPException, Path
from typing import Any
from app.api import deps
from app.services.bridge_service import BridgeService
from app.models import Concept, EntityRequest, LanguageConfig
from app.services.language_service import LanguageService

router = APIRouter()

@router.get("/{lang}/{qid}", response_model=Concept)
async def get_entity(
    lang: str = Path(..., description="Language code"),
    qid: str = Path(..., description="Wikidata QID", pattern=r"^Q[0-9]+$"),
    bridge: BridgeService = Depends(deps.get_bridge_service)
) -> Any:
    """
    Get full entity details (Graph + Metadata).
    """
    # Validate Lang (Explicit check, though Pydantic model would catch it if used in body)
    if lang not in LanguageService.get_active_languages():
        raise HTTPException(status_code=404, detail=f"Language '{lang}' not supported")

    concept = await bridge.get_concept(lang, qid)
    if not concept:
        raise HTTPException(status_code=404, detail="Entity not found")
        
    return concept
