"""Structured logging and request context helpers."""

from __future__ import annotations

import contextvars
import logging
import re
from time import perf_counter
from typing import Any

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")
request_stage_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_stage", default="-")

_NID_RE = re.compile(r"\b(?:\d[ -]?){9,16}\d\b")


def mask_sensitive_text(value: str) -> str:
    return _NID_RE.sub("[REDACTED_NID]", value)


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        record.stage = request_stage_var.get()
        return True


def configure_logging(level: str) -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s request_id=%(request_id)s stage=%(stage)s %(name)s %(message)s"
    )
    handler.setFormatter(formatter)
    handler.addFilter(RequestContextFilter())
    root_logger.addHandler(handler)
    root_logger.setLevel(level.upper())


def set_request_context(request_id: str, stage: str = "request") -> tuple[contextvars.Token[str], contextvars.Token[str]]:
    return request_id_var.set(request_id), request_stage_var.set(stage)


def reset_request_context(tokens: tuple[contextvars.Token[str], contextvars.Token[str]]) -> None:
    request_id_var.reset(tokens[0])
    request_stage_var.reset(tokens[1])


def duration_ms(start: float) -> float:
    return round((perf_counter() - start) * 1000.0, 2)


def sanitize_log_fields(data: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = mask_sensitive_text(value)
        else:
            sanitized[key] = value
    return sanitized
