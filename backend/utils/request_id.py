"""Request correlation ID for structured logs (contextvar + logging filter)."""

from __future__ import annotations

import contextvars
import logging
import uuid

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar('request_id', default='')


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get() or '-'
        return True


def new_request_id(from_header: str | None) -> str:
    return (from_header or '').strip() or str(uuid.uuid4())
