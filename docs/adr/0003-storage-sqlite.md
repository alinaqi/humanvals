# 0003 — Storage: SQLite Default, Pluggable Store Protocol

**Status:** accepted
**Date:** 2026-07-21

## Context
"Super simple for devs" rules out requiring Postgres/vector DBs. Production
users will still want their own storage.

## Decision
- Default store: stdlib `sqlite3`, WAL mode, JSON columns for metadata.
  `HumanVals("humanvals.db")` or `HumanVals(":memory:")` — no server needed.
- All persistence behind a `Store` protocol (typing.Protocol): implement it to
  back HumanVals with Postgres/Supabase/etc. without touching core logic.

## Alternatives considered
- SQLAlchemy: adds a dependency to the zero-dep core — rejected.
- JSON files: no concurrent-writer story for the API server — rejected.

## Consequences
Core stays zero-dependency. Concurrency handled by SQLite WAL + short
transactions; fine for review-scale traffic. High-scale users implement Store.

## Amendment (council review 2026-07-21)
- `PRAGMA busy_timeout=5000` set on every connection so concurrent reviewer
  writes retry instead of failing spuriously; all transactions are single
  statements or tight statement groups (no long-running review transactions).
- Schema versioned via `PRAGMA user_version` (SCHEMA_VERSION in store.py);
  migrations gate on it when the schema first evolves.
- Alternative Store implementations must make `credit_exposure` atomic
  (ledger insert + counter update in one transaction) — this is the one
  read-modify-write that promotion correctness depends on.
