"""HumanVals facade — the two-call integration surface (RFC §5)."""

from __future__ import annotations

import time

from humanvals import curation, retrieval
from humanvals.embedding import Embedder, HashedNgramEmbedder
from humanvals.metrics import Metrics
from humanvals.models import (
    Budget,
    Case,
    EvalResult,
    Evaluation,
    Guideline,
    GuidelineSet,
    Metadata,
    PromotionPolicy,
    new_id,
)
from humanvals.promotion import PromotionChange, run_promotions
from humanvals.store import SQLiteStore

DEFAULT_NS = 'default'


class HumanVals:
    def __init__(self, db: str = 'humanvals.db', *, policy: PromotionPolicy | None = None,
                 embedder: Embedder | None = None, budget: Budget | None = None) -> None:
        self.store = SQLiteStore(db)
        self.policy = policy or PromotionPolicy()
        self.embedder = embedder or HashedNgramEmbedder()
        self.budget = budget or Budget()
        self.metrics = Metrics(self.store)

    # -- agent request path --------------------------------------------------

    def guidelines(self, input: str, *, agent: str,
                   namespace: str = DEFAULT_NS) -> GuidelineSet:
        return retrieval.select_guidelines(self.store, self.embedder, input,
                                           agent, namespace, self.budget)

    def record_case(self, *, agent: str, input: str, output: str,
                    metadata: Metadata | None = None,
                    guidelines: GuidelineSet | None = None,
                    namespace: str = DEFAULT_NS) -> str:
        case = Case(id=new_id(), agent=agent, namespace=namespace, input=input,
                    output=output, metadata=metadata or {},
                    guidelines_injected=guidelines.ids if guidelines else [],
                    created_at=time.time())
        self.store.add_case(case)
        return case.id

    # -- review path ---------------------------------------------------------

    def get_case(self, case_id: str) -> Case:
        return self.store.get_case(case_id)

    def list_cases(self, agent: str | None = None,
                   unreviewed_only: bool = False) -> list[Case]:
        return self.store.list_cases(agent, unreviewed_only)

    def check_conflicts(self, guideline_text: str, *, agent: str,
                        namespace: str = DEFAULT_NS) -> list[Guideline]:
        return curation.find_conflicts(self.store, self.embedder, guideline_text,
                                       agent, namespace)

    def evaluate(self, ev: Evaluation, resolution: str = 'add',
                 target_guideline_id: str | None = None) -> EvalResult:
        if ev.guideline_text:
            curation.validate_resolution(resolution, target_guideline_id, ev)
        case = self.store.get_case(ev.case_id)
        evaluation_id = self.store.add_evaluation(ev)
        self.store.mark_reviewed(ev.case_id)
        for gid in case.guidelines_injected:
            self.store.credit_exposure(case.id, gid, win=ev.output_ok)
        guideline_id = None
        if ev.guideline_text:
            guideline_id = curation.apply_resolution(self.store, self.embedder, ev,
                                                     resolution, target_guideline_id)
        return EvalResult(evaluation_id=evaluation_id, guideline_id=guideline_id)

    # -- lifecycle -----------------------------------------------------------

    def run_promotions(self) -> list[PromotionChange]:
        return run_promotions(self.store, self.policy)

    def list_guidelines(self, agent: str | None = None,
                        status: str | None = None) -> list[Guideline]:
        return self.store.list_guidelines(agent=agent, status=status)
