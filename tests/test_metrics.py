from conftest import add_guideline
from humanvals import Evaluation, HumanVals


def review(hv: HumanVals, text: str, output_ok: bool) -> None:
    gs = hv.guidelines(text, agent='bot')
    case_id = hv.record_case(agent='bot', input=text, output='out', guidelines=gs)
    hv.evaluate(Evaluation(case_id=case_id, intent_ok=True, output_ok=output_ok,
                           context_ok=True, reviewer='ali'))


def test_intervention_rate_declines_when_agent_improves(hv: HumanVals) -> None:
    for _ in range(6):
        review(hv, 'refund my order please', output_ok=False)
    for _ in range(6):
        review(hv, 'refund my order please', output_ok=True)
    report = hv.metrics.intervention_rate(agent='bot')
    assert report.n == 12
    assert report.overall == 0.5
    assert report.series[0] > report.series[-1]


def test_guideline_impact_fields(hv: HumanVals) -> None:
    gid = add_guideline(hv, 'refund my order please', 'Link the refund policy')
    review(hv, 'refund my order please', output_ok=True)
    impact = hv.metrics.guideline_impact(gid)
    assert impact.exposures == 1
    assert impact.wins == 1
    assert 0.0 <= impact.wilson_low <= impact.wilson_high <= 1.0


def test_summary_counts(hv: HumanVals) -> None:
    add_guideline(hv, 'refund my order please', 'Link the refund policy')
    hv.record_case(agent='bot', input='unreviewed one', output='x')
    s = hv.metrics.summary()
    assert s['cases'] == 2
    assert s['unreviewed'] == 1
    assert s['guidelines']['candidate'] == 1
    assert 'intervention_rate' in s
