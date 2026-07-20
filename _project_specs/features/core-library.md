# Feature Spec — Core Library

Public API (everything importable from `humanvals`):

```python
hv = HumanVals(db="humanvals.db", policy=PromotionPolicy(), embedder=None,
               budget=Budget())          # embedder=None -> HashedNgramEmbedder

# retrieval (agent request path)
gs: GuidelineSet = hv.guidelines(input_text, agent="bot", namespace="default")
gs.items            # list[Guideline], budgeted, ranked
gs.as_prompt()      # str, '' when empty
gs.ids              # list[str]

# capture (exposure-logged)
case_id: str = hv.record_case(agent="bot", input=..., output=...,
                              metadata={...}, guidelines=gs, namespace="default")

# review path
case = hv.get_case(case_id); hv.list_cases(agent=None, unreviewed_only=False)
conflicts = hv.check_conflicts(guideline_text, agent="bot", namespace="default")
ev_result = hv.evaluate(Evaluation(case_id=..., intent_ok=True, output_ok=False,
                        context_ok=True, guideline_text="...", applies_when="...",
                        reviewer="ali"), resolution="add", target_guideline_id=None)
# resolution: add | reinforce | override | scope_both (ADR-0007)

# lifecycle
changes = hv.run_promotions()          # list[(guideline_id, from_status, to_status)]
hv.list_guidelines(agent=None, status=None)

# metrics
hv.metrics.intervention_rate(agent="bot")        # overall + per intent cluster series
hv.metrics.guideline_impact(guideline_id)        # exposures, wins, wilson bounds
hv.metrics.summary()                             # counts for dashboard tiles
```

## Acceptance criteria / test cases

| # | Behaviour | Test |
|---|---|---|
| 1 | Cold start: guidelines() returns empty set, as_prompt()=='' | test_client |
| 2 | record_case persists exposure log (empty list ok, never None) | test_client |
| 3 | evaluate with guideline_text creates candidate guideline w/ intent_key | test_client |
| 4 | Same-intent input retrieves the guideline; unrelated input does NOT | test_intent |
| 5 | Namespace + agent isolation: no cross-retrieval | test_intent |
| 6 | Budget: max_items and max_chars enforced; validated ranked above candidate | test_injector |
| 7 | Evaluation of a case increments exposures/wins for injected guidelines, idempotent per case | test_promotion |
| 8 | Wilson: 3/3 does NOT promote; 5/5 with defaults DOES; 1/6 demotes | test_promotion |
| 9 | override supersedes (status, superseded_by), never deletes | test_curation |
| 10 | reinforce increments validation_count, creates no sibling | test_curation |
| 11 | scope_both requires applies_when | test_curation |
| 12 | check_conflicts finds similar-intent guidelines only within agent+ns | test_curation |
| 13 | intervention_rate declines in seeded improving scenario | test_metrics |
| 14 | Store roundtrip: all fields survive persistence; :memory: works | test_store |
| 15 | as_prompt renders validated as instructions, candidates as provisional | test_injector |

Coverage >= 80%, ruff clean, mypy --strict clean.
