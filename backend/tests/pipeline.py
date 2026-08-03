"""The process composition root the pipeline demonstrations run through.

This is where concrete adapters are wired to ports — the one place allowed
to know that Provider Normalization's claim reader is backed by SQL, or
that the Knowledge Graph's resolver needs one. Modules never wire each
other; that is what keeps the boundary in
docs/architecture/05-module-dependencies.md real rather than aspirational.

Each stage is driven by the **events actually published to the outbox**,
read back the way the relay reads them. Calling handlers with hand-built
envelopes would prove the handlers work while proving nothing about the
contract between the modules.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.business_event_engine.application.queries import BusinessEventQueries
from modules.business_event_engine.infrastructure.composition import (
    build_detect_business_events,
)
from modules.business_event_engine.infrastructure.composition import (
    build_queries as build_business_event_queries,
)
from modules.business_event_engine.interface.handlers import detect_from_observation
from modules.buying_score_engine.application.queries import BuyingScoreQueries
from modules.buying_score_engine.application.sweep import SweepStaleScores
from modules.buying_score_engine.infrastructure.composition import (
    build_compute_buying_score,
)
from modules.buying_score_engine.infrastructure.composition import (
    build_queries as build_buying_score_queries,
)
from modules.buying_score_engine.infrastructure.repository import SqlBuyingScoreRepository
from modules.buying_score_engine.interface.handlers import compute_from_signal
from modules.knowledge_graph.application.queries import GraphQueries
from modules.knowledge_graph.infrastructure.composition import (
    build_derive_relationships,
    build_queries,
    build_resolve_entity,
)
from modules.knowledge_graph.interface.handlers import resolve_recorded_claims
from modules.observation_engine.application.queries import ObservationQueries
from modules.observation_engine.infrastructure.composition import (
    build_queries as build_observation_queries,
)
from modules.observation_engine.infrastructure.composition import build_record_observations
from modules.observation_engine.interface.handlers import observe_attached_evidence
from modules.opportunity_engine.application.queries import OpportunityQueries
from modules.opportunity_engine.domain.policy import (
    OpportunityPolicy,
    WorkspaceOpportunityPolicy,
)
from modules.opportunity_engine.infrastructure.composition import (
    build_policies as build_opportunity_policies,
)
from modules.opportunity_engine.infrastructure.composition import (
    build_qualify_opportunity,
)
from modules.opportunity_engine.infrastructure.composition import (
    build_queries as build_opportunity_queries,
)
from modules.opportunity_engine.interface.handlers import qualify_from_buying_score
from modules.provider_normalization.infrastructure.claim_reader import SqlClaimReader
from modules.provider_normalization.interface.handlers import normalize_received_record
from modules.provider_platform.infrastructure.models import RawProviderRecordModel
from modules.provider_platform.infrastructure.record_reader import SqlRawRecordReader
from modules.signal_engine.application.queries import SignalQueries
from modules.signal_engine.infrastructure.composition import build_generate_signals
from modules.signal_engine.infrastructure.composition import (
    build_queries as build_signal_queries,
)
from modules.signal_engine.interface.handlers import generate_from_business_event
from modules.timeline.domain.projection import PROJECTIONS
from modules.timeline.infrastructure.composition import build_project_event
from modules.timeline.interface.handlers import project_to_timeline
from signora_platform.db import tenant_scoped_session
from signora_platform.event_bus import (
    EventEnvelope,
    OutboxEventModel,
    PostgresOutboxEventPublisher,
)


async def _published(
    admin_factory: async_sessionmaker[AsyncSession], event_type: str
) -> list[EventEnvelope]:
    """Read the outbox the way the relay does — under the relay's own
    identity, never the application's.

    `signora_app` holds no SELECT grant on `outbox_event` (migration 0006),
    and that is the Platform Infrastructure Policy working: a business
    module must never read an infrastructure table. The test therefore uses
    the privileged connection rather than quietly restoring the grant.
    """
    async with admin_factory() as session:
        rows = await session.execute(
            select(OutboxEventModel)
            .where(OutboxEventModel.event_type == event_type)
            .order_by(OutboxEventModel.created_at, OutboxEventModel.event_id)
        )
        return [
            EventEnvelope(
                event_id=row.event_id,
                event_type=row.event_type,
                event_version=row.event_version,
                workspace_id=row.workspace_id,
                occurred_at=row.occurred_at,
                producer_module=row.producer_module,
                correlation_id=row.correlation_id,
                causation_id=row.causation_id,
                payload=row.payload,
            )
            for row in rows.scalars()
        ]


async def normalize_all(
    factory: async_sessionmaker[AsyncSession], workspace_id: UUID, user_id: UUID
) -> int:
    """Translate every ingested raw record into claims."""
    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        record_ids = list(
            (
                await session.execute(
                    select(RawProviderRecordModel.id).order_by(RawProviderRecordModel.occurred_at)
                )
            ).scalars()
        )
        for record_id in record_ids:
            await normalize_received_record(
                EventEnvelope(
                    event_id=uuid4(),
                    event_type="provider.record.received",
                    event_version=1,
                    workspace_id=workspace_id,
                    occurred_at=datetime.now(UTC),
                    producer_module="provider_platform",
                    correlation_id=uuid4(),
                    causation_id=None,
                    payload={"record_id": str(record_id)},
                ),
                session=session,
                records=SqlRawRecordReader(session),
                publisher=PostgresOutboxEventPublisher(),
            )
    return len(record_ids)


async def resolve_all(
    factory: async_sessionmaker[AsyncSession],
    admin_factory: async_sessionmaker[AsyncSession],
    workspace_id: UUID,
    user_id: UUID,
    *,
    shuffled_by: int | None = None,
) -> int:
    """Resolve identity for every `claim.recorded` event on the outbox.

    `shuffled_by` rotates the processing order. Resolution must reach the
    same graph regardless, which is the whole of AC-27 — so the knob exists
    to be turned by the test rather than described in a comment.
    """
    envelopes = [
        envelope
        for envelope in await _published(admin_factory, "claim.recorded")
        if envelope.workspace_id == workspace_id
    ]

    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        if shuffled_by:
            offset = shuffled_by % len(envelopes) if envelopes else 0
            envelopes = envelopes[offset:] + envelopes[:offset]

        publisher = PostgresOutboxEventPublisher()
        claims = SqlClaimReader(session, workspace_id=workspace_id)
        for envelope in envelopes:
            await resolve_recorded_claims(
                envelope,
                resolve=build_resolve_entity(session, claims=claims, publisher=publisher),
                relationships=build_derive_relationships(session, publisher=publisher),
            )
    return len(envelopes)


def queries(session: AsyncSession, workspace_id: UUID) -> GraphQueries:
    return build_queries(session, claims=SqlClaimReader(session, workspace_id=workspace_id))


async def observe_all(
    factory: async_sessionmaker[AsyncSession],
    admin_factory: async_sessionmaker[AsyncSession],
    workspace_id: UUID,
    user_id: UUID,
) -> int:
    """Record observations for every `entity.evidence_attached` event."""
    envelopes = [
        envelope
        for envelope in await _published(admin_factory, "entity.evidence_attached")
        if envelope.workspace_id == workspace_id
    ]

    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        graph = queries(session, workspace_id)
        record = build_record_observations(
            session, graph=graph, publisher=PostgresOutboxEventPublisher()
        )
        for envelope in envelopes:
            await observe_attached_evidence(envelope, record=record)
    return len(envelopes)


def observations(session: AsyncSession, workspace_id: UUID) -> ObservationQueries:
    return build_observation_queries(session, graph=queries(session, workspace_id))


async def detect_all(
    factory: async_sessionmaker[AsyncSession],
    admin_factory: async_sessionmaker[AsyncSession],
    workspace_id: UUID,
    user_id: UUID,
) -> int:
    """Detect business events for every `observation.recorded` event."""
    envelopes = [
        envelope
        for envelope in await _published(admin_factory, "observation.recorded")
        if envelope.workspace_id == workspace_id
    ]

    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        detect = build_detect_business_events(
            session,
            observations=observations(session, workspace_id),
            publisher=PostgresOutboxEventPublisher(),
        )
        for envelope in envelopes:
            await detect_from_observation(envelope, detect=detect)
    return len(envelopes)


def business_events(session: AsyncSession, workspace_id: UUID) -> BusinessEventQueries:
    return build_business_event_queries(session, observations=observations(session, workspace_id))


async def signal_all(
    factory: async_sessionmaker[AsyncSession],
    admin_factory: async_sessionmaker[AsyncSession],
    workspace_id: UUID,
    user_id: UUID,
) -> int:
    """Form hypotheses for every `business_event.detected` event."""
    envelopes = [
        envelope
        for envelope in await _published(admin_factory, "business_event.detected")
        if envelope.workspace_id == workspace_id
    ]

    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        generate = build_generate_signals(
            session,
            business_events=business_events(session, workspace_id),
            publisher=PostgresOutboxEventPublisher(),
        )
        for envelope in envelopes:
            await generate_from_business_event(envelope, generate=generate)
    return len(envelopes)


def signals(session: AsyncSession, workspace_id: UUID) -> SignalQueries:
    return build_signal_queries(session, business_events=business_events(session, workspace_id))


async def score_all(
    factory: async_sessionmaker[AsyncSession],
    admin_factory: async_sessionmaker[AsyncSession],
    workspace_id: UUID,
    user_id: UUID,
    *,
    moment: datetime | None = None,
) -> int:
    """Read commercial attention for every signal event.

    Both `signal.generated` and `signal.superseded` are consumed: a
    strengthened hypothesis arrives as both, and a consumer handling only
    the first would keep weighing the reading that was replaced.
    """
    envelopes = [
        envelope
        for event_type in ("signal.generated", "signal.superseded")
        for envelope in await _published(admin_factory, event_type)
        if envelope.workspace_id == workspace_id
    ]

    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        compute = build_compute_buying_score(
            session,
            signals=signals(session, workspace_id),
            publisher=PostgresOutboxEventPublisher(),
            clock=None if moment is None else (lambda: moment),
        )
        for envelope in envelopes:
            await compute_from_signal(envelope, compute=compute)
    return len(envelopes)


def buying_scores(session: AsyncSession, workspace_id: UUID) -> BuyingScoreQueries:
    return build_buying_score_queries(session, signals=signals(session, workspace_id))


async def sweep_stale(
    factory: async_sessionmaker[AsyncSession],
    workspace_id: UUID,
    user_id: UUID,
    *,
    moment: datetime | None = None,
) -> tuple[int, int]:
    """Re-score whatever has passed the moment its own arithmetic changes.

    Shelf-life expiry is the one input to the Buying Score Engine that
    arrives without an event, so this is the stage that keeps scores honest
    as evidence ages rather than letting every account decay into a false
    hot state.
    """
    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        compute = build_compute_buying_score(
            session,
            signals=signals(session, workspace_id),
            publisher=PostgresOutboxEventPublisher(),
            clock=None if moment is None else (lambda: moment),
        )

        sweep = SweepStaleScores(
            repository=SqlBuyingScoreRepository(session),
            compute=compute,
            **({} if moment is None else {"clock": (lambda: moment)}),
        )
        result = await sweep.execute(workspace_id)
    return result.examined, result.rescored


async def set_opportunity_policy(
    factory: async_sessionmaker[AsyncSession],
    workspace_id: UUID,
    user_id: UUID,
    *,
    minimum_score: int,
    contested_qualifies: bool = True,
    automatic_creation: bool = True,
) -> None:
    """Author a workspace's own qualification threshold.

    The demonstration uses this rather than lowering Signora's shipped
    default, which is a product judgement and must not be tuned to make a
    scenario pass. It also exercises the layer that matters: *when do we
    start tracking* belongs to the customer.
    """
    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        await build_opportunity_policies(session).save(
            WorkspaceOpportunityPolicy(
                id=uuid4(),
                workspace_id=workspace_id,
                version=1,
                policy=OpportunityPolicy(
                    version=1,
                    minimum_score=minimum_score,
                    contested_qualifies=contested_qualifies,
                    automatic_creation=automatic_creation,
                ),
                created_at=datetime.now(UTC),
                created_by=user_id,
            )
        )


async def qualify_all(
    factory: async_sessionmaker[AsyncSession],
    admin_factory: async_sessionmaker[AsyncSession],
    workspace_id: UUID,
    user_id: UUID,
    *,
    moment: datetime | None = None,
) -> int:
    """Consider every scored account for tracking.

    **The only automatic path into workflow**, and it can do exactly one
    thing: open an opportunity at `TRACKING`, which commits nobody. There is
    deliberately no stage in this harness that closes or progresses one —
    those require a person, and the absence of the code is the enforcement.

    `moment` is **when the commitment was made**. The use case has always
    accepted a clock and this helper never forwarded one, so every opportunity
    opened at wall-clock now — which is invisible in a test and wrong in a
    demonstration, where it made twelve accounts all report they were opened
    today. Defaulted, so existing callers are unchanged.
    """
    envelopes = [
        envelope
        for envelope in await _published(admin_factory, "buying_score.updated")
        if envelope.workspace_id == workspace_id
    ]

    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        qualify = build_qualify_opportunity(
            session,
            scores=buying_scores(session, workspace_id),
            publisher=PostgresOutboxEventPublisher(),
            clock=None if moment is None else (lambda: moment),
        )
        for envelope in envelopes:
            await qualify_from_buying_score(envelope, qualify=qualify)
    return len(envelopes)


def opportunities(session: AsyncSession, workspace_id: UUID) -> OpportunityQueries:
    return build_opportunity_queries(session, scores=buying_scores(session, workspace_id))


async def project_all(
    factory: async_sessionmaker[AsyncSession],
    admin_factory: async_sessionmaker[AsyncSession],
    workspace_id: UUID,
    user_id: UUID,
) -> int:
    """Project every event Timeline has a rule for onto the account's history.

    **The ninth stage, added after the other eight had run without it for a
    milestone.** Timeline's domain, table, repository, read API and feed
    component were all built, and this file — the composition root every
    demonstration runs through — never wired the projection. So the account
    brief's *"What has happened"* was empty on all twelve Playground accounts,
    in the one environment the product is reviewed in ([B-302](../../docs/BUGS.md)).

    **Reads `PROJECTIONS` rather than naming event types**, exactly as the
    deployed worker does since [B-301](../../docs/BUGS.md): the projection table
    is the single authoritative statement of what Timeline consumes, and a list
    beside it drifts the first time a rule is added.

    **Idempotent, so running it twice is safe.** The entry id derives from
    `event_id`, and the insert is `ON CONFLICT DO NOTHING` — which is also why
    this can run last rather than being interleaved with the stages that
    produce the events.
    """
    envelopes = [
        envelope
        for event_type in PROJECTIONS
        for envelope in await _published(admin_factory, event_type)
        if envelope.workspace_id == workspace_id
    ]

    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        project = build_project_event(session)
        for envelope in envelopes:
            await project_to_timeline(envelope, project=project)
    return len(envelopes)
