"""The worker that turns an acceptance into an application —
[TASK-465](../../../docs/BACKLOG.md), slice 5.

🔴 **What the row asks for**: *"the handler returns before the work completes"*
and *"the consumer is idempotent on `event_id` — §9, and re-delivery is the
failure path that gets skipped."*

⚡ **Fakes, because a handler that needs Postgres to be tested has leaked**
([§11](../../../CLAUDE.md)). ⛔ **The session factory is a fake context manager**
— the handler's own dependency is `tenant_scoped_session`, and what is being
asserted here is its DECISIONS, not the platform's session plumbing.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest

from modules.action_batch.application.batches import ActionBatches, ProposeBatch
from modules.action_batch.domain.batch import (
    ActionBatch,
    ActionBatchError,
    ApplicationProgress,
)
from modules.action_batch.interface import handlers
from tests.action_batch.test_batches import FakePublisher, FakeRepository

NOW = datetime(2026, 8, 10, 9, 0, tzinfo=UTC)
WORKSPACE = UUID("11111111-1111-1111-1111-111111111111")
PROPOSER = UUID("33333333-3333-3333-3333-333333333333")
APPROVER = UUID("44444444-4444-4444-4444-444444444444")


class ScriptedRepository(FakeRepository):
    """A repository whose reads are scripted, for the RACE this handler must survive.

    ⚡ **A subclass rather than a monkey-patched method**, and that is not
    style. ⛔ **Assigning a plain function to `repository.get` is not
    assignable to the bound method's type** — it drops `self` — **so it needed
    a `type: ignore` that silenced the very check worth having.** ✅ **An
    override satisfies the port exactly**, which is what a fake standing in for
    a port is supposed to do ([B-236](../../../docs/BUGS.md) is what a fake
    more permissive than its port costs).
    """

    def __init__(self, reads: list[ActionBatch]) -> None:
        super().__init__()
        self._reads = list(reads)

    async def get(self, workspace_id: UUID, batch_id: UUID) -> ActionBatch | None:
        # ⚡ The last scripted read repeats, so a handler that reads three times
        # is not fighting the fixture.
        return self._reads.pop(0) if len(self._reads) > 1 else (self._reads[0] if self._reads else None)


class Envelope:
    """Only what the handler reads. ⛔ A full `EventEnvelope` would drag the
    platform's validation into a test about this module's decisions."""

    def __init__(self, batch_id: UUID) -> None:
        self.workspace_id = WORKSPACE
        self.payload: dict[str, Any] = {"batch_id": str(batch_id)}
        self.correlation_id = uuid4()


@asynccontextmanager
async def _no_session(*_args: object, **_kwargs: object) -> AsyncIterator[None]:
    yield None


async def _accepted(batches: ActionBatches) -> UUID:
    """A batch that has been approved and durably accepted, and no further."""
    batch = await batches.propose(
        ProposeBatch(
            workspace_id=WORKSPACE,
            name="Archive 12 stale accounts",
            item_count=12,
            proposed_by=PROPOSER,
            reversible_for=timedelta(hours=1),
        ),
        now=NOW,
    )
    await batches.approve(WORKSPACE, batch.id, actor_id=APPROVER, now=NOW + timedelta(minutes=1))
    await batches.request_application(
        WORKSPACE, batch.id, actor_id=APPROVER, now=NOW + timedelta(minutes=2)
    )
    return batch.id


@pytest.fixture
def wiring() -> tuple[ActionBatches, FakeRepository, FakePublisher]:
    repository, publisher = FakeRepository(), FakePublisher()
    return ActionBatches(repository, publisher, session=None), repository, publisher  # type: ignore[arg-type]


async def _run(batches: ActionBatches, batch_id: UUID) -> None:
    with patch.object(handlers, "tenant_scoped_session", _no_session):
        await handlers.apply_accepted_batch(
            Envelope(batch_id),  # type: ignore[arg-type]
            session_factory=None,  # type: ignore[arg-type]
            batches=lambda _session: batches,
        )


class TestTheAcceptedBatchIsApplied:
    async def test_it_applies_and_publishes_the_integration_event(
        self, wiring: tuple[ActionBatches, FakeRepository, FakePublisher]
    ) -> None:
        """🔴 **The whole point of the worker.** ⚡ The acceptance was published
        by the request; ✅ **`applied` is published here, and only here.**"""
        batches, repository, publisher = wiring
        batch_id = await _accepted(batches)
        published_before = len(publisher.published)

        await _run(batches, batch_id)

        stored = repository.stored[(WORKSPACE, batch_id)]
        assert stored.progress is ApplicationProgress.APPLIED
        assert len(publisher.published) == published_before + 1
        assert type(publisher.published[-1]).__name__ == "ActionBatchApplied"


class TestRedelivery:
    async def test_a_second_delivery_changes_nothing_and_reports_no_failure(
        self, wiring: tuple[ActionBatches, FakeRepository, FakePublisher]
    ) -> None:
        """🔴 **§9's idempotency, as convergence rather than a flag.**

        ⛔ **The domain refuses a second application**, and reading that refusal
        as a FAILURE would be the worst outcome available: **a customer told the
        work broke, about work that succeeded.**
        """
        batches, repository, publisher = wiring
        batch_id = await _accepted(batches)
        await _run(batches, batch_id)
        published_after_first = len(publisher.published)

        await _run(batches, batch_id)

        stored = repository.stored[(WORKSPACE, batch_id)]
        assert stored.progress is ApplicationProgress.APPLIED
        assert stored.failure is None
        # ⛔ **No second `applied` event.** A subscriber seeing two would record
        # the work happening twice.
        assert len(publisher.published) == published_after_first


class TestWhenTheDomainRefuses:
    """🔴 **This branch is reachable only by a RACE, and that is why it exists.**

    ⚠️ **Checking how to reach it is what found the defect.** ⛔ **A dispatched
    batch cannot legally become un-appliable on its own**: its state stays
    `APPROVED`, and a reversal needs an application first. ⚡ **The one way in is
    two deliveries in flight** — somebody applies the batch between the
    handler's read and `apply`'s own load.

    ⛔ **And recording a failure there would deny a change that really
    happened.** ✅ **The handler re-reads and converges instead.**
    """

    async def test_a_concurrent_application_converges_instead_of_recording_a_failure(
        self, wiring: tuple[ActionBatches, FakeRepository, FakePublisher]
    ) -> None:
        batches, repository, publisher = wiring
        batch_id = await _accepted(batches)

        # ⚡ **The race, made deterministic.** The first read returns the
        # accepted batch; the second — `apply`'s own load — returns one that has
        # been applied in the meantime, exactly as a competing worker would
        # leave it.
        accepted = repository.stored[(WORKSPACE, batch_id)]
        applied_elsewhere = accepted.applied_on(NOW + timedelta(minutes=3))

        racing = ScriptedRepository([accepted, applied_elsewhere])
        racing.stored = repository.stored
        raced = ActionBatches(racing, publisher, session=None)  # type: ignore[arg-type]

        await _run(raced, batch_id)
        repository = racing

        # ⛔ **No failure recorded.** The work succeeded; somebody else did it.
        recorded_failures = [b for b, _ in repository.recorded if b.failure is not None]
        assert recorded_failures == []

    async def test_any_OTHER_refusal_is_raised_rather_than_recorded(
        self, wiring: tuple[ActionBatches, FakeRepository, FakePublisher]
    ) -> None:
        """⛔ **A refusal this handler cannot explain is a DEFECT, not a
        customer-facing failure.**

        ⚠️ **The first draft recorded it as one**, and writing the test that
        would prove that branch is what found it unreachable: **a dispatched
        batch's state stays `APPROVED`, a reversal needs an application first,
        and `failed_to_apply` refuses a batch that was never dispatched.**
        ✅ **So the branch was removed rather than kept behind a constructed
        fixture** ([§2](../../../CLAUDE.md): *a guard that cannot fail is
        documentation pretending to be code*).

        ⚡ **What remains is asserted here**: anything the handler cannot
        explain **dead-letters with the domain's own sentence attached**, rather
        than writing a reassuring state over an unexplained one.
        """
        batches, repository, publisher = wiring
        batch_id = await _accepted(batches)
        accepted = repository.stored[(WORKSPACE, batch_id)]

        # ⚠️ **Constructed to reach the branch**, and the test says so: this
        # pairing cannot arise from the domain, which is exactly the finding.
        never_dispatched = await batches.propose(
            ProposeBatch(
                workspace_id=WORKSPACE,
                name="Archive 12 stale accounts",
                item_count=12,
                proposed_by=PROPOSER,
            ),
            now=NOW,
        )
        refusing = never_dispatched.withdrawn_by(PROPOSER, at=NOW + timedelta(minutes=1))

        scripted = ScriptedRepository([accepted, refusing])
        scripted.stored = repository.stored
        raced = ActionBatches(scripted, publisher, session=None)  # type: ignore[arg-type]

        with pytest.raises(ActionBatchError, match="did not take effect"):
            await _run(raced, batch_id)
        repository = scripted

        # ⛔ **Nothing was recorded as failed.** The event dead-letters instead,
        # which is the failure mode worth having.
        assert [b for b, _ in repository.recorded if b.failure is not None] == []


class TestWhenTheBatchIsGone:
    async def test_it_drops_the_event_rather_than_failing_forever(
        self, wiring: tuple[ActionBatches, FakeRepository, FakePublisher]
    ) -> None:
        """⛔ **Nothing to retry and nothing to record against.** ⚡ Re-raising
        would dead-letter an event about a batch that cannot be told anything."""
        batches, repository, publisher = wiring

        await _run(batches, uuid4())

        assert repository.recorded == []
        assert publisher.published == []
