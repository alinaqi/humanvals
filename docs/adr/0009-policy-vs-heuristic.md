# 0009 — Two Guideline Classes: Policies vs. Heuristics

**Status:** accepted
**Date:** 2026-07-21
**Spec:** docs/HumanVals_RFC.md §3.5

## Context
The v1 design treats every guideline as an equal-stakes hypothesis subject to
statistical verification (Wilson-bound promotion, eventual hold-out controls).
Review feedback (Ali, 2026-07-21) exposed the flaw: criticality, not traffic
statistics, should govern high-stakes guidance. "Always confirm the order
number before issuing a refund" is not a hypothesis to A/B test — withholding
it from a control group means knowingly serving critical failures to gain
confidence nobody asked for. For critical failure modes, the operator's
judgment IS the verification.

## Decision
Guidelines carry a `kind`, chosen by the operator at review time:

- **`heuristic`** (default) — tone, formatting, style, phrasing, preferences.
  Cheap to be wrong about. Full statistical lifecycle: candidate → measured
  exposures → Wilson-bound promotion/demotion; the only class eligible for
  hold-out experiments (RFC Q5 applies to heuristics ONLY).
- **`policy`** — critical failure modes (money, compliance, safety,
  irreversible actions). Governance is human authority, not statistics:
  - active immediately at creation (`status: validated` on save; `origin`
    remains `stated` — authority-backed, not measurement-backed)
  - exempt from `run_promotions` entirely: never statistically demoted
  - removed only by a human (override/supersede), never by the machine
  - ranked above heuristics at injection and rendered in their own
    "always follow" block, above validated guidance
  - exposure/win counters still accumulate as *monitoring* evidence
    (surfaced in the dashboard), but they never drive a status change

## Who guards the gate
The obvious failure mode is kind-inflation: every reviewer marks their
guideline critical. Mitigations, in order of adoption: the UI frames policy as
the exception (unchecked by default, explicit consequence text); policy
creation is attributed and auditable (reviewer recorded); teams can layer an
approval step server-side later without core changes. Accepted as a social
contract at current scale.

## Consequences
- Schema v3: `guidelines.kind TEXT DEFAULT 'heuristic'` (user_version
  migration; all existing guidelines become heuristics).
- The Wilson machinery is unchanged but scoped to heuristics — statistics
  govern only the tier where being wrong is cheap.
- Future work: policy violation *monitoring* (a policy was injected and
  `output_ok=false`) should alert a human rather than demote; deferred.
