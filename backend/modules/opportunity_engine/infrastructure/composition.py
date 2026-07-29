"""Composition root for the Opportunity Engine.

The Buying Score Engine's query surface and Workspace & Tenancy's query
port are **parameters, not constructions**: building either here would mean
importing another module's infrastructure.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from modules.buying_score_engine.public import BuyingScoreQueries
from modules.opportunity_engine.application.qualify import QualifyOpportunity
from modules.opportunity_engine.application.queries import OpportunityQueries
from modules.opportunity_engine.application.transition import TransitionOpportunity
from modules.opportunity_engine.infrastructure.policy_loader import load_policy
from modules.opportunity_engine.infrastructure.repository import (
    SqlOpportunityPolicyRepository,
    SqlOpportunityRepository,
)
from modules.workspace_tenancy.public import WorkspaceQueryPort
from signora_platform.event_bus import EventPublisher


def build_qualify_opportunity(
    session: AsyncSession,
    *,
    scores: BuyingScoreQueries,
    publisher: EventPublisher,
    clock: Callable[[], datetime] | None = None,
) -> QualifyOpportunity:
    return QualifyOpportunity(
        repository=SqlOpportunityRepository(session),
        policies=SqlOpportunityPolicyRepository(session),
        scores=scores,
        artifact=load_policy(),
        publisher=publisher,
        session=session,
        **({} if clock is None else {"clock": clock}),
    )


def build_transition_opportunity(
    session: AsyncSession,
    *,
    workspaces: WorkspaceQueryPort,
    publisher: EventPublisher,
    clock: Callable[[], datetime] | None = None,
) -> TransitionOpportunity:
    return TransitionOpportunity(
        repository=SqlOpportunityRepository(session),
        workspaces=workspaces,
        publisher=publisher,
        session=session,
        **({} if clock is None else {"clock": clock}),
    )


def build_queries(
    session: AsyncSession, *, scores: BuyingScoreQueries
) -> OpportunityQueries:
    return OpportunityQueries(
        repository=SqlOpportunityRepository(session),
        policies=SqlOpportunityPolicyRepository(session),
        scores=scores,
        artifact=load_policy(),
    )


def build_policies(session: AsyncSession) -> SqlOpportunityPolicyRepository:
    """Customer-authored qualification, deliberately reachable on its own —
    it is not derived data and must not be rebuilt with the rest."""
    return SqlOpportunityPolicyRepository(session)
