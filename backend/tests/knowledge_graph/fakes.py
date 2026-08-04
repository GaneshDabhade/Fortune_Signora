"""In-memory doubles for the graph's ports.

The use cases are tested against these rather than against PostgreSQL. If a
domain or application test needed a real database, the Clean Architecture
boundary would have leaked (CLAUDE.md §11) — so these exist as much to
*prove* the boundary holds as to make the tests fast.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from modules.knowledge_graph.domain.identity import (
    Entity,
    EntityKind,
    IdentityBinding,
    IdentityState,
    Relationship,
    ResolutionDecision,
    ResolutionOutcome,
    ResolvedSubject,
)
from modules.knowledge_graph.domain.resolution import ResolutionCandidate
from modules.provider_normalization.public import (
    ClaimAttribute,
    ClaimView,
    NameMatch,
    SubjectRef,
)


class FakeGraphRepository:
    def __init__(self) -> None:
        self.entities: dict[UUID, Entity] = {}
        self.decisions: list[ResolutionDecision] = []
        self.bindings: list[IdentityBinding] = []
        self.relationships: list[Relationship] = []
        self.canonical: dict[str, Entity] = {}

    async def candidates(self, workspace_id: UUID) -> tuple[ResolutionCandidate, ...]:
        return tuple(
            ResolutionCandidate(
                entity_id=b.entity_id,
                provider=b.provider,
                provider_external_id=b.provider_external_id,
                domain=b.domain,
                legal_name=b.legal_name,
                country=b.country,
            )
            for b in self.bindings
            if b.superseded_by is None and b.entity_id is not None
        )

    async def current_binding(
        self, workspace_id: UUID, *, provider: str, provider_external_id: str
    ) -> IdentityBinding | None:
        return next(
            (
                b
                for b in self.bindings
                if b.superseded_by is None
                and b.provider == provider
                and b.provider_external_id == provider_external_id
            ),
            None,
        )

    async def add_entity(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    async def add_decision(self, decision: ResolutionDecision) -> None:
        self.decisions.append(decision)

    async def add_binding(self, binding: IdentityBinding) -> None:
        self.bindings.append(binding)

    async def supersede_binding(self, binding_id: UUID, *, by: UUID) -> None:
        self.bindings = [
            replace(b, superseded_by=by) if b.id == binding_id else b for b in self.bindings
        ]

    async def entity_by_id(self, workspace_id: UUID, entity_id: UUID) -> Entity | None:
        return self.entities.get(entity_id)

    async def bindings_for_entity(
        self, workspace_id: UUID, entity_id: UUID
    ) -> tuple[IdentityBinding, ...]:
        return tuple(
            b for b in self.bindings if b.entity_id == entity_id and b.superseded_by is None
        )

    async def bindings_for_entities(
        self, workspace_id: UUID, entity_ids: tuple[UUID, ...]
    ) -> tuple[IdentityBinding, ...]:
        """The plural, built from the singular so the two cannot disagree
        about which bindings are live."""
        found: list[IdentityBinding] = []
        for entity_id in entity_ids:
            found.extend(await self.bindings_for_entity(workspace_id, entity_id))
        return tuple(found)

    async def entities_for_subjects(
        self, workspace_id: UUID, subjects: Sequence[SubjectRef]
    ) -> tuple[ResolvedSubject, ...]:
        live = {
            (b.provider, b.provider_external_id): b.entity_id
            for b in self.bindings
            if b.superseded_by is None and b.entity_id is not None
        }
        # **Kind is read from the entity, exactly as the SQL join does.** A
        # fake that assumed `COMPANY` would make the derivation untestable and
        # turn a real field into one nothing could ever contradict.
        kinds = {entity.id: entity.kind for entity in self.entities.values()}
        ordered: list[ResolvedSubject] = []
        seen: set[UUID] = set()
        for subject in subjects:
            entity_id = live.get((subject.provider, subject.provider_external_id))
            if entity_id is None or entity_id in seen or entity_id not in kinds:
                continue
            seen.add(entity_id)
            ordered.append(
                ResolvedSubject(
                    provider=subject.provider,
                    provider_external_id=subject.provider_external_id,
                    entity_id=entity_id,
                    kind=kinds[entity_id],
                )
            )
        return tuple(ordered)

    async def decisions_for_entity(
        self, workspace_id: UUID, entity_id: UUID
    ) -> tuple[ResolutionDecision, ...]:
        return tuple(d for d in self.decisions if d.entity_id == entity_id)

    async def relationships_for_entity(
        self,
        workspace_id: UUID,
        entity_id: UUID,
        *,
        kind: str | None = None,
        as_of: datetime | None = None,
    ) -> tuple[Relationship, ...]:
        return tuple(
            r
            for r in self.relationships
            if r.source_entity_id == entity_id
            and (kind is None or r.kind == kind)
            and r.superseded_by is None
            and (
                as_of is None
                or (r.valid_from <= as_of and (r.valid_to is None or r.valid_to > as_of))
            )
        )

    async def add_relationship(self, relationship: Relationship) -> None:
        self.relationships.append(relationship)

    async def end_relationship(self, relationship_id: UUID, *, at: datetime) -> None:
        self.relationships = [
            r.ended(at=at, evidence=()) if r.id == relationship_id else r
            for r in self.relationships
        ]

    async def find_or_create_canonical_entity(
        self, workspace_id: UUID, *, kind: EntityKind, canonical_key: str, now: datetime
    ) -> tuple[Entity, bool]:
        if canonical_key in self.canonical:
            return self.canonical[canonical_key], False
        entity = Entity.create(workspace_id=workspace_id, kind=kind, now=now)
        self.entities[entity.id] = entity
        self.canonical[canonical_key] = entity
        return entity, True

    async def entity_ids(self, workspace_id: UUID) -> Sequence[UUID]:
        return list(self.entities)


class FakeClaimReader:
    def __init__(self, claims: Sequence[ClaimView] = ()) -> None:
        self.claims = list(claims)

    async def for_record(self, raw_record_id: UUID) -> tuple[ClaimView, ...]:
        return tuple(self.claims)

    async def for_subjects(
        self, subjects: Sequence[SubjectRef], *, attribute: ClaimAttribute | None = None
    ) -> tuple[ClaimView, ...]:
        wanted = {(s.provider, s.provider_external_id) for s in subjects}
        return tuple(
            c
            for c in self.claims
            if (c.provider, c.subject_external_id) in wanted
            and (attribute is None or c.attribute is attribute)
        )

    async def subjects_named_like(self, text: str, *, limit: int) -> tuple[NameMatch, ...]:
        """Case-insensitive substring over LEGAL_NAME claims, ordered by the
        matched name — the same contract the SQL reader implements, because a
        fake that orders differently would let a caller depend on an order the
        database does not produce.

        **The name carried is the one that matched, not the newest**, which is
        the whole point of the field: an identity claimed under two names
        matches on whichever the customer typed."""
        matched = [
            c
            for c in self.claims
            if c.attribute is ClaimAttribute.LEGAL_NAME
            and isinstance(c.value, str)
            and text.lower() in c.value.lower()
        ]
        found: list[NameMatch] = []
        seen: set[SubjectRef] = set()
        for claim in sorted(matched, key=lambda c: (str(c.value), c.provider, c.subject_external_id)):
            ref = SubjectRef(provider=claim.provider, provider_external_id=claim.subject_external_id)
            if ref in seen:
                continue
            seen.add(ref)
            found.append(NameMatch(subject=ref, name=str(claim.value)))
        return tuple(found[:limit])

    async def latest_observed_at(
        self, subjects: Sequence[SubjectRef]
    ) -> dict[SubjectRef, datetime]:
        """A subject with no claims is **absent**, matching the real reader:
        a `GROUP BY` returns no row rather than a null one, and a fake that
        invented one would hide a caller that cannot handle absence."""
        wanted = {(s.provider, s.provider_external_id) for s in subjects}
        latest: dict[SubjectRef, datetime] = {}
        for claim in self.claims:
            key = (claim.provider, claim.subject_external_id)
            if key not in wanted:
                continue
            ref = SubjectRef(provider=claim.provider, provider_external_id=claim.subject_external_id)
            known = latest.get(ref)
            if known is None or claim.observed_at > known:
                latest[ref] = claim.observed_at
        return latest


class RecordingPublisher:
    def __init__(self) -> None:
        self.events: list[Any] = []

    async def publish(
        self,
        events: Sequence[Any],
        *,
        session: Any,
        producer_module: str,
        correlation_id: UUID,
    ) -> None:
        self.events.extend(events)

    def types(self) -> list[str]:
        return [e.event_type for e in self.events]


def claim(
    *,
    provider: str = "apollo",
    attribute: ClaimAttribute = ClaimAttribute.EMPLOYEE_COUNT,
    value: Any = 120,
    external_id: str = "acme-corp",
    domain: str | None = "acme.example",
    legal_name: str | None = "Acme Corp",
    observed_at: datetime | None = None,
) -> ClaimView:
    return ClaimView(
        id=uuid4(),
        provider=provider,
        attribute=attribute,
        value=value,
        observed_at=observed_at or datetime(2026, 3, 1, tzinfo=UTC),
        subject_external_id=external_id,
        subject_domain=domain,
        subject_legal_name=legal_name,
        payload_provenance="DEVELOPMENT_FIXTURE",
    )


def bound_binding(
    entity: Entity, *, provider: str, external_id: str, domain: str | None = None
) -> IdentityBinding:
    """**`domain` is optional because `IdentityBinding.domain` is.**

    It was annotated `str` and had been narrower than the type it builds since
    it was written — invisible until a caller used the type honestly, which
    a `TECHNOLOGY` entity resolved from a technographic provider does: it has
    no domain, and that is the case rather than an omission
    ([B-115](../../../docs/BUGS.md)).
    """
    decision = ResolutionDecision(
        id=uuid4(),
        workspace_id=entity.workspace_id,
        provider=provider,
        provider_external_id=external_id,
        outcome=ResolutionOutcome.CREATED,
        reasons=(),
        entity_id=entity.id,
        candidate_entity_ids=(entity.id,),
        evidence_claim_ids=(),
        decided_at=entity.created_at,
    )
    return IdentityBinding(
        id=uuid4(),
        workspace_id=entity.workspace_id,
        provider=provider,
        provider_external_id=external_id,
        state=IdentityState.IDENTIFIED,
        entity_id=entity.id,
        decision_id=decision.id,
        created_at=entity.created_at,
        domain=domain,
    )
