from conftest import add_guideline
from humanvals import Budget, HumanVals


def test_budget_max_items(tmp_path) -> None:  # type: ignore[no-untyped-def]
    hv = HumanVals(':memory:', budget=Budget(max_items=2, max_chars=2000))
    for i in range(4):
        add_guideline(hv, f'refund my order number {i}', f'Refund rule number {i} for orders')
    gs = hv.guidelines('refund my order number 9', agent='bot')
    assert len(gs.items) <= 2


def test_budget_max_chars(tmp_path) -> None:  # type: ignore[no-untyped-def]
    hv = HumanVals(':memory:', budget=Budget(max_items=10, max_chars=120))
    for i in range(4):
        add_guideline(
            hv,
            f'refund my order number {i}',
            f'Refund rule number {i}: always double check the order status before refunding',
        )
    gs = hv.guidelines('refund my order number 9', agent='bot')
    assert 0 < len(gs.as_prompt()) <= 400  # header + <=120 chars of guideline text


def test_prompt_renders_provisional_vs_validated(hv: HumanVals) -> None:
    add_guideline(hv, 'refund my order today', 'Always link the refund policy')
    prompt = hv.guidelines('refund my order now', agent='bot').as_prompt()
    assert 'provisional' in prompt.lower()
    assert 'Always link the refund policy' in prompt


def test_empty_prompt_is_empty_string(hv: HumanVals) -> None:
    assert hv.guidelines('anything at all', agent='bot').as_prompt() == ''


def test_validated_ranked_above_candidate(hv: HumanVals) -> None:
    from humanvals import Evaluation

    a = add_guideline(hv, 'refund my order please', 'Rule A about refund orders')
    b = add_guideline(hv, 'refund my order please', 'Rule B about refund orders')
    # win evidence for b only, then promote
    for _ in range(5):
        gs = hv.guidelines('refund my order please', agent='bot')
        case_id = hv.record_case(agent='bot', input='refund my order please',
                                 output='ok', guidelines=gs)
        hv.evaluate(Evaluation(case_id=case_id, intent_ok=True, output_ok=True,
                               context_ok=True, reviewer='ali'))
    hv.run_promotions()
    statuses = {g.id: g.status for g in hv.list_guidelines()}
    if statuses[b] == 'validated' or statuses[a] == 'validated':
        gs = hv.guidelines('refund my order please', agent='bot')
        assert gs.items[0].status == 'validated'
    else:  # pragma: no cover - guard
        raise AssertionError('expected at least one promotion')
