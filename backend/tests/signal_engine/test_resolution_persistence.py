"""What the database refuses about a resolution, and what it keeps.

**Against a real database, not a double.** Every invariant here is a `CHECK`
constraint, a missing grant or a foreign key — a repository fake would
reproduce whatever its author believed those meant, which is exactly the thing
under test. `test_profile_currency.py` is here for the same reason and after a
defect that a double had hidden (`B-001`).

**The domain types already make three of these unconstructable in Python.**
That is not a reason to leave the database permissive: the type protects the
code written today, and the constraint protects the row written by whatever
writes it next — a backfill, a repair script, a second service. A rule that
lives only in the caller is a rule the next caller does not have.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.signal_engine.domain.resolution import (
    Actioned,
    Assigned,
    DismissalReason,
    Dismissed,
    Outcome,
    Resolution,
    Snoozed,
)
from modules.signal_engine.infrastructure.models import SignalModel, SignalResolutionModel
from modules.signal_engine.infrastructure.repository import SqlResolutionRepository
from signora_platform.db import tenant_scoped_session
from tests.signal_engine.test_signal_pipeline import _pipeline

pytestmark = pytest.mark.integration

NOW = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)
LATER = NOW + timedelta(days=7)


async def _a_signal(
    factory: async_sessionmaker[AsyncSession], workspace_id: UUID, user_id: UUID
) -> UUID:
    """Any real signal from the pipeline. **A resolution needs one to point
    at**, and the foreign key is one of the things under test."""
    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        rows = await session.execute(select(SignalModel.id).order_by(SignalModel.id).limit(1))
        signal_id = rows.scalars().first()
    assert signal_id is not None, "the baseline scenario is expected to produce signals"
    return signal_id


def _resolution(
    workspace_id: UUID,
    signal_id: UUID,
    actor_id: UUID,
    *,
    outcome: Outcome,
    recorded_at: datetime = NOW,
    supersedes: UUID | None = None,
) -> Resolution:
    return Resolution(
        id=uuid4(),
        workspace_id=workspace_id,
        signal_id=signal_id,
        outcome=outcome,
        actor_id=actor_id,
        recorded_at=recorded_at,
        supersedes=supersedes,
    )


class TestEveryOutcomeSurvivesTheRoundTrip:
    """**The payload is columns, not a blob**, so each one has to come back as
    the type it went in as rather than as a dictionary somebody re-reads."""

    async def test_an_actioned_signal_carries_nothing_back(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Acme")
        signal_id = await _a_signal(session_factory, workspace_id, user_id)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            await SqlResolutionRepository(session).record(
                _resolution(workspace_id, signal_id, user_id, outcome=Actioned())
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            current = await SqlResolutionRepository(session).current_for_signals(
                workspace_id, [signal_id]
            )

        assert isinstance(current[signal_id].outcome, Actioned)
        assert current[signal_id].closes_the_signal

    async def test_an_assignment_names_the_person_it_went_to(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Acme")
        signal_id = await _a_signal(session_factory, workspace_id, user_id)
        colleague = uuid4()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            await SqlResolutionRepository(session).record(
                _resolution(workspace_id, signal_id, user_id, outcome=Assigned(to=colleague))
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            current = await SqlResolutionRepository(session).current_for_signals(
                workspace_id, [signal_id]
            )

        outcome = current[signal_id].outcome
        assert isinstance(outcome, Assigned)
        assert outcome.to == colleague
        # **Routing is not resolving.** A queue that closed on assignment would
        # lose every signal handed to a colleague.
        assert not current[signal_id].closes_the_signal

    async def test_a_snooze_comes_back_with_its_time_and_its_timezone(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**`timestamptz`, and the assertion is about the offset.** A naive
        column would return a moment whose meaning depends on who reads it,
        and *"returns at the stated time"* would be true only in one timezone.
        """
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Acme")
        signal_id = await _a_signal(session_factory, workspace_id, user_id)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            await SqlResolutionRepository(session).record(
                _resolution(workspace_id, signal_id, user_id, outcome=Snoozed(until=LATER))
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            current = await SqlResolutionRepository(session).current_for_signals(
                workspace_id, [signal_id]
            )

        resolution = current[signal_id]
        outcome = resolution.outcome
        assert isinstance(outcome, Snoozed)
        assert outcome.until == LATER
        assert outcome.until.tzinfo is not None
        assert not resolution.is_due(LATER - timedelta(days=1))
        assert resolution.is_due(LATER)

    async def test_a_dismissal_comes_back_with_the_words_somebody_wrote(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Verbatim. The reason is the only part of a dismissal a rule can
        learn from, and a normalised one would be a different sentence."""
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Acme")
        signal_id = await _a_signal(session_factory, workspace_id, user_id)
        reason = "They hired for the role internally."

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            await SqlResolutionRepository(session).record(
                _resolution(
                    workspace_id,
                    signal_id,
                    user_id,
                    outcome=Dismissed(reason=DismissalReason(reason)),
                )
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            current = await SqlResolutionRepository(session).current_for_signals(
                workspace_id, [signal_id]
            )

        outcome = current[signal_id].outcome
        assert isinstance(outcome, Dismissed)
        assert outcome.reason.text == reason
        assert current[signal_id].closes_the_signal


class TestTheDatabaseRefusesWhatTheTypesRefuse:
    """**The same invariants, one layer down.** The types protect the code
    written today; these protect the row written by whatever writes it next."""

    async def test_a_dismissal_without_a_reason_is_refused_by_the_database(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The acceptance criterion, at the storage layer.** `Dismissed` has
        no default and cannot be built without one; this is what stops a
        backfill or a repair script from writing the row the type forbids."""
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Acme")
        signal_id = await _a_signal(session_factory, workspace_id, user_id)

        with pytest.raises(IntegrityError, match="dismissal_gives_a_reason"):
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                await _insert_raw(
                    session, workspace_id, signal_id, user_id, outcome="dismissed", reason=None
                )

    async def test_a_blank_reason_is_refused_by_the_database(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Present, non-null, and says nothing — the failure a `NOT NULL`
        alone would let through."""
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Acme")
        signal_id = await _a_signal(session_factory, workspace_id, user_id)

        with pytest.raises(IntegrityError, match="reason_is_not_blank"):
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                await _insert_raw(
                    session, workspace_id, signal_id, user_id, outcome="dismissed", reason="   "
                )

    async def test_an_actioned_row_cannot_smuggle_in_a_reason(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Why the constraint is an equivalence rather than an implication.**
        A reason on an `actioned` row is a dismissal the queue would show as
        success, and it would read back as one for as long as nobody looked."""
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Acme")
        signal_id = await _a_signal(session_factory, workspace_id, user_id)

        with pytest.raises(IntegrityError, match="dismissal_gives_a_reason"):
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                await _insert_raw(
                    session,
                    workspace_id,
                    signal_id,
                    user_id,
                    outcome="actioned",
                    reason="Not why this was actioned.",
                )

    async def test_an_assignment_that_names_nobody_is_refused(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Acme")
        signal_id = await _a_signal(session_factory, workspace_id, user_id)

        with pytest.raises(IntegrityError, match="assignment_names_somebody"):
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                await _insert_raw(
                    session, workspace_id, signal_id, user_id, outcome="assigned", assigned_to=None
                )

    async def test_a_snooze_that_has_already_elapsed_is_refused(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Acme")
        signal_id = await _a_signal(session_factory, workspace_id, user_id)

        with pytest.raises(IntegrityError, match="snooze_is_not_already_over"):
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                await _insert_raw(
                    session,
                    workspace_id,
                    signal_id,
                    user_id,
                    outcome="snoozed",
                    snoozed_until=NOW - timedelta(hours=1),
                )

    async def test_an_outcome_the_product_does_not_have_is_refused(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """`Outcome` is a closed union because a fifth outcome is a product
        decision about what triage means. The column says the same thing."""
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Acme")
        signal_id = await _a_signal(session_factory, workspace_id, user_id)

        with pytest.raises(IntegrityError, match="outcome_known"):
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                await _insert_raw(session, workspace_id, signal_id, user_id, outcome="escalated")


class TestNothingHereCanBeEdited:
    async def test_the_application_role_holds_no_update_grant(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The enforcement, rather than the convention.** The repository
        offers no update method, but a method is a thing somebody can add. The
        absent grant is a thing they cannot."""
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Acme")
        signal_id = await _a_signal(session_factory, workspace_id, user_id)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            await SqlResolutionRepository(session).record(
                _resolution(
                    workspace_id,
                    signal_id,
                    user_id,
                    outcome=Dismissed(reason=DismissalReason("Wrong account.")),
                )
            )

        with pytest.raises(DBAPIError, match="permission denied"):
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                await session.execute(
                    text("UPDATE signal_resolution SET dismissal_reason = 'Actually it was right.'")
                )

    async def test_changing_your_mind_leaves_both_records_readable(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """*"Nothing is deleted: every resolution is auditable."* The current
        answer is the later one; **the regretted dismissal is still there**,
        which is the whole reason a correction is a new row."""
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Acme")
        signal_id = await _a_signal(session_factory, workspace_id, user_id)
        regretted = _resolution(
            workspace_id,
            signal_id,
            user_id,
            outcome=Dismissed(reason=DismissalReason("Not relevant.")),
        )
        correction = _resolution(
            workspace_id,
            signal_id,
            user_id,
            outcome=Actioned(),
            recorded_at=NOW + timedelta(hours=1),
            supersedes=regretted.id,
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            repository = SqlResolutionRepository(session)
            await repository.record(regretted)
            await repository.record(correction)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            repository = SqlResolutionRepository(session)
            current = await repository.current_for_signals(workspace_id, [signal_id])
            history = await repository.history_for_signal(workspace_id, signal_id)

        assert isinstance(current[signal_id].outcome, Actioned)
        assert [entry.id for entry in history] == [regretted.id, correction.id]
        assert isinstance(history[0].outcome, Dismissed)


class TestResolvingDoesNotTouchTheSignal:
    async def test_the_signal_and_its_evidence_are_byte_for_byte_unchanged(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The acceptance criterion, read from the database rather than
        argued from the code.** A signal records what Signora concluded from
        evidence at a moment; a person disagreeing with it later has not
        changed what was concluded."""
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Acme")
        signal_id = await _a_signal(session_factory, workspace_id, user_id)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            before = (
                (
                    await session.execute(
                        text("SELECT to_jsonb(s) FROM signal s ORDER BY id").bindparams()
                    )
                )
                .scalars()
                .all()
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            await SqlResolutionRepository(session).record(
                _resolution(
                    workspace_id,
                    signal_id,
                    user_id,
                    outcome=Dismissed(reason=DismissalReason("Wrong account.")),
                )
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            after = (
                (await session.execute(text("SELECT to_jsonb(s) FROM signal s ORDER BY id")))
                .scalars()
                .all()
            )

        assert after == before


class TestOneWorkspaceNeverSeesAnothersDecisions:
    async def test_a_resolution_is_invisible_to_a_second_tenant(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Forced RLS, exercised rather than asserted to be configured. What a
        customer decided about their own pipeline is theirs."""
        first, first_user = await _pipeline(session_factory, admin_session_factory, "Tenant A")
        second, second_user = await _pipeline(session_factory, admin_session_factory, "Tenant B")
        signal_id = await _a_signal(session_factory, first, first_user)

        async with tenant_scoped_session(
            session_factory, workspace_id=first, user_id=first_user
        ) as session:
            await SqlResolutionRepository(session).record(
                _resolution(first, signal_id, first_user, outcome=Actioned())
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=second, user_id=second_user
        ) as session:
            visible = (await session.execute(select(SignalResolutionModel.id))).scalars().all()

        assert visible == []


async def _insert_raw(
    session: AsyncSession,
    workspace_id: UUID,
    signal_id: UUID,
    actor_id: UUID,
    *,
    outcome: str,
    reason: str | None = None,
    assigned_to: UUID | None = None,
    snoozed_until: datetime | None = None,
) -> None:
    """Write a row the domain types would not let anybody construct.

    **Deliberately going around the repository.** The point of each constraint
    is what happens when the next writer is not this code — so a test that went
    through the mapper would be testing the mapper, and would pass on a table
    with no constraints at all.
    """
    await session.execute(
        text(
            """
            INSERT INTO signal_resolution (
                id, workspace_id, signal_id, outcome, assigned_to, snoozed_until,
                dismissal_reason, actor_id, recorded_at, payload_version,
                created_by, updated_by
            ) VALUES (
                :id, :workspace_id, :signal_id, :outcome, :assigned_to, :snoozed_until,
                :reason, :actor_id, :recorded_at, 1, :actor_id, :actor_id
            )
            """
        ),
        {
            "id": uuid4(),
            "workspace_id": workspace_id,
            "signal_id": signal_id,
            "outcome": outcome,
            "assigned_to": assigned_to,
            "snoozed_until": snoozed_until,
            "reason": reason,
            "actor_id": actor_id,
            "recorded_at": NOW,
        },
    )
