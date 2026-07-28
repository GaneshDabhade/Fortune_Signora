"""Structured JSON logging with automatic context and secret redaction.

Two properties this module is responsible for, both required by
docs/architecture/07-data-flow.md and docs/architecture/10-security.md:

1. **Every line carries correlation context.** Debugging an asynchronous
   pipeline that spans API, relay, and worker processes is only tractable
   if one identifier threads through all of them.
2. **No line ever carries a secret.** Redaction is applied structurally
   here rather than left to each call site, because "remember not to log
   the token" is a rule that holds until the one time it doesn't.
"""

import json
import logging
import re
import sys
from typing import Any, Final

from signora_platform.observability.context import current_context

_SENSITIVE_KEY_PATTERN: Final = re.compile(
    r"(password|secret|token|authorization|api[_-]?key|private[_-]?key|credential|cookie)",
    re.IGNORECASE,
)
REDACTED: Final = "[REDACTED]"

# Matches a JWT anywhere in free text. Tokens reach logs most often inside
# an exception message or a URL rather than as a named field, so key-based
# redaction alone is not sufficient.
_JWT_PATTERN: Final = re.compile(r"\beyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")

_BEARER_PATTERN: Final = re.compile(r"(?i)\b(bearer\s+)\S+")

_STANDARD_ATTRS: Final = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    }
)


def redact(value: Any) -> Any:
    """Recursively redact secrets from a value about to be logged.

    Applies both key-based redaction (a field *named* like a secret) and
    value-based redaction (a JWT or bearer token appearing in free text),
    because either alone leaves a real gap.
    """
    if isinstance(value, dict):
        return {
            key: (REDACTED if _SENSITIVE_KEY_PATTERN.search(str(key)) else redact(item))
            for key, item in value.items()
        }
    if isinstance(value, list | tuple):
        return [redact(item) for item in value]
    if isinstance(value, str):
        return _BEARER_PATTERN.sub(rf"\1{REDACTED}", _JWT_PATTERN.sub(REDACTED, value))
    return value


class JsonFormatter(logging.Formatter):
    """Renders records as single-line JSON, merging in ambient context.

    Structured rather than free text so logs are queryable — grepping a
    multi-process async pipeline for a correlation id is not a workable
    debugging strategy at any real volume.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        payload.update(current_context())

        # Anything passed via logger.info(..., extra={...}).
        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS and not key.startswith("_"):
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(redact(payload), default=str, separators=(",", ":"))


def configure_logging(*, level: str = "INFO", json_output: bool = True) -> None:
    """Install the root logging configuration for a process.

    Called once at process start by ``apps/api`` and ``apps/worker``.
    Replaces existing handlers rather than adding to them, so repeated
    calls (in tests, or under a reloader) do not duplicate every line.
    """
    root = logging.getLogger()
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        JsonFormatter() if json_output else logging.Formatter("%(levelname)s %(name)s %(message)s")
    )
    root.addHandler(handler)
    root.setLevel(level.upper())

    # uvicorn installs its own handlers; without this its access log bypasses
    # the JSON formatter and context, producing two log formats in one stream.
    for noisy in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        logger = logging.getLogger(noisy)
        logger.handlers.clear()
        logger.propagate = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
