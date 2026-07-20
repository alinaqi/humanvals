# 0006 — Promotion Policy: Wilson Lower Bound

**Status:** accepted
**Date:** 2026-07-21
**Spec:** docs/HumanVals_RFC.md §3.5

## Context
"Positive impact verified" needs statistics, not vibes: 3 exposures with 3
wins must not promote.

## Decision
- Evidence: when a case is evaluated, each guideline in its exposure log gets
  `exposures += 1` and `wins += 1` if `output_ok` (idempotent per case).
- `PromotionPolicy` dataclass (pluggable): `min_exposures=5`,
  `promote_threshold=0.55` on Wilson 95% lower bound, `demote_threshold=0.4`
  on Wilson 95% upper bound. (0.55, not 0.6: wilson_lower(5/5) = 0.5655, so a
  perfect 5-exposure record must clear the bar; 4/5 = 0.376 correctly does not.
  Demotion example: 0/6 has wilson_upper = 0.39 < 0.4.)
- `run_promotions()` applies the policy: candidate→validated (origin becomes
  `validated`, `promoted_at` set) or validated→candidate (demotion, evidence
  kept for review). Rejected/superseded are terminal for injection but never
  deleted.

## Alternatives considered
- Plain win-rate threshold: promotes on tiny samples — rejected.
- Sequential testing (SPRT): better power, more complexity — deferred; policy
  is pluggable so it can ship later without breaking changes.

## Amendment: evidence window resets on promotion
Promotion zeroes `exposures`/`wins`. Rationale: counters are cumulative, so a
guideline promoted at 5/5 then failing 6 straight would still show 5/11
(Wilson upper 0.72) and never demote. Each status tier must earn its keep on
evidence gathered *in that tier*. Lifetime history remains reconstructable
from the evaluations + exposure_credits tables.

## Consequences
Promotion is auditable arithmetic over exposure evidence. Thresholds are
config, not code.

## Amendment (council review 2026-07-21)
- **Re-measurement window**: after promotion resets evidence, a validated
  guideline is injected with validated confidence until `min_exposures` fresh
  exposures accumulate — a deliberate grace window (promotion required 5/5
  wins, so short-lived trust is earned). Accepted trade-off; a
  provisional-demotion guard can layer on via a custom PromotionPolicy.
- **Correlational attribution**: `output_ok` credits every injected guideline
  without a counterfactual arm. Wilson bounds quantify sampling noise, not
  causal effect. Documented in RFC §7; hold-out control is open question Q5.
- **Reinforcement is not evidence**: `validation_count` (operator reinforce)
  is provenance strength shown in the UI; it never enters the Wilson
  statistics. Only measured exposures do — this keeps "measured impact"
  uncontaminated by operator conviction.
