"""The authenticated caller, as established from a verified JWT.

This is the *only* representation of caller identity in the system. Nothing
downstream re-reads the token; if a handler needs an identity fact the
principal does not carry, the principal is extended — the token is not
parsed a second time (docs/architecture/18-authentication.md).
"""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    """A caller whose token has passed signature and claim validation.

    Construction of this type is the assertion that verification succeeded.
    It is only ever built inside ``signora_platform.auth``.
    """

    user_id: UUID
    """The Better Auth user id (``sub``). Becomes ``app.user_id`` in the RLS
    session context."""

    session_id: str
    """The Better Auth session id (``sid``). Carried for future session-level
    revocation and to correlate API activity with a sign-in."""

    email: str
    email_verified: bool

    active_workspace_id: UUID | None
    """The workspace the user has selected, if any.

    **A routing hint, never a grant.** Membership is re-verified server-side
    against Workspace & Tenancy before any RLS context is established, so a
    stale or forged value here grants nothing.
    """

    token_id: str
    """The token's unique id (``jti``), for future replay detection and
    revocation lists."""
