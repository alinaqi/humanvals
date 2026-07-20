# 0005 — Injection Budget & Prompt Format

**Status:** accepted
**Date:** 2026-07-21
**Spec:** docs/HumanVals_RFC.md §3.3

## Context
The guideline corpus grows forever; per-request context must not. The
anti-pollution invariant.

## Decision
- `GuidelineSet` returned by `guidelines()` carries at most `max_items`
  (default 5) guidelines within `max_chars` (default 2000, ~500 tokens).
- Ranking: cosine similarity × (1 + validated bonus). Validated guidelines
  outrank candidates at equal relevance.
- `GuidelineSet.as_prompt()` renders a clearly delimited block; validated
  guidelines render as instructions, candidates as "provisional guidance" —
  Engram confabulation-prevention: never present unvalidated memory with
  validated confidence.
- Empty set renders empty string — integration code needs no branching.

## Consequences
Devs concatenate one string; context stays bounded regardless of corpus size.
