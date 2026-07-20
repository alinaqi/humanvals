# Decision Log

Append-only. Format: date, decision, context, options, choice, reasoning, trade-offs.

---

## [2026-07-21] Own git repo inside AI-Playground
**Decision**: `humanvals/` gets its own git repo; parent dir is the 31app repo.
**Context**: Parent AI-Playground working tree points at alinaqi/31app.git.
**Reasoning**: Publishing to github.com/alinaqi/humanvals requires isolation.

## [2026-07-21] Python 3.12 via uv (not 3.14 system default)
**Decision**: Pin 3.12.
**Context**: crewai/langgraph/pydantic-ai lag on 3.14 support.
**Trade-offs**: None significant; requires-python stays >=3.10.

## [2026-07-21] Zero-dependency core
**Decision**: humanvals core uses stdlib only (sqlite3, math, json). FastAPI is
an optional extra; frameworks are examples, not dependencies.
**Reasoning**: "super simple for devs" — pip install humanvals must never drag
in a framework. See ADR-0003/0004.
