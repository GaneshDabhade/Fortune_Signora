"""Resolve one provider identity to an entity — the graph's core use case.

**The Knowledge Graph resolves identity. The Knowledge Graph does not
resolve truth.** (Permanent invariant, ratified 2026-07-28.) This use case
decides *which company* a provider is talking about, records why in a
decision that outlives it, and stops. What the company's headcount is
remains a question for whoever has the context to weigh it.

The order here matters. The entity is created before the decision is
persisted, so a decision never references an entity that does not exist;
and the binding is written last, so its unique constraint is what settles a
race between two workers resolving the same identity at once.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from modules.knowledge_graph.application.ports import GraphRepository
from modules.knowledge_graph.domain.events import (
    EntityCreated,
    EntityIdentityBound,
    EntityResolutionAmbiguous,
)
from modules.knowledge_graph.domain.identity import (
    Entity,
    EntityKind,
    IdentityBinding,
    IdentityState,
    ResolutionDecision,
    ResolutionOutcome,
)
from modules.knowledge_graph.domain.resolution import ResolutionInput, resolve
from modules.provider_normalization.public import ClaimAttribute, ClaimReader, ClaimView
from signora_platform.event_bus import EventPublisher
from signora_platform.observability import get_logger

logger = get_logger(__name__)

PRODUCER_MODULE = "knowledge_graph"


@dataclass(frozen=True, slots=True)
class ResolveEntityInput:
    workspace_id: UUID
    raw_record_id: UUID
    provider: str
    provider_external_id: str


@dataclass(frozen=True, slots=True)
class ResolveEntityResult:
    binding: IdentityBinding
    claims: tuple[ClaimView, ...]
    #: None when re-resolution reached the same answer. A decision records a
    #: *change* of identity; writing one per re-sync would bury the
    #: corrections that matter under thousands that say nothing.
    decision: ResolutionDecision | None
    entity_created: bool


@dataclass(frozen=True, slots=True)
class IdentityHints:
    """What the claims say about who this is — never about what they are.

    Only the three fields the deterministic rules compare. Pulling anything
    else in would be assembling a record, and the entity deliberately does
    not have one.
    """

    domain: str | None
    legal_name: str | None
    country: str | None


def hints_from_claims(claims: tuple[ClaimView, ...]) -> IdentityHints:
    """Identity hints, preferring what the provider stated about the subject
    over what it claimed as an attribute.

    A `LEGAL_NAME` claim and a subject hint can disagree — the subject hint
    is what the provider used to identify the record, so it wins for
    matching purposes. The claim is untouched either way; nothing here
    reconciles them, it only chooses what to match on.
    """
    domain = next((c.subject_domain for c in claims if c.subject_domain), None)
    legal_name = next((c.subject_legal_name for c in claims if c.subject_legal_name), None)
    if legal_name is None:
        legal_name = next(
            (
                c.as_text()
                for c in claims
                if c.attribute is ClaimAttribute.LEGAL_NAME and c.as_text()
            ),
            None,
        )
    country = next(
        (c.as_text() for c in claims if c.attribute is ClaimAttribute.COUNTRY and c.as_text()),
        None,
    )
    return IdentityHints(domain=domain, legal_name=legal_name, country=country)


class ResolveEntity:
    def __init__(
        self,
        *,
        repository: GraphRepository,
        claims: ClaimReader,
        publisher: EventPublisher,
        session: AsyncSession,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._repository = repository
        self._claims = claims
        self._publisher = publisher
        # Injected rather than reached for: publication must commit in the
        # same transaction as the decision that caused it.
        self._session = session
        self._clock = clock

    async def execute(
        self, request: ResolveEntityInput, *, correlation_id: UUID, causation_id: UUID | None = None
    ) -> ResolveEntityResult | None:
        claims = await self._claims.for_record(request.raw_record_id)
        if not claims:
            # No evidence, nothing to identify. Not an error: a record may
            # legitimately produce no claims, and inventing an entity from
            # an empty record would create one entity per empty record.
            logger.info(
                "no claims for record; nothing to resolve",
                extra={"raw_record_id": str(request.raw_record_id)},
            )
            return None

        hints = hints_from_claims(claims)
        now = self._clock()

        decision, state = resolve(
            ResolutionInput(
                provider=request.provider,
                provider_external_id=request.provider_external_id,
                domain=hints.domain,
                legal_name=hints.legal_name,
                country=hints.country,
                evidence_claim_ids=tuple(c.id for c in claims),
            ),
            await self._repository.candidates(request.workspace_id),
            workspace_id=request.workspace_id,
            now=now,
        )

        previous = await self._repository.current_binding(
            request.workspace_id,
            provider=request.provider,
            provider_external_id=request.provider_external_id,
        )
        if previous is not None:
            if previous.state is state and previous.entity_id == decision.entity_id:
                # Re-resolution reached the same answer. Nothing changed, so
                # nothing is written — a re-sync must not manufacture a
                # supersession chain of identical decisions.
                return ResolveEntityResult(
                    binding=previous, claims=claims, decision=None, entity_created=False
                )
            decision = decision.correcting(previous.decision_id)

        entity_created = False
        if decision.outcome is ResolutionOutcome.CREATED:
            entity = Entity.create(
                workspace_id=request.workspace_id, kind=EntityKind.COMPANY, now=now
            )
            await self._repository.add_entity(entity)
            decision = decision.resolved_to(entity.id)
            entity_created = True

        await self._repository.add_decision(decision)

        binding = IdentityBinding(
            id=uuid4(),
            workspace_id=request.workspace_id,
            provider=request.provider,
            provider_external_id=request.provider_external_id,
            state=state,
            entity_id=decision.entity_id,
            decision_id=decision.id,
            domain=hints.domain,
            legal_name=hints.legal_name,
            country=hints.country,
            created_at=now,
        )
        if previous is not None:
            # Supersede before inserting: the partial unique index permits
            # exactly one current binding per identity, so the old one must
            # stop being current first.
            await self._repository.supersede_binding(previous.id, by=binding.id)
        await self._repository.add_binding(binding)

        await self._publish(decision, binding, now, correlation_id, causation_id, entity_created)

        logger.info(
            "identity resolved",
            extra={
                "provider": request.provider,
                "provider_external_id": request.provider_external_id,
                "outcome": decision.outcome.value,
                "state": state.value,
                "entity_id": str(decision.entity_id) if decision.entity_id else None,
                "decision_id": str(decision.id),
                "explanation": decision.explain(),
            },
        )

        return ResolveEntityResult(
            binding=binding, claims=claims, decision=decision, entity_created=entity_created
        )

    async def _publish(
        self,
        decision: ResolutionDecision,
        binding: IdentityBinding,
        now: datetime,
        correlation_id: UUID,
        causation_id: UUID | None,
        entity_created: bool,
    ) -> None:
        events: list[EntityCreated | EntityIdentityBound | EntityResolutionAmbiguous] = []

        if entity_created and decision.entity_id is not None:
            events.append(
                EntityCreated(
                    event_id=uuid4(),
                    workspace_id=decision.workspace_id,
                    occurred_at=now,
                    entity_id=decision.entity_id,
                    kind=EntityKind.COMPANY.value,
                    decision_id=decision.id,
                    causation_id=causation_id,
                )
            )

        if binding.state is IdentityState.AMBIGUOUS:
            events.append(
                EntityResolutionAmbiguous(
                    event_id=uuid4(),
                    workspace_id=decision.workspace_id,
                    occurred_at=now,
                    provider=decision.provider,
                    provider_external_id=decision.provider_external_id,
                    candidate_entity_ids=decision.candidate_entity_ids,
                    decision_id=decision.id,
                    causation_id=causation_id,
                )
            )
        elif decision.entity_id is not None:
            strength = decision.strength
            events.append(
                EntityIdentityBound(
                    event_id=uuid4(),
                    workspace_id=decision.workspace_id,
                    occurred_at=now,
                    entity_id=decision.entity_id,
                    provider=decision.provider,
                    provider_external_id=decision.provider_external_id,
                    rule=decision.reasons[0].rule.value if decision.reasons else "none",
                    strength=strength.value if strength is not None else "none",
                    decision_id=decision.id,
                    causation_id=causation_id,
                )
            )

        # See the note in provider_normalization's handler: the platform's
        # PublishableEvent Protocol declares settable members, which frozen
        # domain events cannot satisfy. Raised as a finding, not fixed here.
        await self._publisher.publish(
            events,  # type: ignore[arg-type]
            session=self._session,
            producer_module=PRODUCER_MODULE,
            correlation_id=correlation_id,
        )
