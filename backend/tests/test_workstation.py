"""A workstation setup command must never send somebody to break a working one.

RS-2. `backend/.env` and `frontend/.env.local` hold a generated RSA pair that is
**correctly never committed** and **not reproducible** — regenerating it
invalidates every session, and a mismatched pair mints tokens the API rejects
with no clue why. Nothing described the recovery as a procedure, which QE
discovered by performing it by hand ([`REPOSITORY_RESILIENCE.md`](../../docs/REPOSITORY_RESILIENCE.md) R-5).

**The first version of the mismatch check produced a false positive on the first
workstation it was run against**, and that is the case these tests exist for.
`.env.example` writes the PEM escaped onto one line; a value pasted from
`openssl` arrives as real newlines inside quotes. **Two encodings of one key are
the same key.** Comparing raw text reported *"the two tiers hold DIFFERENT
public keys"* about a workstation whose halves `openssl rsa -pubout` confirmed
matching.

> **A setup check that cries wolf is worse than no setup check.** Its advice is
> `--force`, which regenerates the pair — so a false positive tells somebody to
> destroy the working configuration it failed to recognise.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

#: One real key, in the two encodings the repository actually produces.
_BODY = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxqYtyUINJl0zXMnO6boC"
ESCAPED = f'SIGNORA_JWT_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\\n{_BODY}\\n-----END PUBLIC KEY-----"\n'
LITERAL = f'SIGNORA_JWT_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\n{_BODY}\n-----END PUBLIC KEY-----"\n'


@pytest.fixture(scope="module")
def workstation() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "workstation", REPO_ROOT / "infra" / "workstation.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_two_encodings_of_one_key_compare_equal(
    workstation: ModuleType, tmp_path: Path
) -> None:
    """**The false positive, as a test.**

    This is the exact pair of files that existed on QE's workstation when the
    check first ran and wrongly reported a mismatch.
    """
    escaped = tmp_path / "frontend.env"
    literal = tmp_path / "backend.env"
    escaped.write_text(ESCAPED)
    literal.write_text(LITERAL)

    assert workstation.public_key(escaped) == workstation.public_key(literal)
    assert _BODY in (workstation.public_key(escaped) or "")


def test_genuinely_different_keys_still_compare_unequal(
    workstation: ModuleType, tmp_path: Path
) -> None:
    """**The control**, and the reason normalising is not the same as ignoring.

    Fixing the false positive by comparing nothing would have been easy and
    useless. The check must still catch the failure it exists for: a public half
    that does not belong to the private half in the other tier.
    """
    ours = tmp_path / "a.env"
    theirs = tmp_path / "b.env"
    ours.write_text(ESCAPED)
    theirs.write_text(ESCAPED.replace(_BODY, "DIFFERENTKEYENTIRELY0000000000000000000000"))

    assert workstation.public_key(ours) != workstation.public_key(theirs)


def test_an_absent_file_is_not_a_mismatch(workstation: ModuleType, tmp_path: Path) -> None:
    """*Missing* and *wrong* are different findings with different remedies —
    one is `make workstation`, the other is `--force`. Reporting a mismatch for
    a file that does not exist would send somebody to regenerate a pair that was
    never the problem."""
    assert workstation.public_key(tmp_path / "nothing.env") is None


def test_setup_never_overwrites_without_being_told(workstation: ModuleType) -> None:
    """**A `.env` holds the only copy of a working pair.**

    A setup command that quietly replaced one would be the exact class of defect
    the resilience work is about — irreplaceable local state destroyed by a
    command that looked routine. Asserted against the source because the
    behaviour is a branch, and a branch is easy to invert by accident.
    """
    source = (REPO_ROOT / "infra" / "workstation.py").read_text()
    assert "if existing and not force:" in source, (
        "the guard on overwriting an existing configuration was removed"
    )
    assert "Every existing session stops verifying" in source, (
        "the warning printed before regenerating is gone; --force is now silent"
    )


def test_it_reuses_the_repositorys_own_key_generator(workstation: ModuleType) -> None:
    """**No second implementation of key generation.**

    `npm run keys:generate` is what `RUNNING.md` documents and what already
    escapes both halves for a `.env`. A duplicate here would drift from it the
    first time the format changed — and the drift would be silent, because both
    would produce *a* key.
    """
    source = (REPO_ROOT / "infra" / "workstation.py").read_text()
    assert "keys:generate" in source
    assert "rsa.generate" not in source and "RSA.generate" not in source


def test_the_generator_output_is_validated_before_being_written(
    workstation: ModuleType,
) -> None:
    """If `keys:generate` changes its output format, this must fail loudly.

    The alternative is writing an empty key into both tiers and discovering it
    as a 401 storm with nothing naming the cause — which is precisely the
    failure this command exists to prevent, reintroduced by the command itself.
    """
    source = (REPO_ROOT / "infra" / "workstation.py").read_text()
    assert "did not print a pair in the expected form" in source
