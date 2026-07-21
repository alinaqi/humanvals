"""Seed a deployed humanvals instance over its REST API (same story as
seed_demo.py: bad era -> guideline -> injection -> promotion).

    uv run python scripts/seed_remote.py https://humanvals.onrender.com
"""

from __future__ import annotations

import json
import sys
import urllib.request

from seed_demo import EARLY, GUIDELINE, LATER, UNREVIEWED, llm

AGENT = 'support-bot'
CANNED_BAD = 'Refund processed.'
CANNED_GOOD = ('So sorry about that! Confirming your order number now — your refund '
               'is on the way. Policy: https://example.com/refunds')


def call(base: str, method: str, path: str, body: dict | None = None) -> dict | list:
    req = urllib.request.Request(
        f'{base}{path}', method=method,
        data=None if body is None else json.dumps(body).encode(),
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data: dict | list = json.load(resp)
    return data


def record(base: str, text: str, output: str, guideline_ids: list[str]) -> str:
    result = call(base, 'POST', '/api/cases', {
        'agent': AGENT, 'input': text, 'output': output,
        'metadata': {'thought_chain': ['classify: refund request', 'draft reply'],
                     'tool_calls': [{'name': 'orders.lookup'}], 'context': 'seeded demo'},
        'guideline_ids': guideline_ids})
    assert isinstance(result, dict)
    return str(result['case_id'])


def evaluate(base: str, case_id: str, ok: bool, **extra: object) -> None:
    call(base, 'POST', f'/api/cases/{case_id}/evaluate', {
        'intent_ok': True, 'output_ok': ok, 'context_ok': ok,
        'reviewer': 'ali', **extra})


def query_ids(base: str, text: str) -> tuple[list[str], str]:
    from urllib.parse import quote
    result = call(base, 'GET', f'/api/guidelines/query?input={quote(text)}&agent={AGENT}')
    assert isinstance(result, dict)
    return list(result['ids']), str(result['prompt'])


def main() -> None:
    base = sys.argv[1].rstrip('/')
    first = record(base, EARLY[0], CANNED_BAD, [])
    evaluate(base, first, ok=False, tool_ok=False,
             expected_tool_call='orders.lookup(order_id) before replying')
    for text in EARLY[1:-1]:
        evaluate(base, record(base, text, CANNED_BAD, []), ok=False)
    evaluate(base, record(base, EARLY[-1], CANNED_BAD, []), ok=False,
             guideline_text=GUIDELINE, applies_when='refund requests')

    for text in LATER:
        ids, prompt = query_ids(base, text)
        output = llm('You are a concise support agent.\n' + prompt, text) or CANNED_GOOD
        evaluate(base, record(base, text, output, ids), ok=True)

    changes = call(base, 'POST', '/api/promotions/run')
    for text in UNREVIEWED:
        ids, prompt = query_ids(base, text)
        output = llm('You are a concise support agent.\n' + prompt, text) or CANNED_GOOD
        record(base, text, output, ids)

    print('promotions:', changes)
    print('summary:', call(base, 'GET', '/api/summary'))


if __name__ == '__main__':
    main()
