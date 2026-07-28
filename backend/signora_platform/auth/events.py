"""Structured authentication events emitted by the API tier.

The API sees a narrow slice of the authentication lifecycle — it never
signs anyone in — so it emits only the events it can actually observe:
token rejection, and workspace switching. Sign-in, refresh, and logout are
the frontend's to emit, since that is where they happen (ADR-0026).

Event names are shared with the frontend deliberately, so both tiers land
in one queryable stream rather than two that must be correlated by hand.

**Never log a token or PII.** The redaction in
``signora_platform.observability.logging`` applies to everything here, but
these emitters additionally refuse to accept the fields in the first place:
a defence that depends on a downstream filter is one filter change away
from failing.
"""

from enum import StrEnum
from typing import Final
from uuid import UUID

from signora_platform.observability import get_logger

logger = get_logger("signora.auth")


class AuthEvent(StrEnum):
    """Authentication events observable from the API tier."""

    TOKEN_REJECTED = "AUTH_TOKEN_REJECTED"
    TOKEN_ACCEPTED = "AUTH_TOKEN_ACCEPTED"
    WORKSPACE_SWITCH = "AUTH_WORKSPACE_SWITCH"
    WORKSPACE_ACCESS_DENIED = "AUTH_WORKSPACE_ACCESS_DENIED"


_FAILURE_EVENTS: Final = frozenset({AuthEvent.TOKEN_REJECTED, AuthEvent.WORKSPACE_ACCESS_DENIED})


def emit_auth_event(
    event: AuthEvent,
    *,
    user_id: UUID | None = None,
    workspace_id: UUID | None = None,
    session_id: str | None = None,
    token_id: str | None = None,
    reason: str | None = None,
) -> None:
    """Emit an authentication event.

    ``reason`` must stay coarse — a value naming exactly which claim failed
    would help an attacker converge on a forgeable token. The specific cause
    is already retained on the exception for server-side diagnosis.

    ``outcome`` is derived from the event rather than passed in, so a failure
    cannot be recorded as a success by a mistaken argument.
    """
    payload: dict[str, str] = {
        "auth_event": str(event),
        "outcome": "failure" if event in _FAILURE_EVENTS else "success",
        "tier": "api",
    }
    if user_id is not None:
        payload["auth_user_id"] = str(user_id)
    if workspace_id is not None:
        payload["auth_workspace_id"] = str(workspace_id)
    if session_id is not None:
        payload["auth_session_id"] = session_id
    if token_id is not None:
        # jti is an opaque identifier, not a credential, and is what makes a
        # token traceable to a future revocation decision.
        payload["auth_token_id"] = token_id
    if reason is not None:
        payload["auth_reason"] = reason

    if event in _FAILURE_EVENTS:
        logger.warning(str(event), extra=payload)
    else:
        logger.info(str(event), extra=payload)
