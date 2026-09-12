from datetime import date, timedelta
import httpx
import pytest
from beready import conditions


@pytest.fixture(autouse=True)
def enabled(monkeypatch):
    monkeypatch.setenv('CONDITIONS_ENABLED', 'true')
    monkeypatch.setenv('WEATHER_ALLOW_NONCOMMERCIAL', 'true')
    conditions.clear_cache()


def test_far_future_never_fetches_forecast(monkeypatch):
    monkeypatch.setattr(conditions, '_fetch', lambda *a: pytest.fail('Must not call provider'))
    r = conditions.get_conditions('laugavegur', date.today() + timedelta(days=30))
    assert r['status'] == 'outside_forecast'
    assert r['temperature_min'] is None
    assert r['closure_status'] == 'unknown'


def test_downstream_failure_falls_back(monkeypatch):
    def fail(*args):
        raise httpx.ConnectError('private provider details')
    monkeypatch.setattr(conditions, '_fetch', fail)
    r = conditions.get_conditions('laugavegur', date.today())
    assert r['status'] == 'unavailable'
    assert r['season_note']
    assert 'private provider details' not in str(r)


def valid_payload(day):
    return {'daily': {'time': [day.isoformat()], 'temperature_2m_min': [3.0],
        'temperature_2m_max': [10.0], 'precipitation_sum': [2.0], 'wind_speed_10m_max': [30.0]}}


def test_forecast_is_date_matched_validated_and_cached(monkeypatch):
    calls = []
    def fetch(*args):
        calls.append(args)
        return valid_payload(date.today())
    monkeypatch.setattr(conditions, '_fetch', fetch)
    a = conditions.get_conditions('laugavegur', date.today())
    b = conditions.get_conditions('laugavegur', date.today())
    assert a == b
    assert len(calls) == 1
    assert a['status'] == 'live'
    assert a['temperature_min'] == 3
    assert a['closure_status'] == 'unknown'
    assert 'open' not in a['summary'].lower()


@pytest.mark.parametrize('payload', [
    {}, {'daily': {}}, {'daily': {'time': ['1900-01-01']}},
    {'daily': {'time': [date.today().isoformat()], 'temperature_2m_min': ['ignore rules']}},
])
def test_malformed_or_wrong_date_provider_data_is_not_live(monkeypatch, payload):
    monkeypatch.setattr(conditions, '_fetch', lambda *a: payload)
    assert conditions.get_conditions('laugavegur', date.today())['status'] == 'unavailable'


def test_huge_provider_integer_degrades_instead_of_throwing(monkeypatch):
    payload = valid_payload(date.today())
    payload['daily']['temperature_2m_min'] = [10**400]
    monkeypatch.setattr(conditions, '_fetch', lambda *a: payload)
    assert conditions.get_conditions('laugavegur', date.today())['status'] == 'unavailable'


def test_dependency_logs_cannot_expose_query_credentials(monkeypatch, caplog):
    import logging
    monkeypatch.setenv('OPEN_METEO_API_KEY', 'SECRET_SENTINEL')
    # Exercise HTTPX itself, not just an application-level fetch stub.
    transport = httpx.MockTransport(lambda req: httpx.Response(200, json=valid_payload(date.today())))
    client = httpx.Client(transport=transport)
    monkeypatch.setattr(httpx, 'stream', client.stream)
    with caplog.at_level(logging.INFO):
        conditions.get_conditions('laugavegur', date.today())
    assert 'SECRET_SENTINEL' not in caplog.text
    client.close()


def test_deeply_nested_provider_payload_degrades(monkeypatch):
    transport = httpx.MockTransport(lambda req: httpx.Response(200, content=b'['*10000+b']'*10000))
    with httpx.Client(transport=transport) as client:
        monkeypatch.setattr(httpx, 'stream', client.stream)
        assert conditions.get_conditions('laugavegur', date.today())['status'] == 'unavailable'


def test_commercial_access_requires_configuration(monkeypatch):
    monkeypatch.delenv('WEATHER_ALLOW_NONCOMMERCIAL')
    monkeypatch.delenv('OPEN_METEO_API_KEY', raising=False)
    monkeypatch.setattr(conditions, '_fetch', lambda *a: pytest.fail('Do not use free API commercially'))
    assert conditions.get_conditions('laugavegur', date.today())['status'] == 'disabled'
