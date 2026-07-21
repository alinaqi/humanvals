"""Request bodies for the review API (responses are dataclasses serialized as-is)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class CaseIn(BaseModel):
    agent: str
    input: str
    output: str
    metadata: dict[str, Any] = {}
    guideline_ids: list[str] = []
    namespace: str = 'default'


class EvaluationIn(BaseModel):
    intent_ok: bool
    output_ok: bool
    context_ok: bool
    reviewer: str
    tool_ok: bool = True
    expected_tool_call: str = ''
    notes: str = ''
    guideline_text: str = ''
    applies_when: str = ''
    resolution: str = 'add'
    target_guideline_id: str | None = None


class ConflictQuery(BaseModel):
    guideline_text: str
    agent: str
    namespace: str = 'default'
