"""Invariants: only a correctly-signed, correctly-scoped token is accepted,
and this tier is incapable of producing one.

The second half matters as much as the first. Verification can be perfect
and still be worthless if the verifying tier also holds a signing key —
anything able to mint a token it accepts has no boundary at all
(docs/architecture/adr/0026-jwt-boundary-architecture.md).
"""

import inspect
from datetime import timedelta
from pathlib import Path

import pytest

from signora_platform.auth import (
    ALLOWED_ALGORITHMS,
    AuthenticationError,
    ExpiredTokenError,
    InvalidTokenError,
    JwtVerifier,
    check_auth_health,
)
from signora_platform.settings import Settings
from signora_platform.tests.keys import (
    TEST_AUDIENCE,
    TEST_ISSUER,
    KeyPair,
    forge_alg_none_token,
    forge_hs256_token_signed_with,
    generate_key_pair,
    mint_token,
    valid_claims,
)

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_PACKAGES = ("signora_platform", "modules", "apps")


@pytest.fixture
def key_pair() -> KeyPair:
    return generate_key_pair()


@pytest.fixture
def verifier(key_pair: KeyPair) -> JwtVerifier:
    return JwtVerifier(public_key=key_pair.public_pem, issuer=TEST_ISSUER, audience=TEST_AUDIENCE)


class TestTokenAcceptance:
    def test_a_valid_token_is_accepted(self, verifier: JwtVerifier, key_pair: KeyPair) -> None:
        """The positive control. Without it every rejection test below would
        also pass against a verifier that rejects everything, which would
        make this file green and meaningless."""
        principal = verifier.verify(mint_token(key_pair))

        assert principal.user_id is not None
        assert principal.session_id


class TestTokenRejection:
    def test_a_foreign_signing_key_is_rejected(self, verifier: JwtVerifier) -> None:
        with pytest.raises(InvalidTokenError):
            verifier.verify(mint_token(generate_key_pair()))

    def test_an_invalid_issuer_is_rejected(self, verifier: JwtVerifier, key_pair: KeyPair) -> None:
        """A token from a different Better Auth deployment is correctly
        signed for *its* system, not ours."""
        with pytest.raises(InvalidTokenError):
            verifier.verify(mint_token(key_pair, issuer="https://not-signora.example"))

    def test_an_invalid_audience_is_rejected(
        self, verifier: JwtVerifier, key_pair: KeyPair
    ) -> None:
        """Audience is what stops a token minted for another service in the
        same trust domain being replayed against this API."""
        with pytest.raises(InvalidTokenError):
            verifier.verify(mint_token(key_pair, audience="some-other-service"))

    def test_an_expired_token_is_rejected(self, verifier: JwtVerifier, key_pair: KeyPair) -> None:
        """Expiry raises its own type rather than the generic rejection. It
        is the one failure a legitimate client can act on — refresh and
        retry — and collapsing it into ``InvalidTokenError`` would make a
        routine token rotation indistinguishable from an attack.

        It must still be a rejection: the shared base is what any handler
        catching authentication failures relies on.
        """
        with pytest.raises(ExpiredTokenError) as exc_info:
            verifier.verify(mint_token(key_pair, expires_in=timedelta(hours=-1)))

        assert isinstance(exc_info.value, AuthenticationError)
        assert not isinstance(exc_info.value, InvalidTokenError)

    def test_alg_none_is_rejected(self, verifier: JwtVerifier) -> None:
        """The classic JWT forgery: strip the signature and declare the
        algorithm ``none``.

        The token is hand-forged rather than produced by PyJWT, which
        refuses to *mint* one — a test built on PyJWT would pass without the
        verifier being involved at all.
        """
        with pytest.raises(InvalidTokenError):
            verifier.verify(forge_alg_none_token(valid_claims()))

    def test_algorithm_confusion_is_rejected(
        self, verifier: JwtVerifier, key_pair: KeyPair
    ) -> None:
        """RSA public keys are not secret. If the verifier accepted HS256, an
        attacker could sign a token using the *public* key as the HMAC secret
        and the verifier would confirm it against the same value."""
        forged = forge_hs256_token_signed_with(valid_claims(), secret=key_pair.public_pem)

        with pytest.raises(InvalidTokenError):
            verifier.verify(forged)

    def test_a_malformed_token_is_rejected(self, verifier: JwtVerifier) -> None:
        for garbage in ("", "not-a-token", "a.b.c", "Bearer x"):
            with pytest.raises(InvalidTokenError):
                verifier.verify(garbage)


class TestAlgorithmPinning:
    """The single configuration value that makes the two attacks above
    impossible rather than merely unlikely."""

    def test_exactly_one_algorithm_is_permitted(self) -> None:
        assert ALLOWED_ALGORITHMS == ["RS256"]

    def test_the_allowed_list_cannot_be_widened_by_a_caller(self) -> None:
        """An ``algorithms`` parameter on the verifier would let a call site
        reopen alg:none locally, and no amount of pinning at the constant
        would help."""
        parameters = inspect.signature(JwtVerifier.__init__).parameters

        assert "algorithms" not in parameters
        assert "algorithm" not in parameters


class TestThisTierCannotIssueTokens:
    def test_the_verifier_has_no_signing_capability(self) -> None:
        for forbidden in ("sign", "issue", "mint", "encode"):
            assert not hasattr(JwtVerifier, forbidden), (
                f"JwtVerifier.{forbidden} would make the API able to mint tokens it accepts"
            )

    def test_a_private_key_is_refused_as_configuration(self) -> None:
        """The misconfiguration that would quietly grant this tier signing
        power. It must fail readiness, not be accepted because a private key
        happens to also contain the public one."""
        report = check_auth_health(
            Settings(
                environment="test",
                database_url="postgresql+asyncpg://u:p@localhost:5432/db",
                jwt_public_key=generate_key_pair().private_pem,
                jwt_issuer=TEST_ISSUER,
                jwt_audience=TEST_AUDIENCE,
            )
        )

        assert report.status == "unavailable"

    def test_no_production_source_carries_private_key_material(self) -> None:
        """Tests legitimately construct private keys in order to prove they
        are rejected; ``health.py`` names the PEM marker in order to detect
        the misconfiguration above. Both are the opposite of holding a key,
        so only production packages are scanned and health.py is exempt."""
        offenders = [
            path.relative_to(BACKEND_ROOT)
            for package in PRODUCTION_PACKAGES
            for path in (BACKEND_ROOT / package).rglob("*.py")
            if "BEGIN PRIVATE KEY" in path.read_text() and path.name != "health.py"
        ]

        assert offenders == [], f"private key material in production code: {offenders}"

    def test_the_settings_surface_has_nowhere_to_put_a_credential(self) -> None:
        """Defence against the gap reopening by configuration rather than by
        code: if no field accepts a secret, no deployment can supply one."""
        auth_fields = {name for name in Settings.model_fields if "jwt" in name or "auth" in name}

        assert auth_fields == {"jwt_public_key", "jwt_issuer", "jwt_audience"}


class TestFailureDisclosure:
    def test_the_reason_a_token_failed_is_not_returned_to_the_caller(
        self, verifier: JwtVerifier, key_pair: KeyPair
    ) -> None:
        """A caller told precisely which claim failed can iterate towards a
        token that passes. The reason is kept for logs, not for the response.
        """
        with pytest.raises(InvalidTokenError) as exc_info:
            verifier.verify(mint_token(key_pair, audience="wrong"))

        assert "audience" not in str(exc_info.value).lower()
