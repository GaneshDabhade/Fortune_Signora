"""Authentication configuration health for the API tier.

The API's share of authentication is narrow — verify a signature, validate
claims — but it fails in ways that are invisible until a request arrives: a
malformed public key, a missing issuer, or (the one that matters most) a
*private* key mistakenly configured here.

These checks surface those at startup and on the readiness endpoint rather
than on a user's first request.
"""

from dataclasses import dataclass
from typing import Literal

from signora_platform.auth.jwt_verifier import ALLOWED_ALGORITHMS
from signora_platform.settings import Settings

CheckStatus = Literal["ok", "degraded", "unavailable"]

_PRIVATE_KEY_MARKERS = ("BEGIN PRIVATE KEY", "BEGIN RSA PRIVATE KEY", "BEGIN EC PRIVATE KEY")


@dataclass(frozen=True)
class AuthHealthReport:
    status: CheckStatus
    public_key: CheckStatus
    jwt_configuration: CheckStatus
    algorithm_pinning: CheckStatus
    detail: str | None = None


def check_auth_health(settings: Settings) -> AuthHealthReport:
    """Validate the API's JWT verification configuration."""
    key = settings.jwt_public_key.strip()

    # The most serious misconfiguration this tier can have. A private key
    # here would make the API capable of minting tokens it accepts, which is
    # precisely the property ADR-0026 chose asymmetric signing to prevent.
    if any(marker in key for marker in _PRIVATE_KEY_MARKERS):
        return AuthHealthReport(
            status="unavailable",
            public_key="unavailable",
            jwt_configuration="unavailable",
            algorithm_pinning="ok",
            detail=(
                "A PRIVATE key is configured as SIGNORA_JWT_PUBLIC_KEY. The API must "
                "never hold a signing key (ADR-0026)."
            ),
        )

    if not key or "BEGIN PUBLIC KEY" not in key:
        return AuthHealthReport(
            status="unavailable",
            public_key="unavailable",
            jwt_configuration="ok",
            algorithm_pinning="ok",
            detail="SIGNORA_JWT_PUBLIC_KEY is missing or is not a PEM public key.",
        )

    if not settings.jwt_issuer or not settings.jwt_audience:
        return AuthHealthReport(
            status="unavailable",
            public_key="ok",
            jwt_configuration="unavailable",
            algorithm_pinning="ok",
            detail="JWT issuer and audience must both be configured.",
        )

    # Guards against a future change widening the allowed-algorithm list,
    # which would reopen alg:none and algorithm-confusion attacks.
    if ALLOWED_ALGORITHMS != ["RS256"]:
        return AuthHealthReport(
            status="unavailable",
            public_key="ok",
            jwt_configuration="ok",
            algorithm_pinning="unavailable",
            detail=f"Allowed algorithms must be exactly ['RS256'], got {ALLOWED_ALGORITHMS}.",
        )

    return AuthHealthReport(
        status="ok", public_key="ok", jwt_configuration="ok", algorithm_pinning="ok"
    )
