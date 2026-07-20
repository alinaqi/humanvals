from conftest import add_guideline
from humanvals import HumanVals


def test_same_intent_retrieves_guideline(hv: HumanVals) -> None:
    gid = add_guideline(
        hv,
        'I want a refund for my order #123',
        'Always include the refund policy link when handling refund requests',
    )
    gs = hv.guidelines('can I get a refund for order #999?', agent='bot')
    assert gid in gs.ids


def test_unrelated_intent_returns_nothing(hv: HumanVals) -> None:
    add_guideline(
        hv,
        'I want a refund for my order #123',
        'Always include the refund policy link when handling refund requests',
    )
    gs = hv.guidelines('what is the weather like in Berlin today?', agent='bot')
    assert gs.items == []


def test_agent_isolation(hv: HumanVals) -> None:
    gid = add_guideline(hv, 'refund my order please', 'Offer the refund form', agent='support')
    gs = hv.guidelines('refund my order please', agent='sales')
    assert gid not in gs.ids


def test_namespace_isolation(hv: HumanVals) -> None:
    from humanvals import Evaluation

    gs0 = hv.guidelines('refund my order', agent='bot', namespace='acme')
    case_id = hv.record_case(
        agent='bot', input='refund my order', output='no', guidelines=gs0, namespace='acme'
    )
    hv.evaluate(
        Evaluation(case_id=case_id, intent_ok=True, output_ok=False, context_ok=True,
                   guideline_text='Be formal with refunds', reviewer='ali')
    )
    same_ns = hv.guidelines('refund my order', agent='bot', namespace='acme')
    other_ns = hv.guidelines('refund my order', agent='bot', namespace='globex')
    assert len(same_ns.items) == 1
    assert other_ns.items == []


def test_superseded_guidelines_not_retrieved(hv: HumanVals) -> None:
    from humanvals import Evaluation

    old = add_guideline(hv, 'refund my order', 'Refunds need manager approval')
    case_id = hv.record_case(agent='bot', input='refund this order', output='x')
    hv.evaluate(
        Evaluation(case_id=case_id, intent_ok=True, output_ok=False, context_ok=True,
                   guideline_text='Refunds are self-serve, no approval needed',
                   reviewer='ali'),
        resolution='override',
        target_guideline_id=old,
    )
    gs = hv.guidelines('please refund my order', agent='bot')
    assert old not in gs.ids
    assert len(gs.ids) == 1
