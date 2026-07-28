"""Ambient request/job context propagated into every log line.

Uses ``contextvars`` so context follows an ``asyncio`` task without being
threaded through every function signature. That matters here because the
values needed for correlation — ``correlation_id``, ``workspace_id``,
``user_id`` — are established at the edge (a FastAPI dependency or an ARQ
job handler) but needed in log lines emitted many layers deeper, including
inside repositories that must not know about HTTP or job frameworks.

The alternative — passing a context object down through domain and
application layers — would put transport concerns in exactly the code
docs/architecture/15-project-structure.md keeps them out of.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Any
from uuid import UUID

_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)
_workspace_id: ContextVar[str | None] = ContextVar("workspace_id", default=None)
_user_id: ContextVar[str | None] = ContextVar("user_id", default=None)
_causation_id: ContextVar[str | None] = ContextVar("causation_id", default=None)
_event_id: ContextVar[str | None] = ContextVar("event_id", default=None)
_consumer_name: ContextVar[str | None] = ContextVar("consumer_name", default=None)

_ALL_VARS: tuple[tuple[str, ContextVar[str | None]], ...] = (
    ("correlation_id", _correlation_id),
    ("workspace_id", _workspace_id),
    ("user_id", _user_id),
    ("causation_id", _causation_id),
    ("event_id", _event_id),
    ("consumer_name", _consumer_name),
)


def current_context() -> dict[str, Any]:
    """Every context value currently set, omitting those that are not.

    Omitting rather than emitting nulls keeps log lines readable: a request
    that has no ``event_id`` should not carry a null one.
    """
    return {name: value for name, var in _ALL_VARS if (value := var.get()) is not None}


@contextmanager
def logging_context(
    *,
    correlation_id: UUID | str | None = None,
    workspace_id: UUID | str | None = None,
    user_id: UUID | str | None = None,
    causation_id: UUID | str | None = None,
    event_id: UUID | str | None = None,
    consumer_name: str | None = None,
) -> Iterator[None]:
    """Bind context for the duration of a block, restoring it on exit.

    Restoration is not optional politeness: ARQ workers reuse tasks across
    jobs, so leaked context would attribute one workspace's log lines to
    another — a correctness problem when debugging a tenant issue, and a
    confidentiality problem if those lines are shared.
    """
    tokens: list[tuple[ContextVar[str | None], Token[str | None]]] = []
    supplied = {
        _correlation_id: correlation_id,
        _workspace_id: workspace_id,
        _user_id: user_id,
        _causation_id: causation_id,
        _event_id: event_id,
        _consumer_name: consumer_name,
    }
    for var, value in supplied.items():
        if value is not None:
            tokens.append((var, var.set(str(value))))
    try:
        yield
    finally:
        for var, token in reversed(tokens):
            var.reset(token)
