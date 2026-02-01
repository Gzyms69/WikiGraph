# Audit Report: Phase 3 (Database Layer)

## 1. SQLite Loader Forensics (`core/sqlite_loader.py`)
**Status:** ✅ **CLEAN**

-   **Path Construction:** `db_path = Path(f"data/db/{args.lang}.db")`. Configurable via CLI.
-   **Schema:** Generic tables (`pages`, `id_mapping`, `infobox` JSON). No language columns, meaning each language is a siloed DB. This is a design choice (Federated) rather than a flaw.
-   **Dump Parsing:** Generic `mwsql`.
-   **Data Storage:** Stores `infobox` as generic JSON. No hardcoded keys.

## 2. Neo4j CSV Generation (`core/tools/prepare_neo4j_csv.py`)
**Status:** ❓ **PENDING** (Next Step)

We need to verify if the CSVs produced have a `language` property. If not, importing multiple languages into one Neo4j instance will cause collisions or ambiguity if QIDs overlap (which they shouldn't, but titles might).

## 3. Findings & Remediation

| ID | Type | Description | Remediation |
| :--- | :--- | :--- | :--- |
| D-01 | **INFO** | SQLite databases are siloed per language (`de.db`, `pl.db`). | This is acceptable for the "Federated" architecture. |
| D-02 | **RISK** | `category_links` table stores `category_name`. Is this localized? | Yes, categories are localized. `Category:Physiker` vs `Kategoria:Fizycy`. |

## 4. Conclusion
The SQLite layer is solid. It creates identical schemas for any language. The abstraction holds.
