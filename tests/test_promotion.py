from conftest import add_guideline
from humanvals import Evaluation, HumanVals
from humanvals.promotion import wilson_lower, wilson_upper

INPUT = 'refund my order please'


def expose(hv: HumanVals, output_ok: bool, text: str = INPUT) -> str:
    gs = hv.guidelines(text, agent='bot')
    case_id = hv.record_case(agent='bot', input=text, output='out', guidelines=gs)
    hv.evaluate(Evaluation(case_id=case_id, intent_ok=True, output_ok=output_ok,
                           context_ok=True, reviewer='ali'))
    return case_id


def test_wilson_bounds_sanity() -> None:
    assert 0.56 < wilson_lower(5, 5) < 0.57
    assert wilson_lower(0, 0) == 0.0
    assert wilson_upper(0, 6) < 0.40
    assert wilson_upper(3, 3) == 1.0


def test_three_of_three_does_not_promote(hv: HumanVals) -> None:
    gid = add_guideline(hv, INPUT, 'Always link the refund policy')
    for _ in range(3):
        expose(hv, output_ok=True)
    changes = hv.run_promotions()
    assert changes == []
    assert hv.metrics.guideline_impact(gid).exposures == 3
    assert next(g for g in hv.list_guidelines() if g.id == gid).status == 'candidate'


def test_five_of_five_promotes(hv: HumanVals) -> None:
    gid = add_guideline(hv, INPUT, 'Always link the refund policy')
    for _ in range(5):
        expose(hv, output_ok=True)
    changes = hv.run_promotions()
    assert (gid, 'candidate', 'validated') in changes
    g = next(g for g in hv.list_guidelines() if g.id == gid)
    assert g.status == 'validated'
    assert g.origin == 'validated'
    assert g.promoted_at is not None


def test_zero_of_six_demotes_after_promotion(hv: HumanVals) -> None:
    gid = add_guideline(hv, INPUT, 'Always link the refund policy')
    for _ in range(5):
        expose(hv, output_ok=True)
    hv.run_promotions()
    for _ in range(6):
        expose(hv, output_ok=False)
    changes = hv.run_promotions()
    assert (gid, 'validated', 'candidate') in changes


def test_exposure_credit_idempotent_per_case(hv: HumanVals) -> None:
    gid = add_guideline(hv, INPUT, 'Always link the refund policy')
    gs = hv.guidelines(INPUT, agent='bot')
    case_id = hv.record_case(agent='bot', input=INPUT, output='out', guidelines=gs)
    ev = Evaluation(case_id=case_id, intent_ok=True, output_ok=True, context_ok=True,
                    reviewer='ali')
    hv.evaluate(ev)
    hv.evaluate(ev)  # re-review of the same case
    assert hv.metrics.guideline_impact(gid).exposures == 1


def test_unexposed_guideline_gets_no_credit(hv: HumanVals) -> None:
    gid = add_guideline(hv, 'completely different topic about invoices', 'Invoice rule')
    expose(hv, output_ok=True)  # retrieval for INPUT should not include gid
    assert hv.metrics.guideline_impact(gid).exposures == 0
