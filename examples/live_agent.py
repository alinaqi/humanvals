"""Live example: humanvals with a real LLM via any OpenAI-compatible gateway.

Reads standard env vars (works with srooter, LiteLLM, OpenRouter, vLLM, ...):

    OPENAI_BASE_URL   e.g. https://your-gateway/v1
    OPENAI_API_KEY    gateway key
    HUMANVALS_MODEL   default: glm-5.2
    HUMANVALS_DB      default: humanvals.db

    uv run python examples/live_agent.py "refund my order #22, arrived broken"
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

from humanvals import HumanVals

AGENT = 'live-support'
SYSTEM = 'You are a concise customer support agent. Reply in at most 3 sentences.'


def chat(system: str, user: str) -> str:
    base = os.environ['OPENAI_BASE_URL'].rstrip('/')
    req = urllib.request.Request(
        f'{base}/chat/completions',
        data=json.dumps({
            'model': os.environ.get('HUMANVALS_MODEL', 'glm-5.2'),
            'messages': [{'role': 'system', 'content': system},
                         {'role': 'user', 'content': user}],
            'max_tokens': 4000,
        }).encode(),
        headers={'Authorization': f'Bearer {os.environ["OPENAI_API_KEY"]}',
                 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.load(resp)
    content: str = data['choices'][0]['message']['content']
    return content.strip()


def handle(hv: HumanVals, request: str) -> str:
    gs = hv.guidelines(request, agent=AGENT)
    output = chat(SYSTEM + '\n' + gs.as_prompt(), request)
    case_id = hv.record_case(
        agent=AGENT, input=request, output=output,
        metadata={'thought_chain': ['single-shot chat'], 'tool_calls': [],
                  'context': f'model={os.environ.get("HUMANVALS_MODEL", "glm-5.2")}'},
        guidelines=gs)
    print(f'guidelines injected: {len(gs.ids)}  case: {case_id}')
    print(output)
    return case_id


def main() -> None:
    if 'OPENAI_BASE_URL' not in os.environ:
        sys.exit('Set OPENAI_BASE_URL / OPENAI_API_KEY (your gateway), then retry.')
    hv = HumanVals(os.environ.get('HUMANVALS_DB', 'humanvals.db'))
    request = ' '.join(sys.argv[1:]) or 'I want a refund for my order #4411, it arrived broken'
    handle(hv, request)


if __name__ == '__main__':
    main()
