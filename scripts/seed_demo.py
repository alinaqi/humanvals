"""Seed a demo database that shows the full humanvals story:
cold start -> operator guideline -> injection -> promotion -> declining
intervention rate. Uses a real LLM via OPENAI_BASE_URL if set (srooter/any
OpenAI-compatible gateway); falls back to canned outputs offline.

    uv run python scripts/seed_demo.py demo.db
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

from humanvals import Evaluation, HumanVals

GUIDELINE = ('For refund requests: apologize briefly, confirm the order number, '
             'and always include the refund policy link https://example.com/refunds')

EARLY = [  # cold start — outputs reviewed as needing correction
    'I want a refund for my order #4411, it arrived broken',
    'Please refund my order #9903, it arrived in the wrong size',
    'Can you refund my order #1177? It never arrived',
    'Refund my order #8080 please, wrong colour delivered',
    'I need a refund on order #3355, item stopped working',
    'Requesting a refund for order #7742, packaging was damaged',
]
LATER = [  # guideline injected — outputs pass review
    'Please refund my order #2210, it arrived scratched',
    'I want a refund for order #6591, it arrived faulty',
    'Refund for my order #4478 please, it arrived late and broken',
    'Can I get a refund on my order #9134? It arrived defective',
    'I would like a refund for order #5520, it arrived cracked',
    'Refund my order #7008, the item arrived dead on arrival',
]
UNREVIEWED = [  # left for the Review queue screenshot
    'My order #6402 arrived with a missing part, refund please',
    'I want to return order #1812 for a refund, it arrived bent',
    'Order #9977 needs a refund, the screen arrived shattered',
]


def llm(system: str, user: str) -> str | None:
    if 'OPENAI_BASE_URL' not in os.environ:
        return None
    try:
        base = os.environ['OPENAI_BASE_URL'].rstrip('/')
        req = urllib.request.Request(
            f'{base}/chat/completions',
            data=json.dumps({'model': os.environ.get('HUMANVALS_MODEL', 'glm-5.2'),
                             'messages': [{'role': 'system', 'content': system},
                                          {'role': 'user', 'content': user}],
                             'max_tokens': 2000}).encode(),
            headers={'Authorization': f'Bearer {os.environ["OPENAI_API_KEY"]}',
                     'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=90) as resp:
            content: str = json.load(resp)['choices'][0]['message']['content']
        return content.strip()
    except Exception as exc:  # noqa: BLE001 - seed must not die on gateway hiccups
        print(f'  (gateway unavailable, canned output: {exc})', file=sys.stderr)
        return None


def generate(hv: HumanVals, request: str, live: bool) -> tuple[str, object]:
    gs = hv.guidelines(request, agent='support-bot')
    system = ('You are a concise customer support agent. Reply in at most 3 sentences.\n'
              + gs.as_prompt())
    output = (llm(system, request) if live else None) or (
        'So sorry about that! Confirming your order number now — your refund is on '
        'the way. Policy: https://example.com/refunds'
        if gs.ids else 'Refund processed.')
    case_id = hv.record_case(
        agent='support-bot', input=request, output=output,
        metadata={'thought_chain': ['classify: refund request', 'draft reply'],
                  'tool_calls': [{'name': 'orders.lookup'}], 'context': system[:200]},
        guidelines=gs)
    return case_id, gs


def review(hv: HumanVals, case_id: str, ok: bool, guideline: str = '',
           applies_when: str = '') -> None:
    hv.evaluate(Evaluation(case_id=case_id, intent_ok=True, output_ok=ok,
                           context_ok=ok, guideline_text=guideline,
                           applies_when=applies_when, reviewer='ali'))


def main() -> None:
    db = sys.argv[1] if len(sys.argv) > 1 else 'demo.db'
    if os.path.exists(db):
        os.remove(db)
    hv = HumanVals(db)
    live = 'OPENAI_BASE_URL' in os.environ

    # Bad era: no guidelines exist yet; every review is a correction. The
    # operator leaves the guideline on the LAST bad case (so no earlier case
    # has it injected — exposures must reflect what was actually in prompts).
    early_ids = [generate(hv, request, live=False)[0] for request in EARLY]
    for case_id in early_ids[:-1]:
        review(hv, case_id, ok=False)
    review(hv, early_ids[-1], ok=False, guideline=GUIDELINE,
           applies_when='refund requests')

    for request in LATER:
        case_id, gs = generate(hv, request, live)
        review(hv, case_id, ok=True)

    changes = hv.run_promotions()
    for request in UNREVIEWED:
        generate(hv, request, live)

    s = hv.metrics.summary()
    print(f'seeded {db}: {s["cases"]} cases, guidelines={s["guidelines"]}, '
          f'promotions={changes}, '
          f'intervention series={hv.metrics.intervention_rate().series}')


if __name__ == '__main__':
    main()
