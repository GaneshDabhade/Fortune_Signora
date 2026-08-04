"""What other modules may read from Integrations.

**`public/__init__.py` had never been executed by any test**, which
[B-109](../../../docs/BUGS.md) counted among five such files. The reason was
real rather than negligent: **nothing in the repository imports it.** Its only
intended consumer is whatever synchronizes through a connection, and that is
[ADR-0300](../../../docs/architecture/adr/0300-inbound-customer-systems.md)'s to
decide — so the contract has been correct and unused since it was written.

**A contract with no consumer is exactly the one worth pinning.** Nothing else
would notice it drifting: an internal type added to `__all__`, an import that
quietly drags infrastructure along behind it, a name removed while a future
consumer is being written. These assert the boundary itself, which is what
`public/` exists to be.

> **Two lanes wrote this file independently, from the same row, within hours**
> ([C-103](../../../docs/LANE_COORDINATION.md)). Lane A's version and this one
> assert *different* things and both are right, so **the union is here rather
> than a winner.** `TestNoNameCanCarryACredentialConcern` below is Lane A's
> reasoning and is stronger than what this file originally had: it forbids a
> *shape* of name rather than a list of known ones, so it catches the export
> nobody has written yet. Attributed rather than absorbed, and merged here
> because `modules/integrations` is this lane's — which is what made the
> resolution a judgement somebody had to own.
"""

from __future__ import annotations

import importlib
import pkgutil

import modules.integrations.public as public

#: The published surface, written out rather than read from `__all__`.
#:
#: **Comparing `__all__` to itself proves nothing.** The point of naming them
#: here is that widening the contract requires editing a test, which is where
#: somebody asks whether the new name belongs to another module's business.
PUBLISHED = {
    "ConnectedAccount",
    "ConnectionState",
    "ConnectionUnusable",
    "Credential",
    "ExecutionContext",
}


class TestTheContractIsExactlyWhatItSays:
    def test_it_publishes_these_five_names_and_no_others(self) -> None:
        assert set(public.__all__) == PUBLISHED

    def test_every_published_name_resolves(self) -> None:
        """An `__all__` naming something absent fails at a consumer's import,
        which is the worst place for it to fail."""
        for name in PUBLISHED:
            assert getattr(public, name, None) is not None, name

    def test_it_publishes_no_use_case(self) -> None:
        """**Deliberately narrow.** A consumer needs to know a connection
        exists, whether it is usable, and how to obtain an execution context —
        never how a credential was acquired, stored, renewed or destroyed.

        `ConnectSystem`, `DisconnectSystem` and `RefreshGrant` are this
        module's behaviour, and a consumer able to invoke them would be a
        consumer able to disconnect a customer's CRM.
        """
        assert not any(
            name in public.__all__
            for name in ("ConnectSystem", "DisconnectSystem", "RefreshGrant",
                         "ResolveExecutionContext", "IntegrationQueries")
        )

    def test_it_publishes_nothing_about_where_credentials_live(self) -> None:
        """`secret_ref`, the store, the settings and the vendor tables are all
        this module's business. **A consumer that could reach them could read a
        customer's credential**, which is the one thing the whole module is
        arranged to prevent."""
        assert not any(
            name in public.__all__
            for name in ("SecretStore", "SecretWriter", "SecretPurger",
                         "IntegrationSettings", "IntegrationGrant", "OAuth2Material")
        )


class TestNoNameCanCarryACredentialConcern:
    """**Lane A's assertions, kept because they are the better ones.**

    The tests above name the types that must not appear. These forbid a *shape*
    of name, which catches the export nobody has written yet — and that is the
    export the boundary is actually at risk from.
    """

    #: Words that describe how a credential is obtained, kept or renewed.
    FORBIDDEN = ("refresh", "token", "secret", "oauth", "store", "vault", "encrypt")

    def test_no_credential_lifecycle_reaches_a_consumer(self) -> None:
        """*"never how a credential was acquired, stored or refreshed."*

        A consumer that could see a refresh, a secret reference or a token
        store could build its own credential handling — and the second
        implementation of that is the one nobody reviews.
        """
        offenders = [
            name
            for name in public.__all__
            for word in self.FORBIDDEN
            if word in name.lower()
        ]
        assert offenders == []

    def test_it_publishes_no_repository_or_session(self) -> None:
        """The direction of the 2026-08-02 ruling made physical: Provider
        Platform consumes a Connected Account and never learns where one is
        stored."""
        leaked = [
            name
            for name in public.__all__
            if name.endswith(("Repository", "Session", "Model", "Row"))
        ]
        assert leaked == []


class TestImportingItDragsNoInfrastructure:
    def test_the_contract_does_not_reach_this_modules_infrastructure(self) -> None:
        """**A public contract that imports SQLAlchemy is not a contract.**

        `public/` is what another module compiles against, and a consumer
        importing it must not transitively acquire this module's database
        models, its HTTP adapters or its settings — that is what makes the
        boundary a boundary rather than a naming convention.

        Asserted over the import graph rather than by reading: the chain is
        `public → application → domain`, and any future edge into
        `infrastructure` fails here rather than at whatever consumer discovers
        it by deploying.
        """
        reached = _transitively_imported("modules.integrations.public")

        assert not [
            name for name in reached if name.startswith("modules.integrations.infrastructure")
        ]

    def test_it_reaches_no_other_module(self) -> None:
        """**Integrations depends on nothing** — the ownership ruling of
        2026-08-02 made physical. Provider Platform consumes this contract; it
        must never be reached back through."""
        reached = _transitively_imported("modules.integrations.public")

        assert not [
            name
            for name in reached
            if name.startswith("modules.") and not name.startswith("modules.integrations")
        ]


def _transitively_imported(root: str) -> set[str]:
    """Every module reachable from `root`, walked rather than guessed."""
    seen: set[str] = set()
    frontier = [root]
    while frontier:
        name = frontier.pop()
        if name in seen:
            continue
        seen.add(name)
        module = importlib.import_module(name)
        for attribute in vars(module).values():
            candidate = getattr(attribute, "__module__", None) or getattr(
                attribute, "__name__", None
            )
            if isinstance(candidate, str) and candidate.startswith("modules."):
                frontier.append(candidate)
        if hasattr(module, "__path__"):
            frontier.extend(
                f"{name}.{sub.name}" for sub in pkgutil.iter_modules(module.__path__)
            )
    return seen
