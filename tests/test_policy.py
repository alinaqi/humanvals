"""Policy vs. heuristic guideline classes (ADR-0009)."""

import pytest

from conftest import add_guideline
from humanvals import Evaluation, HumanVals
from test_promotion import INPUT, expose


def add_policy(hv: HumanVals, case_input: str, text: str) -> str:
    case_id = hv.record_case(agent='bot', input=case_input, output='out')
    result = hv.evaluate(Evaluation(
        case_id=case_id, intent_ok=True, output_ok=False, context_ok=True,
        guideline_text=text, applies_when='refund requests', reviewer='ali',
        guideline_kind='policy'))
    assert result.guideline_id is not None
    return result.guideline_id


def test_policy_active_immediately(hv: HumanVals) -> None:
    gid = add_policy(hv, INPUT, 'Always confirm the order number before refunding')
    g = next(g for g in hv.list_guidelines() if g.id == gid)
    assert g.kind == 'policy'
    assert g.status == 'validated'   # active without measurement
    assert g.origin == 'stated'      # authority-backed, not measurement-backed
    gs = hv.guidelines(INPUT, agent='bot')
    assert gid in gs.ids


def test_heuristic_is_default_and_starts_candidate(hv: HumanVals) -> None:
    gid = add_guideline(hv, INPUT, 'Prefer a friendly tone')
    g = next(g for g in hv.list_guidelines() if g.id == gid)
    assert g.kind == 'heuristic'
    assert g.status == 'candidate'


def test_policy_never_statistically_demoted(hv: HumanVals) -> None:
    gid = add_policy(hv, INPUT, 'Always confirm the order number before refunding')
    for _ in range(6):
        expose(hv, output_ok=False)  # 0/6 would demote any validated heuristic
    changes = hv.run_promotions()
    assert all(change[0] != gid for change in changes)
    assert next(g for g in hv.list_guidelines() if g.id == gid).status == 'validated'
    # monitoring evidence still accumulates
    assert hv.metrics.guideline_impact(gid).exposures == 6


def test_policy_ranked_above_validated_heuristic(hv: HumanVals) -> None:
    heuristic = add_guideline(hv, INPUT, 'Prefer a friendly tone in refund replies')
    for _ in range(5):
        expose(hv, output_ok=True)
    hv.run_promotions()  # heuristic now validated
    policy = add_policy(hv, INPUT, 'Always confirm the order number before refunding')
    gs = hv.guidelines(INPUT, agent='bot')
    assert gs.ids.index(policy) < gs.ids.index(heuristic)


def test_prompt_renders_policy_block_first(hv: HumanVals) -> None:
    add_guideline(hv, INPUT, 'Prefer a friendly tone in refund replies')
    add_policy(hv, INPUT, 'Always confirm the order number before refunding')
    prompt = hv.guidelines(INPUT, agent='bot').as_prompt()
    assert 'always follow' in prompt.lower()
    policy_pos = prompt.index('Always confirm the order number')
    heuristic_pos = prompt.index('Prefer a friendly tone')
    assert policy_pos < heuristic_pos


def test_invalid_kind_rejected(hv: HumanVals) -> None:
    case_id = hv.record_case(agent='bot', input='x', output='y')
    with pytest.raises(ValueError, match='guideline_kind'):
        hv.evaluate(Evaluation(
            case_id=case_id, intent_ok=True, output_ok=True, context_ok=True,
            guideline_text='rule', reviewer='ali', guideline_kind='critical'))


def test_migration_from_v2_adds_kind(tmp_path) -> None:  # type: ignore[no-untyped-def]
    import sqlite3
    from pathlib import Path

    db = str(Path(tmp_path) / 'v2.db')
    conn = sqlite3.connect(db)
    conn.executescript(
        'CREATE TABLE cases (id TEXT PRIMARY KEY, agent TEXT, namespace TEXT,'
        ' input TEXT, output TEXT, metadata TEXT, guidelines_injected TEXT,'
        ' created_at REAL, reviewed INTEGER DEFAULT 0);'
        'CREATE TABLE evaluations (id TEXT PRIMARY KEY, case_id TEXT,'
        ' intent_ok INTEGER, output_ok INTEGER, context_ok INTEGER,'
        " tool_ok INTEGER DEFAULT 1, expected_tool_call TEXT DEFAULT '',"
        ' notes TEXT, guideline_text TEXT, applies_when TEXT, reviewer TEXT,'
        ' created_at REAL);'
        'CREATE TABLE guidelines (id TEXT PRIMARY KEY, agent TEXT, namespace TEXT,'
        ' intent_text TEXT, intent_vec TEXT, text TEXT, applies_when TEXT,'
        ' origin TEXT, status TEXT, exposures INTEGER DEFAULT 0,'
        ' wins INTEGER DEFAULT 0, validation_count INTEGER DEFAULT 0,'
        ' superseded_by TEXT, source_case_id TEXT, created_at REAL, promoted_at REAL);'
        'CREATE TABLE exposure_credits (case_id TEXT, guideline_id TEXT,'
        ' PRIMARY KEY (case_id, guideline_id));'
        "INSERT INTO guidelines VALUES ('g1','bot','default','intent','[]','rule','',"
        "'stated','candidate',0,0,0,NULL,NULL,0.0,NULL);"
    )
    conn.execute('PRAGMA user_version=2')
    conn.commit()
    conn.close()

    hv = HumanVals(db)
    g = hv.list_guidelines()[0]
    assert g.kind == 'heuristic'  # legacy rows default to the measured tier
