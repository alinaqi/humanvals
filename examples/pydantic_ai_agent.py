"""Pydantic AI + humanvals: guidelines appended to instructions per run.

Runs with NO API keys — uses pydantic-ai's FunctionModel as a deterministic
stand-in; swap for 'anthropic:claude-sonnet-5' (or any model) in production.

    uv run python examples/pydantic_ai_agent.py
"""

from __future__ import annotations

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from scenario import REQUESTS, operator_reviews_first_case, print_case

from humanvals import HumanVals

hv = HumanVals(':memory:')
AGENT = 'pydantic-ai-support'


def support_model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    """Deterministic 'LLM': follows the refund guideline iff it's in instructions."""
    instructions = info.instructions or ''
    if 'refund policy link' in instructions:
        reply = ('So sorry! Confirming your order number now — refund incoming. '
                 'Policy: https://example.com/refunds')
    else:
        reply = 'Refund processed.'
    return ModelResponse(parts=[TextPart(reply)])


def run_case(request: str) -> str:
    gs = hv.guidelines(request, agent=AGENT)
    agent = Agent(FunctionModel(support_model),
                  instructions='You are a support agent.\n' + gs.as_prompt())
    result = agent.run_sync(request)
    case_id = hv.record_case(
        agent=AGENT, input=request, output=result.output,
        metadata={'thought_chain': ['single-shot'], 'tool_calls': [],
                  'context': 'pydantic-ai demo'},
        guidelines=gs)
    print_case('pydantic-ai', gs.as_prompt(), result.output)
    return case_id


def main() -> None:
    first = run_case(REQUESTS[0])               # cold start: no guidelines
    operator_reviews_first_case(hv, first)      # operator adds one
    for request in REQUESTS[1:]:
        run_case(request)                       # guideline now injected

    assert len(hv.list_cases()) == 3
    assert len(hv.list_guidelines()) == 1
    print('\nOK: pydantic-ai example recorded 3 cases, 1 guideline learned & injected')


if __name__ == '__main__':
    main()
