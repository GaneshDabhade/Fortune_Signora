"""What Integrations promises other modules, asserted rather than read.

**Written for [B-109](../../../docs/BUGS.md)**, which found `public/__init__.py`
at 0% — the module's only contract with the rest of the repository had never
been imported by a test, so nothing would have noticed if a re-export broke.

**A `public/` module is the one file whose *absences* are load-bearing.** The
docstring states them: a consumer may learn that a connection exists, whether
it is usable, and how to obtain an execution context — **never how a credential
was acquired, stored or refreshed.** A name added here is a promise; these
assert the promise is exactly the one that was made.
"""

from __future__ import annotations

import modules.integrations.public as public


class TestTheSurface:
    def test_it_exports_what_it_says_it_exports(self) -> None:
        assert set(public.__all__) == {
            "ConnectedAccount",
            "ConnectionState",
            "ConnectionUnusable",
            "Credential",
            "ExecutionContext",
        }

    def test_every_exported_name_resolves(self) -> None:
        """`__all__` is a claim, and an entry naming nothing fails only at the
        moment a consumer imports it."""
        missing = [name for name in public.__all__ if not hasattr(public, name)]
        assert missing == []


class TestWhatItMustNeverPublish:
    def test_no_credential_lifecycle_reaches_a_consumer(self) -> None:
        """*"never how a credential was acquired, stored or refreshed."*

        A consumer that could see a refresh, a secret reference or a token
        store would be able to build its own credential handling — and the
        second implementation of that is the one nobody reviews.
        """
        forbidden = ("refresh", "token", "secret", "oauth", "store", "vault", "encrypt")
        offenders = [
            name
            for name in public.__all__
            for word in forbidden
            if word in name.lower()
        ]
        assert offenders == []

    def test_it_publishes_no_repository_or_session(self) -> None:
        """The direction of the 2026-08-02 ruling made physical: Provider
        Platform consumes a Connected Account, and never learns where one is
        stored."""
        leaked = [
            name
            for name in public.__all__
            if name.endswith(("Repository", "Session", "Model", "Row"))
        ]
        assert leaked == []
