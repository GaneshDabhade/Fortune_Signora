"""RS256 JWT verification — the API's entire authentication surface.

Per ADR-0026, this tier does not authenticate users. It verifies tokens
minted by Better Auth in Next.js, using a public key only, and converts a
valid token into an ``AuthenticatedPrincipal``.
"""

from typing import Any, Final
from uuid import UUID

import jwt

from signora_platform.auth.errors import ExpiredTokenError, InvalidTokenError
from signora_platform.auth.principal import AuthenticatedPrincipal

ALLOWED_ALGORITHMS: Final[list[str]] = ["RS256"]
"""Pinned to exactly RS256. This is a security control, not configuration.

An unpinned verifier accepts whatever the token's own header claims, which
enables two classic attacks: ``alg: none`` forgery, and algorithm confusion
in which a token is re-signed with HS256 using the RSA *public* key — which
is not secret — as the HMAC secret. Never widen this list, and never make it
caller-supplied.
"""

CLOCK_SKEW_LEEWAY_SECONDS: Final[int] = 60
"""Tolerance applied to ``exp`` and ``nbf`` for clock drift between the
Next.js and FastAPI hosts. Deliberately small — a generous leeway silently
extends the usable life of expired tokens. If expiry failures appear in
production, fix host time synchronisation rather than widening this.
"""

_REQUIRED_CLAIMS: Final[tuple[str, ...]] = (
    "sub",
    "sid",
    "email",
    "email_verified",
    "jti",
    "exp",
    "iat",
    "iss",
    "aud",
)


class JwtVerifier:
    """Verifies bearer tokens against a configured public key, issuer, and
    audience.

    Holds no private key and is structurally incapable of issuing a token.
    """

    def __init__(self, *, public_key: str, issuer: str, audience: str) -> None:
        self._public_key = public_key
        self._issuer = issuer
        self._audience = audience

    def verify(self, token: str) -> AuthenticatedPrincipal:
        """Verify a token and return the authenticated principal.

        Raises ``ExpiredTokenError`` if the token has expired, or
        ``InvalidTokenError`` for every other failure.
        """
        try:
            claims: dict[str, Any] = jwt.decode(
                token,
                self._public_key,
                algorithms=ALLOWED_ALGORITHMS,
                issuer=self._issuer,
                audience=self._audience,
                leeway=CLOCK_SKEW_LEEWAY_SECONDS,
                options={"require": list(_REQUIRED_CLAIMS)},
            )
        except jwt.ExpiredSignatureError as exc:
            raise ExpiredTokenError() from exc
        except jwt.InvalidTokenError as exc:
            # Covers bad signature, wrong issuer/audience, missing required
            # claims, unsupported algorithm, and malformed tokens. The
            # specific cause is retained for logging but never returned.
            raise InvalidTokenError(str(exc)) from exc

        return self._to_principal(claims)

    def _to_principal(self, claims: dict[str, Any]) -> AuthenticatedPrincipal:
        """Convert verified claims into a principal.

        A token can be cryptographically valid and still carry claims of the
        wrong shape (a non-UUID ``sub``, a non-boolean ``email_verified``).
        That is an invalid token, not a server error, so it is rejected here
        rather than allowed to raise deeper in the request.
        """
        try:
            user_id = UUID(str(claims["sub"]))
        except ValueError as exc:
            raise InvalidTokenError(f"'sub' is not a valid UUID: {claims['sub']!r}") from exc

        raw_workspace = claims.get("active_workspace_id")
        active_workspace_id: UUID | None = None
        if raw_workspace is not None:
            try:
                active_workspace_id = UUID(str(raw_workspace))
            except ValueError as exc:
                raise InvalidTokenError(
                    f"'active_workspace_id' is not a valid UUID: {raw_workspace!r}"
                ) from exc

        email_verified = claims["email_verified"]
        if not isinstance(email_verified, bool):
            raise InvalidTokenError("'email_verified' must be a boolean")

        return AuthenticatedPrincipal(
            user_id=user_id,
            session_id=str(claims["sid"]),
            email=str(claims["email"]),
            email_verified=email_verified,
            active_workspace_id=active_workspace_id,
            token_id=str(claims["jti"]),
        )
