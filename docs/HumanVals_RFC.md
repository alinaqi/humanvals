# HumanVals RFC v1 — Human Feedback as Verified Agent Memory

**Status:** Draft
**Author:** Ali Naqi Shaheen
**Series:** [alinaqi RFC series](https://github.com/alinaqi/alinaqi/tree/main/docs) · builds on [Engram RFC v3](https://github.com/alinaqi/alinaqi/blob/main/docs/Engram_RFC_v3.md)
**Implementation:** [github.com/alinaqi/humanvals](https://github.com/alinaqi/humanvals)

---

## 1. Abstract

Production agents produce structured outputs that human operators routinely
correct — and those corrections evaporate. HumanVals defines a closed loop that
captures operator feedback as **cases**, distills it into **guidelines**, injects
guidelines into future agent runs under a strict budget, **measures each
guideline's real impact** through exposure logging, and **promotes** only
verified guidelines into a permanent knowledge layer.

The central claim: *human-approved is not verified-to-help*. Most feedback
systems stop at collection. HumanVals treats every guideline as a hypothesis
that must earn permanence through measured outcomes — an experimentation
pipeline for memory, not a notebook.

## 2. Relationship to Engram

[Engram RFC v3](https://github.com/alinaqi/alinaqi/blob/main/docs/Engram_RFC_v3.md)
reframes agent memory as a diagnostic problem: seven amnesia types, each with
targeted architectural fixes. HumanVals is a **vertical slice of Engram** for
one memory class — operator-stated guidelines — with the lifecycle machinery
Engram specifies applied end to end:

| Engram concept | HumanVals realization |
|---|---|
| EngramRecord `Origin: stated` | New guideline from operator feedback |
| `Origin: validated`, `validation_count` | Promotion after measured positive impact |
| `status: superseded`, `superseded_at` | Override flow — never delete, always supersede |
| Namespace isolation (interference) | Guidelines scoped per agent + namespace |
| Context-binding prevention | Explicit `applies_when` captured at review time |
| Retrieve-time synthesis | Guidelines injected as prompt instructions; no background reflection |
| Amnesia measurement protocol (§6.2) | 4-dimension case evaluation doubles as labeled probes |
| Confabulation prevention | Candidate vs. validated tiers rendered distinctly in the prompt |

Where Engram diagnoses *whether* an agent forgets, HumanVals closes the loop on
*what humans teach it* — and proves whether the teaching worked.

## 3. The Loop

```
        ┌────────────────────────────────────────────────────────┐
        │                                                        │
  agent run ──► case (input, output, thought chain, tools,       │
        ▲        context, guidelines_injected)                   │
        │                     │                                  │
        │                     ▼                                  │
        │           human review (4 dimensions)                  │
        │        a) intent understood?   b) output correct?      │
        │        c) right context used?  d) guideline for future │
        │                     │                                  │
        │                     ▼                                  │
        │        distillation: intent clustering, duplicate      │
        │        reinforcement, contradiction check (write-time, │
        │        human present, may supersede or scope both)     │
        │                     │                                  │
        │                     ▼                                  │
        │        candidate guideline ──(measured exposures)──►   │
        │        promotion policy (Wilson lower bound) ──►       │
        │        validated guideline (permanent layer)           │
        │                     │                                  │
        └──── guidelines(input): intent lookup, budget, ─────────┘
              exposure log
```

### 3.1 Cases

A case is one agent execution packaged for fast human analysis:

```
input               what the agent was asked
output              what it produced
metadata            thought chain, tool calls, context provided
guidelines_injected the exposure log — REQUIRED, the backbone of measurement
```

`guidelines_injected` is non-optional by design. Every downstream mechanism —
impact measurement, promotion, demotion, intervention-rate metrics — joins
through it. A case without an exposure log is unusable as evidence.

### 3.2 Four-dimension evaluation

Operators answer four questions per case. The first three are boolean probes
(with optional notes); the fourth is generative:

1. **Intent** — did the agent understand what was being asked?
2. **Output** — is the output designed and factually correct?
3. **Context** — did the agent use the right context?
4. **Guideline** — one instruction for handling this in future, plus
   **`applies_when`**: the operator states the applicability conditions
   explicitly, so scope is never inferred.

Dimensions 1–3 map onto Engram's amnesia probes (encoding quality,
confabulation, context-binding/interference), which makes every review a
labeled measurement, not just feedback.

### 3.3 Retrieval ("finetuned-prompt")

At decision time the agent sends its input; HumanVals extracts an intent
representation, and returns matching guidelines as plain prompt instructions.
Properties:

- **Precision over recall.** A missed guideline costs one un-improved output; a
  wrongly injected guideline corrupts an output *and* poisons the measurement
  signal. The similarity gate is conservative; the empty result is the default
  posture at the margin, forever — not just at cold start.
- **Multi-path gating** (Engram §Multi-Path Retrieval): intent similarity AND
  namespace gate AND status gate. Single-path semantic lookup is exactly what
  Engram argues against.
- **Budget.** Guidelines compete for a bounded prompt budget, ranked by
  relevance × validation strength. Growth of the corpus must not grow the
  per-request context — this is the anti-pollution invariant.

### 3.4 Write-time curation

When an operator submits a guideline, HumanVals checks the intent cluster it
lands in *while the human is present*:

- **Near-duplicate** → offer *reinforce* (increments validation evidence)
  instead of creating a sibling paraphrase.
- **Contradiction** → notify the operator, who may **override** (supersedes the
  old guideline — status change, never deletion) or **scope both** (the
  contradiction is legitimate context-dependence; both survive with narrower
  `applies_when`). Note the honest scoping: similarity search surfaces
  *neighbors*; whether a neighbor agrees or contradicts is the operator's
  judgment. The system deliberately does not claim automated contradiction
  detection (see §6).

This is deliberate: conflict resolution happens at the moment a human with
context is looking at the evidence, not in a background job.

### 3.5 Measurement and promotion

Every future evaluation of a case is simultaneously an impact measurement for
each guideline in that case's exposure log. No separate A/B infrastructure:
the review process **is** the eval harness.

A guideline's evidence: `exposures` (cases it was injected into that later got
evaluated) and `wins` (those evaluations scored the output positively).
Promotion uses the **Wilson score lower bound** at 95% confidence:

```
promote  iff exposures >= N_min  AND  wilson_lower(wins, exposures) >= p_min
demote   iff exposures >= N_min  AND  wilson_upper(wins, exposures) <  p_demote
```

Defaults: `N_min = 5`, `p_min = 0.6`, `p_demote = 0.4` — all pluggable.
Promotion sets `Origin: stated → validated` (Engram's confabulation-prevention
tier); demotion returns a guideline to review with its evidence attached.
Sample-size floors exist because three thumbs-up is anecdote, not evidence.

### 3.6 The success metric

**Intervention rate per intent cluster** — the fraction of reviewed cases in a
cluster requiring correction, over time. Declining ⇒ the cluster is learned;
human effort provably decreases. Flat despite accumulated guidelines ⇒ a
retrieval or intent-extraction pathology (in Engram terms, context-binding
failure), flagged for diagnosis rather than more feedback. One chart is both
the product's proof of value and its debugging tool.

## 4. Non-goals

- **Not a vector database.** Embedding/intent extraction is a pluggable
  interface; the default is a local, dependency-free embedder. Bring your own.
- **Not fine-tuning.** "Finetuned-prompt" operates purely in prompt space.
- **Not general memory.** Facts, preferences, temporal knowledge, entity graphs
  are Engram's broader scope. HumanVals covers exactly one record class —
  operator guidelines — with full lifecycle rigor.

## 5. Reference implementation

`pip install humanvals` — zero-dependency Python core (SQLite storage), optional
FastAPI review server, React dashboard, and adapters/examples for pydantic-ai,
CrewAI, and LangGraph. Integration is two calls:

```python
hv = HumanVals("humanvals.db")
g = hv.guidelines(user_input, agent="support-bot")   # retrieval + budget
...
hv.record_case(agent="support-bot", input=user_input,
               output=result, guidelines=g)          # exposure-logged case
```

Architecture decisions are recorded in
[docs/adr/](https://github.com/alinaqi/humanvals/tree/main/docs/adr).

## 6. Known limitations (v1, stated plainly)

Reviewed by a multi-model design council (2026-07-21); these are the accepted
trade-offs, not oversights:

1. **Attribution is correlational.** Every guideline injected into a case
   shares credit/blame for that case's `output_ok`. There is no counterfactual
   control arm, so Wilson bounds quantify sampling noise over a correlational
   signal, not causal effect. Mitigations: the injection budget caps
   co-exposure; namespace/agent scoping narrows confounds; Q5 proposes a
   hold-out fraction for causal rigor.
2. **The default embedder is lexical.** Paraphrases with no shared tokens
   ("cancel my plan" / "I want to unsubscribe") won't match, and polarity is
   invisible to it. Precision-first thresholds make this safe but cap recall;
   production deployments should plug in a semantic embedder (one protocol
   method). The 0.35 threshold is calibrated to the default embedder only —
   swapping embedders means recalibrating.
3. **Conflict surfacing ≠ contradiction detection.** Neighbors are surfaced;
   the human judges polarity. By design (the human is present at write time).
4. **First-credit-wins ledger.** A correcting re-review does not retract an
   already-recorded exposure credit; full evaluation history is retained so
   credits can be recomputed offline if needed.

## 7. Open questions

- **Q1** — Cross-agent transfer: can guidelines validated for one agent seed
  candidates for a sibling agent (Engram Q7, calibrated gate)?
- **Q2** — Operator authority: should override weight depend on operator role,
  recency, or per-operator historical accuracy?
- **Q3** — Staleness: what decay schedule should re-open validated guidelines
  for re-measurement when the underlying model or policy changes (config-hash
  invalidation vs. time-based)?
- **Q4** — Cluster consolidation: when a cluster accumulates many validated
  guidelines, should an LLM distill them into one canonical guideline, and does
  the distilled form inherit the originals' validation evidence or restart as a
  candidate?
- **Q5** — Causal attribution: inject candidates into only a fraction of
  matching requests (hold-out control), turning correlational win rates into a
  measured lift. What fraction balances statistical power against withholding
  known-good guidance from live traffic?
