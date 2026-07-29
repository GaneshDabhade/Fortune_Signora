"""Test doubles and builders for the Buying Score Engine.

Signals are built directly rather than generated, so a scoring test states
the hypotheses it is about instead of arranging the business events that
would produce them. What M5B does with a signal is the subject here; how
M5A arrives at one is tested where it belongs.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from modules.business_event_engine.public import BusinessEventType
from modules.buying_score_engine.domain.score import BuyingScore
from modules.buying_score_engine.domain.workspace_model import WorkspaceScoringModel
from modules.signal_engine.public import (
    ProfileEntry,
    Relevance,
    Signal,
    SignalCatalog,
    SignalExplanation,
    SignalProfile,
    SignalType,
)

WORKSPACE = UUID("11111111-1111-4111-8111-111111111111")
ENTITY = UUID("22222222-2222-4222-8222-222222222222")
NOW = datetime(2026, 3, 1, tzinfo=UTC)


def make_signal(
    *,
    signal_type: SignalType,
    events: tuple[UUID, ...],
    relevance: Relevance = Relevance.PRIMARY,
    occurred_at: datetime = NOW,
    window_days: int = 180,
    signal_id: UUID | None = None,
    constituents: tuple[UUID, ...] = (),
) -> Signal:
    return Signal(
        id=signal_id or uuid4(),
        workspace_id=WORKSPACE,
        entity_id=ENTITY,
        signal_type=signal_type,
        relevance=relevance,
        occurred_at=occurred_at,
        window_start=occurred_at,
        window_end=occurred_at,
        generated_at=occurred_at,
        relevant_until=occurred_at + timedelta(days=window_days),
        rationale="because the evidence says so",
        contributing_event_ids=events,
        contributing_event_types=(BusinessEventType.FUNDING_ROUND_CLOSED,),
        constituent_signal_ids=constituents,
        catalog_version=1,
        profile_version=0,
    )


class FakeScoreRepository:
    def __init__(self) -> None:
        self.rows: list[BuyingScore] = []

    def _replaced(self) -> set[UUID]:
        return {s.supersedes for s in self.rows if s.supersedes is not None}

    async def current(self, workspace_id: UUID, entity_id: UUID) -> BuyingScore | None:
        replaced = self._replaced()
        live = [
            s
            for s in self.rows
            if s.workspace_id == workspace_id and s.entity_id == entity_id and s.id not in replaced
        ]
        return max(live, key=lambda s: s.computed_at) if live else None

    async def record(self, score: BuyingScore) -> bool:
        if any(s.id == score.id for s in self.rows):
            return False
        self.rows.append(score)
        return True

    async def by_id(self, workspace_id: UUID, score_id: UUID) -> BuyingScore | None:
        return next(
            (s for s in self.rows if s.workspace_id == workspace_id and s.id == score_id), None
        )

    async def for_entity(
        self, workspace_id: UUID, entity_id: UUID, *, limit: int | None = None
    ) -> tuple[BuyingScore, ...]:
        rows = sorted(
            (
                s
                for s in self.rows
                if s.workspace_id == workspace_id and s.entity_id == entity_id
            ),
            key=lambda s: s.computed_at,
            reverse=True,
        )
        return tuple(rows if limit is None else rows[:limit])

    async def stale(
        self, workspace_id: UUID, moment: datetime, *, limit: int
    ) -> tuple[BuyingScore, ...]:
        replaced = self._replaced()
        rows = [
            s
            for s in self.rows
            if s.workspace_id == workspace_id
            and s.valid_until is not None
            and s.valid_until < moment
            and s.id not in replaced
        ]
        return tuple(sorted(rows, key=lambda s: s.valid_until or moment)[:limit])


class FakeScoringModelRepository:
    def __init__(self) -> None:
        self.rows: list[WorkspaceScoringModel] = []

    async def current(self, workspace_id: UUID) -> WorkspaceScoringModel | None:
        live = [m for m in self.rows if m.workspace_id == workspace_id and m.supersedes is None]
        return live[0] if live else None

    async def by_version(
        self, workspace_id: UUID, version: int
    ) -> WorkspaceScoringModel | None:
        return next(
            (m for m in self.rows if m.workspace_id == workspace_id and m.version == version),
            None,
        )

    async def save(self, model: WorkspaceScoringModel) -> None:
        self.rows.append(model)


class FakeSignalQueries:
    """Satisfies `SignalReader` — the four members M5B actually depends on."""

    def __init__(
        self,
        signals: tuple[Signal, ...],
        catalog: SignalCatalog,
        profile: SignalProfile | None = None,
    ) -> None:
        self._signals = signals
        self._catalog = catalog
        self._profile = profile

    async def signals(
        self,
        workspace_id: UUID,
        entity_id: UUID,
        *,
        signal_type: SignalType | None = None,
        live_only: bool = True,
        now: datetime | None = None,
    ) -> tuple[Signal, ...]:
        moment = now or NOW
        return tuple(
            s
            for s in self._signals
            if s.entity_id == entity_id
            and (not live_only or s.relevant_until >= moment)
        )

    async def explanation(self, workspace_id: UUID, signal_id: UUID) -> SignalExplanation | None:
        signal = next((s for s in self._signals if s.id == signal_id), None)
        if signal is None:
            return None

        return SignalExplanation(
            signal=signal,
            definition=self._catalog.definition(signal.signal_type),
            profile_entry=ProfileEntry(
                signal_type=signal.signal_type, relevance=signal.relevance
            ),
            profile_version=signal.profile_version,
            business_events=(),
            constituents=(),
        )

    async def stored_profile(self, workspace_id: UUID) -> SignalProfile | None:
        return self._profile

    def catalog(self) -> SignalCatalog:
        return self._catalog
