from typing import List, Dict, Any
from config.language_manager import LanguageManager
from app.models import LanguageConfig

class LanguageService:
    """
    Service to provide language configuration and validation.
    Wraps config.language_manager.
    """
    
    @staticmethod
    def get_active_languages() -> List[str]:
        return LanguageManager.list_available_languages()
        
    @staticmethod
    def get_config(lang: str) -> LanguageConfig:
        """
        Returns validated LanguageConfig model.
        """
        raw_config = LanguageManager.get_config(lang)
        
        # Transform raw config object (which is a Namespace or dict) to Pydantic
        # LanguageManager.get_config returns a SimpleNamespace or object with attributes
        
        # We need to map the LanguageManager's output structure to our Pydantic model
        # Based on validate_all_accessors output:
        # get_infrastructure_config -> {'ports': {'bolt': 7687}}
        # get_paths -> {'db': PosixPath(...)}
        
        infra = LanguageManager.get_infrastructure_config(lang)
        info = LanguageManager.get_language_info(lang)
        paths = LanguageManager.get_paths(lang)
        processing = LanguageManager.get_processing_config(lang)
        
        return LanguageConfig(
            code=lang,
            name=info.get('name', 'Wikipedia'),
            db_path=str(paths['db']),
            neo4j_port=infra['ports']['http'], # Mapping http port
            neo4j_bolt=infra['ports']['bolt'],
            enabled=processing.get('enabled', False)
        )
