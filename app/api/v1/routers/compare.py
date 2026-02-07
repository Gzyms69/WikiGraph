from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Dict, Optional, Any
from app.api import deps
from app.services.sqlite_service import SQLiteService
from app.services.language_service import LanguageService
from pydantic import BaseModel

router = APIRouter()

class ConceptMetadata(BaseModel):
    title: Optional[str]
    infobox: List[Dict[str, Any]]

@router.get("/{qid}", response_model=Dict[str, Optional[ConceptMetadata]])
async def compare_entities(
    qid: str = Path(..., description="Wikidata QID", pattern=r"^Q[0-9]+$"),
    langs: str = Query("pl,de", description="Comma-separated language codes"),
    sqlite: SQLiteService = Depends(deps.get_sqlite_service)
):
    """
    Compare metadata for a QID across multiple languages.
    """
    requested_langs = [l.strip() for l in langs.split(",") if l.strip()]
    if not requested_langs:
        raise HTTPException(status_code=400, detail="No languages specified")

    # Validate langs
    active_langs = LanguageService.get_active_languages()
    for lang in requested_langs:
        if lang not in active_langs:
            raise HTTPException(status_code=404, detail=f"Language '{lang}' not supported")

    results = await sqlite.get_compare_metadata(qid, requested_langs)
    return results
