from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Dict
from app.api import deps
from app.services.sqlite_service import SQLiteService
from app.services.language_service import LanguageService
from pydantic import BaseModel

router = APIRouter()

class SearchResult(BaseModel):
    title: str
    qid: str

@router.get("/{lang}", response_model=List[SearchResult])
async def search_entities(
    lang: str = Path(..., description="Language code"),
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(50, ge=1, le=100),
    sqlite: SQLiteService = Depends(deps.get_sqlite_service) # Assuming we add this dependency
):
    """
    Search for articles using Full-Text Search (FTS5).
    """
    if lang not in LanguageService.get_active_languages():
        raise HTTPException(status_code=404, detail=f"Language '{lang}' not supported")

    results = await sqlite.search_articles(lang, q, limit)
    return results
