"""Composition root for the Buying Score Engine.

The Signal Engine's query surface is a **parameter, not a construction**:
building it here would mean importing another module's infrastructure.

The scoring model artifact is validated against the signal catalog once, at
wiring time rather than at first scoring. A signal type nobody weighted
contributes nothing, and an account holding a strong hypothesis nobody
weighted looks exactly like an account where nothing has happened — a
failure that is invisible in production and obvious at startup.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from modules.buying_score_engine.application.compute import ComputeBuyingScore
from modules.buying_score_engine.application.queries import BuyingScoreQueries
from modules.buying_score_engine.domain.scoring_model import ScoringModel
from modules.buying_score_engine.infrastructure.model_loader import load_scoring_model
from modules.buying_score_engine.infrastructure.repository import (
    SqlBuyingScoreRepository,
    SqlScoringModelRepository,
)
from modules.signal_engine.public import SignalQueries
from signora_platform.event_bus import EventPublisher


def validated_artifact(signals: SignalQueries) -> ScoringModel:
    artifact = load_scoring_model()
    artifact.validate_covers(frozenset(d.key for d in signals.catalog().types))
    return artifact


def build_compute_buying_score(
    session: AsyncSession,
    *,
    signals: SignalQueries,
    publisher: EventPublisher,
    clock: Callable[[], datetime] | None = None,
) -> ComputeBuyingScore:
    """`clock` is the point at which a score is read.

    Injectable because scoring is time-dependent in a way the stages before
    it are not: **historical replay** reproduces the number a customer was
    shown at a past moment, which requires asking the question *as of* then.
    Defaulted, so ordinary event-driven scoring reads the wall clock.
    """
    return ComputeBuyingScore(
        repository=SqlBuyingScoreRepository(session),
        models=SqlScoringModelRepository(session),
        signals=signals,
        artifact=validated_artifact(signals),
        publisher=publisher,
        session=session,
        **({} if clock is None else {"clock": clock}),
    )


def build_queries(session: AsyncSession, *, signals: SignalQueries) -> BuyingScoreQueries:
    return BuyingScoreQueries(
        repository=SqlBuyingScoreRepository(session),
        models=SqlScoringModelRepository(session),
        signals=signals,
        artifact=validated_artifact(signals),
    )


def build_scoring_models(session: AsyncSession) -> SqlScoringModelRepository:
    """Customer-authored weighting, deliberately reachable on its own — it
    is not derived data and must not be rebuilt with the rest."""
    return SqlScoringModelRepository(session)
