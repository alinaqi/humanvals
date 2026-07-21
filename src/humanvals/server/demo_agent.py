"""Hosted demo support agent — the two-call humanvals pattern, live.

Uses any OpenAI-compatible gateway when OPENAI_BASE_URL/OPENAI_API_KEY are
set (model via HUMANVALS_MODEL, default glm-5.2); falls back to a
deterministic offline responder so the demo never depends on keys.
Mirrors examples/pydantic_ai_agent.py — same integration, hosted.
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
from typing import Any

from humanvals import HumanVals

AGENT = 'support-bot'
SYSTEM = ('You are the demo customer support agent for an online store. '
          'Reply in at most 3 sentences.')
MAX_MESSAGE_CHARS = 2000

# naive per-IP limiter: enough to keep a public demo from burning gateway credit
RATE_LIMIT = 20          # requests
RATE_WINDOW = 60.0       # per seconds
_hits: dict[str, list[float]] = {}


def rate_limited(ip: str) -> bool:
    now = time.time()
    window = [t for t in _hits.get(ip, []) if now - t < RATE_WINDOW]
    window.append(now)
    _hits[ip] = window
    return len(window) > RATE_LIMIT


def offline_reply(message: str, guideline_block: str) -> str:
    if 'refund policy link' in guideline_block:
        return ('So sorry about that! Confirming your order number now — your refund '
                'is on the way. Policy: https://example.com/refunds')
    if 'refund' in message.lower():
        return 'Refund processed.'
    return ('Thanks for reaching out! I can help with orders, refunds and '
            'delivery questions.')


def _gateway_reply(system: str, message: str) -> str | None:
    base = os.environ.get('OPENAI_BASE_URL', '').rstrip('/')
    key = os.environ.get('OPENAI_API_KEY', '')
    if not base or not key:
        return None
    try:
        req = urllib.request.Request(
            f'{base}/chat/completions',
            data=json.dumps({
                'model': os.environ.get('HUMANVALS_MODEL', 'glm-5.2'),
                'messages': [{'role': 'system', 'content': system},
                             {'role': 'user', 'content': message}],
                'max_tokens': 2000,
            }).encode(),
            headers={'Authorization': f'Bearer {key}',
                     'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=60) as resp:
            reply: str = json.load(resp)['choices'][0]['message']['content']
        return reply.strip()
    except Exception:  # noqa: BLE001 - public demo must degrade, not 500
        return None


def chat(hv: HumanVals, message: str) -> dict[str, Any]:
    """The canonical two-call integration (see docs/AGENT_GUIDE.md)."""
    gs = hv.guidelines(message, agent=AGENT)
    guideline_block = gs.as_prompt()
    system = SYSTEM + ('\n' + guideline_block if guideline_block else '')
    model = os.environ.get('HUMANVALS_MODEL', 'glm-5.2')
    reply = _gateway_reply(system, message)
    used_model = model if reply is not None else 'offline-fallback'
    reply = reply or offline_reply(message, guideline_block)
    case_id = hv.record_case(
        agent=AGENT, input=message, output=reply,
        metadata={'thought_chain': ['demo chat, single-shot'],
                  'tool_calls': [], 'context': f'model={used_model}'},
        guidelines=gs)
    return {'reply': reply, 'case_id': case_id, 'guideline_ids': gs.ids,
            'guideline_block': guideline_block, 'model': used_model}
