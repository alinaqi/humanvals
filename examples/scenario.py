"""Shared demo scenario for the three framework examples.

A small support-agent storyline that shows the full humanvals loop without any
API keys: run cases, review them (as an operator would in the dashboard),
watch the guideline get injected on the next run.
"""

from __future__ import annotations

from humanvals import Evaluation, HumanVals

# Lexically-related phrasings on purpose: the default embedder is a lexical
# proxy (RFC §6.2) — swap in a semantic embedder for paraphrase recall.
REQUESTS = [
    'I want a refund for my order #4411, it arrived broken',
    'Please refund my order #9903, it arrived in the wrong size',
    'Can you refund my order #1177? It never arrived',
]

GUIDELINE = ('For refund requests: apologize, confirm the order number, and '
             'always include the refund policy link https://example.com/refunds')


def operator_reviews_first_case(hv: HumanVals, case_id: str) -> str:
    """Simulates the dashboard review: output was wrong, operator leaves a guideline."""
    result = hv.evaluate(Evaluation(
        case_id=case_id, intent_ok=True, output_ok=False, context_ok=True,
        guideline_text=GUIDELINE, applies_when='refund requests',
        reviewer='demo-operator'))
    assert result.guideline_id is not None
    return result.guideline_id


def print_case(title: str, prompt_extra: str, output: str) -> None:
    print(f'\n--- {title} ---')
    print(f'guidelines injected: {"yes" if prompt_extra else "no (cold start)"}')
    if prompt_extra:
        print(f'  {prompt_extra.splitlines()[-1]}')
    print(f'agent output: {output[:120]}')
