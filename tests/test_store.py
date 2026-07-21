from pathlib import Path

from conftest import add_guideline
from humanvals import HumanVals


def test_file_db_roundtrip_survives_reopen(tmp_path: Path) -> None:
    db = str(tmp_path / 'hv.db')
    hv1 = HumanVals(db)
    gid = add_guideline(hv1, 'refund my order please', 'Link the refund policy',
                        applies_when='enterprise customers')

    hv2 = HumanVals(db)
    g = next(g for g in hv2.list_guidelines() if g.id == gid)
    assert g.text == 'Link the refund policy'
    assert g.applies_when == 'enterprise customers'
    assert g.agent == 'bot'
    assert g.namespace == 'default'
    assert g.status == 'candidate'
    cases = hv2.list_cases()
    assert len(cases) == 1
    gs = hv2.guidelines('refund my order please', agent='bot')
    assert gid in gs.ids  # embedding survives reopen


def test_memory_db_isolated_instances() -> None:
    hv1 = HumanVals(':memory:')
    hv2 = HumanVals(':memory:')
    add_guideline(hv1, 'refund my order', 'rule')
    assert hv2.list_guidelines() == []


def test_migration_from_v1_schema(tmp_path: Path) -> None:
    """A v1 database (no tool dimension) opens cleanly and gains the columns."""
    import sqlite3

    db = str(tmp_path / 'old.db')
    conn = sqlite3.connect(db)
    conn.executescript(
        'CREATE TABLE cases (id TEXT PRIMARY KEY, agent TEXT, namespace TEXT,'
        ' input TEXT, output TEXT, metadata TEXT, guidelines_injected TEXT,'
        ' created_at REAL, reviewed INTEGER DEFAULT 0);'
        'CREATE TABLE evaluations (id TEXT PRIMARY KEY, case_id TEXT,'
        ' intent_ok INTEGER, output_ok INTEGER, context_ok INTEGER, notes TEXT,'
        ' guideline_text TEXT, applies_when TEXT, reviewer TEXT, created_at REAL);'
        'CREATE TABLE guidelines (id TEXT PRIMARY KEY, agent TEXT, namespace TEXT,'
        ' intent_text TEXT, intent_vec TEXT, text TEXT, applies_when TEXT,'
        ' origin TEXT, status TEXT, exposures INTEGER DEFAULT 0,'
        ' wins INTEGER DEFAULT 0, validation_count INTEGER DEFAULT 0,'
        ' superseded_by TEXT, source_case_id TEXT, created_at REAL, promoted_at REAL);'
        'CREATE TABLE exposure_credits (case_id TEXT, guideline_id TEXT,'
        ' PRIMARY KEY (case_id, guideline_id));'
        "INSERT INTO cases VALUES ('c1','bot','default','in','out','{}','[]',0.0,1);"
        "INSERT INTO evaluations VALUES ('e1','c1',1,0,1,'','','','ali',0.0);"
    )
    conn.execute('PRAGMA user_version=1')
    conn.commit()
    conn.close()

    hv = HumanVals(db)  # must migrate, not crash
    row = hv.store.list_evaluations()[0]
    assert row['tool_ok'] == 1  # legacy rows default to 'no tool problem'
    assert row['expected_tool_call'] == ''
    assert hv.store.conn.execute('PRAGMA user_version').fetchone()[0] >= 2
