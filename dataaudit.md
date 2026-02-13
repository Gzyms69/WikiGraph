# WikiGraph Comprehensive Data Audit Report
**Date:** 2026-02-12
**Status:** COMPLETE (Languages: PL, DE, ES)

## 1. Executive Summary
The WikiGraph system spans three major language datasets (Polish, German, Spanish). Data is partitioned between language-specific SQLite databases for detailed properties and metrics, and a Neo4j graph layer for connectivity analysis.

**Total Graph Scale:**
- **Nodes:** 6,763,703 `Concept` nodes across 3 databases.
- **Relationships:** 313,202,222 `LINKS_TO` relationships.
- **Relational Metadata:** 12,819,913 pages across 3 SQLite databases.

---

## 2. Detailed Data Structures (SQLite)

### A. `pages` Table (Core Metadata)
Stores raw page properties and extracted content.
- **Format:**
  - `page_id`: `INTEGER` (Wiki internal ID)
  - `title`: `TEXT` (Cleaned title, e.g., `AWK`)
  - `namespace`: `INTEGER` (0 for Articles, 14 for Categories)
  - `is_redirect`: `BOOLEAN` (0/1)
  - `len`: `INTEGER` (Text length in bytes)
  - `infobox`: `JSON` (Array of objects)
- **`infobox` JSON Structure:**
  ```json
  [
    {
      "template": "Template Name",
      "params": {
        "key1": "value1",
        "key2": "[[Link]] value"
      }
    }
  ]
  ```

### B. `node_metrics` Table (Pre-computed Analytics)
Stores analytical results indexed by QID.
- **Format:**
  - `qid`: `TEXT` (Primary Key part, e.g., `Q213970`)
  - `metric_key`: `TEXT` (Metric type identifier)
  - `metric_value`: `REAL` (The computed value)
  - `computed_at`: `TIMESTAMP` (ISO 8601 format)
- **Example Row:** `Q1 | pagerank | 44.5841 | 2026-02-07 13:33:26`

### C. `id_mapping` Table (The Bridge)
Links Wikipedia Internal IDs to Wikidata Global IDs.
- **Format:** `page_id (INTEGER) | qid (TEXT)`
- **Sample:** `2 | Q213970`

### D. `articles_fts` (Search Index)
SQLite FTS5 virtual table for full-text search.
- **Format:** `title (TEXT, Indexed) | qid (TEXT, UNINDEXED)`
- **Purpose:** Optimized prefix and fuzzy matching on article titles.

---

## 3. Language-Specific Coverage (Audit Revision)
*Note: Infobox coverage calculated against **non-redirect articles**.*

| Language | Non-Redirects | With Infoboxes | Coverage % | Metrics Rows |
| :--- | :--- | :--- | :--- | :--- |
| **Polish (PL)** | 2,015,039 | 1,380,206 | **68.49%** | 8.32M |
| **German (DE)** | 3,635,852 | 1,997,295 | **54.93%** | 15.37M |
| **Spanish (ES)** | 2,585,774 | 1,531,643 | **59.23%** | 10.11M |

---

## 4. Analytical Metrics Catalog

### Tier 1: Node-Level (SQLite)
- **`pagerank`**: Measures "prestige" of the article.
- **`triangle_count`**: Measures local clustering (how "cliquey" a neighborhood is).
- **`auth_score`**: HITS algorithm authority score.
- **`louvain_id`**: Global community ID (Coarse).
- **`leiden_id`**: Global community ID (Fine-grained).

### Tier 2: Similarity (Neo4j Dynamic)
- **`adamic_adar`**: Weighted common neighbors.
- **`jaccard`**: Intersection over union of neighbor sets.
- **`resource_allocation`**: Flow-based similarity.

---

## 5. Neo4j Graph Structure

### Node: `:Concept`
- `qid`: `TEXT` (Unique ID, e.g., `Q213970`)
- `ns`: `INTEGER` (Namespace ID)

### Relationship: `:LINKS_TO`
- Directed edge from Source to Target. No properties are stored on relationships to maximize performance.

---

## 6. Critical Findings & Anomalies
1.  **Metric Integrity:** ES database is verified 100% healthy with all 5 metric types populated.
2.  **Infobox Depth:** Infoboxes are not just strings but structured JSON, enabling complex attribute extraction (e.g., logos, dates, creators).
3.  **Search Optimization:** `articles_fts` uses the `UNINDEXED` flag for `qid` to save space, keeping only `title` searchable.
4.  **Redirects Impact:** German has the highest absolute number of redirects (1.95M), significantly impacting the raw `infobox` percentage if not filtered.
