import pytest
from fastapi.testclient import TestClient

from humanvals import HumanVals
from humanvals.server.app import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(hv=HumanVals(':memory:')))


def seed_case(client: TestClient, text: str = 'refund my order please') -> str:
    r = client.post('/api/cases', json={
        'agent': 'bot', 'input': text, 'output': 'done',
        'metadata': {'thought_chain': ['step1'], 'tool_calls': [], 'context': 'ctx'}})
    assert r.status_code == 201
    case_id: str = r.json()['case_id']
    return case_id


def evaluate(client: TestClient, case_id: str, **overrides: object) -> dict:  # type: ignore[type-arg]
    body: dict = {'intent_ok': True, 'output_ok': False, 'context_ok': True,  # type: ignore[type-arg]
                  'tool_ok': True, 'expected_tool_call': '',
                  'reviewer': 'ali', 'guideline_text': 'Link the refund policy',
                  'applies_when': '', 'resolution': 'add'}
    body.update(overrides)
    r = client.post(f'/api/cases/{case_id}/evaluate', json=body)
    assert r.status_code == 200, r.text
    data: dict = r.json()  # type: ignore[type-arg]
    return data


def test_summary_empty(client: TestClient) -> None:
    r = client.get('/api/summary')
    assert r.status_code == 200
    assert r.json()['cases'] == 0


def test_record_and_list_cases(client: TestClient) -> None:
    seed_case(client)
    r = client.get('/api/cases', params={'unreviewed_only': 'true'})
    assert len(r.json()) == 1
    assert r.json()[0]['input'] == 'refund my order please'


def test_case_detail_includes_metadata(client: TestClient) -> None:
    case_id = seed_case(client)
    r = client.get(f'/api/cases/{case_id}')
    assert r.json()['metadata']['thought_chain'] == ['step1']


def test_case_not_found_404(client: TestClient) -> None:
    assert client.get('/api/cases/nope').status_code == 404


def test_evaluate_creates_guideline(client: TestClient) -> None:
    case_id = seed_case(client)
    data = evaluate(client, case_id)
    assert data['guideline_id'] is not None
    r = client.get('/api/guidelines')
    assert r.json()[0]['status'] == 'candidate'


def test_evaluate_invalid_resolution_400(client: TestClient) -> None:
    case_id = seed_case(client)
    r = client.post(f'/api/cases/{case_id}/evaluate', json={
        'intent_ok': True, 'output_ok': True, 'context_ok': True, 'reviewer': 'ali',
        'guideline_text': 'x', 'resolution': 'scope_both'})
    assert r.status_code == 400
    assert 'applies_when' in r.json()['detail']


def test_conflict_check(client: TestClient) -> None:
    case_id = seed_case(client)
    evaluate(client, case_id, guideline_text='Refunds need manager approval')
    r = client.post('/api/conflicts', json={
        'guideline_text': 'Refunds are self-serve', 'agent': 'bot'})
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_guideline_retrieval_endpoint(client: TestClient) -> None:
    case_id = seed_case(client)
    evaluate(client, case_id)
    r = client.get('/api/guidelines/query',
                   params={'input': 'refund my order now', 'agent': 'bot'})
    assert r.status_code == 200
    assert len(r.json()['guidelines']) == 1
    assert 'prompt' in r.json()


def test_evaluate_with_tool_correction(client: TestClient) -> None:
    case_id = seed_case(client)
    evaluate(client, case_id, tool_ok=False,
             expected_tool_call='orders.lookup(order_id) first')
    r = client.get(f'/api/cases/{case_id}/evaluations')
    assert r.status_code == 200
    assert r.json()[0]['tool_ok'] is False
    assert r.json()[0]['expected_tool_call'] == 'orders.lookup(order_id) first'


def test_promotions_endpoint(client: TestClient) -> None:
    r = client.post('/api/promotions/run')
    assert r.status_code == 200
    assert r.json()['changes'] == []


def test_intervention_metrics(client: TestClient) -> None:
    case_id = seed_case(client)
    evaluate(client, case_id, guideline_text='')
    r = client.get('/api/metrics/intervention')
    assert r.json()['n'] == 1
    assert r.json()['overall'] == 1.0


def test_guideline_impact_endpoint(client: TestClient) -> None:
    case_id = seed_case(client)
    gid = evaluate(client, case_id)['guideline_id']
    r = client.get(f'/api/guidelines/{gid}/impact')
    assert r.status_code == 200
    assert r.json()['exposures'] == 0
