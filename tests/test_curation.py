import pytest

from conftest import add_guideline
from humanvals import Evaluation, HumanVals


def new_eval(case_id: str, text: str, applies_when: str = '') -> Evaluation:
    return Evaluation(case_id=case_id, intent_ok=True, output_ok=False, context_ok=True,
                      guideline_text=text, applies_when=applies_when, reviewer='ali')


def test_check_conflicts_finds_similar_intent(hv: HumanVals) -> None:
    gid = add_guideline(hv, 'refund my order please', 'Refunds need manager approval')
    conflicts = hv.check_conflicts('Refunds are always self-serve', agent='bot')
    assert [g.id for g in conflicts] == [gid]


def test_check_conflicts_scoped_to_agent(hv: HumanVals) -> None:
    add_guideline(hv, 'refund my order please', 'Refunds need manager approval', agent='support')
    assert hv.check_conflicts('Refunds are self-serve', agent='sales') == []


def test_reinforce_increments_no_sibling(hv: HumanVals) -> None:
    gid = add_guideline(hv, 'refund my order please', 'Refunds need manager approval')
    case_id = hv.record_case(agent='bot', input='refund order now', output='x')
    result = hv.evaluate(
        new_eval(case_id, 'Refunds require approval from a manager'),
        resolution='reinforce', target_guideline_id=gid,
    )
    assert result.guideline_id == gid
    gs = hv.list_guidelines()
    assert len(gs) == 1
    assert gs[0].validation_count == 1


def test_override_supersedes_never_deletes(hv: HumanVals) -> None:
    old = add_guideline(hv, 'refund my order please', 'Refunds need manager approval')
    case_id = hv.record_case(agent='bot', input='refund order', output='x')
    result = hv.evaluate(
        new_eval(case_id, 'Refunds are self-serve'),
        resolution='override', target_guideline_id=old,
    )
    all_g = {g.id: g for g in hv.list_guidelines()}
    assert len(all_g) == 2  # superseded record kept
    assert all_g[old].status == 'superseded'
    assert all_g[old].superseded_by == result.guideline_id


def test_scope_both_requires_applies_when(hv: HumanVals) -> None:
    old = add_guideline(hv, 'refund my order please', 'Refunds need manager approval')
    case_id = hv.record_case(agent='bot', input='refund order', output='x')
    with pytest.raises(ValueError, match='applies_when'):
        hv.evaluate(new_eval(case_id, 'Refunds are self-serve'),
                    resolution='scope_both', target_guideline_id=old)


def test_scope_both_keeps_both(hv: HumanVals) -> None:
    old = add_guideline(hv, 'refund my order please', 'Refunds need manager approval')
    case_id = hv.record_case(agent='bot', input='refund order', output='x')
    hv.evaluate(new_eval(case_id, 'Refunds are self-serve', applies_when='SMB customers'),
                resolution='scope_both', target_guideline_id=old)
    statuses = sorted(g.status for g in hv.list_guidelines())
    assert statuses == ['candidate', 'candidate']


def test_override_requires_target(hv: HumanVals) -> None:
    case_id = hv.record_case(agent='bot', input='refund order', output='x')
    with pytest.raises(ValueError, match='target_guideline_id'):
        hv.evaluate(new_eval(case_id, 'Refunds are self-serve'), resolution='override')
