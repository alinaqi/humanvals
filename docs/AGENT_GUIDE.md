# humanvals — Integration Guide for AI Agents

You are an AI coding agent integrating the `humanvals` library into an
application. This document is complete: you do not need to read the source.

## What it does

Collects human-operator feedback on agent outputs, turns it into retrievable
prompt guidelines, measures each guideline's impact via exposure logging, and
promotes verified guidelines. One class (`HumanVals`) is the whole API.

## Install

```bash
pip install humanvals              # core, zero dependencies
pip install 'humanvals[server]'    # optional FastAPI review server
```

Python ≥ 3.10. Storage is a single SQLite file; `':memory:'` works for tests.

## The integration contract (do exactly this)

There are exactly two required calls in the agent's request path, and one rule:

```python
from humanvals import HumanVals

hv = HumanVals('humanvals.db')          # create ONCE per process, reuse

def handle_request(user_input: str) -> str:
    # CALL 1 — before generation. Returns a GuidelineSet; empty at cold start.
    gs = hv.guidelines(user_input, agent='AGENT_NAME')

    # Append gs.as_prompt() to the system prompt / instructions.
    # It returns '' when empty — no branching needed.
    prompt = BASE_SYSTEM_PROMPT + '\n' + gs.as_prompt()

    output = run_llm(prompt, user_input)

    # CALL 2 — after generation. RULE: pass the SAME GuidelineSet you injected.
    # This writes the exposure log; without it, measurement is impossible.
    hv.record_case(agent='AGENT_NAME', input=user_input, output=output,
                   metadata={'thought_chain': [...],   # optional but valuable
                             'tool_calls': [...],      # for the human reviewer
                             'context': '...'},
                   guidelines=gs)
    return output
```

- `agent` scopes guidelines: use one stable name per agent.
- `namespace='tenant-x'` (optional kwarg on both calls) isolates tenants/brands.
- Never inject guidelines you did not pass to `record_case` — the exposure log
  must reflect what was actually in the prompt.

## Review flow (usually via the bundled dashboard)

```python
from humanvals import Evaluation

for case in hv.list_cases(unreviewed_only=True):
    result = hv.evaluate(Evaluation(
        case_id=case.id,
        intent_ok=True,        # did the agent understand the ask?
        output_ok=False,       # is the output correct? (this is the win/loss signal)
        context_ok=True,       # did it use the right context?
        guideline_text='Always include the refund policy link',  # optional
        applies_when='refund requests',                          # scope, optional
        reviewer='ali'))
```

Before saving a guideline, surface similar existing ones:

```python
conflicts = hv.check_conflicts('Refunds are self-serve', agent='AGENT_NAME')
# then choose a resolution:
hv.evaluate(ev, resolution='reinforce', target_guideline_id=g.id)  # no sibling; +1 strength
hv.evaluate(ev, resolution='override',  target_guideline_id=g.id)  # supersedes old one
hv.evaluate(ev, resolution='scope_both', target_guideline_id=g.id) # needs ev.applies_when
# default: resolution='add'
```

`ValueError` is raised for invalid resolutions (e.g. `scope_both` without
`applies_when`); `KeyError` for unknown case ids.

## Lifecycle

```python
changes = hv.run_promotions()
# [(guideline_id, 'candidate', 'validated'), ...] — call periodically (cron/endpoint)
```

Promotion: Wilson 95% lower bound of win-rate ≥ 0.55 over ≥ 5 evaluated
exposures (defaults; `PromotionPolicy(min_exposures=, promote_threshold=,
demote_threshold=)`). Wins = evaluations with `output_ok=True` on cases where
the guideline was injected. Promotion resets the evidence window.

## Metrics

```python
hv.metrics.summary()                    # dict: cases, unreviewed, guidelines by status
hv.metrics.intervention_rate('AGENT_NAME')  # .overall, .series (declining = learning), .n
hv.metrics.guideline_impact(gid)        # .exposures, .wins, .wilson_low, .wilson_high
```

## Review server + dashboard

```bash
uvicorn humanvals.server.app:create_app --factory    # :8000, HUMANVALS_DB env var
```

REST: `GET /api/summary`, `GET/POST /api/cases`, `POST /api/cases/{id}/evaluate`,
`POST /api/conflicts`, `GET /api/guidelines`, `GET /api/guidelines/query?input=&agent=`
(remote retrieval for non-Python agents), `POST /api/promotions/run`,
`GET /api/metrics/intervention`. The React dashboard is served at `/` when built.

## Customization points (protocols, not subclassing)

```python
class MyEmbedder:                        # semantic upgrade — recommended for prod
    def embed(self, text: str) -> list[float]: ...
hv = HumanVals('db.sqlite', embedder=MyEmbedder())

from humanvals import Budget
hv = HumanVals('db.sqlite', budget=Budget(max_items=3, max_chars=1200))
```

Default embedder is lexical (hashed n-grams): deterministic and offline, but
paraphrases without shared tokens won't match. If users report guidelines not
firing, that is why — plug in a real embedding model.

## Pitfalls

1. Forgetting `guidelines=gs` in `record_case` → exposure log empty → nothing
   ever promotes. This is the #1 integration bug.
2. Creating `HumanVals` per request → connection churn. Create once.
3. Different `agent` strings between the two calls → guidelines never retrieved.
4. Calling `hv.guidelines()` a second time instead of reusing `gs` → the second
   retrieval may differ from what was actually injected.
