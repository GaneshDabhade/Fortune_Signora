"""The one place pipeline vocabulary becomes evidence, against the real thing.

Against a live pipeline rather than a fixture, deliberately. A defect in this
translation corrupts every golden dataset and every narration **silently**,
because the output would still be perfectly grounded — in the wrong facts. A
hand-built `OpportunityExplanation` would be shaped by what is convenient to
translate, which is exactly the failure mode.

Nothing here calls a model.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.ai_platform.infrastructure.explanation import (
    BUYING_SCORE,
    CONTRIBUTION,
    OPPORTUNITY,
    OpportunityExplanationSource,
)
from signora_platform.db import tenant_scoped_session
from tests.opportunity_engine.test_opportunity_pipeline import _tracked
from tests.pipeline import opportunities

pytestmark = pytest.mark.integration


class TestAssemblingEvidenceFromTheRealPipeline:
    async def test_it_assembles_the_opportunity_its_score_and_its_signals(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            source = OpportunityExplanationSource(opportunities(session, workspace_id))
            evidence = await source.evidence_for(workspace_id, entity_id)

        assert evidence is not None
        kinds = {fact.ref.kind for fact in evidence}
        assert {OPPORTUNITY, BUYING_SCORE, CONTRIBUTION} == kinds
        assert evidence.workspace_id == workspace_id

    async def test_every_fact_belongs_to_the_requesting_workspace(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The builder refuses a foreign fact outright, so this asserts the
        translation never had one to offer — AC-67 at the assembly boundary."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            source = OpportunityExplanationSource(opportunities(session, workspace_id))
            evidence = await source.evidence_for(workspace_id, entity_id)

        assert evidence is not None
        assert all(fact.workspace_id == workspace_id for fact in evidence)

    async def test_every_quantity_survives_as_the_text_the_model_is_shown(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            source = OpportunityExplanationSource(opportunities(session, workspace_id))
            evidence = await source.evidence_for(workspace_id, entity_id)

        assert evidence is not None
        score = next(f for f in evidence if f.ref.kind == BUYING_SCORE)
        attributes = {name: str(value) for name, value in score.attributes}
        assert attributes["value"].isdigit()
        assert attributes["value"] in score.summary, (
            "the number in the summary and the number in the attributes must be the same "
            "number, or a model citing one and writing the other is ungrounded by construction"
        )

    async def test_an_account_with_no_opportunity_yields_no_evidence(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """`None`, never an empty set. An empty evidence set would reach a
        model and produce a fluent paragraph about nothing."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            source = OpportunityExplanationSource(opportunities(session, workspace_id))
            assert await source.evidence_for(workspace_id, uuid4()) is None
