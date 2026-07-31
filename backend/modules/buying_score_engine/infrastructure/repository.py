"""Persistence for buying scores and workspace scoring models.

**Two repositories, deliberately.** Scores are derived and rebuildable;
scoring models are customer-authored and cannot be regenerated from
anything. Keeping them apart makes it impossible to write a rebuild that
quietly discards a customer's weighting.

Neither offers an update method. Immutability is enforced at the database by
the absent UPDATE grant (migration 0013); not offering the method here means
nobody writes code that would fail at runtime.

The ledger is stored as JSONB rather than as a child table: it is written
once, read whole, never queried across rows, and never updated. A child
table would add a join and a second immutability surface for no gain.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from modules.buying_score_engine.domain.ledger import Contribution, ContributionLedger
from modules.buying_score_engine.domain.score import BuyingScore, ScoreTrigger, Trend
from modules.buying_score_engine.domain.scoring_model import AgeBand, Posture
from modules.buying_score_engine.domain.workspace_model import (
    ScoringOverrides,
    WorkspaceScoringModel,
)
from modules.buying_score_engine.infrastructure.models import (
    BuyingScoreModel,
    WorkspaceScoringModelModel,
)
from modules.signal_engine.public import Relevance, SignalType

SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _contribution_to_json(entry: Contribution) -> dict[str, Any]:
    return {
        "business_event_id": str(entry.business_event_id),
        "signal_id": str(entry.signal_id),
        "signal_type": entry.signal_type.value,
        "posture": entry.posture.value,
        "relevance": entry.relevance.value,
        "base_weight": entry.base_weight,
        "relevance_multiplier": entry.relevance_multiplier,
        "age_band": entry.age_band,
        "age_multiplier": entry.age_multiplier,
        "contribution": entry.contribution,
        "counted": entry.counted,
        "reason": entry.reason,
        "band_started_at": entry.band_started_at.isoformat(),
        "band_ends_at": entry.band_ends_at.isoformat(),
    }


def _contribution_from_json(raw: dict[str, Any]) -> Contribution:
    return Contribution(
        business_event_id=UUID(raw["business_event_id"]),
        signal_id=UUID(raw["signal_id"]),
        signal_type=SignalType(raw["signal_type"]),
        posture=Posture(raw["posture"]),
        relevance=Relevance(raw["relevance"]),
        base_weight=raw["base_weight"],
        relevance_multiplier=raw["relevance_multiplier"],
        age_band=raw["age_band"],
        age_multiplier=raw["age_multiplier"],
        contribution=raw["contribution"],
        counted=raw["counted"],
        reason=raw["reason"],
        band_started_at=datetime.fromisoformat(raw["band_started_at"]),
        band_ends_at=datetime.fromisoformat(raw["band_ends_at"]),
    )


def _to_score(row: BuyingScoreModel) -> BuyingScore:
    return BuyingScore(
        id=row.id,
        workspace_id=row.workspace_id,
        entity_id=row.entity_id,
        value=row.value,
        trend=Trend(row.trend),
        delta=row.delta,
        # Reconstructed rather than recomputed. A score explained by
        # re-running today's model against today's clock would answer a
        # different question than the one the customer was shown.
        ledger=ContributionLedger(
            entries=tuple(_contribution_from_json(raw) for raw in row.ledger),
            ceiling=row.ceiling,
        ),
        contested=row.contested,
        dissenting_signal_ids=tuple(row.dissenting_signal_ids),
        computed_at=row.computed_at,
        valid_until=row.valid_until,
        basis_at=row.basis_at,
        trigger=ScoreTrigger(row.trigger),
        scoring_model_version=row.scoring_model_version,
        model_artifact_version=row.model_artifact_version,
        profile_version=row.profile_version,
        payload_version=row.payload_version,
        supersedes=row.supersedes,
    )


def _to_workspace_model(row: WorkspaceScoringModelModel) -> WorkspaceScoringModel:
    raw = row.overrides
    bands = raw.get("age_bands")
    return WorkspaceScoringModel(
        id=row.id,
        workspace_id=row.workspace_id,
        version=row.version,
        overrides=ScoringOverrides(
            base_weights={
                SignalType(key): value for key, value in raw.get("base_weights", {}).items()
            },
            relevance_multipliers={
                Relevance(key): value
                for key, value in raw.get("relevance_multipliers", {}).items()
            },
            age_bands=None if bands is None else tuple(AgeBand(**band) for band in bands),
            ceiling=raw.get("ceiling"),
            steady_delta=raw.get("steady_delta"),
        ),
        created_at=row.created_at,
        created_by=row.created_by,
        supersedes=row.supersedes,
    )


def _overrides_to_json(overrides: ScoringOverrides) -> dict[str, Any]:
    return {
        "base_weights": {key.value: value for key, value in overrides.base_weights.items()},
        "relevance_multipliers": {
            key.value: value for key, value in overrides.relevance_multipliers.items()
        },
        "age_bands": (
            None
            if overrides.age_bands is None
            else [band.model_dump() for band in overrides.age_bands]
        ),
        "ceiling": overrides.ceiling,
        "steady_delta": overrides.steady_delta,
    }


class SqlBuyingScoreRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def current(self, workspace_id: UUID, entity_id: UUID) -> BuyingScore | None:
        replaced = select(BuyingScoreModel.supersedes).where(
            BuyingScoreModel.workspace_id == workspace_id,
            BuyingScoreModel.supersedes.is_not(None),
        )
        row = (
            await self._session.execute(
                select(BuyingScoreModel)
                .where(
                    BuyingScoreModel.workspace_id == workspace_id,
                    BuyingScoreModel.entity_id == entity_id,
                    BuyingScoreModel.id.not_in(replaced),
                )
                .order_by(BuyingScoreModel.computed_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        return _to_score(row) if row is not None else None

    async def current_for(
        self, workspace_id: UUID, entity_ids: tuple[UUID, ...]
    ) -> dict[UUID, BuyingScore]:
        """The current score for each of these accounts, in **one** query.

        Exists because the attention list needs a live score per row, and
        asking `current()` once per account would make a 50-account page 50
        round trips — an obviously wasteful pattern is a defect at write time
        (CLAUDE.md §14), not a future optimisation.
        """
        if not entity_ids:
            return {}
        replaced = select(BuyingScoreModel.supersedes).where(
            BuyingScoreModel.workspace_id == workspace_id,
            BuyingScoreModel.supersedes.is_not(None),
        )
        rows = (
            await self._session.execute(
                select(BuyingScoreModel)
                .where(
                    BuyingScoreModel.workspace_id == workspace_id,
                    BuyingScoreModel.entity_id.in_(entity_ids),
                    BuyingScoreModel.id.not_in(replaced),
                )
                .order_by(BuyingScoreModel.computed_at.desc())
            )
        ).scalars()
        # Newest first, so the first row seen for an entity is its current one.
        current: dict[UUID, BuyingScore] = {}
        for row in rows:
            current.setdefault(row.entity_id, _to_score(row))
        return current

    async def record(self, score: BuyingScore) -> bool:
        statement = (
            insert(BuyingScoreModel)
            .values(
                {
                    "id": score.id,
                    "workspace_id": score.workspace_id,
                    "entity_id": score.entity_id,
                    "value": score.value,
                    "trend": score.trend.value,
                    "delta": score.delta,
                    "ledger": [_contribution_to_json(e) for e in score.ledger.entries],
                    "ceiling": score.ledger.ceiling,
                    "contested": score.contested,
                    "dissenting_signal_ids": list(score.dissenting_signal_ids),
                    "computed_at": score.computed_at,
                    "valid_until": score.valid_until,
                    "basis_at": score.basis_at,
                    "trigger": score.trigger.value,
                    "scoring_model_version": score.scoring_model_version,
                    "model_artifact_version": score.model_artifact_version,
                    "profile_version": score.profile_version,
                    "payload_version": score.payload_version,
                    "supersedes": score.supersedes,
                    "created_by": SYSTEM_USER_ID,
                    "updated_by": SYSTEM_USER_ID,
                }
            )
            .on_conflict_do_nothing(index_elements=["id"])
            .returning(BuyingScoreModel.id)
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none() is not None

    async def by_id(self, workspace_id: UUID, score_id: UUID) -> BuyingScore | None:
        row = (
            await self._session.execute(
                select(BuyingScoreModel).where(
                    BuyingScoreModel.workspace_id == workspace_id,
                    BuyingScoreModel.id == score_id,
                )
            )
        ).scalar_one_or_none()
        return _to_score(row) if row is not None else None

    async def for_entity(
        self, workspace_id: UUID, entity_id: UUID, *, limit: int | None = None
    ) -> tuple[BuyingScore, ...]:
        statement = (
            select(BuyingScoreModel)
            .where(
                BuyingScoreModel.workspace_id == workspace_id,
                BuyingScoreModel.entity_id == entity_id,
            )
            .order_by(BuyingScoreModel.computed_at.desc(), BuyingScoreModel.id)
        )
        if limit is not None:
            statement = statement.limit(limit)
        rows = await self._session.execute(statement)
        return tuple(_to_score(row) for row in rows.scalars())

    async def stale(
        self, workspace_id: UUID, moment: datetime, *, limit: int
    ) -> tuple[BuyingScore, ...]:
        replaced = select(BuyingScoreModel.supersedes).where(
            BuyingScoreModel.workspace_id == workspace_id,
            BuyingScoreModel.supersedes.is_not(None),
        )
        rows = await self._session.execute(
            select(BuyingScoreModel)
            .where(
                BuyingScoreModel.workspace_id == workspace_id,
                BuyingScoreModel.valid_until.is_not(None),
                BuyingScoreModel.valid_until < moment,
                BuyingScoreModel.id.not_in(replaced),
            )
            .order_by(BuyingScoreModel.valid_until)
            .limit(limit)
        )
        return tuple(_to_score(row) for row in rows.scalars())


class SqlScoringModelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def current(self, workspace_id: UUID) -> WorkspaceScoringModel | None:
        row = (
            await self._session.execute(
                select(WorkspaceScoringModelModel).where(
                    WorkspaceScoringModelModel.workspace_id == workspace_id,
                    WorkspaceScoringModelModel.supersedes.is_(None),
                )
            )
        ).scalar_one_or_none()
        return _to_workspace_model(row) if row is not None else None

    async def by_version(
        self, workspace_id: UUID, version: int
    ) -> WorkspaceScoringModel | None:
        row = (
            await self._session.execute(
                select(WorkspaceScoringModelModel).where(
                    WorkspaceScoringModelModel.workspace_id == workspace_id,
                    WorkspaceScoringModelModel.version == version,
                )
            )
        ).scalar_one_or_none()
        return _to_workspace_model(row) if row is not None else None

    async def save(self, model: WorkspaceScoringModel) -> None:
        self._session.add(
            WorkspaceScoringModelModel(
                id=model.id,
                workspace_id=model.workspace_id,
                version=model.version,
                overrides=_overrides_to_json(model.overrides),
                supersedes=model.supersedes,
                created_by=model.created_by,
                updated_by=model.created_by,
            )
        )
        await self._session.flush()
