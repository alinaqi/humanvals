import pytest

from humanvals import HumanVals


@pytest.fixture
def hv() -> HumanVals:
    return HumanVals(':memory:')


def make_case(hv: HumanVals, text: str, agent: str = 'bot', output: str = 'ok') -> str:
    gs = hv.guidelines(text, agent=agent)
    return hv.record_case(agent=agent, input=text, output=output, guidelines=gs)


def add_guideline(
    hv: HumanVals,
    case_input: str,
    text: str,
    agent: str = 'bot',
    output_ok: bool = False,
    applies_when: str = '',
) -> str:
    from humanvals import Evaluation

    case_id = make_case(hv, case_input, agent=agent)
    result = hv.evaluate(
        Evaluation(
            case_id=case_id,
            intent_ok=True,
            output_ok=output_ok,
            context_ok=True,
            guideline_text=text,
            applies_when=applies_when,
            reviewer='tester',
        )
    )
    assert result.guideline_id is not None
    return result.guideline_id
