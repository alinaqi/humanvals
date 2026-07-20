"""Retrieval + injection budget (ADR-0004, ADR-0005).

Precision-first: conservative similarity gate, empty result over marginal one.
"""

from __future__ import annotations

from humanvals.embedding import Embedder, cosine
from humanvals.models import Budget, Guideline, GuidelineSet
from humanvals.store import SQLiteStore

SIMILARITY_GATE = 0.30  # calibrated for the stopword-filtered default embedder (ADR-0004)
VALIDATED_BONUS = 0.25


def select_guidelines(store: SQLiteStore, embedder: Embedder, query: str,
                      agent: str, namespace: str, budget: Budget) -> GuidelineSet:
    query_vec = embedder.embed(query)
    scored = _score_active(store, query_vec, agent, namespace)
    # Deterministic ranking: score desc, then id — reproducible prompts.
    scored.sort(key=lambda pair: (-pair[0], pair[1].id))
    return GuidelineSet(items=_apply_budget([g for _, g in scored], budget))


def _score_active(store: SQLiteStore, query_vec: list[float], agent: str,
                  namespace: str) -> list[tuple[float, Guideline]]:
    scored = []
    for g in store.list_guidelines(agent=agent, namespace=namespace):
        if g.status not in ('candidate', 'validated'):
            continue
        sim = cosine(query_vec, store.intent_vec(g.id))
        if sim < SIMILARITY_GATE:
            continue
        bonus = VALIDATED_BONUS if g.status == 'validated' else 0.0
        scored.append((sim * (1.0 + bonus), g))
    return scored


def _apply_budget(ranked: list[Guideline], budget: Budget) -> list[Guideline]:
    items: list[Guideline] = []
    chars = 0
    for g in ranked:
        if len(items) >= budget.max_items or chars + len(g.text) > budget.max_chars:
            break
        items.append(g)
        chars += len(g.text)
    return items
