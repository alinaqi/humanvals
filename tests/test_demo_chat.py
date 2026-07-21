"""Hosted demo support agent: chats become reviewable cases (exposure-logged)."""

import pytest
from fastapi.testclient import TestClient

from humanvals import Evaluation, HumanVals
from humanvals.server.app import create_app
from humanvals.server.demo_agent import offline_reply


@pytest.fixture(autouse=True)
def no_gateway(monkeypatch: pytest.MonkeyPatch) -> None:
    """Hermetic tests: never call a real gateway even if the shell exports one."""
    monkeypatch.delenv('OPENAI_BASE_URL', raising=False)
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)


@pytest.fixture
def hv() -> HumanVals:
    return HumanVals(':memory:')


@pytest.fixture
def client(hv: HumanVals) -> TestClient:
    return TestClient(create_app(hv=hv))


def test_chat_records_exposure_logged_case(client: TestClient, hv: HumanVals) -> None:
    r = client.post('/api/demo/chat', json={'message': 'refund my order #1 please'})
    assert r.status_code == 200
    body = r.json()
    assert body['reply']
    case = hv.get_case(body['case_id'])
    assert case.agent == 'support-bot'
    assert case.input == 'refund my order #1 please'
    assert case.guidelines_injected == body['guideline_ids'] == []


def test_chat_injects_learned_guideline(client: TestClient, hv: HumanVals) -> None:
    case_id = hv.record_case(agent='support-bot', input='refund my order #9', output='no')
    hv.evaluate(Evaluation(case_id=case_id, intent_ok=True, output_ok=False,
                           context_ok=True, reviewer='ali',
                           guideline_text='Always include the refund policy link',
                           applies_when='refund requests'))
    r = client.post('/api/demo/chat', json={'message': 'please refund my order #4'})
    body = r.json()
    assert len(body['guideline_ids']) == 1
    assert hv.get_case(body['case_id']).guidelines_injected == body['guideline_ids']


def test_chat_rejects_oversized_message(client: TestClient) -> None:
    r = client.post('/api/demo/chat', json={'message': 'x' * 2001})
    assert r.status_code == 400


def test_chat_rejects_empty_message(client: TestClient) -> None:
    assert client.post('/api/demo/chat', json={'message': '  '}).status_code == 400


def test_chat_rate_limited(hv: HumanVals) -> None:
    client = TestClient(create_app(hv=hv))
    codes = [client.post('/api/demo/chat', json={'message': f'hello {i}'}).status_code
             for i in range(25)]
    assert 429 in codes
    assert codes[0] == 200


def test_offline_reply_follows_injected_guideline() -> None:
    with_guideline = offline_reply('refund my order', 'refund policy link https://x')
    without = offline_reply('refund my order', '')
    assert with_guideline != without
    assert 'refund' in with_guideline.lower()
