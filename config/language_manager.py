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
        config = cls.get_config(lang_code)
        return cls._safe_get(config, 'wikipedia.redirect_keywords', [])

    @classmethod
    def get_namespace_prefixes(cls, lang_code: str) -> Dict[str, List[str]]:
        """Get namespace prefixes for the specified language."""
        config = cls.get_config(lang_code)
        return cls._safe_get(config, 'wikipedia.namespace_prefixes', {})

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
        """Get database name identifier for the specified language.
        
        REQUIRED for locating XML dump files in data/raw/. 
        Raises ValueError with clear message if missing or invalid.
        """
        config = cls.get_config(lang_code)
        
        # Check if wikipedia section exists
        if 'wikipedia' not in config:
            raise ValueError(
                f"Language config '{lang_code}' missing entire 'wikipedia' section. "
                f"Required for dump file location. Config keys: {list(config.keys())}"
            )
        
        dbname = cls._safe_get(config, 'wikipedia.dbname')
        
        if dbname is None:
            raise ValueError(
                f"Language config '{lang_code}' missing required 'wikipedia.dbname'. "
                f"This value is required to locate XML dump files in data/raw/. "
                f"Current wikipedia keys: {list(config.get('wikipedia', {}).keys())}. "
                f"Example: 'enwiki' for English Wikipedia."
            )
        
        if not isinstance(dbname, str):
            raise ValueError(
                f"Invalid dbname type for '{lang_code}': {type(dbname)}. Must be string."
            )
        
        dbname = dbname.strip()
        if dbname == '':
            raise ValueError(
                f"Empty dbname for '{lang_code}'. Must be non-empty string."
            )
        
        # Less restrictive: allow alphanumeric, underscores, hyphens
        # This matches actual Wikipedia dump naming conventions
        cleaned = dbname.replace('_', '').replace('-', '')
        if not cleaned.isalnum():
            raise ValueError(
                f"Invalid dbname format for '{lang_code}': '{dbname}'. "
                f"Must be alphanumeric with underscores/hyphens (e.g., 'enwiki', 'wikidatawiki')."
            )
        
        return dbname

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
        """
        Get basic language information (code, name, local_name).
        Returns safe defaults if configuration is missing.
        """
        config = cls.get_config(lang_code)
        info = cls._safe_get(config, 'language')
        
        if info is None:
            # Return safe defaults if 'language' section is missing
            return {
                'code': lang_code,
                'name': lang_code,       # Fallback to code
                'local_name': lang_code, # Fallback to code
                'iso_code': f"{lang_code}-{lang_code.upper()}" # Best guess
            }
        return info

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
    def get_infobox_config(cls, lang_code: str) -> Dict[str, Any]:
        """
        Get infobox extraction configuration.
        Returns safe defaults (empty lists/dict) if missing.
        """
        config = cls.get_config(lang_code)
        infobox_config = cls._safe_get(config, 'infobox', {})
        
        return {
            'template_prefixes': infobox_config.get('template_prefixes', []),
            'template_suffixes': infobox_config.get('template_suffixes', []),
            'parameter_map': infobox_config.get('parameter_map', {})
        }

    @classmethod
    def get_text_processing_config(cls, lang_code: str) -> Dict[str, Any]:
        """
        Get text processing configuration (e.g., has_spaces).
        Returns safe defaults.
        """
        config = cls.get_config(lang_code)
        text_config = cls._safe_get(config, 'text_processing', {})
        
        return {
            'has_spaces': text_config.get('has_spaces', True),
            'encoding': text_config.get('encoding', 'utf-8')
        }

    @classmethod
    def get_infrastructure_config(cls, lang_code: str) -> Dict[str, Any]:
        """
        Get infrastructure configuration (ports).
        Returns empty dict if missing.
        """
        config = cls.get_config(lang_code)
        infra_config = cls._safe_get(config, 'infrastructure', {})
        
        return {
            'ports': infra_config.get('ports', {})
        }

    @classmethod
    def get_importable_namespaces(cls, lang_code: str) -> List[int]:
        """
        Get the list of namespaces to import into the system.
        Defaults to [0, 14] (Articles and Categories).
        """
        config = cls.get_config(lang_code)
        return cls._safe_get(config, 'processing.import_namespaces', [0, 14])

    @classmethod
    def get_dump_filename(cls, lang_code: str, dump_type: str, date: str = "latest") -> str:
        """
        Construct a standard Wikipedia dump filename.
        Example: dewiki-latest-pages-articles-multistream.xml.bz2
        """
        dbname = cls.get_dbname(lang_code)
        
        # Mapping dump types to their extensions
        extensions = {
            "pages-articles-multistream": ".xml.bz2",
            "pages-articles-multistream-index": ".txt.bz2",
            "page": ".sql.gz",
            "pagelinks": ".sql.gz",
            "redirect": ".sql.gz",
            "langlinks": ".sql.gz",
            "page_props": ".sql.gz",
            "categorylinks": ".sql.gz",
            "linktarget": ".sql.gz"
        }
        
        ext = extensions.get(dump_type, ".sql.gz")
        return f"{dbname}-{date}-{dump_type}{ext}"

    @classmethod
    def get_paths(cls, lang_code: str) -> Dict[str, Path]:
        """
        Get standardized paths for a specific language.
        Performs internal validation to ensure project structure is sane.
        """
        # Resolve project root (relative to this file: ../../)
        project_root = Path(__file__).parent.parent.resolve()
        
        paths = {
            'raw_dir': project_root / "data" / "raw",
            'db_dir': project_root / "data" / "db",
            'processed_dir': project_root / "data" / "processed" / lang_code,
            'neo4j_bulk_dir': project_root / "data" / "neo4j_bulk" / lang_code,
            'checkpoints_dir': project_root / "data" / "checkpoints",
            'db': project_root / "data" / "db" / f"{lang_code}.db"
        }
        
        # Validation: Ensure data directories exist (or at least their parents)
        for name, path in paths.items():
            parent = path.parent if path.suffix else path
            if not parent.exists():
                # We don't auto-create here to remain read-only/safe, 
                # but we warn or raise if the base structure is missing.
                if not (project_root / "data").exists():
                    raise RuntimeError(f"Critical failure: 'data/' directory missing in {project_root}")
        
        return paths

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
