"""Promotion engine: Wilson score bounds over exposure evidence (ADR-0006)."""

from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING

from humanvals.models import PromotionPolicy

if TYPE_CHECKING:
    from humanvals.store import SQLiteStore

Z95 = 1.959963984540054

PromotionChange = tuple[str, str, str]  # (guideline_id, from_status, to_status)


def _wilson(wins: int, n: int, sign: float) -> float:
    if n == 0:
        return 0.0
    p = wins / n
    z2 = Z95 * Z95
    center = p + z2 / (2 * n)
    spread = Z95 * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))
    bound = (center + sign * spread) / (1 + z2 / n)
    return min(1.0, max(0.0, bound))


def wilson_lower(wins: int, n: int) -> float:
    return _wilson(wins, n, -1.0)


def wilson_upper(wins: int, n: int) -> float:
    if n == 0:
        return 1.0
    return _wilson(wins, n, 1.0)


def run_promotions(store: SQLiteStore, policy: PromotionPolicy) -> list[PromotionChange]:
    changes: list[PromotionChange] = []
    for g in store.list_guidelines():
        if g.kind == 'policy':
            continue  # authority tier: never statistically promoted/demoted (ADR-0009)
        if g.exposures < policy.min_exposures:
            continue
        promotable = wilson_lower(g.wins, g.exposures) >= policy.promote_threshold
        if g.status == 'candidate' and promotable:
            # Reset the evidence window: the validated tier must earn its keep
            # on fresh exposures, or demotion could never fire (ADR-0006).
            store.set_guideline_status(g.id, status='validated', origin='validated',
                                       promoted_at=time.time(), reset_evidence=True)
            changes.append((g.id, 'candidate', 'validated'))
        elif (g.status == 'validated'
              and wilson_upper(g.wins, g.exposures) < policy.demote_threshold):
            store.set_guideline_status(g.id, status='candidate')
            changes.append((g.id, 'validated', 'candidate'))
    return changes
