"""The watch list's own rules, with no database and no HTTP.

The fifth declaration, and the first that announces itself. These assert what
the module records, what it refuses, and — the part that is new — **that the
announcement says exactly what ADR-0036 says it may say and nothing more.**
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from modules.commercial_profile.application.declare_target_accounts import (
    DeclareTargetAccounts,
    DeclareTargetAccountsInput,
    TargetAccountsVersionConflictError,
)
from modules.commercial_profile.domain.events import (
    EVENT_TYPE,
    EVENT_VERSION,
    TargetAccountsChanged,
)
from modules.commercial_profile.domain.target_accounts import (
    MAX_ACCOUNTS,
    MAX_NAME,
    TargetAccount,
    TargetAccountError,
    TargetAccountList,
    first_target_accounts,
)

WORKSPACE = UUID("11111111-1111-4111-8111-111111111111")
ACTOR = UUID("22222222-2222-4222-8222-222222222222")
CORRELATION = UUID("55555555-5555-4555-8555-555555555555")
NOW = datetime(2026, 8, 1, tzinfo=UTC)


def _account(name: str = "Acme", **overrides: object) -> TargetAccount:
    return TargetAccount(id=overrides.pop("id", uuid4()), name=name)  # type: ignore[arg-type]


def _list(*accounts: TargetAccount) -> TargetAccountList:
    return first_target_accounts(WORKSPACE, accounts, id=uuid4(), by=ACTOR, now=NOW)


class FakeRepository:
    def __init__(self, stored: TargetAccountList | None = None) -> None:
        self.stored = stored
        self.saved: list[TargetAccountList] = []

    async def current(self, workspace_id: UUID) -> TargetAccountList | None:
        return self.stored

    async def save(self, accounts: TargetAccountList) -> None:
        self.saved.append(accounts)
        self.stored = accounts


class FakePublisher:
    """Stands in for the outbox. **Records the order it was called in**,
    because publishing before the save would be the one sequencing mistake
    this use case can make."""

    def __init__(self, repository: FakeRepository) -> None:
        self._repository = repository
        self.published: list[Any] = []
        self.saved_before_publish: list[bool] = []
        self.producer_modules: list[str] = []
        self.correlation_ids: list[UUID] = []
        self.sessions: list[AsyncSession | None] = []

    async def publish(
        self,
        events: Sequence[Any],
        *,
        session: AsyncSession,
        producer_module: str,
        correlation_id: UUID,
    ) -> None:
        self.saved_before_publish.append(bool(self._repository.saved))
        self.published.extend(events)
        self.producer_modules.append(producer_module)
        self.correlation_ids.append(correlation_id)
        self.sessions.append(session)


def _declare(repository: FakeRepository, publisher: FakePublisher) -> DeclareTargetAccounts:
    return DeclareTargetAccounts(
        repository=repository,
        publisher=publisher,
        session=None,  # type: ignore[arg-type]
        clock=lambda: NOW,
    )


async def _execute(
    repository: FakeRepository,
    publisher: FakePublisher,
    *,
    accounts: tuple[TargetAccount, ...] = (),
    expected_version: int = 0,
) -> TargetAccountList:
    return await _declare(repository, publisher).execute(
        DeclareTargetAccountsInput(
            workspace_id=WORKSPACE,
            accounts=accounts,
            expected_version=expected_version,
            actor_id=ACTOR,
        ),
        correlation_id=CORRELATION,
    )


class TestACompanyIsANameSomebodyTyped:
    def test_it_needs_a_name(self) -> None:
        with pytest.raises(TargetAccountError, match="needs a name"):
            _account("   ")

    def test_a_name_has_a_limit(self) -> None:
        with pytest.raises(TargetAccountError, match=f"{MAX_NAME} characters"):
            _account("x" * (MAX_NAME + 1))

    def test_the_name_is_kept_exactly_as_typed(self) -> None:
        # **Never resolved, never normalised.** Asking a customer for a domain
        # would be asking them to do resolution, and working out which company
        # they mean is Signora's competence rather than theirs.
        assert _account("  ACME Corp.  ").name == "  ACME Corp.  "

    def test_an_entry_carries_a_name_and_an_id_and_nothing_else(self) -> None:
        # A domain, a country, an owner and a sync status were each
        # considered. The first two would ask the customer to resolve, the
        # third is workflow, and the fourth is a fact this module must not
        # hold at all.
        assert TargetAccount.__dataclass_fields__.keys() == {"id", "name"}


class TestTwoCompaniesMustBeTellableApart:
    def test_the_same_entry_cannot_be_listed_twice(self) -> None:
        shared = uuid4()
        with pytest.raises(TargetAccountError, match="listed twice"):
            _list(_account("Acme", id=shared), _account("Globex", id=shared))

    def test_two_entries_cannot_share_a_name(self) -> None:
        # Nothing here resolves a name, so two identical ones are ambiguous to
        # the only person who could tell them apart — the customer.
        with pytest.raises(TargetAccountError, match="share a name"):
            _list(_account("Acme"), _account(" acme "))

    def test_an_empty_list_is_legal(self) -> None:
        # "Watch nobody" is an instruction, and a different one from never
        # having said anything.
        assert _list().accounts == ()

    def test_the_list_has_an_upper_bound(self) -> None:
        # A guard against a pasted spreadsheet — **not a plan limit**, which
        # is a commercial decision this module does not hold.
        with pytest.raises(TargetAccountError, match=f"{MAX_ACCOUNTS} companies"):
            _list(*[_account(f"Company {n}") for n in range(MAX_ACCOUNTS + 1)])


class TestARevisionSupersedesRatherThanEdits:
    def test_it_mints_the_next_version(self) -> None:
        first = _list(_account("Acme"))

        second = first.revise((_account("Globex"),), id=uuid4(), by=ACTOR, now=NOW)

        assert (first.version, second.version) == (1, 2)
        assert second.supersedes == first.id

    def test_an_entry_keeps_its_identity_across_revisions(self) -> None:
        # **What lets a consumer tell a rename from a remove-and-add**, which
        # ADR-0036 asked for and which are different instructions about
        # spending money.
        kept = uuid4()
        first = _list(_account("Acme", id=kept))

        second = first.revise(
            (_account("Acme Corporation", id=kept),), id=uuid4(), by=ACTOR, now=NOW
        )

        assert second.accounts[0].id == kept
        assert second.accounts[0].name == "Acme Corporation"

    def test_a_stored_list_starts_at_version_one(self) -> None:
        with pytest.raises(TargetAccountError, match="version 1 or above"):
            TargetAccountList(
                id=uuid4(),
                workspace_id=WORKSPACE,
                version=0,
                accounts=(),
                created_at=NOW,
                created_by=ACTOR,
            )


class TestDeclaring:
    async def test_the_first_list_supersedes_nothing(self) -> None:
        repository = FakeRepository()

        declaration = await _execute(repository, FakePublisher(repository), accounts=(_account(),))

        assert (declaration.version, declaration.supersedes) == (1, None)

    async def test_a_concurrent_edit_is_refused_rather_than_overwritten(self) -> None:
        repository = FakeRepository(_list(_account("Acme")))
        publisher = FakePublisher(repository)

        with pytest.raises(TargetAccountsVersionConflictError) as refusal:
            await _execute(repository, publisher, accounts=(_account("Globex"),))

        assert (refusal.value.expected, refusal.value.actual) == (0, 1)
        assert repository.saved == [], "a refused declaration must write nothing"
        assert publisher.published == [], "and must announce nothing"


class TestTheAnnouncement:
    async def test_every_accepted_declaration_is_announced(self) -> None:
        repository = FakeRepository()
        publisher = FakePublisher(repository)

        await _execute(repository, publisher, accounts=(_account(),))

        assert len(publisher.published) == 1

    async def test_a_declaration_that_removes_everything_is_announced_too(self) -> None:
        # **Deciding a restatement changes nothing requires knowing what has
        # already been synchronized**, which is a fact Provider Platform holds
        # and this module does not. Suppressing the event here would be this
        # module reasoning about synchronization.
        repository = FakeRepository(_list(_account("Acme")))
        publisher = FakePublisher(repository)

        await _execute(repository, publisher, accounts=(), expected_version=1)

        assert len(publisher.published) == 1

    async def test_it_is_published_after_the_save(self) -> None:
        # Not before. The row and the event share a transaction, and an
        # announcement of something that has not been written is the failure
        # the outbox exists to prevent.
        repository = FakeRepository()
        publisher = FakePublisher(repository)

        await _execute(repository, publisher, accounts=(_account(),))

        assert publisher.saved_before_publish == [True]

    async def test_it_announces_the_version_that_was_written(self) -> None:
        repository = FakeRepository(_list(_account("Acme")))
        publisher = FakePublisher(repository)

        declaration = await _execute(
            repository, publisher, accounts=(_account("Globex"),), expected_version=1
        )

        event = publisher.published[0]
        assert event.declaration_version == declaration.version == 2

    async def test_it_is_attributed_to_this_module_and_the_request(self) -> None:
        repository = FakeRepository()
        publisher = FakePublisher(repository)

        await _execute(repository, publisher)

        assert publisher.producer_modules == ["commercial_profile"]
        assert publisher.correlation_ids == [CORRELATION]

    def test_the_payload_carries_the_version_and_nothing_else(self) -> None:
        """**The contract, asserted.** ADR-0036 §3: `workspace_id` on the
        envelope, `declaration_version` in the payload, nothing about
        accounts. A name here would put a copy of an aggregate's truth on a
        bus, and would make every future field an event-contract change."""
        event = TargetAccountsChanged(
            event_id=uuid4(),
            workspace_id=WORKSPACE,
            occurred_at=NOW,
            declaration_version=7,
        )

        assert event.to_payload() == {"declaration_version": 7}

    def test_the_event_names_itself_the_way_the_catalog_does(self) -> None:
        event = TargetAccountsChanged(
            event_id=uuid4(),
            workspace_id=WORKSPACE,
            occurred_at=NOW,
            declaration_version=1,
        )

        assert event.event_type == "commercial_profile.target_accounts_changed"
        assert (event.event_type, event.event_version) == (EVENT_TYPE, EVENT_VERSION)

    def test_the_payload_names_no_account_provider_or_schedule(self) -> None:
        """Asserted structurally rather than trusted to review. Every one of
        these belongs to a module downstream, and an event is the easiest
        place in a system to smuggle one."""
        payload = TargetAccountsChanged(
            event_id=uuid4(),
            workspace_id=WORKSPACE,
            occurred_at=NOW,
            declaration_version=1,
        ).to_payload()

        assert not {
            field
            for field in payload
            for term in (
                "account",
                "name",
                "company",
                "provider",
                "sync",
                "schedule",
                "delta",
                "entity",
            )
            if term in field.casefold()
        }
