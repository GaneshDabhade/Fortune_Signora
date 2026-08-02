"""What happens when a customer changes which companies they want watched.

**[ADR-0036](../../../docs/architecture/adr/0036-target-account-contract.md) §4
and §7, as behaviour.** Two rules decide this use case and both are the kind
that look like defensive coding until you see the case they exist for:

* the delta is computed against **what has actually been read**, never against
  the previous declaration;
* an event announcing a version already acted on does **nothing at all**.

Unit tests against fakes, deliberately (`CLAUDE.md` §11): none of this needs a
database, a provider or a model, and a test that reached for one would be
hiding a Clean Architecture leak rather than proving anything.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

import pytest

from modules.commercial_profile.public import TargetAccountListView, TargetAccountView
from modules.provider_platform.application.sync_targets import (
    NEVER_DECLARED,
    NOTHING_NEW,
    STALE,
    SyncDeclaredTargets,
    SyncDeclaredTargetsInput,
)
from modules.provider_platform.domain.targets import (
    DeclaredAccount,
    TargetSyncState,
    subjects_needing_sync,
)

WORKSPACE = UUID("11111111-1111-4111-8111-111111111111")


@dataclass
class FakeReader:
    view: TargetAccountListView | None = None

    async def current(self, workspace_id: UUID) -> TargetAccountListView | None:
        return self.view


@dataclass
class FakeState:
    version: int | None = None
    read: frozenset[str] = frozenset()
    saved: list[int] = field(default_factory=list)

    async def get(self, workspace_id: UUID) -> TargetSyncState:
        return TargetSyncState(workspace_id=workspace_id, declaration_version=self.version)

    async def save(self, state: TargetSyncState) -> None:
        assert state.declaration_version is not None
        self.saved.append(state.declaration_version)
        self.version = state.declaration_version

    async def subjects_with_a_position(self, workspace_id: UUID) -> frozenset[str]:
        return self.read


@dataclass
class FakeDispatcher:
    sent: list[str] = field(default_factory=list)

    async def sync(self, *, workspace_id: UUID, subject: str, correlation_id: UUID) -> None:
        self.sent.append(subject)


def _view(*names: str, version: int = 1) -> TargetAccountListView:
    return TargetAccountListView(
        workspace_id=WORKSPACE,
        version=version,
        accounts=tuple(TargetAccountView(id=uuid4(), name=name) for name in names),
    )


def _use_case(
    reader: FakeReader, state: FakeState, dispatcher: FakeDispatcher
) -> SyncDeclaredTargets:
    return SyncDeclaredTargets(targets=reader, state=state, dispatch=dispatcher)


class TestTheDeltaIsAgainstWhatWasRead:
    """**§4.** A delta from Commercial Profile answers a different question —
    it is a delta between two *declarations*, and what matters here is the
    difference against what has actually been fetched."""

    async def test_a_first_declaration_dispatches_everything(self) -> None:
        state, dispatcher = FakeState(), FakeDispatcher()

        result = await _use_case(FakeReader(_view("Acme", "Initech")), state, dispatcher).execute(
            SyncDeclaredTargetsInput(workspace_id=WORKSPACE, declaration_version=1),
            correlation_id=uuid4(),
        )

        assert result.dispatched == ("Acme", "Initech")
        assert dispatcher.sent == ["Acme", "Initech"]

    async def test_a_company_already_read_is_not_fetched_again(self) -> None:
        state = FakeState(read=frozenset({"Acme"}))
        dispatcher = FakeDispatcher()

        result = await _use_case(FakeReader(_view("Acme", "Initech")), state, dispatcher).execute(
            SyncDeclaredTargetsInput(workspace_id=WORKSPACE, declaration_version=2),
            correlation_id=uuid4(),
        )

        assert result.dispatched == ("Initech",)

    async def test_a_company_declared_before_and_never_fetched_is_fetched(self) -> None:
        """**The case that decides §4.** A customer declares Acme, the fetch
        fails, they remove it and later re-add it. A declaration-delta calls
        that *"no change"*. It is not — nothing was ever read."""
        state = FakeState(version=4, read=frozenset())
        dispatcher = FakeDispatcher()

        result = await _use_case(FakeReader(_view("Acme", version=5)), state, dispatcher).execute(
            SyncDeclaredTargetsInput(workspace_id=WORKSPACE, declaration_version=5),
            correlation_id=uuid4(),
        )

        assert result.dispatched == ("Acme",)

    async def test_a_declaration_with_nothing_new_records_the_version_anyway(self) -> None:
        # Otherwise the next event would recompute an identical delta forever,
        # and the stale check would never have anything to compare against.
        state = FakeState(version=1, read=frozenset({"Acme"}))

        result = await _use_case(
            FakeReader(_view("Acme", version=2)), state, FakeDispatcher()
        ).execute(
            SyncDeclaredTargetsInput(workspace_id=WORKSPACE, declaration_version=2),
            correlation_id=uuid4(),
        )

        assert result.skipped == NOTHING_NEW
        assert state.saved == [2]


class TestOrderingIsNotIdempotency:
    """**§7.** Idempotency on `event_id` stops one event being handled twice.
    It does nothing about two events arriving in the wrong order."""

    async def test_an_older_declaration_arriving_late_does_nothing(self) -> None:
        state = FakeState(version=6)
        reader, dispatcher = FakeReader(_view("Acme")), FakeDispatcher()

        result = await _use_case(reader, state, dispatcher).execute(
            SyncDeclaredTargetsInput(workspace_id=WORKSPACE, declaration_version=5),
            correlation_id=uuid4(),
        )

        assert result.skipped == STALE
        assert dispatcher.sent == []

    async def test_it_does_not_even_read_the_declaration(self) -> None:
        """A stale event must cost nothing — the check is before the read, not
        after it, which is the difference between ignoring an event and
        handling one that turns out not to matter."""
        state = FakeState(version=6)
        reader = FakeReader(None)

        result = await _use_case(reader, state, FakeDispatcher()).execute(
            SyncDeclaredTargetsInput(workspace_id=WORKSPACE, declaration_version=6),
            correlation_id=uuid4(),
        )

        # `None` from the reader would have produced NEVER_DECLARED. STALE
        # proves the reader was never consulted.
        assert result.skipped == STALE

    async def test_the_version_recorded_is_the_one_read_not_the_one_announced(self) -> None:
        """A declaration can move on between publication and handling.
        Recording the announced version would claim this run had seen a list
        it never read — and would then let the newer event be discarded."""
        state, dispatcher = FakeState(), FakeDispatcher()

        result = await _use_case(FakeReader(_view("Acme", version=9)), state, dispatcher).execute(
            SyncDeclaredTargetsInput(workspace_id=WORKSPACE, declaration_version=7),
            correlation_id=uuid4(),
        )

        assert result.acted_on == 9
        assert state.saved == [9]

    async def test_the_same_version_twice_is_stale(self) -> None:
        # Re-handling the version already acted on re-derives a delta that is
        # by definition empty. Making it non-empty is a retry's job.
        state = FakeState(version=3)

        result = await _use_case(FakeReader(_view("Acme")), state, FakeDispatcher()).execute(
            SyncDeclaredTargetsInput(workspace_id=WORKSPACE, declaration_version=3),
            correlation_id=uuid4(),
        )

        assert result.skipped == STALE


class TestSilenceAndInstruction:
    async def test_a_workspace_that_has_declared_nothing_is_not_an_empty_list(self) -> None:
        """*"They have not told us yet"* is a state to wait in; *"watch
        nobody"* is an instruction. The port distinguishes them and so does
        this."""
        result = await _use_case(FakeReader(None), FakeState(), FakeDispatcher()).execute(
            SyncDeclaredTargetsInput(workspace_id=WORKSPACE, declaration_version=1),
            correlation_id=uuid4(),
        )

        assert result.skipped == NEVER_DECLARED
        assert result.acted_on is None

    async def test_declaring_an_empty_list_is_acted_on(self) -> None:
        state = FakeState()

        result = await _use_case(FakeReader(_view(version=1)), state, FakeDispatcher()).execute(
            SyncDeclaredTargetsInput(workspace_id=WORKSPACE, declaration_version=1),
            correlation_id=uuid4(),
        )

        assert result.skipped == NOTHING_NEW
        assert state.saved == [1]

    async def test_nothing_is_dispatched_before_the_state_is_written(self) -> None:
        """**Dispatch first, record after.** If recording fails the event
        redelivers, the delta is recomputed against the same watermarks, and
        the same companies are dispatched again — wasteful once. Recording
        first and failing to dispatch would lose the work silently."""
        state, dispatcher = FakeState(), FakeDispatcher()

        await _use_case(FakeReader(_view("Acme")), state, dispatcher).execute(
            SyncDeclaredTargetsInput(workspace_id=WORKSPACE, declaration_version=1),
            correlation_id=uuid4(),
        )

        assert dispatcher.sent == ["Acme"]
        assert state.saved == [1]


class TestTheDeltaRuleItself:
    def test_the_customers_order_is_kept(self) -> None:
        # Nothing in this module knows which of their companies matters more,
        # and inventing a priority would be a commercial judgement nobody
        # asked for.
        declared = tuple(DeclaredAccount(id=uuid4(), subject=n) for n in ("Zeta", "Acme", "Mid"))

        assert subjects_needing_sync(declared, frozenset()) == ("Zeta", "Acme", "Mid")

    def test_the_same_company_typed_twice_is_fetched_once(self) -> None:
        declared = tuple(DeclaredAccount(id=uuid4(), subject=n) for n in ("Acme", "Acme"))

        assert subjects_needing_sync(declared, frozenset()) == ("Acme",)

    @pytest.mark.parametrize(
        ("acted_on", "incoming", "stale"),
        [(None, 1, False), (5, 4, True), (5, 5, True), (5, 6, False)],
    )
    def test_when_a_version_counts_as_overtaken(
        self, acted_on: int | None, incoming: int, stale: bool
    ) -> None:
        state = TargetSyncState(workspace_id=WORKSPACE, declaration_version=acted_on)

        assert state.is_stale(incoming) is stale
