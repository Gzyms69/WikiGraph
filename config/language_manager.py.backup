"""
Language Manager for Multi-Language Wikipedia Processing

This module provides centralized access to language-specific configurations
for Wikipedia dump processing. It supports caching of configurations and
provides methods to access all language-dependent settings.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, List, Optional, Any


class LanguageManager:
    """
    Singleton manager for language configurations.

    Caches loaded YAML configurations and provides access methods
    for all language-specific settings used in Wikipedia processing.
    """

    _configs: Dict[str, Dict[str, Any]] = {}
    _config_dir = Path(__file__).parent / "languages"

    @classmethod
    def get_config(cls, lang_code: str) -> Dict[str, Any]:
        """
        Load and cache language configuration.
        Auto-generates config via API if missing (JIT).

        Args:
            lang_code: Two-letter language code (e.g., 'pl', 'en')

        Returns:
            Dictionary containing the full language configuration

        Raises:
            ValueError: If configuration file not found
            FileNotFoundError: If config file doesn't exist
        """
        if lang_code not in cls._configs:
            config_path = cls._config_dir / f"{lang_code}.yaml"

            if not config_path.exists():
                # JIT: Try to fetch configuration dynamically
                # This makes the system truly language agnostic - 0 config required.
                try:
                    root_dir = Path(__file__).parent.parent
                    tool_path = root_dir / "core" / "tools" / "fetch_lang_config.py"
                    
                    if not tool_path.exists():
                        # If tool is missing, we can't auto-fetch. Fallback to error.
                        raise FileNotFoundError(f"Configuration file {config_path} not found and fetcher tool missing.")

                    import subprocess
                    import sys
                    
                    # Run the fetcher tool as a subprocess to generate the YAML
                    result = subprocess.run(
                        [sys.executable, str(tool_path), "--lang", lang_code],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                except Exception as e:
                    # If JIT fails (no internet, API error), we must fail.
                    raise RuntimeError(f"Failed to auto-generate config for '{lang_code}'. Check internet or API availability. Error: {e}")

            if not config_path.exists():
                raise FileNotFoundError(f"Configuration file not found even after JIT attempt: {config_path}")

            with open(config_path, 'r', encoding='utf-8') as f:
                cls._configs[lang_code] = yaml.safe_load(f)

        return cls._configs[lang_code]

    @classmethod
    def get_redirect_keywords(cls, lang_code: str) -> List[str]:
        """Get redirect keywords for the specified language."""
        return cls.get_config(lang_code)['wikipedia']['redirect_keywords']

    @classmethod
    def get_namespace_prefixes(cls, lang_code: str) -> Dict[str, List[str]]:
        """Get namespace prefixes for the specified language."""
        return cls.get_config(lang_code)['wikipedia']['namespace_prefixes']

    @classmethod
    def get_all_namespace_prefixes(cls, lang_code: str) -> List[str]:
        """
        Get flattened list of all namespace prefixes for link filtering.

        Returns all namespace prefixes as a single list for easy filtering.
        """
        prefixes_dict = cls.get_namespace_prefixes(lang_code)
        all_prefixes = []
        for prefix_list in prefixes_dict.values():
            all_prefixes.extend(prefix_list)
        return all_prefixes

    @classmethod
    def get_dbname(cls, lang_code: str) -> str:
        """Get database name identifier for the specified language."""
        return cls.get_config(lang_code)['wikipedia']['dbname']

    @classmethod
    def get_text_cleanup_patterns(cls, lang_code: str) -> List[str]:
        """Get file patterns to remove during plain text extraction."""
        return cls.get_config(lang_code)['text_cleanup']['file_patterns']

    @classmethod
    def get_language_info(cls, lang_code: str) -> Dict[str, str]:
        """Get basic language information (code, name, local_name)."""
        config = cls.get_config(lang_code)
        return config['language']

    @classmethod
    def get_processing_config(cls, lang_code: str) -> Dict[str, Any]:
        """Get processing configuration settings."""
        return cls.get_config(lang_code)['processing']

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the configuration cache. Useful for testing."""
        cls._configs.clear()

    @classmethod
    def list_available_languages(cls) -> List[str]:
        """List all available language codes based on config files."""
        if not cls._config_dir.exists():
            return []

        config_files = cls._config_dir.glob("*.yaml")
        return [f.stem for f in config_files if f.is_file()]


# Convenience functions for backward compatibility
def get_redirect_keywords(lang_code: str) -> List[str]:
    """Convenience function for getting redirect keywords."""
    return LanguageManager.get_redirect_keywords(lang_code)


def get_namespace_prefixes(lang_code: str) -> List[str]:
    """Convenience function for getting all namespace prefixes."""
    return LanguageManager.get_all_namespace_prefixes(lang_code)


def get_dbname(lang_code: str) -> str:
    """Convenience function for getting database name."""
    return LanguageManager.get_dbname(lang_code)
