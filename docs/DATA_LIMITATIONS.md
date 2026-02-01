# Data Quality & Limitations Report

## Executive Summary
WikiGraph provides a high-performance API serving structured knowledge graph data (Nodes, Edges, Metadata, Infoboxes). The system combines topological data from Neo4j with rich metadata from SQLite.

**Current Data Yields:**
- **German (DE):** ~62% of articles have structured infoboxes.
- **Polish (PL):** ~79% of articles have structured infoboxes.

## Known Data Gaps

### 1. Manual Infobox Tables (The "Berlin" Gap)
**Impact:** Major entities (e.g., *Berlin*, *Hamburg*) are missing structured infobox data.
**Cause:** These articles use manual Wikitable syntax (`{| class="wikitable infobox" ... |}`) instead of standard templates (`{{Infobox ...}}`).
**Current Status:** The extractor currently skips these tables to avoid parsing errors. The API returns `null` for the `infoboxes` key.
**Mitigation:** A "Hybrid Extractor" is planned (See TODO.md) to parse these tables in a future release.

### 2. Missing Templates (The "Tusk" Gap)
**Impact:** Some biographical articles (e.g., *Donald Tusk*) lack standard infobox templates entirely in the source text, often relying on lead paragraphs or bottom-of-page templates (`{{Personendaten}}`) that may vary in structure.
**Current Status:** If no matching template is found, the API returns `null`.

### 3. Redirects & Disambiguations
**Impact:** QIDs pointing to Redirects or Disambiguation pages do not have infoboxes.
**Status:** This is expected behavior. The API returns `null`.

## API Behavior for Missing Data
The API adheres to a strict contract for missing data:
- **Infobox Missing:** Returns `null` (e.g., `"infoboxes": { "de": null }`).
- **Language Missing:** Key is absent from `infoboxes` dict.
- **Empty Infobox:** Returns `[]` (Empty List).

## Future Improvements
- **Universal Discovery:** Automated scanning of template usage to improve config coverage.
- **Hybrid Extraction:** Implementation of a table parser for manual infoboxes.
