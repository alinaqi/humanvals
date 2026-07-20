"""Core domain model. See docs/adr/0002-domain-model.md."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

Metadata = dict[str, Any]


def new_id() -> str:
    return uuid.uuid4().hex[:12]


@dataclass
class Case:
    id: str
    agent: str
    namespace: str
    input: str
    output: str
    metadata: Metadata
    guidelines_injected: list[str]
    created_at: float
    reviewed: bool = False


@dataclass
class Evaluation:
    """Operator review of one case — the 4 dimensions (RFC §3.2)."""

    case_id: str
    intent_ok: bool
    output_ok: bool
    context_ok: bool
    reviewer: str
    notes: str = ''
    guideline_text: str = ''
    applies_when: str = ''


@dataclass
class Guideline:
    id: str
    agent: str
    namespace: str
    intent_text: str
    text: str
    applies_when: str
    origin: str  # stated | validated
    status: str  # candidate | validated | superseded | rejected
    exposures: int = 0
    wins: int = 0
    validation_count: int = 0
    superseded_by: str | None = None
    source_case_id: str | None = None
    created_at: float = 0.0
    promoted_at: float | None = None


@dataclass
class GuidelineSet:
    """Budgeted retrieval result. Empty set renders '' (ADR-0005)."""

    items: list[Guideline] = field(default_factory=list)

    @property
    def ids(self) -> list[str]:
        return [g.id for g in self.items]

    def as_prompt(self) -> str:
        validated = [g for g in self.items if g.status == 'validated']
        candidates = [g for g in self.items if g.status != 'validated']
        parts: list[str] = []
        if validated:
            parts.append('Operator guidance — follow these instructions:')
            parts.extend(_bullet(g) for g in validated)
        if candidates:
            parts.append('Provisional operator guidance (not yet validated — apply with judgment):')
            parts.extend(_bullet(g) for g in candidates)
        return '\n'.join(parts)


def _bullet(g: Guideline) -> str:
    suffix = f' (applies when: {g.applies_when})' if g.applies_when else ''
    return f'- {g.text}{suffix}'


@dataclass
class Budget:
    """Anti-pollution invariant (ADR-0005)."""

    max_items: int = 5
    max_chars: int = 2000


@dataclass
class PromotionPolicy:
    """Wilson-bound thresholds (ADR-0006)."""

    min_exposures: int = 5
    promote_threshold: float = 0.55
    demote_threshold: float = 0.40


@dataclass
class EvalResult:
    evaluation_id: str
    guideline_id: str | None
