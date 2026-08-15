"""The suite refuses to truncate the database a person is reviewing the product in.

⛔ **[B-270](../../docs/BUGS.md).** `require_explicit_consent_to_truncate` asks
*"do you consent to truncation?"* and **never** *"which database?"* — and the
answer to the first was correctly **yes** every time. `make test` supplied the
consent flag with **no database variable**, so a shell without `SIGNORA_TEST_*`
fell through `DEFAULT_APP_DATABASE_URL` to human review's database and emptied
it. **No mistake was required: new shell → documented gate → slot 0 gone.**
Lane A hit it exactly that way and escalated it.

⚡ **Lane C closed the `make` half** — `DESTRUCTIVE_DB_ENV` names a database in
the same breath as the consent, and `refuse-slot-0` blocks the targets. ⛔ **This
closes the half a `Makefile` cannot reach: a bare `pytest`**, which is how it was
actually found.

🔴 **The discrimination is on the DATABASE, not the cluster, and that is
load-bearing.** `make certify` creates a disposable `signora_certify_<sha>` **on
`localhost:5432`** — slot 0's cluster — because `tests/certification/database.py`
pins `_HOST` there. ⚡ **A port-based refusal would break every certification
run.** **Measured before the guard was written, not discovered afterwards.**
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _conftest() -> ModuleType:
    """The real `conftest.py`, loaded as a module so its guard can be called.

    ⚠️ **Not imported as `tests.conftest`** — pytest has already loaded that as
    the active plugin, and re-entering it would rebind fixtures underneath the
    running session.
    """
    spec = importlib.util.spec_from_file_location(
        "_conftest_under_test", REPO_ROOT / "backend" / "tests" / "conftest.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["_conftest_under_test"] = module
    spec.loader.exec_module(module)
    return module


REFUSED = [
    pytest.param(
        "postgresql+asyncpg://a:b@localhost:5432/signora",
        id="human-reviews-database-exactly",
    ),
]

ALLOWED = [
    pytest.param(
        "postgresql+asyncpg://a:b@localhost:5432/signora_certify_9a01139c125b",
        id="certifications-disposable-database-on-slot-0s-CLUSTER",
    ),
    pytest.param(
        "postgresql+asyncpg://a:b@localhost:5632/signora",
        id="QEs-own-cluster-same-database-NAME",
    ),
    pytest.param(
        "postgresql+asyncpg://a:b@localhost:5732/signora",
        id="lane-As-cluster",
    ),
    pytest.param(
        "postgresql+asyncpg://a:b@localhost:5432/signora_lane_qe",
        id="a-legacy-lane-database-on-slot-0s-cluster",
    ),
]


@pytest.mark.parametrize("url", REFUSED)
def test_human_reviews_database_is_refused(
    monkeypatch: pytest.MonkeyPatch, url: str
) -> None:
    """⛔ **The defect, asserted.** Consent was given and the target was wrong."""
    monkeypatch.setenv("SIGNORA_TEST_APP_DATABASE_URL", url)
    monkeypatch.setenv("SIGNORA_TEST_ADMIN_DATABASE_URL", url)
    monkeypatch.delenv("ALLOW_SLOT_0", raising=False)
    with pytest.raises(RuntimeError, match="human review"):
        _conftest()._refuse_human_reviews_database()


@pytest.mark.parametrize("url", ALLOWED)
def test_every_other_target_passes(monkeypatch: pytest.MonkeyPatch, url: str) -> None:
    """🔴 **The cases that make this a guard rather than a blockade.**

    ⚡ **The first is the one that matters most**: certification runs on slot 0's
    *cluster* with a disposable *database*, and refusing it would take the
    repository's release gate offline. **Verified live before this test existed —
    15 invariants passed against an existing `signora_certify_*` on `5432`.**

    ⛔ **The second is the mirror**: the database NAME is `signora` everywhere
    after [B-271](../../docs/BUGS.md), so a name-only check would refuse every
    lane, and a port-only check would refuse certification. **Only the pair
    discriminates.**
    """
    monkeypatch.setenv("SIGNORA_TEST_APP_DATABASE_URL", url)
    monkeypatch.setenv("SIGNORA_TEST_ADMIN_DATABASE_URL", url)
    monkeypatch.delenv("ALLOW_SLOT_0", raising=False)
    _conftest()._refuse_human_reviews_database()


def test_the_admin_url_is_checked_too(monkeypatch: pytest.MonkeyPatch) -> None:
    """**Both URLs, because `clean_database` truncates through the ADMIN engine.**

    ⛔ A guard that checked only the app URL would pass a run whose truncation
    target was human review's database — **the one connection that actually does
    the damage.**
    """
    monkeypatch.setenv("SIGNORA_TEST_APP_DATABASE_URL", "postgresql+asyncpg://a:b@localhost:5632/signora")
    monkeypatch.setenv("SIGNORA_TEST_ADMIN_DATABASE_URL", "postgresql+asyncpg://a:b@localhost:5432/signora")
    monkeypatch.delenv("ALLOW_SLOT_0", raising=False)
    with pytest.raises(RuntimeError, match="ADMIN"):
        _conftest()._refuse_human_reviews_database()


def test_the_unset_fallback_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """🔴 **Lane A's actual path, and the reason this file exists.**

    ⛔ With neither variable set, `conftest` falls through to
    `DEFAULT_APP_DATABASE_URL` — **human review's database** — and the old guard
    saw only that consent had been given. **The fallback must be refused, not
    merely the explicit value.**
    """
    monkeypatch.delenv("SIGNORA_TEST_APP_DATABASE_URL", raising=False)
    monkeypatch.delenv("SIGNORA_TEST_ADMIN_DATABASE_URL", raising=False)
    monkeypatch.delenv("ALLOW_SLOT_0", raising=False)
    with pytest.raises(RuntimeError, match="human review"):
        _conftest()._refuse_human_reviews_database()


def test_allow_slot_zero_is_the_escape(monkeypatch: pytest.MonkeyPatch) -> None:
    """✅ **The same escape `refuse-slot-0` uses in the `Makefile`, deliberately.**

    ⛔ **The environment genuinely cannot distinguish a reviewer from a lane** —
    seeding slot 0 is exactly what a reviewer wants and exactly what a lane must
    never do — **so the human states which.** ⚡ **One vocabulary rather than two:
    a second variable name for the same decision is how they drift.**
    """
    url = "postgresql+asyncpg://a:b@localhost:5432/signora"
    monkeypatch.setenv("SIGNORA_TEST_APP_DATABASE_URL", url)
    monkeypatch.setenv("SIGNORA_TEST_ADMIN_DATABASE_URL", url)
    monkeypatch.setenv("ALLOW_SLOT_0", "1")
    _conftest()._refuse_human_reviews_database()


def test_the_guard_is_actually_wired_in(monkeypatch: pytest.MonkeyPatch) -> None:
    """🔴 **Found by fire-testing this file, and it is the reason the file changed.**

    ⛔ **Deleting the call site from `require_explicit_consent_to_truncate` left
    every case above GREEN**, because they all invoke the guard directly. **A
    function that exists and is never called is exactly
    [B-197](../../docs/BUGS.md)** — a repair that could not run, in a gate,
    undetected because the path was never exercised.

    ⚡ **So this calls the FIXTURE**, which is the thing pytest actually runs.
    """
    import asyncio

    url = "postgresql+asyncpg://a:b@localhost:5432/signora"
    monkeypatch.setenv("SIGNORA_ALLOW_DESTRUCTIVE_TESTS", "1")
    monkeypatch.setenv("SIGNORA_TEST_APP_DATABASE_URL", url)
    monkeypatch.setenv("SIGNORA_TEST_ADMIN_DATABASE_URL", url)
    monkeypatch.delenv("ALLOW_SLOT_0", raising=False)

    module = _conftest()
    fixture = module.require_explicit_consent_to_truncate.__wrapped__
    with pytest.raises(RuntimeError, match="human review"):
        asyncio.run(fixture())


def test_the_target_is_derived_from_the_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    """⛔ **`5432` and `signora` are not written into the guard.**

    They come from `infra/environments.py`'s `review` environment, so a future
    re-slotting moves the guard with it. 📁 [B-1001](../../docs/BUGS.md)'s rule —
    **and the fallback pair exists only so an absent registry cannot silently
    disable the guard**, which is the opposite failure and the worse one.
    """
    assert _conftest()._human_review_target() == ("5432", "signora")
