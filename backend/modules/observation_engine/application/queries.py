"""The Observation Engine's read surface.

**Deliberately absent: any method returning a current value, a consensus,
or a trend.** All three are interpretation. The Signal Engine reads the
series and forms its own — a convenience method here would put a judgement
behind an innocuous-looking call, and within a year every consumer would
use it instead of the evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from modules.knowledge_graph.public import GraphQueries
from modules.observation_engine.application.ports import ObservationRepository
from modules.observation_engine.domain.observation import Observation
from modules.provider_normalization.public import ClaimAttribute, ClaimView


@dataclass(frozen=True, slots=True)
class ObservationEvidence:
    """An observation together with the claims behind it — the traversal an
    evidence export and an AI citation both need."""

    observation: Observation
    claims: tuple[ClaimView, ...]


class ObservationQueries:
    """Read-only. Every method is scoped to one workspace, explicitly."""

    def __init__(self, *, repository: ObservationRepository, graph: GraphQueries) -> None:
        self._repository = repository
        self._graph = graph

    async def observations(
        self,
        workspace_id: UUID,
        entity_id: UUID,
        *,
        attribute: ClaimAttribute | None = None,
        since: datetime | None = None,
    ) -> tuple[Observation, ...]:
        return await self._repository.for_entity(
            workspace_id, entity_id, attribute=attribute, since=since
        )

    async def series(
        self, workspace_id: UUID, entity_id: UUID, provider: str, attribute: ClaimAttribute
    ) -> tuple[Observation, ...]:
        """One provider's changes to one attribute, oldest first.

        Per-provider by construction. A cross-provider series would merge
        Apollo's 120 on Monday with CoreSignal's 145 on Tuesday and call it
        growth — the phantom change this module exists to avoid.
        """
        observations = await self._repository.for_entity(
            workspace_id, entity_id, attribute=attribute
        )
        return tuple(o for o in observations if o.provider == provider)

    async def observation_evidence(
        self, workspace_id: UUID, observation_id: UUID
    ) -> ObservationEvidence | None:
        observation = await self._repository.by_id(workspace_id, observation_id)
        if observation is None:
            return None

        claim_set = await self._graph.claim_set(
            workspace_id, observation.entity_id, observation.attribute
        )
        cited = set(observation.evidence_claim_ids)
        return ObservationEvidence(
            observation=observation,
            claims=tuple(claim for claim in claim_set.claims if claim.id in cited),
        )
