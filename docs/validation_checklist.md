# Phase 5A Validation Checklist

## Gate 5A.1: Backend Skeleton
- [ ] Directory structure correct (backend/api/routers, backend/core)
- [ ] Config loading works (reads infrastructure.yaml)
- [ ] FastAPI server starts on test port 9999
- [ ] Basic endpoint (/test) responds < 200ms
- [ ] Memory stable (< 50MB overhead)

## Gate 5A.2: Connection Manager
- [ ] Connections to PL (7687) and DE (7688) established
- [ ] Health status accurate
- [ ] Graceful degradation (simulate one DB down)
- [ ] Query performance acceptable (< 500ms)

## Gate 5A.3: Health Endpoint
- [ ] /health available
- [ ] Status matches reality
- [ ] Counts accurate (±1%)
- [ ] Performance under load

## Gate 5A.INT: Integration
- [ ] Cross-language query (QID consistency)

