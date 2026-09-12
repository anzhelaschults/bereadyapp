from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from beready.api import app

client = TestClient(app)


def test_health_includes_request_id_and_security_headers():
    response = client.get('/health')
    assert response.json() == {'status': 'ok', 'schema_version': 1}
    assert response.headers['x-request-id']
    assert response.headers['x-content-type-options'] == 'nosniff'


def test_public_plan_free_and_uses_actual_trip_date():
    response = client.post('/plan', json={
        'trail_id': 'laugavegur', 'fitness': 1, 'weeks': 52,
        'start_date': '2026-01-01', 'trip_date': '2026-02-12',
    })
    assert response.status_code == 200, response.text
    plan = response.json()
    assert plan['weeks'] == 6
    assert plan['assessment']['status'] == 'hard'
    assert plan['sessions']


@pytest.mark.parametrize('changes', [
    {'fitness': True}, {'fitness': 4}, {'fitness': '1'}, {'weeks': 0},
    {'weeks': 53}, {'trail_id': 'unknown'}, {'start_date': 'not-a-date'},
    {'trip_date': '2020-01-01'}, {'fitness': None}, {'extra': 'field'},
])
def test_invalid_plan_inputs_are_safe_errors(changes):
    response = client.post('/plan', json={
        'trail_id': 'laugavegur', 'fitness': 1, 'weeks': 8, **changes,
    })
    assert response.status_code == 422
    assert 'message' in response.json()['error']
    assert 'Traceback' not in response.text


def test_invalid_json_is_consistent_error():
    r = client.post('/plan', content='{', headers={'content-type': 'application/json'})
    assert r.status_code == 422
    assert r.json()['error']['code'] == 'VALIDATION_ERROR'


def test_body_size_limit_even_with_no_content_length():
    r = client.post('/ask', content=b'x' * (262144 + 1), headers={'content-type': 'application/json'})
    assert r.status_code == 413


def test_progress_never_trusts_caller_verdict_or_sessions():
    plan = client.post('/plan', json={'trail_id': 'laugavegur', 'fitness': 1, 'weeks': 2}).json()
    plan['assessment']['status'] = 'ready'
    plan['sessions'] = []
    r = client.post('/progress', json={'plan': plan, 'logs': []})
    assert r.status_code == 200, r.text
    assert r.json()['plan']['assessment']['status'] == 'toosoon'
    assert r.json()['plan']['sessions']
    assert r.json()['progress']['score'] == 0


def test_discovery_retains_all_trails_by_default():
    r = client.post('/discover', json={'fitness': 1, 'weeks': 1})
    assert r.status_code == 200, r.text
    rows = r.json()['trails']
    assert len(rows) == 9
    assert rows[-1]['assessment']['status'] == 'toosoon'


def test_conditions_disabled_is_honest_and_does_not_block_plan(monkeypatch):
    monkeypatch.delenv('CONDITIONS_ENABLED', raising=False)
    r = client.get('/conditions', params={'trail': 'laugavegur', 'date': date.today().isoformat()})
    assert r.status_code == 200
    assert r.json()['status'] == 'disabled'
    assert r.json()['closure_status'] == 'unknown'


def test_conditions_invalid_or_unknown_input():
    assert client.get('/conditions?trail=unknown&date=2026-01-01').status_code == 422
    assert client.get('/conditions?trail=laugavegur&date=nope').status_code == 422
