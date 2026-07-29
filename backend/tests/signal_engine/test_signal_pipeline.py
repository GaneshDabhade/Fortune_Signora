"""M5A demonstration: the same company, two customers, two readings.

Proves the sixth link, and the first one that is **not globally true**.
Business events describe what happened to Acme; signals describe what that
might mean to *this* workspace — and two workspaces looking at byte-
identical evidence legitimately see different things.

The assertion that matters most is that both readings are defensible: each
explains itself in two halves, and each can be challenged independently.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.signal_engine.domain.catalog import Relevance, SignalType
from modules.signal_engine.domain.profile import ProfileEntry, SignalProfile
from modules.signal_engine.infrastructure.composition import build_profiles
from modules.signal_engine.infrastructure.models import SignalModel
from signora_platform.db import tenant_scoped_session
from tests.knowledge_graph.test_graph_pipeline import _run_pipeline, _workspace
from tests.observation_engine.test_observation_pipeline import _acme
from tests.pipeline import detect_all, observe_all, signal_all, signals

pytestmark = pytest.mark.integration


async def _pipeline(
    factory: async_sessionmaker[AsyncSession],
    admin_factory: async_sessionmaker[AsyncSession],
    name: str,
    *,
    profile_entries: tuple[ProfileEntry, ...] = (),
) -> tuple[UUID, UUID]:
    workspace_id, user_id = await _run_pipeline(factory, admin_factory, name)
    await observe_all(factory, admin_factory, workspace_id, user_id)
    await detect_all(factory, admin_factory, workspace_id, user_id)

    if profile_entries:
        async with tenant_scoped_session(
            factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            await build_profiles(session).save(
                SignalProfile(
                    id=uuid4(),
                    workspace_id=workspace_id,
                    version=1,
                    entries=profile_entries,
                    created_at=datetime.now(UTC),
                    created_by=user_id,
                )
            )

    await signal_all(factory, admin_factory, workspace_id, user_id)
    return workspace_id, user_id


async def _types(
    factory: async_sessionmaker[AsyncSession], workspace_id: UUID, user_id: UUID
) -> set[str]:
    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        rows = (await session.execute(select(SignalModel.signal_type))).scalars()
        return set(rows)


class TestInterpretationIsCustomerSpecific:
    async def test_the_same_evidence_produces_different_readings(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The defining demonstration of the milestone. Workspace B sells
        something for which a retired ERP is irrelevant; workspace A does
        not. The business events underneath are identical."""
        interested, interested_user = await _pipeline(
            session_factory, admin_session_factory, "Interested"
        )
        indifferent, indifferent_user = await _pipeline(
            session_factory,
            admin_session_factory,
            "Indifferent",
            profile_entries=(
                ProfileEntry(SignalType.DISPLACEMENT_OPPORTUNITY, Relevance.IGNORED),
                ProfileEntry(SignalType.MODERNIZATION_UNDERWAY, Relevance.IGNORED),
            ),
        )

        with_displacement = await _types(session_factory, interested, interested_user)
        without = await _types(session_factory, indifferent, indifferent_user)

        assert SignalType.DISPLACEMENT_OPPORTUNITY.value in with_displacement
        assert SignalType.DISPLACEMENT_OPPORTUNITY.value not in without
        assert SignalType.MODERNIZATION_UNDERWAY.value not in without

    async def test_business_events_are_identical_across_both_workspaces(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Everything above the Signal Engine stays globally true. Only the
        interpretation differs."""
        first, first_user = await _pipeline(session_factory, admin_session_factory, "First")
        second, second_user = await _pipeline(
            session_factory,
            admin_session_factory,
            "Second",
            profile_entries=(ProfileEntry(SignalType.DISPLACEMENT_OPPORTUNITY, Relevance.IGNORED),),
        )

        async def event_types(workspace_id: UUID, user_id: UUID) -> set[str]:
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                rows = await session.execute(text("SELECT DISTINCT type_key FROM business_event"))
                return set(rows.scalars())

        assert await event_types(first, first_user) == await event_types(second, second_user)


class TestTheScenarioProducesHypotheses:
    async def test_the_baseline_scenario_yields_recognisable_signals(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Signals")

        detected = await _types(session_factory, workspace_id, user_id)

        assert SignalType.DISPLACEMENT_OPPORTUNITY.value in detected
        assert SignalType.BUDGET_UNLOCKED.value in detected
        assert SignalType.MODERNIZATION_UNDERWAY.value in detected, (
            "adopting and retiring together is the scenario's one genuine composite"
        )

    async def test_a_composite_enriches_rather_than_replaces(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The constituent hypothesis stays independently visible, and the
        composite names it."""
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Signals")

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            entity_id = await _acme(session, workspace_id)
            # `live_only=False`: the scenario's evidence is months old and
            # these hypotheses have passed their shelf life. That is the
            # lifecycle working, and it is asserted separately — this test
            # is about composition.
            held = await signals(session, workspace_id).signals(
                workspace_id, entity_id, live_only=False
            )

        composite = next(s for s in held if s.signal_type is SignalType.MODERNIZATION_UNDERWAY)
        constituent = next(s for s in held if s.signal_type is SignalType.DISPLACEMENT_OPPORTUNITY)

        assert constituent.id in composite.constituent_signal_ids
        assert constituent in held, "a composite must never suppress what it builds on"

    async def test_re_running_the_pipeline_generates_nothing_new(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Signals")

        async def count() -> int:
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                return int(
                    (await session.execute(text("SELECT count(*) FROM signal"))).scalar_one()
                )

        before = await count()
        await signal_all(session_factory, admin_session_factory, workspace_id, user_id)

        assert await count() == before


class TestExplainability:
    async def test_a_signal_answers_all_four_questions(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Why does this hypothesis exist · which business events produced
        it · which profile interpreted it · how long it stays relevant."""
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Signals")

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            entity_id = await _acme(session, workspace_id)
            queries = signals(session, workspace_id)
            held = await queries.signals(workspace_id, entity_id, live_only=False)
            assert held, "the demonstration needs at least one hypothesis"

            explanation = await queries.explanation(workspace_id, held[0].id)

        assert explanation is not None
        assert explanation.signal.rationale
        assert explanation.business_events, "a hypothesis must cite what it rests on"
        assert all(event.summary for event in explanation.business_events)
        assert explanation.profile_entry.relevance is not Relevance.IGNORED
        assert explanation.signal.relevant_until > explanation.signal.occurred_at


class TestShelfLife:
    async def test_a_hypothesis_older_than_its_window_is_no_longer_live(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The baseline scenario's evidence is months old, and every catalog
        type declares a shelf life shorter than that. The hypotheses were
        formed and remain readable — they are simply no longer current.

        Capturing that here rather than downstream keeps temporal
        interpretation inside the module that knows the window.
        """
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Signals")

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            entity_id = await _acme(session, workspace_id)
            queries = signals(session, workspace_id)
            recorded = await queries.signals(workspace_id, entity_id, live_only=False)
            live = await queries.signals(workspace_id, entity_id)

        assert recorded, "the hypotheses were formed"
        assert live == (), "and they are past the shelf life the catalog declares"
        assert all(s.relevant_until < datetime.now(UTC) for s in recorded)

    async def test_every_signal_traces_to_business_events_that_exist(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Everything below the Signal Engine must remain traceable back to
        globally true information."""
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Signals")

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            orphans = (
                await session.execute(
                    text(
                        "SELECT count(*) FROM signal s "
                        "WHERE NOT EXISTS (SELECT 1 FROM business_event b "
                        "WHERE b.id = ANY(s.contributing_event_ids))"
                    )
                )
            ).scalar_one()

        assert orphans == 0

    async def test_no_rationale_names_a_provider(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Signals")

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            rationales = (await session.execute(select(SignalModel.rationale))).scalars().all()

        forbidden = ("apollo", "builtwith", "crunchbase", "coresignal", "bombora")
        leaked = [r for r in rationales if any(word in r.lower() for word in forbidden)]

        assert leaked == []


class TestReplay:
    async def test_signals_rebuild_identically_from_business_events(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Current replay — *"what would we say now?"* — against an unchanged
        profile reproduces the same set."""
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Signals")

        async def snapshot() -> set[tuple[str, ...]]:
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                rows = (
                    await session.execute(
                        select(
                            SignalModel.id,
                            SignalModel.signal_type,
                            SignalModel.relevance,
                            SignalModel.occurred_at,
                        ).where(SignalModel.supersedes.is_(None))
                    )
                ).all()
            return {tuple(str(field) for field in row) for row in rows}

        before = await snapshot()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            await session.execute(text("DELETE FROM signal"))

        await signal_all(session_factory, admin_session_factory, workspace_id, user_id)

        assert await snapshot() == before
        assert before, "the comparison is meaningless against an empty table"

    async def test_the_customer_s_profile_survives_a_signal_rebuild(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Signals are derived and rebuildable; the profile is
        customer-authored and cannot be regenerated from anything."""
        workspace_id, user_id = await _pipeline(
            session_factory,
            admin_session_factory,
            "Signals",
            profile_entries=(ProfileEntry(SignalType.DISPLACEMENT_OPPORTUNITY, Relevance.PRIMARY),),
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            await session.execute(text("DELETE FROM signal"))

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            stored = await signals(session, workspace_id).stored_profile(workspace_id)

        assert stored is not None
        assert stored.version == 1


class TestTenantIsolation:
    async def test_one_workspace_never_sees_another_s_hypotheses(
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
                    select(SignalModel.id).where(SignalModel.workspace_id == first)
                )
            ).scalars()
            profiles = (
                await session.execute(text("SELECT count(*) FROM signal_profile"))
            ).scalar_one()

        assert list(visible) == []
        assert profiles == 0, "a customer's configuration is as tenant-scoped as their data"
