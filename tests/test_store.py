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
