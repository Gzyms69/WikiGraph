# Language Agnostic Standard

## Definition
A "Language Agnostic" system in WikiGraph is defined as:
1.  **Config-Driven:** All language-specific logic (prefixes, keywords, templates, stop words) is defined in external configuration files (`config/languages/*.yaml`), never in code.
2.  **Generic Logic:** Code operates on abstract concepts ("Namespace 0", "Infobox Template"), not specific strings ("Kategorie:", "Infobox").
3.  **Dynamic Loading:** The system discovers enabled languages at runtime from configuration, iterating through them without hardcoded lists (`['de', 'pl']`).
4.  **Scalable Schema:** Database schemas and API responses follow a consistent structure that accommodates any language without schema migration.

## Audit Protocol
Each finding must include:
-   **File:** Path to the file.
-   **Line:** Line number (approximate).
-   **Code:** The offending snippet.
-   **Type:**
    -   **CRITICAL:** Blocks adding a new language (e.g., hardcoded `if lang == 'de'`).
    -   **MAJOR:** Requires refactoring to support new languages cleanly.
    -   **MINOR:** Technical debt or cleanup.
-   **Impact:** What happens if `es` (Spanish) is added?

## Success Metrics
-   Can we add `es` by adding `es.yaml` and running ingest?
-   Does the API serve `es` data automatically?
