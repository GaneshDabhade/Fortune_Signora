"""M4 demonstration: the pipeline says something a seller would recognise.

Proves the fifth link. Observations become typed business events — module
to module, over the event bus, with the chain intact from raw provider
payload through claim, decision, entity, and observation to a sentence a
CRO can read.

The assertion that matters most is still the negative one: re-running the
whole pipeline produces no new business events. The restraint M3B proved,
one layer up.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.business_event_engine.domain.taxonomy import BusinessEventType
from modules.business_event_engine.infrastructure.models import BusinessEventModel
from modules.business_event_engine.infrastructure.taxonomy_loader import load_taxonomy
from signora_platform.db import tenant_scoped_session
from tests.knowledge_graph.test_graph_pipeline import _run_pipeline, _workspace
from tests.observation_engine.test_observation_pipeline import _acme
from tests.pipeline import business_events, detect_all, observe_all

pytestmark = pytest.mark.integration


async def _pipeline(
    factory: async_sessionmaker[AsyncSession],
    admin_factory: async_sessionmaker[AsyncSession],
    name: str,
) -> tuple[object, object]:
    workspace_id, user_id = await _run_pipeline(factory, admin_factory, name)
    await observe_all(factory, admin_factory, workspace_id, user_id)
    await detect_all(factory, admin_factory, workspace_id, user_id)
    return workspace_id, user_id


class TestTheScenarioProducesBusinessNews:
    async def test_the_baseline_scenario_yields_recognisable_events(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Technology adopted and retired, and a funding round — what the
        baseline scenario actually contains.

        **Not a buying intent surge.** The scenario's intent ramp peaks at 88
        but clears the taxonomy's elevated threshold for only two weeks,
        short of the three a sustained surge requires. Lowering the threshold
        to make this demonstration richer would be fitting a business
        judgement to a fixture — the parameters stay defensible and the
        scenario is what needs extending (scheduled M2.0 work).
        """
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Business")

        async with tenant_scoped_session(
            session_factory,
            workspace_id=workspace_id,  # type: ignore[arg-type]
            user_id=user_id,  # type: ignore[arg-type]
        ) as session:
            rows = (
                await session.execute(
                    select(BusinessEventModel.type_key, BusinessEventModel.summary)
                )
            ).all()

        detected = {row.type_key for row in rows}
        assert BusinessEventType.TECHNOLOGY_ADOPTED.value in detected
        assert BusinessEventType.TECHNOLOGY_RETIRED.value in detected
        assert BusinessEventType.FUNDING_ROUND_CLOSED.value in detected
        assert BusinessEventType.BUYING_INTENT_SURGE.value not in detected
        assert all(row.summary for row in rows)

    async def test_every_summary_is_written_for_a_customer(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """*If a CRO opened Signora today, would they immediately understand
        what this event means?*"""
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Business")

        async with tenant_scoped_session(
            session_factory,
            workspace_id=workspace_id,  # type: ignore[arg-type]
            user_id=user_id,  # type: ignore[arg-type]
        ) as session:
            summaries = (await session.execute(select(BusinessEventModel.summary))).scalars().all()

        forbidden = ("apollo", "builtwith", "crunchbase", "coresignal", "bombora", "claim")
        leaked = [s for s in summaries if any(word in s.lower() for word in forbidden)]

        assert leaked == [], f"{leaked} names how Signora found out rather than what happened"

    async def test_every_event_records_the_taxonomy_in_force(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Business")

        async with tenant_scoped_session(
            session_factory,
            workspace_id=workspace_id,  # type: ignore[arg-type]
            user_id=user_id,  # type: ignore[arg-type]
        ) as session:
            versions = (
                (await session.execute(select(BusinessEventModel.taxonomy_version))).scalars().all()
            )

        assert set(versions) == {load_taxonomy().version}


class TestRestraint:
    async def test_re_running_the_pipeline_detects_nothing_new(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Identity is derived from the evidence, so the whole detection pass
        is idempotent without any handler-level guard."""
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Business")

        async with tenant_scoped_session(
            session_factory,
            workspace_id=workspace_id,  # type: ignore[arg-type]
            user_id=user_id,  # type: ignore[arg-type]
        ) as session:
            before = (
                await session.execute(text("SELECT count(*) FROM business_event"))
            ).scalar_one()

        await detect_all(
            session_factory,
            admin_session_factory,
            workspace_id,  # type: ignore[arg-type]
            user_id,  # type: ignore[arg-type]
        )

        async with tenant_scoped_session(
            session_factory,
            workspace_id=workspace_id,  # type: ignore[arg-type]
            user_id=user_id,  # type: ignore[arg-type]
        ) as session:
            after = (
                await session.execute(text("SELECT count(*) FROM business_event"))
            ).scalar_one()

        assert after == before


class TestProvenance:
    async def test_every_event_cites_observations_that_exist(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """AC-37. An event that cannot be traced back is an assertion, not
        intelligence."""
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Business")

        async with tenant_scoped_session(
            session_factory,
            workspace_id=workspace_id,  # type: ignore[arg-type]
            user_id=user_id,  # type: ignore[arg-type]
        ) as session:
            orphans = (
                await session.execute(
                    text(
                        "SELECT count(*) FROM business_event b "
                        "WHERE NOT EXISTS (SELECT 1 FROM observation o "
                        "WHERE o.id = ANY(b.evidence_observation_ids))"
                    )
                )
            ).scalar_one()

        assert orphans == 0

    async def test_an_event_traverses_to_the_observations_behind_it(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """One call, through the module's own read port — the traversal an
        evidence export and an AI citation both need."""
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Business")

        async with tenant_scoped_session(
            session_factory,
            workspace_id=workspace_id,  # type: ignore[arg-type]
            user_id=user_id,  # type: ignore[arg-type]
        ) as session:
            entity_id = await _acme(session, workspace_id)  # type: ignore[arg-type]
            queries = business_events(session, workspace_id)  # type: ignore[arg-type]
            events = await queries.business_events(workspace_id, entity_id)  # type: ignore[arg-type]
            assert events, "the demonstration needs at least one business event"

            evidence = await queries.business_event_evidence(
                workspace_id,  # type: ignore[arg-type]
                events[0].id,
            )

        assert evidence is not None
        assert evidence.observations
        assert all(o.provider for o in evidence.observations)

    async def test_the_taxonomy_is_readable_through_the_public_surface(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The product, analytics, and documentation should all read the same
        definitions rather than re-describing them."""
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Business")

        async with tenant_scoped_session(
            session_factory,
            workspace_id=workspace_id,  # type: ignore[arg-type]
            user_id=user_id,  # type: ignore[arg-type]
        ) as session:
            taxonomy = business_events(session, workspace_id).taxonomy()  # type: ignore[arg-type]

        assert len(taxonomy.types) == len(BusinessEventType)
        assert all(definition.why_it_matters for definition in taxonomy.types)


class TestReplay:
    async def test_business_events_rebuild_identically_from_observations(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """AC-38. The rollback for a bad rule — and the mechanism that makes
        a taxonomy change evaluable before it ships."""
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Business")

        async def snapshot() -> set[tuple[str, ...]]:
            async with tenant_scoped_session(
                session_factory,
                workspace_id=workspace_id,  # type: ignore[arg-type]
                user_id=user_id,  # type: ignore[arg-type]
            ) as session:
                rows = (
                    await session.execute(
                        select(
                            BusinessEventModel.id,
                            BusinessEventModel.type_key,
                            BusinessEventModel.summary,
                            BusinessEventModel.occurred_at,
                        ).where(BusinessEventModel.supersedes.is_(None))
                    )
                ).all()
            return {tuple(str(field) for field in row) for row in rows}

        before = await snapshot()

        async with tenant_scoped_session(
            session_factory,
            workspace_id=workspace_id,  # type: ignore[arg-type]
            user_id=user_id,  # type: ignore[arg-type]
        ) as session:
            await session.execute(text("DELETE FROM business_event"))

        await detect_all(
            session_factory,
            admin_session_factory,
            workspace_id,  # type: ignore[arg-type]
            user_id,  # type: ignore[arg-type]
        )

        assert await snapshot() == before
        assert before, "the comparison is meaningless against an empty table"


class TestTenantIsolation:
    async def test_one_workspace_never_sees_another_s_business_events(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        first, _ = await _pipeline(session_factory, admin_session_factory, "Tenant A")
        second, second_user = await _workspace(session_factory, "Tenant B")

        async with tenant_scoped_session(
            session_factory, workspace_id=second, user_id=second_user
        ) as session:
            visible = (
                await session.execute(
                    select(BusinessEventModel.id).where(BusinessEventModel.workspace_id == first)
                )
            ).scalars()

        assert list(visible) == []
