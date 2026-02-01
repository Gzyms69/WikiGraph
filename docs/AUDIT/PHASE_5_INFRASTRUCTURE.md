# Audit Report: Phase 5 (Infrastructure Layer)

## 1. `dev.sh` Forensics
**Status:** ❌ **CRITICAL VIOLATION**

-   **Hardcoded Languages:**
    ```bash
    case "$CMD" in
        start)
            start_container "pl" 7474 7687  <-- HARDCODED
            start_container "de" 7475 7688  <-- HARDCODED
    ```
-   **Loop Violation:** `for lang in pl de; do` in `stop_all()`.
-   **Impact:** Adding `es` requires editing this script manually. It does NOT read `infrastructure.yaml`.

## 2. `run_neo4j_import.sh` Forensics
**Status:** ✅ **CLEAN**

-   **Dynamic Arg:** `LANG=${1:-pl}`. Accepts any language code.
-   **Dynamic Paths:** Uses `data/neo4j_data/$LANG` and `data/neo4j_bulk/$LANG`.
-   **Dependencies:** Calls `dev.sh start $LANG` at the end. This will FAIL if `dev.sh` logic for `start_container` doesn't support the new language (see above).

## 3. `infrastructure.yaml` Analysis
**Status:** ✅ **GOOD DESIGN, UNUSED**

-   **Structure:** Defines `pl` and `de` with ports.
-   **The Gap:** `dev.sh` IGNORES this file and uses hardcoded values. `app/core/config.py` (via `settings`) likely uses it, but the shell scripts do not.

## 4. Findings & Remediation

| ID | Type | Description | Remediation |
| :--- | :--- | :--- | :--- |
| I-01 | **CRITICAL** | `dev.sh` hardcodes `pl` and `de` logic and ports. | Rewrite `dev.sh` to parse `infrastructure.yaml` using `yq` or Python helper. |
| I-02 | **MAJOR** | `run_neo4j_import.sh` relies on `dev.sh` to restart containers. | Fix `dev.sh` first. |

## 5. Conclusion
The infrastructure automation is **Brittle**. It is manually configured for DE/PL. Adding ES requires manual port assignment and script editing.
