# WikiGraph Universal Configuration Schema

## 1. Overview
This document defines the **Unified Configuration Schema (UCS)** for the WikiGraph system.
*   **Goal:** Enable adding new languages (e.g., `es`, `ja`) purely by creating a YAML configuration file.
*   **Philosophy:** "Configuration over Code." No hardcoded language logic in Python or Bash.
*   **Safety:** The schema distinguishes between **Metadata Tier** (Required) and **Processing Tier** (Optional but validated).

---

## 2. Tiered Architecture

### Tier 1: Metadata & API (Required)
*   **Purpose:** Allows the API to serve the language, display UI names, and perform basic routing.
*   **Requirement:** Mandatory for *all* languages.
*   **Failure Mode:** If missing, the language is invalid and skipped.

### Tier 2: Processing & Extraction (Optional)
*   **Purpose:** Allows the ETL pipeline (`ingest`, `extract_infoboxes`, `graph_build`) to process raw dumps.
*   **Requirement:** Mandatory only if `processing: enabled` is true.
*   **Failure Mode:** If missing/incomplete, extraction tools will exit gracefully, but API remains online.

---

## 3. Schema Definition

```yaml
# -----------------------------------------------------------------------------
# TIER 1: METADATA & API (REQUIRED)
# -----------------------------------------------------------------------------
language:
  code: "es"                  # ISO 639-1 code (Required)
  name: "Wikipedia"           # Default "Wikipedia"
  local_name: "Español"       # Native name for UI (Required)
  iso_code: "es-ES"           # Full locale code (Required)

ui:
  search_placeholder: "Buscar en Wikipedia..."  # (Required)
  language_name: "Español"                      # (Required)
  interface_translations:                       # (Required)
    show_connections: "Mostrar conexiones"
    related_articles: "Artículos relacionados"
    categories: "Categorías"

# -----------------------------------------------------------------------------
# TIER 2: PROCESSING & EXTRACTION (OPTIONAL)
# -----------------------------------------------------------------------------
processing:
  enabled: true               # If false, Tier 2 checks are skipped

wikipedia:
  dbname: "eswiki"            # Dump database name (Required if processing=true)
  base_url: "https://es.wikipedia.org"
  
  redirect_keywords:          # (Required if processing=true)
    - "#REDIRECT"
    - "#REDIRECCIÓN"
    
  disambiguation_markers:     # (Required if processing=true)
    - "{{desambiguación}}"
    
  # Standardized Namespace Structure (Required if processing=true)
  # Must provide lists for all keys. Empty lists allowed.
  namespace_prefixes:
    file: ["Archivo:", "File:", "Image:"]
    category: ["Categoría:", "Category:"]
    template: ["Plantilla:", "Template:"]

# Text Processing Rules (Required if processing=true)
text_processing:
  encoding: "utf-8"
  has_spaces: true
  word_separator: " "
  stopwords_path: "config/stopwords/es.txt" # Path relative to project root
  stemmer: "snowball"         # NLTK stemmer name

# Infobox Extraction Rules (Required if processing=true)
infobox:
  # At least one of prefixes OR suffixes must be non-empty
  template_prefixes:          # Templates starting with...
    - "Ficha de"
    - "Infobox"
  template_suffixes:          # Templates ending with...
    - "infobox"
  
  # Parameter Normalization (Optional)
  # Maps local parameter names to canonical schema keys
  parameter_map:
    fecha_de_nacimiento: born
    fecha_de_fallecimiento: died
    superficie: area
    población: population

# Text Cleanup Patterns (Optional - defaults to file namespace)
text_cleanup:
  file_patterns: []           # Regex or strings to strip from plain text
```

---

## 4. Validation Rules

### 4.1 Global Validation (LanguageManager Load Time)
1.  **File Existence:** `config/languages/{code}.yaml` must exist.
2.  **Tier 1 Check:** `language` and `ui` sections must be present and complete.
    *   *Error:* `CriticalConfigurationError: '{lang}' missing required metadata.`

### 4.2 Processing Validation (ETL Start Time)
1.  **Tier 2 Check:** If tool requests `processing_config`, check `processing.enabled`.
2.  **Completeness:** If enabled, `wikipedia`, `text_processing`, and `infobox` must exist.
3.  **Infobox Logic:** `len(template_prefixes) + len(template_suffixes) > 0`.
    *   *Error:* `ExtractionError: '{lang}' has no infobox patterns defined.`

---

## 5. Infrastructure Integration

The configuration drives the infrastructure:

1.  **Port Allocation:**
    *   **Auto-Assignment (Proposed):** `base_port + (lang_index * 2)`.
    *   **Override:** `infrastructure.yaml` can explicitly override ports for specific languages.

2.  **Container Naming:**
    *   Format: `neo4j-{lang}` (e.g., `neo4j-es`).

3.  **Data Paths:**
    *   DB: `data/db/{lang}.db`
    *   Neo4j: `data/neo4j_data/{lang}/`

---

## 6. Migration Guide

### 6.1 Migrating `en.yaml`
*   **Current State:** Missing `text_cleanup`, `infobox` empty.
*   **Action:**
    1.  Add `processing: { enabled: false }` to disable extraction for now.
    2.  OR: Fill in `text_cleanup` with default `file` namespace patterns to enable extraction.

### 6.2 Migrating `de.yaml` / `pl.yaml`
*   **Action:** 
    1.  Add `processing: { enabled: true }`.
    2.  Ensure `template_suffixes` exists in `de.yaml` (empty list `[]`).
    3.  Ensure `text_cleanup` exists in all.

---

## 7. Example: Minimal Spanish Config (`es.yaml`)

```yaml
language:
  code: es
  name: Wikipedia
  local_name: Español
  iso_code: es-ES

ui:
  search_placeholder: "Buscar..."
  language_name: "Español"
  interface_translations:
    show_connections: "Mostrar conexiones"
    related_articles: "Artículos relacionados"
    categories: "Categorías"

processing:
  enabled: true

wikipedia:
  dbname: eswiki
  redirect_keywords: ["#REDIRECCIÓN"]
  namespace_prefixes:
    file: ["Archivo:"]
    category: ["Categoría:"]
    template: ["Plantilla:"]

text_processing:
  encoding: utf-8
  has_spaces: true
  word_separator: " "
  stopwords_path: config/stopwords/es.txt
  stemmer: spanish

infobox:
  template_prefixes: ["Ficha de"]
  template_suffixes: []
  parameter_map: {}

text_cleanup:
  file_patterns: ["Archivo:"]
```
