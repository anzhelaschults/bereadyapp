"""Date-specific forecast with explicit unavailable and no-closure-knowledge states.

Source: https://open-meteo.com/en/docs (daily fields, 16-day horizon).
Commercial access: https://open-meteo.com/en/pricing. The free endpoint must be
explicitly enabled for non-commercial evaluation, not silently used for launch.
"""
from collections import OrderedDict
from datetime import date, datetime, timezone
import logging
import math
import os
from threading import Lock
from time import monotonic

import httpx
from .trails import TRAILS
from .telemetry import event, redact_transport_logs

_cache: OrderedDict[tuple, tuple[float, dict]] = OrderedDict()
_lock = Lock()
_TTL = 900


def clear_cache() -> None:
    with _lock:
        _cache.clear()


def _fetch(trail: dict, day: date) -> dict:
    redact_transport_logs()
    key = os.getenv('OPEN_METEO_API_KEY', '')
    host = 'customer-api.open-meteo.com' if key else 'api.open-meteo.com'
    params = {
        'latitude': trail['latitude'], 'longitude': trail['longitude'],
        'start_date': day.isoformat(), 'end_date': day.isoformat(), 'timezone': 'UTC',
        'daily': 'temperature_2m_min,temperature_2m_max,precipitation_sum,wind_speed_10m_max',
    }
    if key:
        params['apikey'] = key
    # Neither host nor path can come from a caller. Never follow provider redirects.
    with httpx.stream('GET', f'https://{host}/v1/forecast', params=params,
                      timeout=httpx.Timeout(5.0), follow_redirects=False) as response:
        response.raise_for_status()
        data = bytearray()
        for chunk in response.iter_bytes():
            data.extend(chunk)
            if len(data) > 262144:
                raise ValueError('Forecast payload too large')
        import json
        return json.loads(data)


def _measure(payload: dict, key: str, low: float, high: float) -> float:
    values = payload[key]
    if not isinstance(values, list) or len(values) != 1:
        raise ValueError('Expected one daily value')
    value = values[0]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not low <= value <= high or not math.isfinite(value):
        raise ValueError('Invalid daily value')
    return value


def get_conditions(trail_id: str, day: date) -> dict:
    if trail_id not in TRAILS:
        raise ValueError('Unknown trail')
    trail = TRAILS[trail_id]
    base = {
        'status': 'disabled', 'date': day.isoformat(),
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'source': 'Typical season notes', 'source_url': trail['sources'][0],
        'summary': 'Live conditions are not configured. These are typical conditions, not a trail access report.',
        'season_note': trail['season_note'], 'closure_status': 'unknown',
        'temperature_min': None, 'temperature_max': None, 'precipitation_mm': None, 'wind_kmh': None,
    }
    if os.getenv('CONDITIONS_ENABLED') != 'true':
        return base
    if not os.getenv('OPEN_METEO_API_KEY') and os.getenv('WEATHER_ALLOW_NONCOMMERCIAL') != 'true':
        return base
    today = datetime.now(timezone.utc).date()
    if not 0 <= (day - today).days <= 15:
        return {**base, 'status': 'outside_forecast',
                'summary': 'Your date is outside the 16-day forecast window. Check again closer to departure. The season note is typical, not live.'}
    cache_key = (trail_id, day.isoformat(), bool(os.getenv('OPEN_METEO_API_KEY')))
    with _lock:
        cached = _cache.get(cache_key)
        if cached and monotonic() - cached[0] < _TTL:
            return dict(cached[1])
    started = monotonic()
    try:
        payload = _fetch(trail, day)
        daily = payload['daily']
        if not isinstance(daily, dict) or daily.get('time') != [day.isoformat()]:
            raise ValueError('Forecast date mismatch')
        minimum = _measure(daily, 'temperature_2m_min', -100, 65)
        maximum = _measure(daily, 'temperature_2m_max', -100, 65)
        if minimum > maximum:
            raise ValueError('Temperature bounds reversed')
        result = {**base, 'status': 'live', 'source': 'Open-Meteo', 'source_url': 'https://open-meteo.com/',
                  'summary': 'Forecast for a representative point, not the entire route. Snow on the trail and closures are unverified. Check the route operator before departure.',
                  'temperature_min': minimum, 'temperature_max': maximum,
                  'precipitation_mm': _measure(daily, 'precipitation_sum', 0, 2000),
                  'wind_kmh': _measure(daily, 'wind_speed_10m_max', 0, 500)}
        event('conditions_fetch', outcome='live', duration_ms=round((monotonic()-started)*1000))
    except (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError, RecursionError):
        result = {**base, 'status': 'unavailable',
                  'summary': 'The forecast is unavailable. Your plan still works. Use this typical season note and check the route operator.'}
        event('conditions_fetch', level=logging.WARNING, outcome='unavailable', duration_ms=round((monotonic()-started)*1000))
    with _lock:
        _cache[cache_key] = (monotonic(), result)
        _cache.move_to_end(cache_key)
        while len(_cache) > 144:
            _cache.popitem(last=False)
    return dict(result)
