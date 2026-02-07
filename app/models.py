from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from config.language_manager import LanguageManager

class LanguageConfig(BaseModel):
    """
    Represents the runtime configuration for a language.
    Wraps LanguageManager output.
    """
    code: str
    name: str
    db_path: str
    neo4j_port: int
    neo4j_bolt: int
    enabled: bool

    @validator('code')
    def validate_code(cls, v):
        active = LanguageManager.list_available_languages()
        if v not in active:
            # We don't raise error here because this might be used to display inactive langs
            pass 
        return v

class EntityRequest(BaseModel):
    """
    Request model for entity lookup.
    """
    qid: str = Field(..., description="Wikidata QID (e.g., Q42)")
    lang: str = Field(..., description="Language code (e.g., 'en', 'de')")

    @validator('lang')
    def validate_lang(cls, v):
        active = LanguageManager.list_available_languages()
        if v not in active:
            raise ValueError(f"Language '{v}' is not active. Available: {active}")
        return v

class Infobox(BaseModel):
    """
    Flexible container for Infobox data.
    """
    template: str
    data: Dict[str, Any]

class ConceptNeighbor(BaseModel):
    qid: str
    title: Optional[str] = None

class Concept(BaseModel):
    """
    The Unified Concept Model.
    Merges Graph Topology (Neo4j) with Rich Metadata (SQLite).
    """
    qid: str
    lang: str
    title: Optional[str] = None
    infobox: Optional[List[Dict[str, Any]]] = None
    neighbors: Optional[List[ConceptNeighbor]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "qid": "Q42",
                "lang": "en",
                "title": "Douglas Adams",
                "infobox": [{"template": "Infobox person", "data": {"born": "1952"}}],
                "neighbors": [{"qid": "Q315", "title": "Language"}]
            }
        }

class HealthResponse(BaseModel):
    status: str
    languages: Dict[str, Dict[str, Any]]
