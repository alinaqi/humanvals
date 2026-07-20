"""CrewAI + humanvals: guidelines woven into the task description.

Runs with NO API keys — a custom BaseLLM stand-in answers deterministically;
swap `OfflineLLM` for e.g. LLM(model='anthropic/claude-sonnet-5') in production.

    uv run python examples/crewai_agent.py
"""

from __future__ import annotations

from typing import Any

from crewai import Agent, BaseLLM, Crew, Task
from scenario import REQUESTS, operator_reviews_first_case, print_case

from humanvals import HumanVals

hv = HumanVals(':memory:')
AGENT = 'crewai-support'


class OfflineLLM(BaseLLM):
    """Deterministic 'LLM': follows the refund guideline iff present in the prompt."""

    def call(self, messages: str | list[Any], **kwargs: Any) -> str:
        text = messages if isinstance(messages, str) else str(messages)
        if 'refund policy link' in text:
            return ('So sorry! Confirming your order number — refund incoming. '
                    'Policy: https://example.com/refunds')
        return 'Refund processed.'

    def supports_function_calling(self) -> bool:
        return False


def run_case(request: str) -> str:
    gs = hv.guidelines(request, agent=AGENT)
    agent = Agent(role='Support agent', goal='Resolve customer requests well',
                  backstory='Handles refunds and order issues.',
                  llm=OfflineLLM(model='offline-demo'), verbose=False)
    task = Task(description=f'{gs.as_prompt()}\nCustomer request: {request}',
                expected_output='A helpful reply to the customer', agent=agent)
    output = str(Crew(agents=[agent], tasks=[task], verbose=False).kickoff())
    case_id = hv.record_case(
        agent=AGENT, input=request, output=output,
        metadata={'thought_chain': ['crew kickoff'], 'tool_calls': [],
                  'context': 'crewai demo'},
        guidelines=gs)
    print_case('crewai', gs.as_prompt(), output)
    return case_id


def main() -> None:
    first = run_case(REQUESTS[0])               # cold start: no guidelines
    operator_reviews_first_case(hv, first)      # operator adds one
    for request in REQUESTS[1:]:
        run_case(request)                       # guideline now injected

    assert len(hv.list_cases()) == 3
    assert len(hv.list_guidelines()) == 1
    print('\nOK: crewai example recorded 3 cases, 1 guideline learned & injected')


if __name__ == '__main__':
    main()
