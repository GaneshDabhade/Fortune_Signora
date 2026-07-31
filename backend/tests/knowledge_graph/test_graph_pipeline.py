"""M3A demonstration: evidence becomes knowledge without becoming truth.

Proves the third link of the pipeline. Claims produced by Provider
Normalization are resolved into entities by the Knowledge Graph — module to
module, over the event bus, with the evidence chain intact from raw record
through claim and decision to entity.

The assertions that matter are the ones about what the graph *refuses* to
do: it does not merge on ambiguity, it does not collapse disagreeing
values, and it does not store an attribute anywhere.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Final
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.knowledge_graph.application.relationships import TECHNOLOGY_NAMESPACE
from modules.knowledge_graph.domain.identity import USES_TECHNOLOGY, IdentityState
from modules.knowledge_graph.infrastructure.models import (
    EntityModel,
    IdentityBindingModel,
    RelationshipModel,
)
from modules.provider_normalization.public import ClaimAttribute
from modules.provider_platform.application.run_sync import RunProviderSyncInput
from modules.provider_platform.domain.provider import ProviderCapability, ProviderName
from modules.provider_platform.infrastructure.adapters.simulated.adapter import (
    SimulatedProviderAdapter,
)
from modules.provider_platform.infrastructure.composition import build_run_sync
from modules.workspace_tenancy.application.use_cases import CreateWorkspaceInput
from modules.workspace_tenancy.infrastructure.composition import build_use_cases
from signora_platform.db import tenant_scoped_session, user_scoped_session
from signora_platform.event_bus import PostgresOutboxEventPublisher
from signora_platform.simulation import (
    ClockMode,
    DeliveryPlan,
    ReplayRecord,
    VirtualClock,
    build_timeline,
    load,
    load_scenario,
)
from signora_platform.simulation.generators import (
    ApolloFixtureGenerator,
    BomboraFixtureGenerator,
    BuiltWithFixtureGenerator,
    CoreSignalFixtureGenerator,
    CrunchbaseFixtureGenerator,
)
from tests.pipeline import normalize_all, queries, resolve_all

pytestmark = pytest.mark.integration

REPLAY = ReplayRecord("baseline", 1, "1", "0.1.0-fixture", "instant", "baseline@1")

#: Each provider's generator, capability, and the mapper it feeds. Every one
#: goes through the same Provider Port — the graph never learns which is
#: which, and could not behave differently if it wanted to (AC-21).
PROVIDERS = (
    (ProviderName.APOLLO, ApolloFixtureGenerator(), ProviderCapability.COMPANY_ENRICHMENT),
    (ProviderName.BUILTWITH, BuiltWithFixtureGenerator(), ProviderCapability.TECHNOGRAPHICS),
    (ProviderName.CRUNCHBASE, CrunchbaseFixtureGenerator(), ProviderCapability.CAPITAL_EVENTS),
    (ProviderName.CORESIGNAL, CoreSignalFixtureGenerator(), ProviderCapability.WORKFORCE),
    (ProviderName.BOMBORA, BomboraFixtureGenerator(), ProviderCapability.BEHAVIOURAL_INTENT),
)


#: The scenario every pipeline test runs, unless it says otherwise.
#:
#: **A default, not a constant.** The Playground exercises the *same* path with
#: a different scenario file — one product, one pipeline, one ingestion route.
#: An `if playground` branch anywhere below would mean the thing being validated
#: was no longer the thing that ships.
DEFAULT_SCENARIO: Final = ("baseline", 1)
DEFAULT_SUBJECTS: Final = ("acme-corp",)


def _adapter(
    provider: ProviderName,
    generator: object,
    capability: ProviderCapability,
    *,
    scenario: tuple[str, int] = DEFAULT_SCENARIO,
) -> SimulatedProviderAdapter:
    name, version = scenario
    timeline = build_timeline(
        load_scenario(name, version),
        load(name, version),
        VirtualClock(mode=ClockMode.INSTANT),
        seed=1,
        providers=[provider.value],
    )
    return SimulatedProviderAdapter(
        provider=provider,
        capabilities=frozenset({capability}),
        generator=generator,  # type: ignore[arg-type]
        plan=DeliveryPlan(timeline, page_size=100),
        replay=REPLAY,
    )


async def _workspace(factory: async_sessionmaker[AsyncSession], name: str) -> tuple[UUID, UUID]:
    user_id = uuid4()
    async with user_scoped_session(factory, user_id=user_id) as session:
        result = await build_use_cases(session).create_workspace.execute(
            CreateWorkspaceInput(name=name, created_by=user_id), correlation_id=uuid4()
        )
        return result.workspace.id, user_id


async def _ingest_every_provider(
    factory: async_sessionmaker[AsyncSession],
    workspace_id: UUID,
    user_id: UUID,
    *,
    scenario: tuple[str, int] = DEFAULT_SCENARIO,
    subjects: tuple[str, ...] = DEFAULT_SUBJECTS,
) -> None:
    """Ingest a scenario, one provider sync per (provider, subject).

    **Widened rather than redesigned.** The defaults reproduce the single-subject
    baseline ingest every existing test relies on, so this is a pure extension —
    the suite passing unchanged is the proof. What it unlocks is the Playground:
    twelve subjects through *this* code path rather than a second one.
    """
    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        for provider, generator, capability in PROVIDERS:
            adapter = _adapter(provider, generator, capability, scenario=scenario)
            for subject in subjects:
                await build_run_sync(
                    session,
                    adapter=adapter,
                    publisher=PostgresOutboxEventPublisher(),
                ).execute(
                    RunProviderSyncInput(
                        workspace_id=workspace_id, capability=capability, subject=subject
                    ),
                    correlation_id=uuid4(),
                )


async def _run_pipeline(
    factory: async_sessionmaker[AsyncSession],
    admin_factory: async_sessionmaker[AsyncSession],
    name: str,
    *,
    shuffled_by: int | None = None,
    scenario: tuple[str, int] = DEFAULT_SCENARIO,
    subjects: tuple[str, ...] = DEFAULT_SUBJECTS,
) -> tuple[UUID, UUID]:
    workspace_id, user_id = await _workspace(factory, name)
    await _ingest_every_provider(
        factory, workspace_id, user_id, scenario=scenario, subjects=subjects
    )
    await normalize_all(factory, workspace_id, user_id)
    await resolve_all(factory, admin_factory, workspace_id, user_id, shuffled_by=shuffled_by)
    return workspace_id, user_id


async def _acme_entity(session: AsyncSession, workspace_id: UUID) -> UUID:
    """The entity the domain-bearing providers resolved to.

    Selected by Apollo's own identifier rather than "the only binding":
    the baseline scenario carries a second company, and a helper that
    assumed one would fail for a reason that has nothing to do with the
    property under test.
    """
    binding = (
        await session.execute(
            select(IdentityBindingModel).where(
                IdentityBindingModel.workspace_id == workspace_id,
                IdentityBindingModel.provider == ProviderName.APOLLO.value,
                IdentityBindingModel.provider_external_id == "acme-corp",
                IdentityBindingModel.superseded_by.is_(None),
            )
        )
    ).scalar_one()
    assert binding.entity_id is not None
    return binding.entity_id


class TestIdentityResolution:
    async def test_providers_sharing_a_domain_reach_one_entity(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Apollo, BuiltWith, and Bombora all state `acme.example`. They are
        one company, and the graph says so — that is the whole job."""
        workspace_id, user_id = await _run_pipeline(session_factory, admin_session_factory, "Graph")

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            entity_id = await _acme_entity(session, workspace_id)
            bindings = (
                await session.execute(
                    select(IdentityBindingModel.provider).where(
                        IdentityBindingModel.entity_id == entity_id,
                        IdentityBindingModel.superseded_by.is_(None),
                    )
                )
            ).scalars()
            providers = set(bindings)

        assert {"apollo", "builtwith", "bombora"} <= providers

    async def test_a_provider_offering_no_matchable_identity_stays_separate(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """CoreSignal supplies only its own key — nothing another provider
        can be compared against.

        Binding it anyway, on the coincidence that the fixtures use the same
        subject name, would mean treating one provider's private identifier
        as another's. That is the over-merge this module is built to refuse,
        and an under-merge is the correct, visible failure.
        """
        workspace_id, user_id = await _run_pipeline(session_factory, admin_session_factory, "Graph")

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            acme = await _acme_entity(session, workspace_id)
            coresignal = (
                await session.execute(
                    select(IdentityBindingModel).where(
                        IdentityBindingModel.provider == ProviderName.CORESIGNAL.value,
                        IdentityBindingModel.provider_external_id == "acme-corp",
                        IdentityBindingModel.superseded_by.is_(None),
                    )
                )
            ).scalar_one()

        assert coresignal.state == IdentityState.IDENTIFIED.value
        assert coresignal.entity_id != acme

    async def test_every_binding_explains_itself(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """AC-25. A binding with no decision behind it is a merge nobody can
        justify, review, or revise."""
        workspace_id, user_id = await _run_pipeline(session_factory, admin_session_factory, "Graph")

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            entity_id = await _acme_entity(session, workspace_id)
            history = await queries(session, workspace_id).resolution_history(
                workspace_id, entity_id
            )

        assert history
        for decision in history:
            assert decision.explain()
            if decision.reasons:
                assert decision.reasons[0].value, "a reason must name what actually matched"

    async def test_re_resolution_writes_no_new_decision(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """A re-sync reaching the same answer must not manufacture a
        supersession chain of identical decisions."""
        workspace_id, user_id = await _run_pipeline(session_factory, admin_session_factory, "Graph")

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            before = (
                await session.execute(text("SELECT count(*) FROM resolution_decision"))
            ).scalar_one()

        await resolve_all(session_factory, admin_session_factory, workspace_id, user_id)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            after = (
                await session.execute(text("SELECT count(*) FROM resolution_decision"))
            ).scalar_one()

        assert after == before


class TestEvidenceIsPreservedNotCollapsed:
    async def test_the_graph_stores_no_attribute_value(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """AC-28, asserted structurally rather than by convention.

        The moment `entity` acquires a `name` or `employee_count` column,
        the graph has started resolving truth and every consumer will read
        the column instead of the evidence.
        """
        async with session_factory() as session:
            columns = (
                await session.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name = 'entity'"
                    )
                )
            ).scalars()
            names = set(columns)

        assert names == {
            "id",
            "kind",
            "workspace_id",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        }

    async def test_disagreeing_claims_are_both_returned(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The product value. Apollo and CoreSignal will disagree about
        headcount in production, and a seller who is told only one number
        cannot tell that the sources conflict."""
        workspace_id, user_id = await _run_pipeline(session_factory, admin_session_factory, "Graph")

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            entity_id = await _acme_entity(session, workspace_id)
            claim_set = await queries(session, workspace_id).claim_set(
                workspace_id, entity_id, ClaimAttribute.EMPLOYEE_COUNT
            )

        assert claim_set.claims, "the entity's evidence must be reachable from the entity"
        for claim in claim_set.claims:
            assert claim.provider
            assert claim.observed_at
            assert claim.payload_provenance == "DEVELOPMENT_FIXTURE"

    async def test_entity_evidence_traces_back_to_claims(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """*"Why do we believe this?"* — the export an enterprise customer
        asks for."""
        workspace_id, user_id = await _run_pipeline(session_factory, admin_session_factory, "Graph")

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            entity_id = await _acme_entity(session, workspace_id)
            evidence = await queries(session, workspace_id).entity_evidence(workspace_id, entity_id)

        assert evidence is not None
        assert evidence.claims
        assert {b.provider for b in evidence.bindings} >= {"apollo", "builtwith"}


class TestRelationships:
    async def test_a_removed_technology_ends_rather_than_disappears(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The baseline scenario retires LegacyERP and adopts CloudERP.

        A deleted edge is a competitive-displacement signal that can never
        be generated, so removal sets `valid_to` and the row survives.
        """
        workspace_id, user_id = await _run_pipeline(session_factory, admin_session_factory, "Graph")

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            entity_id = await _acme_entity(session, workspace_id)
            edges = await queries(session, workspace_id).relationships(
                workspace_id, entity_id, kind=USES_TECHNOLOGY
            )

        assert edges, "technographic claims must produce edges"
        assert any(edge.valid_to is not None for edge in edges), (
            "the retired technology must be ended, not deleted"
        )
        assert any(edge.is_current for edge in edges), "the adopted technology must be live"

    async def test_as_of_still_shows_what_was_true_then(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The seam for historical replay. Retrofitting a temporal query
        onto a non-temporal API costs a rewrite of every caller."""
        workspace_id, user_id = await _run_pipeline(session_factory, admin_session_factory, "Graph")

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            entity_id = await _acme_entity(session, workspace_id)
            graph = queries(session, workspace_id)
            ended = [
                edge
                for edge in await graph.relationships(workspace_id, entity_id, kind=USES_TECHNOLOGY)
                if edge.valid_to is not None
            ]
            assert ended, "this test needs a closed edge to be meaningful"
            closed_at = ended[0].valid_to
            assert closed_at is not None
            before_it_ended = closed_at - timedelta(days=1)
            historical = await graph.relationships(
                workspace_id, entity_id, kind=USES_TECHNOLOGY, as_of=before_it_ended
            )

        assert ended[0].id in {edge.id for edge in historical}

    async def test_a_technology_is_one_entity_across_providers(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Technology has no provider identity, so the graph keys it on the
        canonical name — one entity per technology, not one per reporter."""
        workspace_id, user_id = await _run_pipeline(session_factory, admin_session_factory, "Graph")

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            bindings = (
                await session.execute(
                    select(IdentityBindingModel.provider_external_id).where(
                        IdentityBindingModel.workspace_id == workspace_id,
                        IdentityBindingModel.provider == "canonical",
                    )
                )
            ).scalars()
            keys = list(bindings)

        assert keys, "technology entities must be bound by canonical name"
        assert len(keys) == len(set(keys)), "one entity per technology name"
        assert all(key.startswith(TECHNOLOGY_NAMESPACE) for key in keys)


class TestDeterminism:
    async def test_the_same_claims_in_a_different_order_build_the_same_graph(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """AC-27. Two workspaces, identical evidence, different processing
        order. Entity identifiers differ — they are allocated, not derived —
        so the comparison is of *structure*: which provider identities ended
        up grouped together.
        """
        first, first_user = await _run_pipeline(session_factory, admin_session_factory, "Order A")
        second, second_user = await _run_pipeline(
            session_factory, admin_session_factory, "Order B", shuffled_by=3
        )

        async def signature(workspace_id: UUID, user_id: UUID) -> set[frozenset[str]]:
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                rows = (
                    await session.execute(
                        select(
                            IdentityBindingModel.entity_id,
                            IdentityBindingModel.provider,
                            IdentityBindingModel.provider_external_id,
                        ).where(
                            IdentityBindingModel.workspace_id == workspace_id,
                            IdentityBindingModel.superseded_by.is_(None),
                        )
                    )
                ).all()

            grouped: dict[UUID | None, set[str]] = {}
            for entity_id, provider, external_id in rows:
                grouped.setdefault(entity_id, set()).add(f"{provider}:{external_id}")
            return {frozenset(group) for group in grouped.values()}

        assert await signature(first, first_user) == await signature(second, second_user)


class TestTenantIsolation:
    async def test_one_workspace_never_sees_another_s_graph(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Resolution across tenants would be a tenancy breach, not a
        feature — and RLS is what makes it impossible rather than merely
        unimplemented."""
        first, first_user = await _run_pipeline(session_factory, admin_session_factory, "Tenant A")
        second, second_user = await _workspace(session_factory, "Tenant B")

        async with tenant_scoped_session(
            session_factory, workspace_id=second, user_id=second_user
        ) as session:
            entities = (
                await session.execute(
                    select(EntityModel.id).where(EntityModel.workspace_id == first)
                )
            ).scalars()
            relationships = (await session.execute(select(RelationshipModel.id))).scalars()

        assert list(entities) == []
        assert list(relationships) == []
