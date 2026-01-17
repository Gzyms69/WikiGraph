# Phase 4 Recovery Protocol

## Trigger
If `run_neo4j_import.sh` fails, hangs for >30 minutes, or Gate 5 validation fails.

## Procedure
1. **Stop the Service:**
   `docker stop neo4j`

2. **Check Logs:**
   Inspect `data/neo4j_data/logs/neo4j.log` and `debug.log` for errors.

3. **Clean Corrupt Data (Safe):**
   `rm -rf data/neo4j_data/data/*`
   `rm -rf data/neo4j_data/logs/*`

4. **Verify Source CSVs:**
   Run Gate 4 check again: `python3 tools/verify_neo4j_csvs.py`

5. **Resource Check:**
   Ensure Docker has at least 12GB RAM allocated.

6. **Retry:**
   Run `bash core/tools/run_neo4j_import.sh` again.

