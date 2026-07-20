# 0004 — Intent Matching: Local Hashed-ngram Embedder, Pluggable

**Status:** accepted
**Date:** 2026-07-21
**Spec:** docs/HumanVals_RFC.md §3.3

## Context
Retrieval keys on intent similarity. Real embeddings need API keys or heavy
local models; the library must work offline with zero deps, and Engram warns
against single-path retrieval.

## Decision
- `Embedder` protocol: `embed(text) -> list[float]`.
- Default: `HashedNgramEmbedder` — lowercased word + character-trigram features
  hashed into a fixed 512-dim vector (feature-hashing trick), L2-normalized,
  cosine similarity. Deterministic, stdlib-only, good lexical-intent proxy.
- Retrieval gate = intent cosine >= threshold (default 0.35, conservative,
  precision-first) AND namespace/agent match AND status in
  {candidate, validated}. Ranked by similarity × validation strength; then
  budget applied (ADR-0005).
- Drop-in upgrades documented: OpenAI/sentence-transformers embedder in ~10
  lines via the protocol.

## Consequences
Cold start works on a plane. Lexical embedding is weaker than semantic — the
conservative threshold plus precision-first posture compensates; quality users
plug in a real embedder without core changes.

## Amendment (calibration, 2026-07-21)
Council asked for a calibration procedure; measured on a refund-intent probe
set (tests/test_embedding.py::test_varied_phrasings_clear_the_gate keeps it
honest in CI):

- **Stopword filtering added**: function words diluted norms and let unrelated
  queries score up to 0.14 while dropping related paraphrases to 0.26. After
  filtering: related phrasings 0.32–0.42, unrelated ≤ 0.13.
- **Gate recalibrated 0.35 → 0.30** for the filtered embedder: every related
  probe clears it; unrelated stays ≥ 0.17 below it (>2x margin).
- **applies_when joins the intent vector**: the operator's stated activation
  context is embedded with the source-case input at guideline creation
  (Engram activation_contexts) so a guideline generalizes past the single
  case that spawned it.
- The gate is calibrated to THIS embedder. Swapping in a semantic embedder
  requires re-running the probe set and setting a new gate.
