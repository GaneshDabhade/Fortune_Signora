"""Persistence for signals, profiles and resolutions.

**Three repositories, deliberately, because the three hold different kinds of
truth.** Signals are derived and rebuildable; profiles are customer-authored
and cannot be regenerated from anything; resolutions are decisions people made
about a signal. Keeping them apart makes it impossible to write a rebuild that
quietly discards a customer's configuration — or the record of what they
decided.

**None offers an update method.** Immutability is enforced at the database by
the absent UPDATE grant (migrations 0012 and 0039); not offering the method
here means nobody writes code that would fail at runtime.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from modules.business_event_engine.public import BusinessEventType
from modules.signal_engine.domain.catalog import Relevance, SignalType
from modules.signal_engine.domain.profile import ProfileEntry, SignalProfile
from modules.signal_engine.domain.resolution import (
    ACTIONED,
    ASSIGNED,
    DISMISSED,
    SNOOZED,
    Actioned,
    Assigned,
    DismissalReason,
    Dismissed,
    Outcome,
    Resolution,
    Snoozed,
    UnreadableOutcomeError,
    discriminator,
)
from modules.signal_engine.domain.signal import Signal
from modules.signal_engine.infrastructure.models import (
    SignalModel,
    SignalProfileModel,
    SignalResolutionModel,
)

SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _to_signal(row: SignalModel) -> Signal:
    return Signal(
        id=row.id,
        workspace_id=row.workspace_id,
        entity_id=row.entity_id,
        signal_type=SignalType(row.signal_type),
        relevance=Relevance(row.relevance),
        occurred_at=row.occurred_at,
        window_start=row.window_start,
        window_end=row.window_end,
        generated_at=row.generated_at,
        relevant_until=row.relevant_until,
        rationale=row.rationale,
        contributing_event_ids=tuple(row.contributing_event_ids),
        contributing_event_types=tuple(
            BusinessEventType(value) for value in row.contributing_event_types
        ),
        constituent_signal_ids=tuple(row.constituent_signal_ids),
        catalog_version=row.catalog_version,
        profile_version=row.profile_version,
        payload_version=row.payload_version,
        supersedes=row.supersedes,
    )


def _to_profile(row: SignalProfileModel) -> SignalProfile:
    return SignalProfile(
        id=row.id,
        workspace_id=row.workspace_id,
        version=row.version,
        entries=tuple(_to_entry(entry) for entry in row.entries),
        created_at=row.created_at,
        created_by=row.created_by,
        supersedes=row.supersedes,
    )


def _to_entry(raw: dict[str, Any]) -> ProfileEntry:
    return ProfileEntry(
        signal_type=SignalType(raw["signal_type"]),
        relevance=Relevance(raw["relevance"]),
        window_days=raw.get("window_days"),
        minimum_contributors=raw.get("minimum_contributors"),
    )


class SqlSignalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def current_for_entity(
        self, workspace_id: UUID, entity_id: UUID, *, signal_type: SignalType
    ) -> tuple[Signal, ...]:
        replaced = select(SignalModel.supersedes).where(
            SignalModel.workspace_id == workspace_id, SignalModel.supersedes.is_not(None)
        )
        rows = await self._session.execute(
            select(SignalModel)
            .where(
                SignalModel.workspace_id == workspace_id,
                SignalModel.entity_id == entity_id,
                SignalModel.signal_type == signal_type.value,
                SignalModel.id.not_in(replaced),
            )
            .order_by(SignalModel.occurred_at, SignalModel.id)
        )
        return tuple(_to_signal(row) for row in rows.scalars())

    async def record(self, signals: tuple[Signal, ...]) -> int:
        if not signals:
            return 0

        statement = (
            insert(SignalModel)
            .values(
                [
                    {
                        "id": signal.id,
                        "workspace_id": signal.workspace_id,
                        "entity_id": signal.entity_id,
                        "signal_type": signal.signal_type.value,
                        "relevance": signal.relevance.value,
                        "occurred_at": signal.occurred_at,
                        "window_start": signal.window_start,
                        "window_end": signal.window_end,
                        "generated_at": signal.generated_at,
                        "relevant_until": signal.relevant_until,
                        "rationale": signal.rationale,
                        "contributing_event_ids": list(signal.contributing_event_ids),
                        "contributing_event_types": [
                            t.value for t in signal.contributing_event_types
                        ],
                        "constituent_signal_ids": list(signal.constituent_signal_ids),
                        "catalog_version": signal.catalog_version,
                        "profile_version": signal.profile_version,
                        "payload_version": signal.payload_version,
                        "supersedes": signal.supersedes,
                        "created_by": SYSTEM_USER_ID,
                        "updated_by": SYSTEM_USER_ID,
                    }
                    for signal in signals
                ]
            )
            .on_conflict_do_nothing(index_elements=["id"])
            .returning(SignalModel.id)
        )
        result = await self._session.execute(statement)
        return len(result.scalars().all())

    async def for_entity(
        self,
        workspace_id: UUID,
        entity_id: UUID,
        *,
        signal_type: SignalType | None = None,
        live_at: datetime | None = None,
    ) -> tuple[Signal, ...]:
        statement = select(SignalModel).where(
            SignalModel.workspace_id == workspace_id, SignalModel.entity_id == entity_id
        )
        if signal_type is not None:
            statement = statement.where(SignalModel.signal_type == signal_type.value)
        if live_at is not None:
            # A hypothesis stops being current in three ways; two of them
            # are here. The third — the workspace no longer holding the
            # type — is a profile question the query layer resolves.
            replaced = select(SignalModel.supersedes).where(
                SignalModel.workspace_id == workspace_id, SignalModel.supersedes.is_not(None)
            )
            statement = statement.where(
                SignalModel.relevant_until >= live_at, SignalModel.id.not_in(replaced)
            )

        rows = await self._session.execute(
            statement.order_by(SignalModel.occurred_at, SignalModel.id)
        )
        return tuple(_to_signal(row) for row in rows.scalars())

    async def by_id(self, workspace_id: UUID, signal_id: UUID) -> Signal | None:
        row = (
            await self._session.execute(
                select(SignalModel).where(
                    SignalModel.workspace_id == workspace_id, SignalModel.id == signal_id
                )
            )
        ).scalar_one_or_none()
        return _to_signal(row) if row is not None else None

    async def citing_events(
        self, workspace_id: UUID, business_event_ids: Sequence[UUID]
    ) -> tuple[Signal, ...]:
        if not business_event_ids:
            return ()
        rows = await self._session.execute(
            select(SignalModel)
            .where(
                SignalModel.workspace_id == workspace_id,
                SignalModel.contributing_event_ids.overlap(list(business_event_ids)),
            )
            .order_by(SignalModel.occurred_at, SignalModel.id)
        )
        return tuple(_to_signal(row) for row in rows.scalars())


class SqlProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def current(self, workspace_id: UUID) -> SignalProfile | None:
        """The profile in force: **the highest version.**

        **Not `WHERE supersedes IS NULL`** (`B-001`). On an immutable table the
        row with a null `supersedes` is the *first* version — the new row is
        the one that names its predecessor — so that predicate returned
        version 1 forever and silently ignored every revision a customer made.
        It never bit because nothing has ever written a second version, which
        is exactly the shape of defect that waits for a feature.

        A maximum cannot invert. `product_catalog` (migration `0019`) and
        `research_request` (`0021`) both read currency this way, for this
        reason.
        """
        row = (
            await self._session.execute(
                select(SignalProfileModel)
                .where(SignalProfileModel.workspace_id == workspace_id)
                .order_by(SignalProfileModel.version.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        return _to_profile(row) if row is not None else None

    async def by_version(self, workspace_id: UUID, version: int) -> SignalProfile | None:
        row = (
            await self._session.execute(
                select(SignalProfileModel).where(
                    SignalProfileModel.workspace_id == workspace_id,
                    SignalProfileModel.version == version,
                )
            )
        ).scalar_one_or_none()
        return _to_profile(row) if row is not None else None

    async def save(self, profile: SignalProfile) -> None:
        self._session.add(
            SignalProfileModel(
                id=profile.id,
                workspace_id=profile.workspace_id,
                version=profile.version,
                entries=[
                    {
                        "signal_type": entry.signal_type.value,
                        "relevance": entry.relevance.value,
                        "window_days": entry.window_days,
                        "minimum_contributors": entry.minimum_contributors,
                    }
                    for entry in profile.entries
                ],
                supersedes=profile.supersedes,
                created_by=profile.created_by,
                updated_by=profile.created_by,
            )
        )
        await self._session.flush()


#: **One table, not four**, because they are four shapes of the same fact —
#: *how this signal left the queue* — and a queue read that had to union four
#: tables would be reading one concept through four doors.
#:
#: ⚡ **The four words moved to `domain/resolution.py` when `signal.resolved`
#: began publishing them.** They were private here and correct while the column
#: was the only place they appeared; a published event spelling them out a
#: second time would be one fact with two representations, and the copy that
#: drifts is the one nobody is looking at (§2). **The names are unchanged, so
#: no stored row means anything different.**
_ACTIONED = ACTIONED
_ASSIGNED = ASSIGNED
_SNOOZED = SNOOZED
_DISMISSED = DISMISSED


def _to_outcome(row: SignalResolutionModel) -> Outcome:
    """Rebuild the outcome from its discriminator and payload.

    **Raises rather than defaulting on an unknown discriminator.** A row this
    code cannot interpret is a deployment reading data written by a newer one,
    and returning `Actioned()` for it would silently tell a customer their
    signal was handled.
    """
    # **`if`, not `match`.** A bare name in a `case` is a capture pattern, so
    # `case _ACTIONED` would bind the discriminator and match everything —
    # every row would read back as actioned, and the first branch would have
    # answered *"somebody handled it"* for a dismissal. `ruff` refused it
    # (`N806`) before a test could.
    if row.outcome == _ACTIONED:
        return Actioned()
    if row.outcome == _ASSIGNED:
        # The check constraint makes this non-null for this outcome; the
        # assertion is what tells `mypy` so, and would fire only if the
        # constraint had been dropped.
        assert row.assigned_to is not None
        return Assigned(to=row.assigned_to)
    if row.outcome == _SNOOZED:
        assert row.snoozed_until is not None
        return Snoozed(until=row.snoozed_until)
    if row.outcome == _DISMISSED:
        assert row.dismissal_reason is not None
        return Dismissed(reason=DismissalReason(row.dismissal_reason))
    # **No identifier, and not a `422`.** A row this build cannot read is a
    # deployment behind the data, never something the reader did.
    raise UnreadableOutcomeError(
        f"A decision recorded against this signal names an outcome this version of "
        f"Signora does not know: {row.outcome!r}."
    )


def _to_resolution(row: SignalResolutionModel) -> Resolution:
    return Resolution(
        id=row.id,
        workspace_id=row.workspace_id,
        signal_id=row.signal_id,
        outcome=_to_outcome(row),
        actor_id=row.actor_id,
        recorded_at=row.recorded_at,
        supersedes=row.supersedes,
        payload_version=row.payload_version,
    )


class SqlResolutionRepository:
    """How a signal left the queue.

    **A third repository rather than a method on the signal one**, on the rule
    the module already follows: signals are derived and rebuildable, profiles
    are customer-authored, and these are decisions people made. A rebuild that
    could reach a resolution is a rebuild that could discard one.

    No update method, and no method that writes a signal.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(self, resolution: Resolution) -> None:
        outcome = resolution.outcome
        self._session.add(
            SignalResolutionModel(
                id=resolution.id,
                workspace_id=resolution.workspace_id,
                signal_id=resolution.signal_id,
                outcome=discriminator(outcome),
                assigned_to=outcome.to if isinstance(outcome, Assigned) else None,
                snoozed_until=outcome.until if isinstance(outcome, Snoozed) else None,
                dismissal_reason=(outcome.reason.text if isinstance(outcome, Dismissed) else None),
                actor_id=resolution.actor_id,
                recorded_at=resolution.recorded_at,
                supersedes=resolution.supersedes,
                payload_version=resolution.payload_version,
                # **The audit columns name the same person, not the platform.**
                # `SYSTEM_USER_ID` appears above because a signal is machine-
                # authored; nothing in this table is.
                created_by=resolution.actor_id,
                updated_by=resolution.actor_id,
            )
        )
        await self._session.flush()

    async def current_for_signals(
        self, workspace_id: UUID, signal_ids: Sequence[UUID]
    ) -> dict[UUID, Resolution]:
        """**A signal with no key is open**, and that is deliberately not the
        same as one resolved to do nothing.

        Currency is *"nothing supersedes it"*, read the way this module already
        reads it for signals — the superseded set, excluded — rather than by a
        flag a writer has to remember to clear.
        """
        if not signal_ids:
            return {}
        replaced = select(SignalResolutionModel.supersedes).where(
            SignalResolutionModel.workspace_id == workspace_id,
            SignalResolutionModel.supersedes.is_not(None),
        )
        rows = await self._session.execute(
            select(SignalResolutionModel).where(
                SignalResolutionModel.workspace_id == workspace_id,
                SignalResolutionModel.signal_id.in_(list(signal_ids)),
                SignalResolutionModel.id.not_in(replaced),
            )
        )
        return {row.signal_id: _to_resolution(row) for row in rows.scalars()}

    async def history_for_signal(
        self, workspace_id: UUID, signal_id: UUID
    ) -> tuple[Resolution, ...]:
        """Oldest first, **ordered by the supersession chain rather than by
        time.**

        `ORDER BY recorded_at, id` looked right and is not. Two corrections
        made in the same instant — one request, one clock reading — tie on
        `recorded_at` and fall through to a random UUID, so the audit trail
        would render in an arbitrary order and a dismissal could appear to
        follow the decision that replaced it. **A test caught it by fixing the
        clock**, which is the case a real clock makes rare rather than
        impossible.

        **The chain is total and cannot tie**: each resolution names exactly
        the one it replaces, which is why `supersedes` exists. Time is kept
        only as the tie-break for rows outside the chain, so a row is never
        dropped from an audit trail on account of being unexpected.
        """
        rows = await self._session.execute(
            select(SignalResolutionModel)
            .where(
                SignalResolutionModel.workspace_id == workspace_id,
                SignalResolutionModel.signal_id == signal_id,
            )
            .order_by(SignalResolutionModel.recorded_at, SignalResolutionModel.id)
        )
        return _in_chain_order(tuple(_to_resolution(row) for row in rows.scalars()))


def _in_chain_order(resolutions: tuple[Resolution, ...]) -> tuple[Resolution, ...]:
    """Sort by *what replaced what*, which is the only total order here.

    **Anything not reachable from the chain is appended, never dropped.** A
    history that silently omitted a row it could not place would be the one
    kind of bug an audit trail must not have — and the caller cannot tell the
    difference between a row that does not exist and one this function failed
    to thread.
    """
    if len(resolutions) < 2:
        return resolutions

    successors = {r.supersedes: r for r in resolutions if r.supersedes is not None}
    roots = [r for r in resolutions if r.supersedes is None]
    ordered: list[Resolution] = []
    seen: set[UUID] = set()
    for root in roots:
        current: Resolution | None = root
        while current is not None and current.id not in seen:
            ordered.append(current)
            seen.add(current.id)
            current = successors.get(current.id)
    # Orphans keep their time order, behind everything the chain explains.
    ordered.extend(r for r in resolutions if r.id not in seen)
    return tuple(ordered)
