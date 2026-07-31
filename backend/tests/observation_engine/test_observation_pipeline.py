"""M3B demonstration: the pipeline notices what moved, and never invents it.

Proves the fourth link. Claims attached to a resolved entity by the
Knowledge Graph become observations — module to module, over the event bus,
with the evidence chain intact from raw record through claim, decision, and
entity to observation.

The assertion that matters most is the negative one: running the same sync
twice produces **zero** observations. A change-detection engine that fires
on a no-op sync is worse than no change detection, because every downstream
stage would then be reacting to noise it cannot distinguish from signal.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.knowledge_graph.infrastructure.models import IdentityBindingModel
from modules.observation_engine.domain.observation import ObservationDirection, ObservationKind
from modules.observation_engine.infrastructure.models import ObservationModel
from modules.provider_normalization.public import ClaimAttribute
from modules.provider_platform.domain.provider import ProviderName
from signora_platform.db import tenant_scoped_session
from tests.knowledge_graph.test_graph_pipeline import (
    _ingest_every_provider,
    _run_pipeline,
    _workspace,
)
from tests.pipeline import normalize_all, observations, observe_all, resolve_all

pytestmark = pytest.mark.integration


async def _observe_pipeline(
    factory: async_sessionmaker[AsyncSession],
    admin_factory: async_sessionmaker[AsyncSession],
    name: str,
) -> tuple[UUID, UUID]:
    workspace_id, user_id = await _run_pipeline(factory, admin_factory, name)
    await observe_all(factory, admin_factory, workspace_id, user_id)
    return workspace_id, user_id


async def _acme(
    session: AsyncSession, workspace_id: UUID, *, subject: str = "acme-corp"
) -> UUID:
    """The entity one provider identity resolved to.

    Selected by Apollo's own identifier rather than "the only binding": a
    scenario carries several companies, and a helper assuming one would fail
    for a reason unrelated to the property under test.

    `subject` defaults to the baseline's account so every existing caller is
    unchanged; the Playground names its own anchor.
    """
    binding = (
        await session.execute(
            select(IdentityBindingModel).where(
                IdentityBindingModel.workspace_id == workspace_id,
                IdentityBindingModel.provider == ProviderName.APOLLO.value,
                IdentityBindingModel.provider_external_id == subject,
                IdentityBindingModel.superseded_by.is_(None),
            )
        )
    ).scalar_one()
    assert binding.entity_id is not None
    return binding.entity_id


class TestRestraint:
    """What the pipeline refuses to call a change. The most important
    assertions in the milestone."""

    async def test_a_first_sync_observes_nothing(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Every attribute is being seen for the first time. Nothing moved —
        Signora merely started knowing. Emitting here would mean an
        onboarding sync flooding every consumer on day one."""
        workspace_id, user_id = await _observe_pipeline(
            session_factory, admin_session_factory, "Observe"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            transitions = (
                await session.execute(
                    text("SELECT count(*) FROM observation WHERE kind = :kind"),
                    {"kind": ObservationKind.VALUE_CHANGED.value},
                )
            ).scalar_one()

        assert transitions == 0, (
            "a first observation of an attribute is knowledge established, not change"
        )

    async def test_re_running_the_same_sync_observes_nothing_new(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The assertion the whole module exists to satisfy. In a polling
        pipeline this is the dominant case by an enormous margin."""
        workspace_id, user_id = await _observe_pipeline(
            session_factory, admin_session_factory, "Observe"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            before = (await session.execute(text("SELECT count(*) FROM observation"))).scalar_one()

        await _ingest_every_provider(session_factory, workspace_id, user_id)
        await normalize_all(session_factory, workspace_id, user_id)
        await resolve_all(session_factory, admin_session_factory, workspace_id, user_id)
        await observe_all(session_factory, admin_session_factory, workspace_id, user_id)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            after = (await session.execute(text("SELECT count(*) FROM observation"))).scalar_one()

        assert after == before, "a sync that re-asserts what is known must observe nothing"


class TestOccurrencesAreObserved:
    async def test_the_scenario_s_occurrences_are_recorded_once_each(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Technology, funding, intent weeks — things that *happened*, as
        distinct from values that are currently true."""
        workspace_id, user_id = await _observe_pipeline(
            session_factory, admin_session_factory, "Observe"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            rows = (
                await session.execute(
                    select(ObservationModel.attribute, ObservationModel.direction).where(
                        ObservationModel.kind == ObservationKind.OCCURRENCE_OBSERVED.value
                    )
                )
            ).all()

        assert rows, "the baseline scenario contains occurrences to observe"
        assert {row.direction for row in rows} == {ObservationDirection.OCCURRED.value}
        assert ClaimAttribute.TECHNOLOGY_DETECTED.value in {row.attribute for row in rows}

    async def test_every_intent_week_is_its_own_observation(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The trajectory is product value, and it survives as a series."""
        workspace_id, user_id = await _observe_pipeline(
            session_factory, admin_session_factory, "Observe"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            weeks = (
                await session.execute(
                    select(ObservationModel.id).where(
                        ObservationModel.attribute == ClaimAttribute.INTENT_TOPIC_SURGE.value
                    )
                )
            ).scalars()
            count = len(list(weeks))

        assert count > 1, "one claim per observed week must yield one observation per week"


class TestProvenance:
    async def test_every_observation_cites_evidence(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """AC-32. An observation nobody can trace looks like knowledge
        without being it."""
        workspace_id, user_id = await _observe_pipeline(
            session_factory, admin_session_factory, "Observe"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            orphans = (
                await session.execute(
                    text(
                        "SELECT count(*) FROM observation o "
                        "WHERE NOT EXISTS (SELECT 1 FROM claim c "
                        "WHERE c.id = ANY(o.evidence_claim_ids))"
                    )
                )
            ).scalar_one()

        assert orphans == 0

    async def test_an_observation_traverses_to_its_claims(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """*"Why do we believe this?"* — one call, through the module's own
        read port."""
        workspace_id, user_id = await _observe_pipeline(
            session_factory, admin_session_factory, "Observe"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            entity_id = await _acme(session, workspace_id)
            queries = observations(session, workspace_id)
            recorded = await queries.observations(workspace_id, entity_id)
            assert recorded, "the demonstration needs at least one observation"

            evidence = await queries.observation_evidence(workspace_id, recorded[0].id)

        assert evidence is not None
        assert evidence.claims
        assert all(claim.payload_provenance == "DEVELOPMENT_FIXTURE" for claim in evidence.claims)

    async def test_every_observation_belongs_to_a_resolved_entity(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The engine reasons over evidence already attached to an identity,
        so it can never observe something it cannot attribute."""
        workspace_id, user_id = await _observe_pipeline(
            session_factory, admin_session_factory, "Observe"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            unattributed = (
                await session.execute(
                    text(
                        "SELECT count(*) FROM observation o "
                        "WHERE NOT EXISTS (SELECT 1 FROM entity e WHERE e.id = o.entity_id)"
                    )
                )
            ).scalar_one()

        assert unattributed == 0


class TestReplay:
    async def test_observations_rebuild_identically_from_claims(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """AC-33. The rollback for a bad derivation rule, and the reason
        claims are stored rather than streamed.

        Superseded rows legitimately do not reappear — they record what was
        briefly believed, not what is true — so the comparison is of the
        current set.
        """
        workspace_id, user_id = await _observe_pipeline(
            session_factory, admin_session_factory, "Observe"
        )

        async def snapshot() -> set[tuple[str, ...]]:
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                rows = (
                    await session.execute(
                        select(
                            ObservationModel.id,
                            ObservationModel.provider,
                            ObservationModel.attribute,
                            ObservationModel.kind,
                            ObservationModel.observed_at,
                        ).where(ObservationModel.supersedes.is_(None))
                    )
                ).all()
            return {tuple(str(field) for field in row) for row in rows}

        before = await snapshot()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            await session.execute(text("DELETE FROM observation"))

        await observe_all(session_factory, admin_session_factory, workspace_id, user_id)

        assert await snapshot() == before
        assert before, "the comparison is meaningless against an empty table"


class TestTenantIsolation:
    async def test_one_workspace_never_sees_another_s_observations(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        first, _ = await _observe_pipeline(session_factory, admin_session_factory, "Tenant A")
        second, second_user = await _workspace(session_factory, "Tenant B")

        async with tenant_scoped_session(
            session_factory, workspace_id=second, user_id=second_user
        ) as session:
            visible = (
                await session.execute(
                    select(ObservationModel.id).where(ObservationModel.workspace_id == first)
                )
            ).scalars()

        assert list(visible) == []


class TestChangeIsDetectedWhenItHappens:
    """The positive case, driven directly rather than through the simulator.

    The baseline scenario reports each subject once per provider, so it
    contains no *movement* — proving the engine detects change needs a
    second, different assertion, which is constructed here explicitly.
    """

    async def test_a_second_differing_claim_produces_a_transition(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id = await _observe_pipeline(
            session_factory, admin_session_factory, "Observe"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            entity_id = await _acme(session, workspace_id)
            existing = (
                (
                    await session.execute(
                        text(
                            # Pinned to Acme's own subject. The baseline
                            # scenario carries a second company, so an
                            # unpinned LIMIT 1 attaches the new claim to
                            # Globex about half the time and fails for a
                            # reason unrelated to the property under test.
                            "SELECT raw_record_id, provider, subject_external_id, mapper_version, "
                            "payload_provenance, value, observed_at FROM claim "
                            "WHERE attribute = :attribute AND provider = 'apollo' "
                            "AND subject_external_id = :subject LIMIT 1"
                        ),
                        {
                            "attribute": ClaimAttribute.EMPLOYEE_COUNT.value,
                            "subject": "acme-corp",
                        },
                    )
                )
                .mappings()
                .one()
            )

            # A later assertion of a different value by the same provider —
            # the shape a real re-sync takes once a company has actually
            # grown.
            later_claim_id = uuid4()
            await session.execute(
                text(
                    "INSERT INTO claim (id, workspace_id, raw_record_id, provider, attribute, "
                    "claim_domain, value, observed_at, subject_external_id, mapper_version, "
                    "payload_provenance, created_by, updated_by) VALUES "
                    "(:id, :workspace_id, :raw_record_id, :provider, :attribute, 'firmographic', "
                    ":value, :observed_at, :subject, :mapper_version, :provenance, :actor, :actor)"
                ),
                {
                    "id": later_claim_id,
                    "workspace_id": workspace_id,
                    "raw_record_id": existing["raw_record_id"],
                    "provider": "apollo",
                    "attribute": ClaimAttribute.EMPLOYEE_COUNT.value,
                    "value": '{"v": 240}',
                    "observed_at": datetime(2026, 6, 1, tzinfo=UTC),
                    "subject": existing["subject_external_id"],
                    "mapper_version": existing["mapper_version"],
                    "provenance": existing["payload_provenance"],
                    "actor": UUID("00000000-0000-0000-0000-000000000001"),
                },
            )

        await observe_all(session_factory, admin_session_factory, workspace_id, user_id)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            transitions = (
                (
                    await session.execute(
                        select(ObservationModel).where(
                            ObservationModel.kind == ObservationKind.VALUE_CHANGED.value,
                            ObservationModel.entity_id == entity_id,
                        )
                    )
                )
                .scalars()
                .all()
            )

        assert len(transitions) == 1
        observation = transitions[0]
        assert observation.provider == "apollo"
        assert observation.direction == ObservationDirection.INCREASED.value
        assert observation.previous_observed_at is not None
        assert observation.previous_observed_at < observation.observed_at
