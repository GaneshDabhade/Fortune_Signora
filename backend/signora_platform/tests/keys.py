"""Ephemeral RSA key material and token minting, for tests only.

Key pairs are generated in-process per test session and never written to
disk, so no fixture private key exists to leak. Tests mint tokens exactly as
Next.js would (ADR-0026), which keeps the test path identical to the
production path — there is no "skip verification" mode to diverge from.
"""

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

TEST_ISSUER = "https://auth.signora.test"
TEST_AUDIENCE = "signora-api-test"


@dataclass(frozen=True)
class KeyPair:
    private_pem: str
    public_pem: str


def generate_key_pair() -> KeyPair:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = (
        key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
    return KeyPair(private_pem=private_pem, public_pem=public_pem)


def mint_token(
    key_pair: KeyPair,
    *,
    user_id: UUID | None = None,
    session_id: str = "sess_test",
    email: str = "rep@customer.test",
    email_verified: bool = True,
    active_workspace_id: UUID | None = None,
    issuer: str = TEST_ISSUER,
    audience: str = TEST_AUDIENCE,
    expires_in: timedelta = timedelta(minutes=15),
    issued_at: datetime | None = None,
    algorithm: str = "RS256",
    signing_key: str | None = None,
    omit_claims: tuple[str, ...] = (),
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Mint a token. Every parameter that a negative test needs to corrupt —
    issuer, audience, expiry, algorithm, signing key, missing claims — is
    overridable, so attack cases are expressed as data rather than as
    hand-built token strings."""
    now = issued_at or datetime.now(UTC)
    claims: dict[str, Any] = {
        "iss": issuer,
        "aud": audience,
        "sub": str(user_id or uuid4()),
        "sid": session_id,
        "email": email,
        "email_verified": email_verified,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_in).timestamp()),
        "jti": f"tok_{uuid4().hex}",
    }
    if active_workspace_id is not None:
        claims["active_workspace_id"] = str(active_workspace_id)
    for claim in omit_claims:
        claims.pop(claim, None)
    if extra_claims:
        claims.update(extra_claims)

    return jwt.encode(claims, signing_key or key_pair.private_pem, algorithm=algorithm)


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def forge_alg_none_token(claims: dict[str, Any]) -> str:
    """Hand-craft an ``alg: none`` token.

    Built manually because PyJWT refuses to *mint* one — a guardrail on the
    signing side that says nothing about whether our verifier would accept
    it. Simulating the attack faithfully requires bypassing that guardrail,
    exactly as an attacker would.
    """
    header = _b64(json.dumps({"alg": "none", "typ": "JWT"}).encode())
    payload = _b64(json.dumps(claims).encode())
    return f"{header}.{payload}."


def forge_hs256_token_signed_with(claims: dict[str, Any], *, secret: str) -> str:
    """Hand-craft an HS256 token signed with an arbitrary secret.

    Used to simulate algorithm confusion, where the attacker signs with the
    RSA *public* key — which is not secret. PyJWT blocks minting this, so
    the HMAC is computed directly.
    """
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64(json.dumps(claims).encode())
    signing_input = f"{header}.{payload}".encode()
    signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    return f"{header}.{payload}.{_b64(signature)}"


def valid_claims(
    *, user_id: UUID | None = None, issuer: str = TEST_ISSUER, audience: str = TEST_AUDIENCE
) -> dict[str, Any]:
    """A well-formed claim set, for forging attack tokens whose *only*
    defect is the signature or algorithm."""
    now = datetime.now(UTC)
    return {
        "iss": issuer,
        "aud": audience,
        "sub": str(user_id or uuid4()),
        "sid": "sess_test",
        "email": "rep@customer.test",
        "email_verified": True,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=15)).timestamp()),
        "jti": f"tok_{uuid4().hex}",
    }
