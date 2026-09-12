"""Allowlisted events only. Never include user queries, cookies or provider responses."""
import json
import logging
import re
from contextvars import ContextVar

class _TransportRedaction(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        record.msg = re.sub(r"(?i)(apikey|api_key|access_token|refresh_token)=([^&\s\"']+)", r'\1=[REDACTED]', message)
        record.args = ()
        return True


_redactor = _TransportRedaction()


def redact_transport_logs() -> None:
    # HTTPX logs the full request URL at INFO, including Open-Meteo query keys.
    # Keep useful transport events, but scrub key-bearing URLs before handlers.
    logging.getLogger('httpx').addFilter(_redactor)
    logging.getLogger('httpcore').setLevel(logging.WARNING)


request_id: ContextVar[str] = ContextVar('request_id', default='background')
logger = logging.getLogger('beready')


def event(name: str, *, level: int = logging.INFO, **fields: str | int | float) -> None:
    logger.log(level, json.dumps({'event': name, 'request_id': request_id.get(), **fields}, sort_keys=True))
