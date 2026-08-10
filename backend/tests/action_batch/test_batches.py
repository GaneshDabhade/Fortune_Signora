"""The Action Batch's use cases, executed — [B-172](../../../docs/BUGS.md).

## 🔴 What QE returned, and it was right

⛔ **`application/batches.py` (69 statements) and `domain/events.py` (24) shipped
with no test that executes them**, and the repository landed at **94.66% against
a 95.0% floor** — 📁 *"measured: 95.09% without the two files; no other slice in
the candidate moves the number."*

⚠️ **`test_public_contract.py` imported them and asserted their shape.** ⛔ **An
import is not an execution**: it runs the `@dataclass` lines and nothing else, so
every branch in `apply`, `reverse` and `_decide` was unproven while the file
looked covered. ⚡ **That is [§2](../../../CLAUDE.md)'s decorative class wearing a
test's clothes**, and the coverage gate is what saw through it.

## ⚡ Fakes, because a use case that needs Postgres to be tested has leaked

📁 [§11](../../../CLAUDE.md): *"if a domain test requires a real database,
provider or AI vendor, the Clean Architecture boundary has leaked."* ✅ **The
repository fake below replays exactly what the real one does — it stores the
aggregate the transition produced** — and the publisher fake records what was
handed to the outbox, ⛔ **which is the only place the two events can be observed
without asserting on a table this module does not own** ([§8](../../../CLAUDE.md)).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from modules.action_batch.application.batches import (
    ActionBatches,
    ActionBatchNotFound,
    ProposeBatch,
)
from modules.action_batch.domain.batch import ActionBatch, ActionBatchError, ApprovalState
from modules.action_batch.domain.events import (
    EVENT_VERSION,
    ActionBatchApplied,
    ActionBatchReversed,
)

NOW = datetime(2026, 8, 10, 9, 0, tzinfo=UTC)
WORKSPACE = UUID("11111111-1111-1111-1111-111111111111")
OTHER_WORKSPACE = UUID("22222222-2222-2222-2222-222222222222")
PROPOSER = UUID("33333333-3333-3333-3333-333333333333")
APPROVER = UUID("44444444-4444-4444-4444-444444444444")


class FakeRepository:
    """What the real repository does, minus the SQL.

    ⚡ **Keyed by `(workspace_id, id)` on purpose.** The port's contract is that
    a batch in another workspace *is not found*, and a fake keyed by id alone
    would satisfy every test here while hiding the one property that matters.
    """

    def __init__(self) -> None:
        self.stored: dict[tuple[UUID, UUID], ActionBatch] = {}
        #: Every `record` call, so a test can assert the log was appended to —
        #: ⛔ the port has no `update`, and neither has this.
        self.recorded: list[tuple[ActionBatch, UUID]] = []

    async def add(self, batch: ActionBatch, *, actor_id: UUID) -> None:
        self.stored[(batch.workspace_id, batch.id)] = batch

    async def record(self, batch: ActionBatch, *, actor_id: UUID) -> None:
        self.stored[(batch.workspace_id, batch.id)] = batch
        self.recorded.append((batch, actor_id))

    async def get(self, workspace_id: UUID, batch_id: UUID) -> ActionBatch | None:
        return self.stored.get((workspace_id, batch_id))


class FakePublisher:
    def __init__(self) -> None:
        self.published: list[object] = []
        self.producer_modules: list[str] = []

    async def publish(
        self,
        events: object,
        *,
        session: AsyncSession | None = None,
        producer_module: str,
        correlation_id: UUID,
    ) -> None:
        self.published.extend(events)  # type: ignore[arg-type]
        self.producer_modules.append(producer_module)


@pytest.fixture
def repository() -> FakeRepository:
    return FakeRepository()


@pytest.fixture
def publisher() -> FakePublisher:
    return FakePublisher()


@pytest.fixture
def batches(repository: FakeRepository, publisher: FakePublisher) -> ActionBatches:
    # ⚠️ The session is never touched by these paths — it is handed straight to
    # the publisher, whose real implementation writes the outbox row inside the
    # caller's transaction. `None` here is honest about that rather than a stub
    # pretending to be a database.
    return ActionBatches(repository, publisher, session=None)  # type: ignore[arg-type]


async def _proposed(
    batches: ActionBatches, *, reversible_for: timedelta | None = timedelta(hours=1)
) -> ActionBatch:
    return await batches.propose(
        ProposeBatch(
            workspace_id=WORKSPACE,
            name="Archive 12 stale accounts",
            item_count=12,
            proposed_by=PROPOSER,
            reversible_for=reversible_for,
        ),
        now=NOW,
    )


class TestProposing:
    async def test_a_proposal_is_stored_and_tells_nobody(
        self, batches: ActionBatches, repository: FakeRepository, publisher: FakePublisher
    ) -> None:
        """⛔ **A proposal is a question, and no domain acts on a question.**"""
        batch = await _proposed(batches)

        assert repository.stored[(WORKSPACE, batch.id)] is batch
        assert batch.state is ApprovalState.PROPOSED
        assert publisher.published == []
        # ⚡ `add` writes no log row — the proposal is how a batch begins, not a
        # transition — so `record` has not been called.
        assert repository.recorded == []

    async def test_it_carries_the_customer_s_own_words_and_count(
        self, batches: ActionBatches
    ) -> None:
        batch = await _proposed(batches)
        assert batch.name == "Archive 12 stale accounts"
        assert batch.item_count == 12
        assert batch.proposed.actor_id == PROPOSER


class TestTheThreeDecisions:
    """⛔ **None of them publishes**, and that is the assertion worth having."""

    @pytest.mark.parametrize(
        ("call", "expected"),
        [
            ("approve", ApprovalState.APPROVED),
            ("reject", ApprovalState.REJECTED),
            ("withdraw", ApprovalState.WITHDRAWN),
        ],
    )
    async def test_each_decision_is_recorded_and_none_is_announced(
        self,
        batches: ActionBatches,
        repository: FakeRepository,
        publisher: FakePublisher,
        call: str,
        expected: ApprovalState,
    ) -> None:
        batch = await _proposed(batches)

        decided = await getattr(batches, call)(
            WORKSPACE, batch.id, actor_id=APPROVER, now=NOW + timedelta(minutes=5)
        )

        assert decided.state is expected
        # ⚡ The log was appended to, attributed to whoever decided.
        assert repository.recorded == [(decided, APPROVER)]
        # 🔴 The whole reason there are two events and not six: approving is
        # permission for work that has not happened yet.
        assert publisher.published == []

    async def test_a_decision_on_a_batch_in_another_workspace_is_not_found(
        self, batches: ActionBatches
    ) -> None:
        """⛔ **Not `Forbidden`** — *forbidden* confirms the id exists."""
        batch = await _proposed(batches)

        with pytest.raises(ActionBatchNotFound) as raised:
            await batches.approve(OTHER_WORKSPACE, batch.id, actor_id=APPROVER, now=NOW)

        assert "not found rather than forbidden" in str(raised.value)

    async def test_deciding_twice_is_refused_by_the_domain_not_by_this_layer(
        self, batches: ActionBatches, publisher: FakePublisher
    ) -> None:
        """⚡ **The guard is the domain's, and the use case does not re-implement it.**"""
        batch = await _proposed(batches)
        await batches.approve(WORKSPACE, batch.id, actor_id=APPROVER, now=NOW)

        with pytest.raises(ActionBatchError):
            await batches.reject(WORKSPACE, batch.id, actor_id=APPROVER, now=NOW)

        assert publisher.published == []


class TestApplying:
    async def test_applying_publishes_exactly_one_applied_event(
        self, batches: ActionBatches, publisher: FakePublisher
    ) -> None:
        batch = await _proposed(batches)
        await batches.approve(WORKSPACE, batch.id, actor_id=APPROVER, now=NOW)

        applied = await batches.apply(WORKSPACE, batch.id, now=NOW + timedelta(minutes=10))

        assert len(publisher.published) == 1
        event = publisher.published[0]
        assert isinstance(event, ActionBatchApplied)
        assert event.batch_id == applied.id
        assert event.workspace_id == WORKSPACE
        assert event.name == "Archive 12 stale accounts"
        assert event.item_count == 12
        # 🔴 *Intelligence suggests; humans commit* — the approver, never the
        # actor who happened to flush it.
        assert event.approved_by == APPROVER
        assert publisher.producer_modules == ["action_batch"]

    async def test_the_reversible_window_is_stated_as_a_moment_not_a_duration(
        self, batches: ActionBatches, publisher: FakePublisher
    ) -> None:
        """⚡ **A subscriber cannot compute it** — it does not know when the
        window started, and would have to trust its own clock."""
        batch = await _proposed(batches, reversible_for=timedelta(hours=1))
        await batches.approve(WORKSPACE, batch.id, actor_id=APPROVER, now=NOW)

        moment = NOW + timedelta(minutes=10)
        await batches.apply(WORKSPACE, batch.id, now=moment)

        event = publisher.published[0]
        assert isinstance(event, ActionBatchApplied)
        assert event.reversible_until == moment + timedelta(hours=1)

    async def test_reversal_never_offered_is_told_differently_from_a_closed_window(
        self, batches: ActionBatches, publisher: FakePublisher
    ) -> None:
        """🔴 **`None` means never offered.** ⛔ A closed window is a *past*
        `reversible_until`, and collapsing the two would tell a subscriber that
        a batch it may never undo is one whose moment has passed."""
        batch = await _proposed(batches, reversible_for=None)
        await batches.approve(WORKSPACE, batch.id, actor_id=APPROVER, now=NOW)

        await batches.apply(WORKSPACE, batch.id, now=NOW + timedelta(minutes=10))

        event = publisher.published[0]
        assert isinstance(event, ActionBatchApplied)
        assert event.reversible_until is None

    async def test_applying_something_nobody_approved_is_refused_and_announces_nothing(
        self, batches: ActionBatches, publisher: FakePublisher
    ) -> None:
        batch = await _proposed(batches)

        with pytest.raises(ActionBatchError):
            await batches.apply(WORKSPACE, batch.id, now=NOW)

        # ⛔ **The order matters and this is what pins it**: a use case that
        # published before the domain refused would tell the rest of Signora
        # that work took effect which never did.
        assert publisher.published == []

    async def test_applying_a_batch_from_another_workspace_is_not_found(
        self, batches: ActionBatches
    ) -> None:
        batch = await _proposed(batches)
        await batches.approve(WORKSPACE, batch.id, actor_id=APPROVER, now=NOW)

        with pytest.raises(ActionBatchNotFound):
            await batches.apply(OTHER_WORKSPACE, batch.id, now=NOW)


class TestReversing:
    async def test_reversing_publishes_the_second_and_keeps_the_first(
        self, batches: ActionBatches, publisher: FakePublisher
    ) -> None:
        """⚠️ **Not a correction of the applied event, and never its retraction.**

        ⚡ **Both happened, in that order**, and a subscriber that dropped the
        first on seeing the second would lose the fact that the work was live in
        between — **which is exactly the interval a customer asks about.**
        """
        batch = await _proposed(batches, reversible_for=timedelta(hours=2))
        await batches.approve(WORKSPACE, batch.id, actor_id=APPROVER, now=NOW)
        applied_at = NOW + timedelta(minutes=10)
        await batches.apply(WORKSPACE, batch.id, now=applied_at)

        await batches.reverse(
            WORKSPACE, batch.id, actor_id=APPROVER, now=applied_at + timedelta(minutes=5)
        )

        assert len(publisher.published) == 2
        assert isinstance(publisher.published[0], ActionBatchApplied)
        reversed_event = publisher.published[1]
        assert isinstance(reversed_event, ActionBatchReversed)
        # 🔴 **Stated, not inferred from ordering** — a subscriber may see the
        # two out of order, so the reversal names the application it undoes.
        assert reversed_event.applied_at == applied_at
        assert reversed_event.reversed_by == APPROVER
        assert reversed_event.batch_id == batch.id

    async def test_reversing_after_the_window_is_refused_and_announces_nothing(
        self, batches: ActionBatches, publisher: FakePublisher
    ) -> None:
        """⚡ **This is what makes `has_settled` load-bearing rather than
        descriptive** — the window the customer was shown is the window."""
        batch = await _proposed(batches, reversible_for=timedelta(hours=1))
        await batches.approve(WORKSPACE, batch.id, actor_id=APPROVER, now=NOW)
        applied_at = NOW + timedelta(minutes=10)
        await batches.apply(WORKSPACE, batch.id, now=applied_at)

        with pytest.raises(ActionBatchError):
            await batches.reverse(
                WORKSPACE, batch.id, actor_id=APPROVER, now=applied_at + timedelta(hours=2)
            )

        # ⛔ Still exactly one event: the application. Nothing announced a
        # reversal that the domain refused.
        assert len(publisher.published) == 1

    async def test_reversing_something_that_never_applied_is_refused(
        self, batches: ActionBatches, publisher: FakePublisher
    ) -> None:
        batch = await _proposed(batches)
        await batches.approve(WORKSPACE, batch.id, actor_id=APPROVER, now=NOW)

        with pytest.raises(ActionBatchError):
            await batches.reverse(WORKSPACE, batch.id, actor_id=APPROVER, now=NOW)

        assert publisher.published == []

    async def test_reversing_a_batch_from_another_workspace_is_not_found(
        self, batches: ActionBatches
    ) -> None:
        batch = await _proposed(batches)

        with pytest.raises(ActionBatchNotFound):
            await batches.reverse(OTHER_WORKSPACE, batch.id, actor_id=APPROVER, now=NOW)


class TestTheEventsThemselves:
    """📁 [`domain/events.py`](../../modules/action_batch/domain/events.py) — the
    other file B-172 named."""

    def test_there_is_no_approved_event_and_that_is_the_design(self) -> None:
        """⛔ **No `action_batch.approved`.**

        ⚡ **Approval is permission to apply, not the application** — a
        subscriber acting on it would act before the work happened, and the gap
        between the two moments is real. **Asserted on the module rather than
        left to the docstring**, because a docstring cannot refuse the third
        event somebody adds.
        """
        import modules.action_batch.domain.events as events

        published = {
            name
            for name in dir(events)
            if name.startswith("ActionBatch") and not name.startswith("_")
        }
        assert published == {"ActionBatchApplied", "ActionBatchReversed"}

    def test_both_events_are_frozen_because_they_record_something_that_was_true(
        self,
    ) -> None:
        """📁 [§2](../../../CLAUDE.md): *immutability is the default for anything
        that records a fact.*"""
        applied = ActionBatchApplied(
            event_id=uuid4(),
            workspace_id=WORKSPACE,
            occurred_at=NOW,
            batch_id=uuid4(),
            name="Archive 12 stale accounts",
            item_count=12,
            approved_by=APPROVER,
            reversible_until=None,
        )
        with pytest.raises(AttributeError):
            applied.item_count = 13  # type: ignore[misc]

        undone = ActionBatchReversed(
            event_id=uuid4(),
            workspace_id=WORKSPACE,
            occurred_at=NOW,
            batch_id=uuid4(),
            applied_at=NOW,
            reversed_by=APPROVER,
        )
        with pytest.raises(AttributeError):
            undone.reversed_by = PROPOSER  # type: ignore[misc]

    def test_the_version_is_declared_because_a_payload_change_needs_one(self) -> None:
        # 📁 §9: a breaking payload change is a version bump, never a silent
        # shape change.
        assert EVENT_VERSION == 1
