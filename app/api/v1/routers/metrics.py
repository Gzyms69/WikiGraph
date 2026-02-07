from fastapi import APIRouter, Depends, HTTPException
from app.api import deps
from app.services.sqlite_service import SQLiteService
import re

router = APIRouter()

QID_REGEX = re.compile(r"^Q[0-9]+$")

@router.get("/{lang}/{qid}")
async def get_node_metrics(
    lang: str,
    qid: str,
    sqlite_service: SQLiteService = Depends(deps.get_sqlite_service)
):
    """
    Fetch all pre-computed graph metrics (PageRank, Communities, etc.) for a concept.
    """
    if not QID_REGEX.match(qid):
        raise HTTPException(status_code=400, detail="Invalid QID format")
    
    metrics = await sqlite_service.get_node_metrics(lang, qid)
    
    if not metrics:
        return {
            "qid": qid,
            "lang": lang,
            "metrics": {},
            "status": "No metrics found or node does not exist"
        }
    
    return {
        "qid": qid,
        "lang": lang,
        "metrics": metrics
    }
