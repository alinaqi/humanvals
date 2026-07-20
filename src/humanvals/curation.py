"""Write-time curation: conflict detection and resolution (ADR-0007)."""

from __future__ import annotations

import time

from humanvals.embedding import Embedder, cosine
from humanvals.models import Evaluation, Guideline, new_id
from humanvals.store import SQLiteStore

CONFLICT_GATE = 0.25  # lexical embedder scale; 'same neighborhood', not 'same text'
RESOLUTIONS = ('add', 'reinforce', 'override', 'scope_both')


def find_conflicts(store: SQLiteStore, embedder: Embedder, text: str,
                   agent: str, namespace: str) -> list[Guideline]:
    text_vec = embedder.embed(text)
    matches = []
    for g in store.list_guidelines(agent=agent, namespace=namespace):
        if g.status in ('superseded', 'rejected'):
            continue
        sim = max(cosine(text_vec, embedder.embed(g.text)),
                  cosine(text_vec, store.intent_vec(g.id)))
        if sim >= CONFLICT_GATE:
            matches.append(g)
    return matches


def validate_resolution(resolution: str, target: str | None, ev: Evaluation) -> None:
    if resolution not in RESOLUTIONS:
        raise ValueError(f'resolution must be one of {RESOLUTIONS}')
    if resolution == 'scope_both' and not ev.applies_when:
        raise ValueError('applies_when is required for scope_both: state when the new '
                         'guideline applies so both can coexist')
    if resolution != 'add' and target is None:
        raise ValueError(f'target_guideline_id is required for resolution={resolution!r}')


def apply_resolution(store: SQLiteStore, embedder: Embedder, ev: Evaluation,
                     resolution: str, target: str | None) -> str:
    """Returns the id of the guideline that now carries the feedback."""
    if resolution == 'reinforce':
        assert target is not None
        store.reinforce(target)
        return target
    case = store.get_case(ev.case_id)
    new = Guideline(id=new_id(), agent=case.agent, namespace=case.namespace,
                    intent_text=case.input, text=ev.guideline_text,
                    applies_when=ev.applies_when, origin='stated', status='candidate',
                    source_case_id=case.id, created_at=time.time())
    # applies_when is the operator's activation context (Engram): folding it
    # into the intent vector lets the guideline generalize past the one case
    # that spawned it.
    intent_source = f'{case.input} {ev.applies_when}'.strip()
    store.add_guideline(new, embedder.embed(intent_source))
    if resolution == 'override':
        assert target is not None
        store.set_guideline_status(target, status='superseded', superseded_by=new.id)
    return new.id
