"""Event handler: resolve identity when evidence arrives.

Subscribes to `claim.recorded` from Provider Normalization. The claims
themselves are read through that module's public `ClaimReader` port — the
event carries identity and counts, never bodies.

Resolution and relationship derivation run in one transaction: an entity
that exists without the edges its own evidence implies is a graph that is
briefly wrong in a way no consumer can detect.
"""

from __future__ import annotations

from uuid import UUID

from modules.knowledge_graph.application.relationships import (
    DeriveRelationships,
    DeriveRelationshipsInput,
)
from modules.knowledge_graph.application.resolve import ResolveEntity, ResolveEntityInput
from modules.knowledge_graph.domain.identity import IdentityState
from signora_platform.event_bus import EventEnvelope
from signora_platform.observability import get_logger

logger = get_logger(__name__)

CONSUMER_NAME = "knowledge_graph.resolve_identity"
"""A permanent contract. Renaming it resets the idempotency ledger and
every historical event would be re-processed on replay."""


async def resolve_recorded_claims(
    envelope: EventEnvelope,
    *,
    resolve: ResolveEntity,
    relationships: DeriveRelationships,
) -> None:
    result = await resolve.execute(
        ResolveEntityInput(
            workspace_id=envelope.workspace_id,
            raw_record_id=UUID(str(envelope.payload["raw_record_id"])),
            provider=str(envelope.payload["provider"]),
            provider_external_id=str(envelope.payload["subject_external_id"]),
        ),
        correlation_id=envelope.correlation_id,
        causation_id=envelope.event_id,
    )

    if result is None:
        return

    if result.binding.state is not IdentityState.IDENTIFIED or result.binding.entity_id is None:
        # Ambiguity merges nothing, and it must not derive edges either: an
        # edge hung off one of two candidate entities would attribute a
        # company's technology to a company that may not be it.
        logger.info(
            "identity not usable; no relationships derived",
            extra={
                "state": result.binding.state.value,
                "provider": result.binding.provider,
                "provider_external_id": result.binding.provider_external_id,
            },
        )
        return

    derived = await relationships.execute(
        DeriveRelationshipsInput(
            workspace_id=envelope.workspace_id,
            entity_id=result.binding.entity_id,
            claims=result.claims,
        ),
        correlation_id=envelope.correlation_id,
        causation_id=envelope.event_id,
    )

    logger.info(
        "claims resolved into the graph",
        extra={
            "entity_id": str(result.binding.entity_id),
            "entity_created": result.entity_created,
            "relationships_established": derived.established,
            "relationships_ended": derived.ended,
        },
    )
