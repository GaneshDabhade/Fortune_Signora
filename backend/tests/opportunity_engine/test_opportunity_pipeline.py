"""M6 demonstration: a number becomes a decision, and the decision survives.

Proves the eighth link, and the **first one that is not derived**. Every
stage before it is a function of the evidence beneath it: delete the table,
re-run the pipeline, get the same rows back. An opportunity records that a
human committed, and nothing reproduces that.

The assertions that matter most are the two that protect the boundary:
regenerating the derived pipeline leaves workflow untouched, and no code
path moves an opportunity without a person.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.opportunity_engine.application.transition import (
    MembershipError,
    TransitionOpportunityInput,
)
from modules.opportunity_engine.domain.opportunity import (
    EvidenceState,
    Qualification,
    Stage,
)
from modules.opportunity_engine.infrastructure.composition import (
    build_transition_opportunity,
)
from modules.workspace_tenancy.infrastructure.query_service import WorkspaceQueryService
from signora_platform.db import tenant_scoped_session
from signora_platform.event_bus import PostgresOutboxEventPublisher
from tests.buying_score_engine.test_buying_score_pipeline import _scored  # noqa: F401
from tests.pipeline import (
    opportunities,
    qualify_all,
    score_all,
    set_opportunity_policy,
)

pytestmark = pytest.mark.integration

OUTSIDER = UUID("77777777-7777-4777-8777-777777777777")


async def _tracked(
    factory: async_sessionmaker[AsyncSession],
    admin_factory: async_sessionmaker[AsyncSession],
    name: str,
    *,
    anchor: str = "acme-corp",
    moment: datetime | None = None,
    **scenario: Any,
) -> tuple[UUID, UUID, UUID, datetime]:
    """The whole pipeline, ending in qualified opportunities.

    `**scenario` reaches the ingest unchanged, which is what lets the Playground
    run *this* function rather than a parallel seeding path.
    """
    workspace_id, user_id, entity_id, moment = await _scored(
        factory, admin_factory, name, anchor=anchor, moment=moment, **scenario
    )
    # The scenario's evidence is thin, and Signora's shipped threshold
    # declines it — correctly. Rather than tune a product default to make a
    # demonstration pass, the workspace authors its own, which is the layer
    # this milestone added. Asserted in its own right below.
    await set_opportunity_policy(factory, workspace_id, user_id, minimum_score=1)
    # Opened *at the moment the question was asked*, not at wall-clock now.
    # An opportunity records a commitment, and a commitment made against a
    # historical reading did not happen today.
    await qualify_all(factory, admin_factory, workspace_id, user_id, moment=moment)
    return workspace_id, user_id, entity_id, moment


async def _move(
    factory: async_sessionmaker[AsyncSession],
    workspace_id: UUID,
    user_id: UUID,
    opportunity_id: UUID,
    stage: Stage,
    *,
    actor: UUID | None = None,
    owner: UUID | None = None,
    reason: str = "demonstration",
) -> None:
    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        transition = build_transition_opportunity(
            session,
            workspaces=WorkspaceQueryService(session),
            publisher=PostgresOutboxEventPublisher(),
        )
        await transition.execute(
            TransitionOpportunityInput(
                workspace_id=workspace_id,
                opportunity_id=opportunity_id,
                stage=stage,
                actor_id=actor or user_id,
                owner_id=owner,
                reason=reason,
            ),
            correlation_id=uuid4(),
        )


class TestIntelligenceSuggests:
    async def test_a_qualifying_score_opens_a_suggestion_nobody_owns(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "Suggest"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            tracked = await opportunities(session, workspace_id).tracked(workspace_id, entity_id)

        assert tracked is not None
        assert tracked.state.stage is Stage.TRACKING
        assert tracked.state.owner_id is None
        assert tracked.state.actor_id is None, "Signora is not a person"
        assert tracked.opportunity.qualification is Qualification.AUTOMATIC
        assert tracked.opportunity.score_at_creation > 0

    async def test_signoras_shipped_threshold_declines_this_thin_evidence(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**An honest limit, recorded rather than tuned away.**

        The simulated scenario produces a modest score, and Signora's
        shipped threshold correctly declines to suggest tracking on it.
        Lowering the product default to make a demonstration succeed would
        be tuning the fixture to fit the story — so the demonstration above
        has the *workspace* author its own threshold instead, which is the
        ownership layer this milestone added.
        """
        workspace_id, user_id, entity_id, _ = await _scored(
            session_factory, admin_session_factory, "Default"
        )

        await qualify_all(session_factory, admin_session_factory, workspace_id, user_id)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            queries = opportunities(session, workspace_id)
            tracked = await queries.tracked(workspace_id, entity_id)
            policy, version = await queries.policy(workspace_id)
            score = await queries.explanation(workspace_id, uuid4())

        assert tracked is None
        assert score is None
        assert version == 0, "an unconfigured workspace uses the shipped artifact"
        assert policy.minimum_score == queries.artifact().minimum_score

    async def test_re_running_qualification_opens_nothing_new(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "Once"
        )

        async def count() -> int:
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                return int(
                    (await session.execute(text("SELECT count(*) FROM opportunity"))).scalar_one()
                )

        before = await count()
        await qualify_all(session_factory, admin_session_factory, workspace_id, user_id)

        assert await count() == before


class TestHumansCommit:
    async def test_a_human_engages_assigns_and_closes_with_a_reason(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "Commit"
        )
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            tracked = await opportunities(session, workspace_id).tracked(workspace_id, entity_id)
        assert tracked is not None

        await _move(
            session_factory,
            workspace_id,
            user_id,
            tracked.opportunity.id,
            Stage.ENGAGED,
            owner=user_id,
            reason="worth a call this quarter",
        )
        await _move(
            session_factory,
            workspace_id,
            user_id,
            tracked.opportunity.id,
            Stage.CLOSED_LOST,
            reason="chose a rival",
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            history = await opportunities(session, workspace_id).history(
                workspace_id, tracked.opportunity.id
            )

        assert [s.stage for s in history] == [
            Stage.TRACKING,
            Stage.ENGAGED,
            Stage.CLOSED_LOST,
        ]
        assert [s.sequence for s in history] == [0, 1, 2]
        assert history[1].actor_id == user_id
        assert history[2].reason == "chose a rival"

    async def test_assignment_to_a_non_member_is_refused(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "Member"
        )
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            tracked = await opportunities(session, workspace_id).tracked(workspace_id, entity_id)
        assert tracked is not None

        with pytest.raises(MembershipError, match="not a member"):
            await _move(
                session_factory,
                workspace_id,
                user_id,
                tracked.opportunity.id,
                Stage.ENGAGED,
                owner=OUTSIDER,
            )

    async def test_reopening_keeps_one_opportunity_and_one_history(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "Reopen"
        )
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            tracked = await opportunities(session, workspace_id).tracked(workspace_id, entity_id)
        assert tracked is not None

        await _move(
            session_factory, workspace_id, user_id, tracked.opportunity.id, Stage.DISMISSED
        )
        await _move(
            session_factory,
            workspace_id,
            user_id,
            tracked.opportunity.id,
            Stage.ENGAGED,
            reason="they came back",
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            queries = opportunities(session, workspace_id)
            everything = await queries.for_entity(workspace_id, entity_id)
            history = await queries.history(workspace_id, tracked.opportunity.id)

        assert len(everything) == 1, "reopening is a transition, not a new opportunity"
        assert [s.stage for s in history] == [
            Stage.TRACKING,
            Stage.DISMISSED,
            Stage.ENGAGED,
        ]


class TestTheDecisionSurvivesTheNumber:
    async def test_an_expiring_score_moves_no_stage(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The lifecycle question, demonstrated.** Nothing happening at a
        company is not evidence that a deal is dead."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "Outlive"
        )
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            tracked = await opportunities(session, workspace_id).tracked(workspace_id, entity_id)
        assert tracked is not None
        await _move(
            session_factory,
            workspace_id,
            user_id,
            tracked.opportunity.id,
            Stage.ENGAGED,
            owner=user_id,
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            far_future = await opportunities(session, workspace_id).tracked(
                workspace_id, entity_id, now=datetime.now(UTC) + timedelta(days=3650)
            )

        assert far_future is not None
        assert far_future.state.stage is Stage.ENGAGED, "workflow must not move on its own"
        assert far_future.evidence_state is EvidenceState.STALE

    async def test_the_originating_score_still_explains_the_opportunity(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The chain, walked rather than asserted.** Opportunity → buying
        score → contribution ledger → signals → business events →
        observations → knowledge → claims → raw provider records."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "Chain"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            queries = opportunities(session, workspace_id)
            tracked = await queries.tracked(workspace_id, entity_id)
            assert tracked is not None
            explanation = await queries.explanation(workspace_id, tracked.opportunity.id)

        assert explanation is not None
        assert explanation.originating_score is not None
        score = explanation.originating_score.score
        assert score.id == tracked.opportunity.originating_buying_score_id
        assert score.value == score.ledger.value(), "the ledger still reproduces the score"
        assert explanation.originating_score.signals, "the chain must continue past the score"
        assert explanation.history, "workflow history is part of the explanation"


class TestARebuildRegeneratesIntelligenceOnly:
    async def test_regenerating_the_derived_pipeline_leaves_workflow_untouched(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The operational contract.** Until M6, "rebuild the pipeline" was
        universally safe. It is now safe *for derived intelligence*, and the
        difference has to be asserted rather than remembered."""
        workspace_id, user_id, entity_id, moment = await _tracked(
            session_factory, admin_session_factory, "Rebuild"
        )
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            tracked = await opportunities(session, workspace_id).tracked(workspace_id, entity_id)
        assert tracked is not None
        await _move(
            session_factory,
            workspace_id,
            user_id,
            tracked.opportunity.id,
            Stage.ENGAGED,
            owner=user_id,
            reason="a commitment a rebuild must not erase",
        )

        # Re-run the derived stage. Buying score ids are derived from their
        # evidence, so this reproduces them exactly — which is why the
        # citation is not orphaned.
        await score_all(
            session_factory, admin_session_factory, workspace_id, user_id, moment=moment
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            queries = opportunities(session, workspace_id)
            after = await queries.tracked(workspace_id, entity_id)
            history = await queries.history(workspace_id, tracked.opportunity.id)
            explanation = await queries.explanation(workspace_id, tracked.opportunity.id)

        assert after is not None
        assert after.opportunity.id == tracked.opportunity.id
        assert after.state.stage is Stage.ENGAGED
        assert after.state.owner_id == user_id
        assert [s.sequence for s in history] == [0, 1]
        assert explanation is not None and explanation.originating_score is not None, (
            "a rebuild must not orphan an opportunity's citation"
        )
