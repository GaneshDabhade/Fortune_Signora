"""Unit tests for JWT verification.

The negative cases here are the security surface of the whole API — each one
corresponds to a documented attack or misconfiguration in
18-authentication.md, not to a hypothetical.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from signora_platform.auth import ExpiredTokenError, InvalidTokenError, JwtVerifier
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


@pytest.fixture(scope="module")
def key_pair() -> KeyPair:
    return generate_key_pair()


@pytest.fixture
def verifier(key_pair: KeyPair) -> JwtVerifier:
    return JwtVerifier(public_key=key_pair.public_pem, issuer=TEST_ISSUER, audience=TEST_AUDIENCE)


class TestValidTokens:
    def test_returns_principal_for_a_valid_token(
        self, verifier: JwtVerifier, key_pair: KeyPair
    ) -> None:
        user_id = uuid4()
        workspace_id = uuid4()

        principal = verifier.verify(
            mint_token(
                key_pair,
                user_id=user_id,
                active_workspace_id=workspace_id,
                session_id="sess_abc",
                email="rep@acme.test",
            )
        )

        assert principal.user_id == user_id
        assert principal.active_workspace_id == workspace_id
        assert principal.session_id == "sess_abc"
        assert principal.email == "rep@acme.test"
        assert principal.email_verified is True

    def test_active_workspace_is_optional(self, verifier: JwtVerifier, key_pair: KeyPair) -> None:
        """Absent immediately after sign-in, before a workspace is chosen."""
        principal = verifier.verify(mint_token(key_pair, active_workspace_id=None))

        assert principal.active_workspace_id is None

    def test_accepts_token_within_clock_skew_leeway(
        self, verifier: JwtVerifier, key_pair: KeyPair
    ) -> None:
        """Expired 30s ago is inside the 60s leeway, so still accepted."""
        token = mint_token(
            key_pair,
            issued_at=datetime.now(UTC) - timedelta(minutes=20),
            expires_in=timedelta(minutes=19, seconds=30),
        )

        assert verifier.verify(token) is not None


class TestRejectedTokens:
    def test_rejects_token_signed_by_a_different_key(self, verifier: JwtVerifier) -> None:
        """The core guarantee: only the real issuer's key produces a token
        this API accepts."""
        attacker = generate_key_pair()

        with pytest.raises(InvalidTokenError):
            verifier.verify(mint_token(attacker))

    def test_rejects_wrong_issuer(self, verifier: JwtVerifier, key_pair: KeyPair) -> None:
        with pytest.raises(InvalidTokenError):
            verifier.verify(mint_token(key_pair, issuer="https://evil.test"))

    def test_rejects_wrong_audience(self, verifier: JwtVerifier, key_pair: KeyPair) -> None:
        """A token minted for another service must not be replayable here."""
        with pytest.raises(InvalidTokenError):
            verifier.verify(mint_token(key_pair, audience="some-other-service"))

    def test_rejects_expired_token_beyond_leeway(
        self, verifier: JwtVerifier, key_pair: KeyPair
    ) -> None:
        token = mint_token(
            key_pair,
            issued_at=datetime.now(UTC) - timedelta(hours=2),
            expires_in=timedelta(minutes=15),
        )

        with pytest.raises(ExpiredTokenError):
            verifier.verify(token)

    def test_rejects_unsigned_alg_none_token(self, verifier: JwtVerifier) -> None:
        """The classic ``alg: none`` forgery: otherwise-valid claims with the
        signature stripped. Defeated by pinning the allowed algorithm list
        (18-authentication.md)."""
        with pytest.raises(InvalidTokenError):
            verifier.verify(forge_alg_none_token(valid_claims()))

    def test_rejects_algorithm_confusion_with_public_key_as_hmac_secret(
        self, verifier: JwtVerifier, key_pair: KeyPair
    ) -> None:
        """Algorithm confusion: the attacker re-signs with HS256 using the RSA
        *public* key — which is published, not secret — as the HMAC secret.
        A verifier that trusted the token's own ``alg`` header would compute
        the same HMAC and accept it."""
        with pytest.raises(InvalidTokenError):
            verifier.verify(
                forge_hs256_token_signed_with(valid_claims(), secret=key_pair.public_pem)
            )

    def test_rejects_garbage(self, verifier: JwtVerifier) -> None:
        with pytest.raises(InvalidTokenError):
            verifier.verify("not-a-token")

    @pytest.mark.parametrize("missing", ["sub", "sid", "email", "jti", "exp", "iat"])
    def test_rejects_token_missing_a_required_claim(
        self, verifier: JwtVerifier, key_pair: KeyPair, missing: str
    ) -> None:
        with pytest.raises(InvalidTokenError):
            verifier.verify(mint_token(key_pair, omit_claims=(missing,)))

    def test_rejects_non_uuid_subject(self, verifier: JwtVerifier, key_pair: KeyPair) -> None:
        """A cryptographically valid token can still carry claims of the
        wrong shape; that is an invalid token, not a server error."""
        with pytest.raises(InvalidTokenError):
            verifier.verify(mint_token(key_pair, extra_claims={"sub": "not-a-uuid"}))

    def test_rejects_non_uuid_active_workspace(
        self, verifier: JwtVerifier, key_pair: KeyPair
    ) -> None:
        with pytest.raises(InvalidTokenError):
            verifier.verify(mint_token(key_pair, extra_claims={"active_workspace_id": "nope"}))

    def test_rejects_non_boolean_email_verified(
        self, verifier: JwtVerifier, key_pair: KeyPair
    ) -> None:
        with pytest.raises(InvalidTokenError):
            verifier.verify(mint_token(key_pair, extra_claims={"email_verified": "yes"}))


def test_failure_reason_is_retained_for_logging_but_not_exposed(
    verifier: JwtVerifier,
) -> None:
    """The caller sees a generic message; the specific cause is kept on the
    exception for server-side logs only."""
    with pytest.raises(InvalidTokenError) as exc_info:
        verifier.verify("not-a-token")

    assert str(exc_info.value) == "The supplied token is not valid."
    assert exc_info.value.reason
