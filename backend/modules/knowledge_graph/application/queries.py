"""The graph's read surface.

**Claim sets, never resolved values.** For `(entity, attribute)` this
returns every contributing claim with its provider, value, and time — a
*set*, deliberately not a value. The graph adds knowledge (these claims
describe the same company) without destroying evidence (they disagree, and
here is exactly how).

Adding a `current_value()` here would be Option A arriving by the back
door: within a year every consumer would call it and nobody would read the
claims. If a downstream module demonstrates it needs a resolved value, that
is a projection to design with its rule stated — not a convenience method
(docs/architecture/22-knowledge-graph.md).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from modules.knowledge_graph.application.ports import GraphRepository
from modules.knowledge_graph.domain.identity import (
    Entity,
    IdentityBinding,
    Relationship,
    ResolutionDecision,
)
from modules.provider_normalization.public import (
    ClaimAttribute,
    ClaimReader,
    ClaimView,
    SubjectRef,
)


def _subjects(bindings: tuple[IdentityBinding, ...]) -> list[SubjectRef]:
    """The provider identities that resolved to one entity.

    Claims are fetched by subject rather than from a stored evidence list so
    that claims recorded *after* a resolution still appear — a snapshot
    taken at binding time would silently stop growing.
    """
    return [
        SubjectRef(provider=b.provider, provider_external_id=b.provider_external_id)
        for b in bindings
    ]


def _comparable(value: Any) -> str:
    """A stable form for equality across providers.

    JSON with sorted keys rather than the raw object: two providers can
    report the same technology with their keys in a different order, and
    that is agreement, not disagreement.
    """
    return json.dumps(value, sort_keys=True, default=str)


@dataclass(frozen=True, slots=True)
class ClaimSet:
    """Everything known about one attribute of one entity."""

    entity_id: UUID
    attribute: ClaimAttribute
    claims: tuple[ClaimView, ...]

    @property
    def providers(self) -> tuple[str, ...]:
        return tuple(sorted({claim.provider for claim in self.claims}))

    @property
    def latest_by_provider(self) -> dict[str, ClaimView]:
        latest: dict[str, ClaimView] = {}
        for claim in sorted(self.claims, key=lambda c: (c.observed_at, str(c.id))):
            latest[claim.provider] = claim
        return latest

    @property
    def agrees(self) -> bool:
        """Whether the sources agree — comparing each provider's *most
        recent* observation, not every claim ever recorded.

        Comparing all claims would report disagreement whenever a value
        legitimately changed over time, which is a different fact and one
        the Observation Engine exists to read. Fewer than two providers
        agrees trivially.

        This is the one derived signal the graph offers, and it is computed
        rather than stored, because "do sources agree?" is a question about
        identity resolution having grouped them — which is the graph's own
        job.
        """
        values = {_comparable(claim.value) for claim in self.latest_by_provider.values()}
        return len(values) <= 1


@dataclass(frozen=True, slots=True)
class EntityEvidence:
    entity: Entity
    bindings: tuple[IdentityBinding, ...]
    claims: tuple[ClaimView, ...]


class GraphQueries:
    """Read-only. Every method is scoped to one workspace, explicitly."""

    def __init__(self, *, repository: GraphRepository, claims: ClaimReader) -> None:
        self._repository = repository
        self._claims = claims

    async def claim_set(
        self, workspace_id: UUID, entity_id: UUID, attribute: ClaimAttribute
    ) -> ClaimSet:
        bindings = await self._repository.bindings_for_entity(workspace_id, entity_id)
        claims = await self._claims.for_subjects(_subjects(bindings), attribute=attribute)
        return ClaimSet(entity_id=entity_id, attribute=attribute, claims=claims)

    async def entity_evidence(self, workspace_id: UUID, entity_id: UUID) -> EntityEvidence | None:
        """*"Why do we believe this?"* — the export an enterprise customer
        asks for, and the reason every link in the chain is preserved."""
        entity = await self._repository.entity_by_id(workspace_id, entity_id)
        if entity is None:
            return None
        bindings = await self._repository.bindings_for_entity(workspace_id, entity_id)
        claims = await self._claims.for_subjects(_subjects(bindings))
        return EntityEvidence(entity=entity, bindings=bindings, claims=claims)

    async def relationships(
        self,
        workspace_id: UUID,
        entity_id: UUID,
        *,
        kind: str | None = None,
        as_of: datetime | None = None,
    ) -> tuple[Relationship, ...]:
        return await self._repository.relationships_for_entity(
            workspace_id, entity_id, kind=kind, as_of=as_of
        )

    async def resolution_history(
        self, workspace_id: UUID, entity_id: UUID
    ) -> tuple[ResolutionDecision, ...]:
        """Every decision that bound an identity to this entity, oldest
        first — the full explanation of how it came to be what it is."""
        return await self._repository.decisions_for_entity(workspace_id, entity_id)
