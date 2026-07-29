"""Domain events published by the Knowledge Graph.

Cataloged in docs/architecture/06-events.md. Every event names the decision
that produced it, so a consumer — or an auditor — can follow any downstream
conclusion back to the rule and the matched value that justified it.

**No event carries an attribute value.** The graph resolves identity, not
truth; an event announcing "Acme has 120 employees" would be the collapse
this module exists to avoid. Consumers read the claim set instead.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final
from uuid import UUID

EVENT_VERSION: Final = 1


@dataclass(frozen=True, slots=True)
class EntityCreated:
    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    entity_id: UUID
    kind: str
    decision_id: UUID
    causation_id: UUID | None = None
    event_type: str = "entity.created"
    event_version: int = EVENT_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "entity_id": str(self.entity_id),
            "kind": self.kind,
            "decision_id": str(self.decision_id),
        }


@dataclass(frozen=True, slots=True)
class EntityIdentityBound:
    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    entity_id: UUID
    provider: str
    provider_external_id: str
    rule: str
    strength: str
    decision_id: UUID
    causation_id: UUID | None = None
    event_type: str = "entity.identity_bound"
    event_version: int = EVENT_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "entity_id": str(self.entity_id),
            "provider": self.provider,
            "provider_external_id": self.provider_external_id,
            "rule": self.rule,
            # A category, never a number — see MatchStrength. It travels as
            # the string it is so no consumer can read it as a weight.
            "strength": self.strength,
            "decision_id": str(self.decision_id),
        }


@dataclass(frozen=True, slots=True)
class EntityResolutionAmbiguous:
    """A first-class event, not a log line.

    It is a work queue and an operational signal that a provider's identity
    data has degraded. Rising volume here is the leading indicator the
    deterministic rules need extending.
    """

    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    provider: str
    provider_external_id: str
    candidate_entity_ids: tuple[UUID, ...]
    decision_id: UUID
    causation_id: UUID | None = None
    event_type: str = "entity.resolution_ambiguous"
    event_version: int = EVENT_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "provider_external_id": self.provider_external_id,
            "candidate_entity_ids": [str(i) for i in self.candidate_entity_ids],
            "decision_id": str(self.decision_id),
        }


@dataclass(frozen=True, slots=True)
class RelationshipEstablished:
    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    relationship_id: UUID
    kind: str
    source_entity_id: UUID
    target_entity_id: UUID
    valid_from: datetime
    causation_id: UUID | None = None
    event_type: str = "relationship.established"
    event_version: int = EVENT_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "relationship_id": str(self.relationship_id),
            "kind": self.kind,
            "source_entity_id": str(self.source_entity_id),
            "target_entity_id": str(self.target_entity_id),
            "valid_from": self.valid_from.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class RelationshipEnded:
    """An edge closed. **The row survives** — `valid_to` is set rather than
    the relationship deleted, because what a company used and stopped using
    is exactly what a competitive-displacement signal reads."""

    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    relationship_id: UUID
    kind: str
    source_entity_id: UUID
    target_entity_id: UUID
    valid_to: datetime
    causation_id: UUID | None = None
    event_type: str = "relationship.ended"
    event_version: int = EVENT_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "relationship_id": str(self.relationship_id),
            "kind": self.kind,
            "source_entity_id": str(self.source_entity_id),
            "target_entity_id": str(self.target_entity_id),
            "valid_to": self.valid_to.isoformat(),
        }
