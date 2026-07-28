"""Cross-tier JWT contract test.

**The single highest-value test in M1.2.** Every other test in either tier
verifies one side's understanding of the boundary; this one is the only
check that the two sides actually agree.

It shells out to the real TypeScript issuance path (`lib/auth/jwt.ts`, via
`tests/contract/mint-token.ts`) and verifies the resulting token with the
real Python verifier. Nothing is mocked, and neither side's claim set is
restated here — a hand-written token would pass while production drifted,
which is exactly the failure this exists to catch.

Skips rather than fails when Node or the frontend dependencies are absent,
so a backend-only environment is not blocked. CI installs both, so the test
runs there.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from signora_platform.auth import JwtVerifier
from signora_platform.tests.keys import generate_key_pair

ISSUER = "https://auth.signora.contract-test"
AUDIENCE = "signora-api-contract-test"

_FRONTEND = Path(__file__).resolve().parents[3] / "frontend"
_MINTER = _FRONTEND / "tests" / "contract" / "mint-token.ts"

_reason = None
if shutil.which("npx") is None:
    _reason = "Node/npx unavailable"
elif not (_FRONTEND / "node_modules").exists():
    _reason = "frontend dependencies not installed"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(_reason is not None, reason=_reason or ""),
]


def _mint(private_pem: str) -> str:
    """Mint a token using the frontend's production issuance code."""
    result = subprocess.run(  # noqa: S603 - fixed argv, no shell
        ["npx", "tsx", str(_MINTER), private_pem, ISSUER, AUDIENCE],
        capture_output=True,
        text=True,
        cwd=_FRONTEND,
        timeout=120,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(f"Frontend token minting failed:\n{result.stderr}")
    return result.stdout.strip()


class TestCrossTierContract:
    def test_frontend_minted_token_verifies_with_the_python_verifier(self) -> None:
        """The boundary works end to end.

        If this fails, authentication is broken in production regardless of
        how green each tier's own tests are.
        """
        key_pair = generate_key_pair()

        token = _mint(key_pair.private_pem)
        principal = JwtVerifier(
            public_key=key_pair.public_pem, issuer=ISSUER, audience=AUDIENCE
        ).verify(token)

        assert str(principal.user_id) == "3f6c8a1e-0000-4000-8000-000000000001"
        assert principal.session_id == "sess_contract_test"
        assert principal.email == "contract@signora.test"
        assert principal.email_verified is True
        assert str(principal.active_workspace_id) == "8b0f2c4d-0000-4000-8000-000000000002"
        assert principal.token_id

    def test_frontend_token_is_rejected_by_a_different_public_key(self) -> None:
        """Confirms the verification above was real rather than incidental."""
        signing_pair = generate_key_pair()
        unrelated_pair = generate_key_pair()

        token = _mint(signing_pair.private_pem)
        verifier = JwtVerifier(
            public_key=unrelated_pair.public_pem, issuer=ISSUER, audience=AUDIENCE
        )

        from signora_platform.auth import InvalidTokenError

        with pytest.raises(InvalidTokenError):
            verifier.verify(token)

    def test_frontend_token_is_rejected_for_the_wrong_audience(self) -> None:
        """A token minted for another service must not be replayable here."""
        key_pair = generate_key_pair()

        token = _mint(key_pair.private_pem)
        verifier = JwtVerifier(
            public_key=key_pair.public_pem, issuer=ISSUER, audience="some-other-service"
        )

        from signora_platform.auth import InvalidTokenError

        with pytest.raises(InvalidTokenError):
            verifier.verify(token)
