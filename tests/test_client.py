from humanvals import Evaluation, HumanVals


def test_cold_start_returns_empty_set(hv: HumanVals) -> None:
    gs = hv.guidelines('how do I get a refund?', agent='bot')
    assert gs.items == []
    assert gs.as_prompt() == ''
    assert gs.ids == []


def test_record_case_persists_exposure_log(hv: HumanVals) -> None:
    gs = hv.guidelines('hello', agent='bot')
    case_id = hv.record_case(agent='bot', input='hello', output='hi', guidelines=gs)
    case = hv.get_case(case_id)
    assert case.guidelines_injected == []
    assert case.input == 'hello'
    assert case.agent == 'bot'


def test_record_case_without_guidelines_set_defaults_to_empty_log(hv: HumanVals) -> None:
    case_id = hv.record_case(agent='bot', input='x', output='y')
    assert hv.get_case(case_id).guidelines_injected == []


def test_metadata_roundtrip(hv: HumanVals) -> None:
    meta = {'thought_chain': ['a', 'b'], 'tool_calls': [{'name': 't'}], 'context': 'ctx'}
    case_id = hv.record_case(agent='bot', input='x', output='y', metadata=meta)
    assert hv.get_case(case_id).metadata == meta


def test_evaluate_with_guideline_creates_candidate(hv: HumanVals) -> None:
    case_id = hv.record_case(agent='bot', input='refund for order 12', output='no')
    result = hv.evaluate(
        Evaluation(
            case_id=case_id,
            intent_ok=True,
            output_ok=False,
            context_ok=True,
            guideline_text='Always offer a refund link for refund requests',
            reviewer='ali',
        )
    )
    assert result.guideline_id is not None
    g = hv.list_guidelines(agent='bot')[0]
    assert g.status == 'candidate'
    assert g.origin == 'stated'
    assert g.source_case_id == case_id


def test_evaluate_without_guideline_creates_none(hv: HumanVals) -> None:
    case_id = hv.record_case(agent='bot', input='x', output='y')
    result = hv.evaluate(
        Evaluation(case_id=case_id, intent_ok=True, output_ok=True, context_ok=True,
                   reviewer='ali')
    )
    assert result.guideline_id is None
    assert hv.list_guidelines() == []


def test_list_cases_unreviewed_only(hv: HumanVals) -> None:
    a = hv.record_case(agent='bot', input='a', output='1')
    hv.record_case(agent='bot', input='b', output='2')
    hv.evaluate(Evaluation(case_id=a, intent_ok=True, output_ok=True, context_ok=True,
                           reviewer='ali'))
    unreviewed = hv.list_cases(unreviewed_only=True)
    assert [c.input for c in unreviewed] == ['b']
    assert len(hv.list_cases()) == 2
