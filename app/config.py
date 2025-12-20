"""
Configuration for WikiGraph Flask Application
"""

from pathlib import Path
from config.language_manager import LanguageManager

class Config:
    """Base configuration."""

    # Project structure
    ROOT_DIR = Path(__file__).parent.parent
    DATABASES_DIR = ROOT_DIR / 'databases'
    
    # Database path
    DATABASE_PATH = DATABASES_DIR / 'wikigraph_multilang.db'

    # API Settings
    AVAILABLE_LANGUAGES = LanguageManager.list_available_languages()
    DEFAULT_LANGUAGE = 'pl'
    MAX_SEARCH_RESULTS = 50
    SEARCH_QUERY_MIN_LENGTH = 2
    SEARCH_QUERY_MAX_LENGTH = 100

    # Flask
    SECRET_KEY = 'wikigraph-dev-key-change-in-production'
    DEBUG = True

    # CORS
    CORS_ORIGINS = ['*']  # Configure appropriately for production
