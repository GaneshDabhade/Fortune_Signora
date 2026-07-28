"""Authentication failures.

All of these map to HTTP 401. They are deliberately coarse at the boundary:
the API tells a caller *that* authentication failed, never *why* in a way
that would help forge a valid token (which claim was wrong, whether the
signature or the issuer was the problem). The specific cause is logged
server-side.
"""


class AuthenticationError(Exception):
    """Base for every authentication failure. Maps to HTTP 401."""


class MissingCredentialsError(AuthenticationError):
    def __init__(self) -> None:
        super().__init__("No bearer token was supplied.")


class InvalidTokenError(AuthenticationError):
    """Signature, issuer, audience, or structural validation failed.

    Deliberately does not distinguish between these cases in its public
    message — see the module docstring.
    """

    def __init__(self, reason: str) -> None:
        super().__init__("The supplied token is not valid.")
        self.reason = reason
        """Specific cause, for server-side logging only. Never returned to
        the caller."""


class ExpiredTokenError(AuthenticationError):
    """Separated from ``InvalidTokenError`` because expiry is the one failure
    a legitimate client must be able to act on: it signals "refresh and retry"
    rather than "your credentials are wrong". Refresh is handled by Next.js
    (ADR-0026); this API has no refresh endpoint."""

    def __init__(self) -> None:
        super().__init__("The supplied token has expired.")
