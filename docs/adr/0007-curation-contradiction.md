# 0007 — Write-time Curation: Duplicates, Contradictions, Supersession

**Status:** accepted
**Date:** 2026-07-21
**Spec:** docs/HumanVals_RFC.md §3.4

## Context
Raw operator feedback is noisy and sometimes conflicting. Post-hoc background
reconciliation loses the human's context. Engram: supersede, never delete.

## Decision
- On guideline submission, `check_conflicts()` searches the same intent
  neighborhood (similarity >= 0.6) in the same agent+namespace and returns
  `similar` matches for the UI to surface BEFORE saving.
- Resolutions offered to the operator:
  - `add` — save as new guideline (default when no conflicts)
  - `reinforce` — existing guideline gets `validation_count += 1`; no sibling
  - `override` — old guideline `status=superseded`, `superseded_by=new_id`
  - `scope_both` — both survive; the new one must carry `applies_when`
- Supersede is a status transition; nothing is ever deleted (audit trail +
  retrograde-amnesia prevention).

## Consequences
The API server exposes conflicts in the evaluate flow; the dashboard shows
them inline while the reviewer types. Cheap heuristic (similarity) — an LLM
contradiction check can layer on later behind the same interface.

## Amendment (council review 2026-07-21)
- **Scope honestly**: similarity surfaces *neighbors*, not contradictions. A
  lexical embedder cannot tell "always refund" from "never refund". The
  polarity judgment is the operator's — which is exactly why conflicts are
  surfaced at write time to a present human rather than auto-resolved. UI and
  docs say "similar guidelines found", never "contradiction detected".
- **Concurrency**: check→resolve→save is not one transaction across HTTP
  round-trips; two simultaneous operators can still create siblings. Accepted
  at review-scale traffic; the store-level ledger stays consistent, and
  duplicates surface at the next conflict check.
