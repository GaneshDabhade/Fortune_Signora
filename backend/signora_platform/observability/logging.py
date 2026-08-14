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

# **The password inside a connection string** — `postgres://user:secret@host`.
# ⛔ **The gap that made this ADR's invariant worth writing** (ADR-0412): every
# credential this platform actually holds is a URI. `SIGNORA_DATABASE_URL`,
# `SIGNORA_REDIS_URL` and the object-store URL are the secrets most likely to
# reach a log, and none of them was caught: the key is `url`, so the key
# pattern misses it, and the value is neither a JWT nor a bearer token.
#
# ⚡ **Measured, not foreseen** — `logging.getLogger(...).info("connecting to
# postgres://signora_app:S3cr3tPassw0rd@db:5432/signora")` emitted the password
# verbatim through the JSON formatter with redaction enabled.
#
# **The userinfo alone is replaced**, never the whole URI: a redacted host and
# database name would remove the diagnostic value the line exists for, and the
# username is not the secret.
#
# ⚠️ **The username is `*` and not `+`, and that was a live miss.** The first
# version required one, and `redis://:secret@cache:6379/2` — **the form Redis
# URLs actually take, with no username** — walked straight through it. Caught
# by the check written to prove the fix, which is the argument for writing one.
#
# ⚠️ **And the password is `[^\s]*` — greedy to the LAST `@` — which was the
# second live miss.** With `[^\s@]+` it stopped at the *first* `@`, so
# `postgres://user:p@ss@host/db` redacted `p` and left `ss` standing. **A
# password containing an unencoded `@` is malformed per RFC 3986 and happens
# anyway**, and a partial leak is a leak: for `S3cr@tP@ssw0rd` it would have
# published `tP` and `ssw0rd`.
#
# ⛔ **Greedy is the safe direction here.** Two URIs run together without
# whitespace over-redact rather than under-redact, and losing a host name is
# recoverable where losing a password is not.
_URI_CREDENTIAL_PATTERN: Final = re.compile(r"(?i)\b([a-z][a-z0-9+.-]*://[^\s:/@]*):[^\s]*@")

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
        redacted = _JWT_PATTERN.sub(REDACTED, value)
        redacted = _BEARER_PATTERN.sub(rf"\1{REDACTED}", redacted)
        return _URI_CREDENTIAL_PATTERN.sub(rf"\1:{REDACTED}@", redacted)
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


class PlainFormatter(logging.Formatter):
    """Human-readable output, **redacted on the same terms as JSON.**

    ⛔ **Added by ADR-0412, and it closes a real hole.** `json_output=False`
    previously installed a bare `logging.Formatter`, so **the only sink that
    redacted anything was the JSON one** — a developer who turned on readable
    logs turned off redaction, without asking to and without being told.

    📁 The ruling is explicit: ***"A developer must opt IN to verbosity, never
    opt OUT of redaction"***, and *"the default is safe"* in **every**
    environment. ⚡ **A format choice must not be a security choice**, which is
    what it silently was.
    """

    def format(self, record: logging.LogRecord) -> str:
        rendered = super().format(record)
        redacted = redact(rendered)
        return redacted if isinstance(redacted, str) else rendered


def configure_logging(*, level: str = "INFO", json_output: bool = True) -> None:
    """Install the root logging configuration for a process.

    Called once at process start by ``apps/api`` and ``apps/worker``.
    Replaces existing handlers rather than adding to them, so repeated
    calls (in tests, or under a reloader) do not duplicate every line.

    ⚠️ **`json_output` chooses a FORMAT and never a level of protection**
    (ADR-0412). Both formatters redact; the flag decides whether a human or a
    log aggregator is reading.
    """
    root = logging.getLogger()
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        JsonFormatter()
        if json_output
        else PlainFormatter("%(levelname)s %(name)s %(message)s")
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
