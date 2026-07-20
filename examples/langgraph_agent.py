"""LangGraph + humanvals: guideline retrieval as a graph node.

Runs with NO API keys — the generate node is a deterministic stand-in for an
LLM call; swap `fake_llm` for your model of choice.

    uv run python examples/langgraph_agent.py
"""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from scenario import REQUESTS, operator_reviews_first_case, print_case

from humanvals import HumanVals

hv = HumanVals(':memory:')
AGENT = 'langgraph-support'


class State(TypedDict):
    request: str
    guideline_prompt: str
    guideline_ids: list[str]
    reply: str


def fetch_guidelines(state: State) -> dict[str, object]:
    gs = hv.guidelines(state['request'], agent=AGENT)
    return {'guideline_prompt': gs.as_prompt(), 'guideline_ids': gs.ids}


def fake_llm(system: str, request: str) -> str:
    if 'refund policy link' in system:
        return ('So sorry about that! Confirming your order — refund is on the way. '
                'Policy: https://example.com/refunds')
    return 'Refund processed.'


def generate(state: State) -> dict[str, str]:
    system = 'You are a support agent.\n' + state['guideline_prompt']
    return {'reply': fake_llm(system, state['request'])}


def build_graph() -> StateGraph[State]:
    graph = StateGraph(State)
    graph.add_node('fetch_guidelines', fetch_guidelines)
    graph.add_node('generate', generate)
    graph.add_edge(START, 'fetch_guidelines')
    graph.add_edge('fetch_guidelines', 'generate')
    graph.add_edge('generate', END)
    return graph


def run_case(app: object, request: str) -> str:
    state: State = app.invoke({'request': request})  # type: ignore[attr-defined]
    gs = hv.guidelines(request, agent=AGENT)
    case_id = hv.record_case(
        agent=AGENT, input=request, output=state['reply'],
        metadata={'thought_chain': ['fetch_guidelines', 'generate'],
                  'tool_calls': [], 'context': 'langgraph demo'},
        guidelines=gs)
    print_case('langgraph', state['guideline_prompt'], state['reply'])
    return case_id


def main() -> None:
    app = build_graph().compile()
    first = run_case(app, REQUESTS[0])          # cold start: no guidelines
    operator_reviews_first_case(hv, first)      # operator adds one
    for request in REQUESTS[1:]:
        run_case(app, request)                  # guideline now injected

    assert len(hv.list_cases()) == 3
    assert len(hv.list_guidelines()) == 1
    print('\nOK: langgraph example recorded 3 cases, 1 guideline learned & injected')


if __name__ == '__main__':
    main()
