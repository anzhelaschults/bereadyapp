"""Public stateless policy API. Account state stays in owner-scoped Supabase.

Boundary validation follows https://fastapi.tiangolo.com/tutorial/body/.
No CORS wildcard: the web app proxies an allowlist of endpoints server-side.
"""
from datetime import date, datetime, timedelta, timezone
import logging
import re
from time import monotonic
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, StrictBool, StrictInt

from .conditions import get_conditions
from .core import adapt_plan, build_plan, discover, readiness
from .discovery import answer
from .telemetry import event, request_id

app = FastAPI(title='BeReady policy API', version='0.1.0')
Fitness = Annotated[StrictInt, Field(ge=1, le=3)]
Weeks = Annotated[StrictInt, Field(ge=1, le=52)]


def calendar_date(value):
    if type(value) is not str or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('Use YYYY-MM-DD')
    return date.fromisoformat(value)


CalendarDate = Annotated[date, BeforeValidator(calendar_date)]


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid')


class PlanInput(Input):
    trail_id: Annotated[str, Field(min_length=1, max_length=40)]
    fitness: Fitness
    weeks: Weeks
    start_date: CalendarDate | None = None
    trip_date: CalendarDate | None = None


class Filters(Input):
    region: Annotated[str, Field(max_length=30)] | None = None
    length: Annotated[str, Field(pattern='^(day|multi)$')] | None = None
    max_grade: Annotated[StrictInt, Field(ge=1, le=4)] | None = None
    hide_exposed: StrictBool = False
    in_season: StrictBool = False
    reachable: StrictBool = False


class DiscoverInput(Input):
    fitness: Fitness
    weeks: Weeks
    filters: Filters = Field(default_factory=Filters)


class AskInput(Input):
    query: Annotated[str, Field(min_length=1, max_length=1000)]


class SessionLog(Input):
    session_id: Annotated[str, Field(min_length=1, max_length=100)]
    done_at: Annotated[str, Field(min_length=10, max_length=40)]


class ProgressInput(Input):
    plan: dict
    logs: Annotated[list[SessionLog], Field(max_length=156)]
    today: CalendarDate | None = None


def error_response(code: str, message: str, status: int) -> JSONResponse:
    return JSONResponse({'error': {'code': code, 'message': message}}, status_code=status)


class BodyLimitMiddleware:
    """Bound memory before JSON parsing, including chunked/forged-length requests."""
    def __init__(self, app, limit=262144):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        body = bytearray()
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            body.extend(message.get('body', b''))
            if len(body) > self.limit:
                response = error_response('PAYLOAD_TOO_LARGE', 'Request body is too large.', 413)
                return await response(scope, receive, send)
            if not message.get('more_body', False):
                break
        supplied = False

        async def bounded_receive():
            nonlocal supplied
            if not supplied:
                supplied = True
                return {'type': 'http.request', 'body': bytes(body), 'more_body': False}
            return await receive()
        await self.app(scope, bounded_receive, send)


app.add_middleware(BodyLimitMiddleware)


@app.middleware('http')
async def observe(request: Request, call_next):
    try:
        correlation_id = str(UUID(request.headers.get('x-request-id', '')))
    except ValueError:
        correlation_id = str(uuid4())
    token = request_id.set(correlation_id)
    started = monotonic()
    try:
        response = await call_next(request)
    except Exception:
        event('request_failed', level=logging.ERROR, code='INTERNAL_ERROR')
        response = error_response('INTERNAL_ERROR', 'The service could not complete this request.', 500)
    response.headers['X-Request-ID'] = request_id.get()
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Referrer-Policy'] = 'no-referrer'
    route = request.scope.get('route')
    event('http_request', method=request.method,
          route=getattr(route, 'path', 'unmatched'), status=response.status_code,
          duration_ms=round((monotonic()-started)*1000))
    request_id.reset(token)
    return response


@app.exception_handler(RequestValidationError)
async def invalid_request(_request: Request, _exc: RequestValidationError):
    # Pydantic errors can contain the original request data. Never reflect them.
    return error_response('VALIDATION_ERROR', 'Check the trail, training level, weeks, and dates.', 422)


@app.exception_handler(ValueError)
async def invalid_policy_input(_request: Request, _exc: ValueError):
    return error_response('VALIDATION_ERROR', 'Use a covered trail, training level 1 to 3, and 1 to 52 whole weeks. Check your dates.', 422)


@app.get('/health')
def health():
    return {'status': 'ok', 'schema_version': 1}


@app.post('/plan')
def plan(body: PlanInput):
    start = body.start_date or datetime.now(timezone.utc).date()
    try:
        trip = body.trip_date or start + timedelta(weeks=body.weeks)
    except OverflowError as exc:
        raise ValueError('Trip date exceeds the calendar range') from exc
    return build_plan(body.trail_id, body.fitness, start, trip)


@app.post('/progress')
def progress(body: ProgressInput):
    # Regenerate policy output. Client-supplied session labels, dates and verdicts
    # are not authoritative, even for a logged-out plan preview.
    p = body.plan
    try:
        canonical = build_plan(p['trail_id'], p['fitness'], calendar_date(p['start_date']), calendar_date(p['trip_date']))
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError('Invalid saved plan inputs') from exc
    today = body.today or datetime.now(timezone.utc).date()
    logs = []
    for log in body.logs:
        try:
            raw = log.done_at
            day = datetime.fromisoformat(raw.replace('Z', '+00:00')).astimezone(timezone.utc).date() if 'T' in raw else date.fromisoformat(raw)
            logs.append({'session_id': log.session_id, 'done_at': day.isoformat()})
        except ValueError:
            continue
    return {'plan': adapt_plan(canonical, logs, today), 'progress': readiness(canonical, logs, today)}


@app.post('/discover')
def discovery(body: DiscoverInput):
    return {'trails': discover(body.fitness, body.weeks, body.filters.model_dump(exclude_none=True))}


@app.post('/ask')
def ask(body: AskInput):
    return answer(body.query)


@app.get('/conditions')
def conditions(trail: Annotated[str, Query(max_length=40)], date: CalendarDate):
    return get_conditions(trail, date)
