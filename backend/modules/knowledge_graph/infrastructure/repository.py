"""Persistence for the graph.

**There is no update method for decisions, deliberately.** Immutability is
enforced at the database by the absent UPDATE grant (migration 0009); not
offering the method here means nobody writes code that would fail at
runtime.

Every query filters `workspace_id` explicitly even though RLS already
scopes the session — RLS is the authoritative control, not the only one
(CLAUDE.md §8).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from modules.knowledge_graph.domain.identity import (
    Entity,
    EntityKind,
    IdentityBinding,
    IdentityState,
    Relationship,
    ResolutionDecision,
    ResolutionOutcome,
    ResolutionReason,
    ResolutionRule,
)
from modules.knowledge_graph.domain.resolution import ResolutionCandidate
from modules.knowledge_graph.infrastructure.models import (
    EntityModel,
    IdentityBindingModel,
    RelationshipModel,
    ResolutionDecisionModel,
)

SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

#: Technology entities are keyed by canonical name rather than by a
#: provider identity, so their binding uses this synthetic provider. Kept
#: here as well as in the application layer so a reader of the table can
#: tell at a glance why a binding has no real provider behind it.
CANONICAL_PROVIDER = "canonical"


def _encode_reasons(reasons: tuple[ResolutionReason, ...]) -> list[dict[str, str]]:
    """Strength is written alongside the rule deliberately.

    It is denormalized at decision time so the audit record stays
    self-describing: if a rule's declared strength is revised later, what
    past decisions said must not silently change underneath them.
    """
    return [
        {
            "rule": reason.rule.value,
            "field": reason.field,
            "value": reason.value,
            "strength": reason.strength.value,
        }
        for reason in reasons
    ]


def _decode_reasons(raw: list[dict[str, Any]]) -> tuple[ResolutionReason, ...]:
    # `strength` is not read back: it is audit data describing what was
    # declared then, while the domain object derives strength from the rule
    # as it is declared now. Reading it back would make a stale value
    # authoritative.
    return tuple(
        ResolutionReason(
            rule=ResolutionRule(item["rule"]), field=item["field"], value=item["value"]
        )
        for item in raw
    )


def _to_binding(row: IdentityBindingModel) -> IdentityBinding:
    return IdentityBinding(
        id=row.id,
        workspace_id=row.workspace_id,
        provider=row.provider,
        provider_external_id=row.provider_external_id,
        state=IdentityState(row.state),
        entity_id=row.entity_id,
        decision_id=row.decision_id,
        created_at=row.created_at,
        superseded_by=row.superseded_by,
    )


def _to_decision(row: ResolutionDecisionModel) -> ResolutionDecision:
    return ResolutionDecision(
        id=row.id,
        workspace_id=row.workspace_id,
        provider=row.provider,
        provider_external_id=row.provider_external_id,
        outcome=ResolutionOutcome(row.outcome),
        reasons=_decode_reasons(row.reasons),
        entity_id=row.entity_id,
        candidate_entity_ids=tuple(row.candidate_entity_ids),
        evidence_claim_ids=tuple(row.evidence_claim_ids),
        decided_at=row.decided_at,
        supersedes=row.supersedes,
    )


def _to_relationship(row: RelationshipModel) -> Relationship:
    return Relationship(
        id=row.id,
        workspace_id=row.workspace_id,
        kind=row.kind,
        source_entity_id=row.source_entity_id,
        target_entity_id=row.target_entity_id,
        valid_from=row.valid_from,
        evidence_claim_ids=tuple(row.evidence_claim_ids),
        valid_to=row.valid_to,
        superseded_by=row.superseded_by,
    )


class SqlGraphRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def candidates(self, workspace_id: UUID) -> tuple[ResolutionCandidate, ...]:
        rows = await self._session.execute(
            select(IdentityBindingModel)
            .where(
                IdentityBindingModel.workspace_id == workspace_id,
                IdentityBindingModel.superseded_by.is_(None),
                # An AMBIGUOUS binding resolved to no entity, so it cannot
                # be something to bind *to*. Including it would let an
                # unresolved identity pull later ones into itself.
                IdentityBindingModel.entity_id.is_not(None),
            )
            # Ordered so a shuffled processing order still evaluates
            # candidates in one sequence — determinism (AC-27) has to hold
            # at the storage layer too, not only in the rule engine.
            .order_by(IdentityBindingModel.created_at, IdentityBindingModel.id)
        )
        return tuple(
            ResolutionCandidate(
                entity_id=row.entity_id,
                provider=row.provider,
                provider_external_id=row.provider_external_id,
                domain=row.domain,
                legal_name=row.legal_name,
                country=row.country,
            )
            for row in rows.scalars()
            if row.entity_id is not None
        )

    async def current_binding(
        self, workspace_id: UUID, *, provider: str, provider_external_id: str
    ) -> IdentityBinding | None:
        row = (
            await self._session.execute(
                select(IdentityBindingModel).where(
                    IdentityBindingModel.workspace_id == workspace_id,
                    IdentityBindingModel.provider == provider,
                    IdentityBindingModel.provider_external_id == provider_external_id,
                    IdentityBindingModel.superseded_by.is_(None),
                )
            )
        ).scalar_one_or_none()
        return _to_binding(row) if row is not None else None

    async def add_entity(self, entity: Entity) -> None:
        self._session.add(
            EntityModel(
                id=entity.id,
                workspace_id=entity.workspace_id,
                kind=entity.kind.value,
                created_by=SYSTEM_USER_ID,
                updated_by=SYSTEM_USER_ID,
            )
        )
        await self._session.flush()

    async def add_decision(self, decision: ResolutionDecision) -> None:
        self._session.add(
            ResolutionDecisionModel(
                id=decision.id,
                workspace_id=decision.workspace_id,
                provider=decision.provider,
                provider_external_id=decision.provider_external_id,
                outcome=decision.outcome.value,
                reasons=_encode_reasons(decision.reasons),
                entity_id=decision.entity_id,
                candidate_entity_ids=list(decision.candidate_entity_ids),
                evidence_claim_ids=list(decision.evidence_claim_ids),
                decided_at=decision.decided_at,
                supersedes=decision.supersedes,
                created_by=SYSTEM_USER_ID,
                updated_by=SYSTEM_USER_ID,
            )
        )
        await self._session.flush()

    async def add_binding(self, binding: IdentityBinding) -> None:
        self._session.add(
            IdentityBindingModel(
                id=binding.id,
                workspace_id=binding.workspace_id,
                provider=binding.provider,
                provider_external_id=binding.provider_external_id,
                state=binding.state.value,
                entity_id=binding.entity_id,
                decision_id=binding.decision_id,
                domain=binding.domain,
                legal_name=binding.legal_name,
                country=binding.country,
                superseded_by=binding.superseded_by,
                created_by=SYSTEM_USER_ID,
                updated_by=SYSTEM_USER_ID,
            )
        )
        await self._session.flush()

    async def supersede_binding(self, binding_id: UUID, *, by: UUID) -> None:
        await self._session.execute(
            update(IdentityBindingModel)
            .where(IdentityBindingModel.id == binding_id)
            .values(superseded_by=by, updated_by=SYSTEM_USER_ID)
        )
        await self._session.flush()

    async def entity_by_id(self, workspace_id: UUID, entity_id: UUID) -> Entity | None:
        row = (
            await self._session.execute(
                select(EntityModel).where(
                    EntityModel.workspace_id == workspace_id, EntityModel.id == entity_id
                )
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        return Entity(
            id=row.id,
            workspace_id=row.workspace_id,
            kind=EntityKind(row.kind),
            created_at=row.created_at,
        )

    async def bindings_for_entity(
        self, workspace_id: UUID, entity_id: UUID
    ) -> tuple[IdentityBinding, ...]:
        rows = await self._session.execute(
            select(IdentityBindingModel)
            .where(
                IdentityBindingModel.workspace_id == workspace_id,
                IdentityBindingModel.entity_id == entity_id,
                IdentityBindingModel.superseded_by.is_(None),
            )
            .order_by(IdentityBindingModel.provider, IdentityBindingModel.provider_external_id)
        )
        return tuple(_to_binding(row) for row in rows.scalars())

    async def bindings_for_entities(
        self, workspace_id: UUID, entity_ids: tuple[UUID, ...]
    ) -> tuple[IdentityBinding, ...]:
        if not entity_ids:
            return ()
        rows = await self._session.execute(
            select(IdentityBindingModel)
            .where(
                IdentityBindingModel.workspace_id == workspace_id,
                IdentityBindingModel.entity_id.in_(entity_ids),
                IdentityBindingModel.superseded_by.is_(None),
            )
            .order_by(IdentityBindingModel.provider, IdentityBindingModel.provider_external_id)
        )
        return tuple(_to_binding(row) for row in rows.scalars())

    async def decisions_for_entity(
        self, workspace_id: UUID, entity_id: UUID
    ) -> tuple[ResolutionDecision, ...]:
        rows = await self._session.execute(
            select(ResolutionDecisionModel)
            .where(
                ResolutionDecisionModel.workspace_id == workspace_id,
                ResolutionDecisionModel.entity_id == entity_id,
            )
            .order_by(ResolutionDecisionModel.decided_at, ResolutionDecisionModel.id)
        )
        return tuple(_to_decision(row) for row in rows.scalars())

    async def relationships_for_entity(
        self,
        workspace_id: UUID,
        entity_id: UUID,
        *,
        kind: str | None = None,
        as_of: datetime | None = None,
    ) -> tuple[Relationship, ...]:
        statement = select(RelationshipModel).where(
            RelationshipModel.workspace_id == workspace_id,
            RelationshipModel.source_entity_id == entity_id,
            RelationshipModel.superseded_by.is_(None),
        )
        if kind is not None:
            statement = statement.where(RelationshipModel.kind == kind)
        if as_of is not None:
            # Edges live at that instant: begun by then, and not yet ended.
            # This is what lets a caller ask what was true in January
            # without reconstructing it from event history.
            statement = statement.where(
                RelationshipModel.valid_from <= as_of,
                or_(RelationshipModel.valid_to.is_(None), RelationshipModel.valid_to > as_of),
            )

        rows = await self._session.execute(
            statement.order_by(RelationshipModel.valid_from, RelationshipModel.id)
        )
        return tuple(_to_relationship(row) for row in rows.scalars())

    async def add_relationship(self, relationship: Relationship) -> None:
        self._session.add(
            RelationshipModel(
                id=relationship.id,
                workspace_id=relationship.workspace_id,
                kind=relationship.kind,
                source_entity_id=relationship.source_entity_id,
                target_entity_id=relationship.target_entity_id,
                valid_from=relationship.valid_from,
                valid_to=relationship.valid_to,
                evidence_claim_ids=list(relationship.evidence_claim_ids),
                created_by=SYSTEM_USER_ID,
                updated_by=SYSTEM_USER_ID,
            )
        )
        await self._session.flush()

    async def end_relationship(self, relationship_id: UUID, *, at: datetime) -> None:
        await self._session.execute(
            update(RelationshipModel)
            .where(RelationshipModel.id == relationship_id)
            .values(valid_to=at, updated_by=SYSTEM_USER_ID)
        )
        await self._session.flush()

    async def find_or_create_canonical_entity(
        self,
        workspace_id: UUID,
        *,
        kind: EntityKind,
        canonical_key: str,
        now: datetime,
    ) -> tuple[Entity, bool]:
        """Reuses the binding table as the canonical-name index.

        A technology has no provider identity, so its binding names the
        synthetic `canonical` provider and its normalized name. That keeps
        one lookup path for "have I seen this before?" rather than adding a
        second table whose only job is to answer the same question.
        """
        existing = await self.current_binding(
            workspace_id, provider=CANONICAL_PROVIDER, provider_external_id=canonical_key
        )
        if existing is not None and existing.entity_id is not None:
            entity = await self.entity_by_id(workspace_id, existing.entity_id)
            if entity is not None:
                return entity, False

        entity = Entity.create(workspace_id=workspace_id, kind=kind, now=now)
        await self.add_entity(entity)

        decision = ResolutionDecision(
            id=uuid4(),
            workspace_id=workspace_id,
            provider=CANONICAL_PROVIDER,
            provider_external_id=canonical_key,
            outcome=ResolutionOutcome.CREATED,
            reasons=(),
            entity_id=entity.id,
            candidate_entity_ids=(entity.id,),
            evidence_claim_ids=(),
            decided_at=now,
        )
        await self.add_decision(decision)
        await self.add_binding(
            IdentityBinding(
                id=uuid4(),
                workspace_id=workspace_id,
                provider=CANONICAL_PROVIDER,
                provider_external_id=canonical_key,
                state=IdentityState.IDENTIFIED,
                entity_id=entity.id,
                decision_id=decision.id,
                created_at=now,
            )
        )
        return entity, True

    async def entity_ids(self, workspace_id: UUID) -> Sequence[UUID]:
        rows = await self._session.execute(
            select(EntityModel.id)
            .where(EntityModel.workspace_id == workspace_id)
            .order_by(EntityModel.created_at, EntityModel.id)
        )
        return list(rows.scalars())
