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
    def _safe_get(cls, config: Dict[str, Any], path: str, default: Any = None) -> Any:
        """
        Safely retrieve a value from a nested dictionary using dot notation.
        
        Args:
            config: The configuration dictionary.
            path: Dot-separated path to the value (e.g., 'wikipedia.namespace_prefixes').
            default: Value to return if the key is missing.
        
        Returns:
            The value at the path or the default.
        """
        keys = path.split('.')
        current = config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    @classmethod
    def get_config(cls, lang_code: str) -> Dict[str, Any]:
        """
        Load and cache language configuration.
        Auto-generates config via API if missing (JIT) ONLY if explicitly enabled.

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
                # Check environment variable to enable JIT
                jit_enabled = os.environ.get("WIKIGRAPH_JIT_ENABLED", "false").lower() == "true"
                
                if jit_enabled:
                    # JIT: Try to fetch configuration dynamically
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
                else:
                    # JIT Disabled: Fail fast
                     pass # Will raise FileNotFoundError below

            if not config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_path}. (JIT Auto-generation is DISABLED. Set WIKIGRAPH_JIT_ENABLED=true to enable.)")

            with open(config_path, 'r', encoding='utf-8') as f:
                cls._configs[lang_code] = yaml.safe_load(f)

        return cls._configs[lang_code]

    @classmethod
    def get_redirect_keywords(cls, lang_code: str) -> List[str]:
        """Get redirect keywords for the specified language."""
        return cls._safe_get(cls.get_config(lang_code), 'wikipedia.redirect_keywords', [])

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
        config = cls.get_config(lang_code)
        # Primary path: text_cleanup.file_patterns
        patterns = cls._safe_get(config, 'text_cleanup.file_patterns')
        
        if patterns is None:
            # Fallback 1: Try to get from namespace prefixes if available
            # This is a 'smart default' mentioned in the plan
            ns_prefixes = cls._safe_get(config, 'wikipedia.namespace_prefixes.file')
            if ns_prefixes:
                return ns_prefixes
            # Fallback 2: Return empty list to prevent crash
            return []
            
        return patterns

    @classmethod
    def get_language_info(cls, lang_code: str) -> Dict[str, str]:
        """Get basic language information (code, name, local_name)."""
        config = cls.get_config(lang_code)
        return config['language']

    @classmethod
    def get_processing_config(cls, lang_code: str) -> Dict[str, Any]:
        """Get processing configuration settings."""
        config = cls.get_config(lang_code)
        processing_config = cls._safe_get(config, 'processing')
        
        if processing_config is None:
            import logging
            # Only log if we haven't logged this before for this language to avoid spam
            # For now, just a simple warning
            # logging.warning(f"Language '{lang_code}' missing processing configuration. Defaulting to disabled.")
            return {'enabled': False}
            
        return processing_config

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
