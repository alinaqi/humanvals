# Active Todos

Current work in progress. Atomic todo format from base skill.

---

## TODO-001: Core library (schemas, store, retrieval, promotion)
**Validation criteria**: pytest green, coverage >= 80%, ruff + mypy clean
**Test cases**: tests/test_schemas.py, test_store.py, test_intent.py,
test_injector.py, test_promotion.py, test_metrics.py, test_client.py

## TODO-002: FastAPI review server
**Validation criteria**: TestClient suite green; all dashboard endpoints served
**Test cases**: tests/test_server.py

## TODO-003: React dashboard
**Validation criteria**: builds clean, Vitest green, manual visual check via screenshot
**Test cases**: dashboard/src/**/*.test.tsx

## TODO-004: Example agents (pydantic-ai, langgraph, crewai)
**Validation criteria**: each runs end-to-end with NO API keys, records cases
**Test cases**: tests/test_examples.py (smoke via subprocess)

## TODO-005: Docs (README, RFC, AGENT_GUIDE, llms.txt) + ADRs
**Validation criteria**: RFC links to alinaqi/alinaqi series; README professional
