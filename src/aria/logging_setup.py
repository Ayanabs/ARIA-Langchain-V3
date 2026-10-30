"""Structured (JSON lines) logging with secret masking and a per-request trace ID."""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime

trace_id_var: ContextVar[str | None] = ContextVar("aria_trace_id", default=None)

MASK = "***"

# Attributes every LogRecord has; anything else was passed through `extra=` and is logged as a field.
_STANDARD_RECORD_ATTRIBUTES = frozenset(
    logging.LogRecord("", 0, "", 0, "", None, None).__dict__.keys() | {"message", "asctime", "taskName"}
)


class SecretMasker:
    """Replaces configured secret values in any log output."""

    def __init__(self, secrets: list[str] | None = None):
        # Longest first, so a secret that contains another is masked whole.
        self._secrets = sorted({secret for secret in secrets or [] if secret}, key=len, reverse=True)

    def mask(self, text: str) -> str:
        for secret in self._secrets:
            text = text.replace(secret, MASK)
        return text


class JsonFormatter(logging.Formatter):
    def __init__(self, masker: SecretMasker):
        super().__init__()
        self._masker = masker

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        trace_id = trace_id_var.get()
        if trace_id:
            entry["trace_id"] = trace_id
        for key, value in record.__dict__.items():
            if key not in _STANDARD_RECORD_ATTRIBUTES and not key.startswith("_"):
                entry[key] = value
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        return self._masker.mask(json.dumps(entry, default=str, ensure_ascii=False))


def configure_logging(level: str = "INFO", secrets: list[str] | None = None) -> None:
    """Route all logging, including uvicorn's, through one JSON handler on stderr."""
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter(SecretMasker(secrets)))

    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level.upper())

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
