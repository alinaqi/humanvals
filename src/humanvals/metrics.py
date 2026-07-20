"""Observability: intervention rate (the product's success metric, RFC §3.6),
guideline impact, dashboard summary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from humanvals.promotion import wilson_lower, wilson_upper
from humanvals.store import SQLiteStore

MAX_BUCKETS = 6


@dataclass
class InterventionReport:
    overall: float
    series: list[float]  # chronological bucket rates; declining = agent is learning
    n: int


@dataclass
class GuidelineImpact:
    guideline_id: str
    exposures: int
    wins: int
    wilson_low: float
    wilson_high: float
    status: str


class Metrics:
    def __init__(self, store: SQLiteStore) -> None:
        self._store = store

    def intervention_rate(self, agent: str | None = None) -> InterventionReport:
        flags = [not bool(row['output_ok']) for row in self._store.list_evaluations(agent)]
        n = len(flags)
        if n == 0:
            return InterventionReport(overall=0.0, series=[], n=0)
        overall = sum(flags) / n
        return InterventionReport(overall=overall, series=_bucket_rates(flags), n=n)

    def guideline_impact(self, guideline_id: str) -> GuidelineImpact:
        g = self._store.get_guideline(guideline_id)
        return GuidelineImpact(guideline_id=g.id, exposures=g.exposures, wins=g.wins,
                               wilson_low=wilson_lower(g.wins, g.exposures),
                               wilson_high=wilson_upper(g.wins, g.exposures),
                               status=g.status)

    def summary(self) -> dict[str, Any]:
        cases = self._store.list_cases(agent=None, unreviewed_only=False)
        by_status: dict[str, int] = {}
        for g in self._store.list_guidelines():
            by_status[g.status] = by_status.get(g.status, 0) + 1
        return {
            'cases': len(cases),
            'unreviewed': sum(1 for c in cases if not c.reviewed),
            'guidelines': by_status,
            'intervention_rate': self.intervention_rate().overall,
        }


def _bucket_rates(flags: list[bool]) -> list[float]:
    n = len(flags)
    buckets = min(MAX_BUCKETS, n)
    size = n // buckets
    rates = []
    for i in range(buckets):
        chunk = flags[i * size:(i + 1) * size if i < buckets - 1 else n]
        rates.append(sum(chunk) / len(chunk))
    return rates
