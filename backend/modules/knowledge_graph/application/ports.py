"""Ports the Knowledge Graph's use cases depend on.

Protocols only. The SQLAlchemy implementations live in `infrastructure/`
and are injected at the composition boundary, so the use cases can be
tested against fakes without a database (CLAUDE.md §11).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol
from uuid import UUID

from modules.knowledge_graph.domain.identity import (
    Entity,
    EntityKind,
    IdentityBinding,
    Relationship,
    ResolutionDecision,
    ResolvedSubject,
)
from modules.knowledge_graph.domain.resolution import ResolutionCandidate
from modules.provider_normalization.public import SubjectRef


class GraphRepository(Protocol):
    """Persistence for the graph. Every method is workspace-scoped by the
    caller's tenant session; `workspace_id` is passed explicitly as well,
    because RLS is the authoritative control and not the only one."""

    async def candidates(self, workspace_id: UUID) -> tuple[ResolutionCandidate, ...]:
        """Every *current* binding in the workspace, flattened to the fields
        the rules compare.

        All of them, deliberately: rules are evaluated against the whole
        current state rather than against processing history, which is what
        makes resolution order-independent (AC-27).
        """
        ...

    async def current_binding(
        self, workspace_id: UUID, *, provider: str, provider_external_id: str
    ) -> IdentityBinding | None: ...

    async def add_entity(self, entity: Entity) -> None: ...

    async def add_decision(self, decision: ResolutionDecision) -> None: ...

    async def add_binding(self, binding: IdentityBinding) -> None: ...

    async def supersede_binding(self, binding_id: UUID, *, by: UUID) -> None: ...

    async def entity_by_id(self, workspace_id: UUID, entity_id: UUID) -> Entity | None: ...

    async def bindings_for_entity(
        self, workspace_id: UUID, entity_id: UUID
    ) -> tuple[IdentityBinding, ...]: ...

    async def bindings_for_entities(
        self, workspace_id: UUID, entity_ids: tuple[UUID, ...]
    ) -> tuple[IdentityBinding, ...]:
        """Live bindings for many entities at once.

        The plural of `bindings_for_entity`, and the reason it exists is the
        same reason the Buying Score Engine grew a plural read: naming a page
        of fifty accounts one entity at a time is fifty round trips, and an
        obvious N+1 is a defect at write time rather than a future
        optimisation (CLAUDE.md §14).
        """
        ...

    async def entities_for_subjects(
        self, workspace_id: UUID, subjects: Sequence[SubjectRef]
    ) -> tuple[ResolvedSubject, ...]:
        """Which accounts these provider identities resolved to, in order,
        with duplicates collapsed.

        The inverse of `bindings_for_entities`, and the direction search
        needs: a match is found on a *claim about an identity*, and what a
        customer is looking for is the account.

        **Which identity produced which account is carried, not discarded.**
        Returning bare entity ids made the two orderings correspond by
        position and nothing else, so a caller could not say *which* of an
        account's several identities was the one that matched — which is
        exactly the sentence a search result needs.

        **The entity's kind travels with it**, because a caller grouping
        results by type must read that from the entity rather than assume it
        from the endpoint it called.

        **An unresolved or ambiguous identity contributes nothing.** Its
        binding holds no `entity_id`, and there is genuinely no account to
        send a customer to — inventing one from the identity would be the
        merge this module exists to refuse.
        """
        ...

    async def decisions_for_entity(
        self, workspace_id: UUID, entity_id: UUID
    ) -> tuple[ResolutionDecision, ...]: ...

    async def relationships_for_entity(
        self,
        workspace_id: UUID,
        entity_id: UUID,
        *,
        kind: str | None = None,
        as_of: datetime | None = None,
    ) -> tuple[Relationship, ...]:
        """Edges from this entity.

        `as_of` selects the edges that were live at that instant rather than
        those live now — the seam for historical replay. Retrofitting a
        temporal query onto a non-temporal API costs a rewrite of every
        caller, so it exists from the first version.
        """
        ...

    async def add_relationship(self, relationship: Relationship) -> None: ...

    async def end_relationship(self, relationship_id: UUID, *, at: datetime) -> None: ...

    async def find_or_create_canonical_entity(
        self,
        workspace_id: UUID,
        *,
        kind: EntityKind,
        canonical_key: str,
        now: datetime,
    ) -> tuple[Entity, bool]:
        """The entity for a canonically-named thing, creating it if absent.

        Returns the entity and whether it was created. Used for technology,
        which has no provider identity of its own — see
        `TECHNOLOGY_NAMESPACE` in `application/relationships.py`.
        """
        ...

    async def entity_ids(self, workspace_id: UUID) -> Sequence[UUID]: ...
