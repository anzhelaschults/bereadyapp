import pytest
from fastapi.testclient import TestClient
from beready.api import app

client = TestClient(app)


@pytest.mark.parametrize('start', [0, 1780000000, '20260101', '2026-W01-1', '2026-01-01T00:00:00Z'])
def test_plan_requires_iso_calendar_date_not_epoch_or_week_date(start):
    r = client.post('/plan', json={'trail_id':'laugavegur', 'fitness':1, 'weeks':8, 'start_date':start})
    assert r.status_code == 422


def test_progress_regeneration_uses_the_same_strict_date_boundary():
    r = client.post('/progress', json={'plan': {'trail_id': 'laugavegur', 'fitness': 1,
        'start_date': '2026-W01-1', 'trip_date': '2026-W03-1'}, 'logs': []})
    assert r.status_code == 422


def test_default_trip_date_overflow_returns_validation_error():
    r = client.post('/plan', json={'trail_id':'laugavegur', 'fitness':1, 'weeks':8, 'start_date':'9999-12-31'})
    assert r.status_code == 422


def test_invalid_internal_request_id_is_not_echoed():
    r = client.get('/health', headers={'x-request-id':'secret untrusted text'})
    assert r.headers['x-request-id'] != 'secret untrusted text'


def test_valid_request_id_propagates_for_proxy_correlation():
    request_id = 'd0996a08-71c5-4aac-8db4-8149e5cc4826'
    r = client.get('/health', headers={'x-request-id': request_id})
    assert r.headers['x-request-id'] == request_id
