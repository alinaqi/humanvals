# 0002 — Domain Model: Case, Evaluation, Guideline, Exposure Log

**Status:** accepted
**Date:** 2026-07-21
**Spec:** docs/HumanVals_RFC.md §3

## Context
We need a minimal model that carries the whole loop: capture → review →
distill → inject → measure → promote. Engram RFC v3 supplies the record
semantics (Origin, status, namespaces, supersession).

## Decision
Three aggregates, stdlib dataclasses:

- **Case**: `id, agent, namespace, input, output, metadata (thought_chain,
  tool_calls, context), guidelines_injected, created_at`. The
  `guidelines_injected` exposure log is REQUIRED (may be empty list, never
  absent) — every impact measurement joins through it.
- **Evaluation**: `case_id, intent_ok, output_ok, context_ok, notes,
  guideline_text?, applies_when?, reviewer, created_at`. `output_ok` is the
  win/loss signal for exposed guidelines.
- **Guideline**: `id, agent, namespace, intent_key, text, applies_when,
  origin (stated|validated), status (candidate|validated|superseded|rejected),
  exposures, wins, validation_count, superseded_by, source_case_id,
  created_at, promoted_at`.

Engram mapping: origin stated→validated on promotion; supersede instead of
delete; namespace scoping per agent + tenant/entity.

## Consequences
Exposures live on the Case (`guidelines_injected`) and are aggregated onto
Guideline counters at evaluation time through a persisted credit ledger:

- **exposure_credits(case_id, guideline_id)** — primary-keyed ledger enforcing
  idempotency: a `(case, guideline)` pair is credited exactly once regardless
  of how many times the case is (re-)evaluated.
- **Evaluation cardinality**: multiple evaluations per case are allowed
  (re-review, multiple reviewers). First-credit-wins: a correcting re-review
  does not flip an already-recorded credit. Known limitation, accepted for
  simplicity; the full evaluation history is retained, so credits can be
  recomputed offline if a stricter policy is ever needed.
- **Win signal**: `output_ok` alone credits/blames exposed guidelines.
  Rationale: it is the dimension closest to "did the final output serve the
  user"; intent/context failures usually also surface as output failures.
  Collapsing to one binary keeps the Wilson statistics interpretable.

## Amendment (council review 2026-07-21)
Attribution is correlational: every guideline injected into a case shares
credit/blame for that case's outcome, without a counterfactual control. This
is a documented, accepted bias at this stage — see RFC §7 (Limitations) and
open question Q5 (hold-out control fraction).
