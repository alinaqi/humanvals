"""Review API — thin REST over the HumanVals library (ADR-0008).

Run: uvicorn humanvals.server.app:create_app --factory
"""

from __future__ import annotations

import dataclasses
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from humanvals import Evaluation, HumanVals
from humanvals.models import Case, GuidelineSet
from humanvals.server.schemas import CaseIn, ConflictQuery, EvaluationIn


def create_app(hv: HumanVals | None = None) -> FastAPI:
    hv = hv or HumanVals(os.environ.get('HUMANVALS_DB', 'humanvals.db'))
    app = FastAPI(title='humanvals', version='0.1.0')
    _register_routes(app, hv)
    _mount_dashboard(app)
    return app


def _register_routes(app: FastAPI, hv: HumanVals) -> None:  # noqa: C901
    @app.get('/api/summary')
    def summary() -> dict[str, Any]:
        return hv.metrics.summary()

    @app.post('/api/cases', status_code=201)
    def record_case(body: CaseIn) -> dict[str, str]:
        gs = GuidelineSet(items=[hv.store.get_guideline(g) for g in body.guideline_ids])
        case_id = hv.record_case(agent=body.agent, input=body.input, output=body.output,
                                 metadata=body.metadata, guidelines=gs,
                                 namespace=body.namespace)
        return {'case_id': case_id}

    @app.get('/api/cases')
    def list_cases(agent: str | None = None, unreviewed_only: bool = False) -> list[Case]:
        return hv.list_cases(agent=agent, unreviewed_only=unreviewed_only)

    @app.get('/api/cases/{case_id}')
    def get_case(case_id: str) -> Case:
        try:
            return hv.get_case(case_id)
        except KeyError as exc:
            raise HTTPException(404, str(exc)) from exc

    @app.post('/api/cases/{case_id}/evaluate')
    def evaluate(case_id: str, body: EvaluationIn) -> dict[str, Any]:
        ev = Evaluation(case_id=case_id, intent_ok=body.intent_ok,
                        output_ok=body.output_ok, context_ok=body.context_ok,
                        tool_ok=body.tool_ok,
                        expected_tool_call=body.expected_tool_call,
                        reviewer=body.reviewer, notes=body.notes,
                        guideline_text=body.guideline_text,
                        applies_when=body.applies_when)
        try:
            result = hv.evaluate(ev, resolution=body.resolution,
                                 target_guideline_id=body.target_guideline_id)
        except KeyError as exc:
            raise HTTPException(404, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return dataclasses.asdict(result)

    @app.get('/api/cases/{case_id}/evaluations')
    def case_evaluations(case_id: str) -> list[dict[str, Any]]:
        rows = hv.store.list_case_evaluations(case_id)
        return [{**dict(r),
                 'intent_ok': bool(r['intent_ok']), 'output_ok': bool(r['output_ok']),
                 'context_ok': bool(r['context_ok']), 'tool_ok': bool(r['tool_ok'])}
                for r in rows]

    @app.post('/api/conflicts')
    def conflicts(body: ConflictQuery) -> list[dict[str, Any]]:
        found = hv.check_conflicts(body.guideline_text, agent=body.agent,
                                   namespace=body.namespace)
        return [dataclasses.asdict(g) for g in found]

    @app.get('/api/guidelines/query')
    def query_guidelines(input: str, agent: str, namespace: str = 'default') -> dict[str, Any]:
        gs = hv.guidelines(input, agent=agent, namespace=namespace)
        return {'guidelines': [dataclasses.asdict(g) for g in gs.items],
                'prompt': gs.as_prompt(), 'ids': gs.ids}

    @app.get('/api/guidelines')
    def list_guidelines(agent: str | None = None,
                        status: str | None = None) -> list[dict[str, Any]]:
        return [dataclasses.asdict(g) for g in hv.list_guidelines(agent=agent, status=status)]

    @app.get('/api/guidelines/{guideline_id}/impact')
    def impact(guideline_id: str) -> dict[str, Any]:
        try:
            return dataclasses.asdict(hv.metrics.guideline_impact(guideline_id))
        except KeyError as exc:
            raise HTTPException(404, str(exc)) from exc

    @app.post('/api/promotions/run')
    def run_promotions() -> dict[str, Any]:
        return {'changes': hv.run_promotions()}

    @app.get('/api/metrics/intervention')
    def intervention(agent: str | None = None) -> dict[str, Any]:
        return dataclasses.asdict(hv.metrics.intervention_rate(agent))


def _mount_dashboard(app: FastAPI) -> None:
    dist = Path(__file__).resolve().parents[3] / 'dashboard' / 'dist'
    if dist.is_dir():
        app.mount('/', StaticFiles(directory=dist, html=True), name='dashboard')
