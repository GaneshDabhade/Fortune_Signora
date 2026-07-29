"""The graph's use cases, tested against fakes.

No database, no event bus, no provider. If any of these needed one, the
Clean Architecture boundary would have leaked — so the absence of
infrastructure here is itself part of what is being asserted.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

from modules.knowledge_graph.application.queries import ClaimSet, GraphQueries
from modules.knowledge_graph.application.relationships import (
    DeriveRelationships,
    DeriveRelationshipsInput,
    canonical_technology_key,
)
from modules.knowledge_graph.application.resolve import (
    ResolveEntity,
    ResolveEntityInput,
    hints_from_claims,
)
from modules.knowledge_graph.domain.identity import (
    USES_TECHNOLOGY,
    Entity,
    EntityKind,
    IdentityState,
)
from modules.knowledge_graph.public import MatchStrength
from modules.provider_normalization.public import ClaimAttribute
from tests.knowledge_graph.fakes import (
    FakeClaimReader,
    FakeGraphRepository,
    RecordingPublisher,
    bound_binding,
    claim,
)

WORKSPACE = uuid4()
NOW = datetime(2026, 3, 1, tzinfo=UTC)


def _resolver(
    repository: FakeGraphRepository, claims: FakeClaimReader
) -> tuple[ResolveEntity, RecordingPublisher]:
    publisher = RecordingPublisher()
    return (
        ResolveEntity(
            repository=repository,
            claims=claims,
            publisher=publisher,
            session=None,  # type: ignore[arg-type]
            clock=lambda: NOW,
        ),
        publisher,
    )


def _request(provider: str = "apollo", external_id: str = "acme-corp") -> ResolveEntityInput:
    return ResolveEntityInput(
        workspace_id=WORKSPACE,
        raw_record_id=uuid4(),
        provider=provider,
        provider_external_id=external_id,
    )


class TestResolveEntity:
    async def test_a_record_with_no_claims_resolves_to_nothing(self) -> None:
        """Not an error. Inventing an entity from an empty record would
        create one entity per empty record — the failure mode that looks
        like a working pipeline."""
        resolve, publisher = _resolver(FakeGraphRepository(), FakeClaimReader())

        assert await resolve.execute(_request(), correlation_id=uuid4()) is None
        assert publisher.events == []

    async def test_an_unknown_identity_creates_an_entity(self) -> None:
        repository = FakeGraphRepository()
        resolve, publisher = _resolver(repository, FakeClaimReader([claim()]))

        result = await resolve.execute(_request(), correlation_id=uuid4())

        assert result is not None
        assert result.entity_created is True
        assert result.binding.state is IdentityState.IDENTIFIED
        assert publisher.types() == ["entity.created", "entity.identity_bound"]

    async def test_a_second_provider_on_the_same_domain_binds_rather_than_creates(self) -> None:
        repository = FakeGraphRepository()
        entity = Entity.create(workspace_id=WORKSPACE, kind=EntityKind.COMPANY, now=NOW)
        repository.entities[entity.id] = entity
        repository.bindings.append(
            bound_binding(entity, provider="apollo", external_id="acme-corp", domain="acme.example")
        )
        resolve, publisher = _resolver(
            repository,
            FakeClaimReader([claim(provider="builtwith", external_id="acme.example")]),
        )

        result = await resolve.execute(
            _request(provider="builtwith", external_id="acme.example"), correlation_id=uuid4()
        )

        assert result is not None
        assert result.entity_created is False
        assert result.binding.entity_id == entity.id
        assert publisher.types() == ["entity.identity_bound"]

    async def test_two_candidates_produce_ambiguity_and_merge_nothing(self) -> None:
        """The property the whole module is shaped around. A wrong merge is
        invisible and corrupts every downstream signal."""
        repository = FakeGraphRepository()
        for _ in range(2):
            entity = Entity.create(workspace_id=WORKSPACE, kind=EntityKind.COMPANY, now=NOW)
            repository.entities[entity.id] = entity
            repository.bindings.append(
                bound_binding(
                    entity,
                    provider=f"p{entity.id.hex[:4]}",
                    external_id=entity.id.hex[:4],
                    domain="acme.example",
                )
            )
        resolve, publisher = _resolver(repository, FakeClaimReader([claim()]))

        result = await resolve.execute(_request(), correlation_id=uuid4())

        assert result is not None
        assert result.binding.state is IdentityState.AMBIGUOUS
        assert result.binding.entity_id is None
        assert publisher.types() == ["entity.resolution_ambiguous"]

    async def test_re_resolving_the_same_identity_writes_nothing(self) -> None:
        repository = FakeGraphRepository()
        resolve, _ = _resolver(repository, FakeClaimReader([claim()]))
        await resolve.execute(_request(), correlation_id=uuid4())
        decisions_after_first = len(repository.decisions)

        resolve, publisher = _resolver(repository, FakeClaimReader([claim()]))
        result = await resolve.execute(_request(), correlation_id=uuid4())

        assert result is not None
        assert result.decision is None, "an unchanged answer must not be recorded as a decision"
        assert len(repository.decisions) == decisions_after_first
        assert publisher.events == []

    async def test_a_resolved_ambiguity_supersedes_the_decision_that_recorded_it(self) -> None:
        """The supersession path M3A actually has.

        Once an identity is *bound*, `SAME_PROVIDER_ID` matches it on every
        later pass — a provider cannot be wrong about its own key — so a
        binding never drifts to another entity on its own. An **ambiguous**
        identity is different: it binds to nothing, so it is reconsidered
        each time, and it becomes identified once the duplicate candidate is
        gone. Correcting a *wrong* merge is an operator action (deferred to
        M12), not something re-resolution does behind anyone's back.

        Either way the earlier decision survives: knowledge has history for
        the same reason evidence does.
        """
        repository = FakeGraphRepository()
        keeper = Entity.create(workspace_id=WORKSPACE, kind=EntityKind.COMPANY, now=NOW)
        duplicate = Entity.create(workspace_id=WORKSPACE, kind=EntityKind.COMPANY, now=NOW)
        for entity, provider in ((keeper, "crunchbase"), (duplicate, "coresignal")):
            repository.entities[entity.id] = entity
            repository.bindings.append(
                bound_binding(entity, provider=provider, external_id="x", domain="acme.example")
            )

        resolve, _ = _resolver(repository, FakeClaimReader([claim()]))
        ambiguous = await resolve.execute(_request(), correlation_id=uuid4())
        assert ambiguous is not None and ambiguous.decision is not None
        assert ambiguous.binding.state is IdentityState.AMBIGUOUS
        first_decision = ambiguous.decision

        # An operator retires the duplicate; the identity is now resolvable.
        repository.bindings = [b for b in repository.bindings if b.entity_id != duplicate.id]

        resolve, publisher = _resolver(repository, FakeClaimReader([claim()]))
        result = await resolve.execute(_request(), correlation_id=uuid4())

        assert result is not None and result.decision is not None
        assert result.binding.state is IdentityState.IDENTIFIED
        assert result.binding.entity_id == keeper.id
        assert result.decision.supersedes == first_decision.id
        assert first_decision in repository.decisions, "history must not be rewritten"
        assert publisher.types() == ["entity.identity_bound"]

    async def test_the_binding_records_the_strength_of_the_rule_that_decided(self) -> None:
        repository = FakeGraphRepository()
        entity = Entity.create(workspace_id=WORKSPACE, kind=EntityKind.COMPANY, now=NOW)
        repository.entities[entity.id] = entity
        repository.bindings.append(
            bound_binding(entity, provider="apollo", external_id="a-1", domain="acme.example")
        )
        resolve, _ = _resolver(
            repository, FakeClaimReader([claim(provider="builtwith", external_id="bw-1")])
        )

        result = await resolve.execute(
            _request(provider="builtwith", external_id="bw-1"), correlation_id=uuid4()
        )

        assert result is not None and result.decision is not None
        assert result.decision.strength is MatchStrength.STRONG


class TestIdentityHints:
    def test_a_legal_name_claim_fills_in_for_a_missing_subject_hint(self) -> None:
        hints = hints_from_claims(
            (
                claim(legal_name=None, domain=None),
                claim(attribute=ClaimAttribute.LEGAL_NAME, value="Acme Corp", legal_name=None),
            )
        )

        assert hints.legal_name == "Acme Corp"

    def test_country_comes_from_a_country_claim(self) -> None:
        hints = hints_from_claims((claim(attribute=ClaimAttribute.COUNTRY, value="US"),))

        assert hints.country == "US"

    def test_nothing_is_invented_when_the_evidence_is_silent(self) -> None:
        hints = hints_from_claims((claim(domain=None, legal_name=None),))

        assert hints == hints.__class__(domain=None, legal_name=None, country=None)


class TestClaimSetAgreement:
    """`agrees` compares each provider's *most recent* observation.

    Comparing every claim ever recorded would report disagreement whenever
    a value legitimately changed over time — a different fact entirely, and
    one the Observation Engine exists to read.
    """

    def _set(self, *claims: object) -> ClaimSet:
        return ClaimSet(
            entity_id=uuid4(),
            attribute=ClaimAttribute.EMPLOYEE_COUNT,
            claims=claims,  # type: ignore[arg-type]
        )

    def test_one_provider_agrees_trivially(self) -> None:
        assert self._set(claim(value=120)).agrees is True

    def test_two_providers_reporting_the_same_value_agree(self) -> None:
        assert self._set(claim(value=120), claim(provider="coresignal", value=120)).agrees is True

    def test_two_providers_reporting_different_values_disagree(self) -> None:
        """The product value: a seller told only one number cannot tell the
        sources conflict."""
        assert self._set(claim(value=120), claim(provider="coresignal", value=145)).agrees is False

    def test_a_value_changing_over_time_is_not_disagreement(self) -> None:
        assert (
            self._set(
                claim(value=120, observed_at=datetime(2026, 1, 1, tzinfo=UTC)),
                claim(value=145, observed_at=datetime(2026, 2, 1, tzinfo=UTC)),
            ).agrees
            is True
        )

    def test_providers_are_listed_once_and_sorted(self) -> None:
        claim_set = self._set(claim(), claim(), claim(provider="coresignal"))

        assert claim_set.providers == ("apollo", "coresignal")

    def test_an_empty_set_agrees(self) -> None:
        assert self._set().agrees is True


class TestGraphQueries:
    async def test_evidence_for_an_unknown_entity_is_none_not_empty(self) -> None:
        """Absent and empty mean different things, and only one of them is
        a bug."""
        queries = GraphQueries(repository=FakeGraphRepository(), claims=FakeClaimReader())

        assert await queries.entity_evidence(WORKSPACE, uuid4()) is None

    async def test_a_claim_set_is_scoped_to_the_entity_s_own_identities(self) -> None:
        repository = FakeGraphRepository()
        entity = Entity.create(workspace_id=WORKSPACE, kind=EntityKind.COMPANY, now=NOW)
        repository.entities[entity.id] = entity
        repository.bindings.append(
            bound_binding(entity, provider="apollo", external_id="acme-corp", domain="acme.example")
        )
        reader = FakeClaimReader([claim(), claim(provider="apollo", external_id="globex")])
        queries = GraphQueries(repository=repository, claims=reader)

        claim_set = await queries.claim_set(WORKSPACE, entity.id, ClaimAttribute.EMPLOYEE_COUNT)

        assert [c.subject_external_id for c in claim_set.claims] == ["acme-corp"]


class TestRelationshipDerivation:
    def _derive(
        self, repository: FakeGraphRepository
    ) -> tuple[DeriveRelationships, RecordingPublisher]:
        publisher = RecordingPublisher()
        return (
            DeriveRelationships(
                repository=repository,
                publisher=publisher,
                session=None,  # type: ignore[arg-type]
                clock=lambda: NOW,
            ),
            publisher,
        )

    def _tech(self, name: str, *, removed: bool = False, **window: date) -> object:
        return claim(
            provider="builtwith",
            attribute=(
                ClaimAttribute.TECHNOLOGY_REMOVED if removed else ClaimAttribute.TECHNOLOGY_DETECTED
            ),
            value={
                "name": name,
                "category": "erp",
                **{k: v.isoformat() for k, v in window.items()},
            },
        )

    async def test_a_detection_opens_an_edge(self) -> None:
        repository = FakeGraphRepository()
        derive, publisher = self._derive(repository)
        entity_id = uuid4()

        result = await derive.execute(
            DeriveRelationshipsInput(WORKSPACE, entity_id, (self._tech("CloudERP"),)),  # type: ignore[arg-type]
            correlation_id=uuid4(),
        )

        assert result.established == 1
        assert publisher.types() == ["relationship.established"]
        assert repository.relationships[0].is_current

    async def test_a_removal_closes_the_edge_rather_than_deleting_it(self) -> None:
        repository = FakeGraphRepository()
        derive, _ = self._derive(repository)
        entity_id = uuid4()
        await derive.execute(
            DeriveRelationshipsInput(WORKSPACE, entity_id, (self._tech("CloudERP"),)),  # type: ignore[arg-type]
            correlation_id=uuid4(),
        )

        derive, publisher = self._derive(repository)
        result = await derive.execute(
            DeriveRelationshipsInput(
                WORKSPACE,
                entity_id,
                (self._tech("CloudERP", removed=True, last_seen=date(2026, 2, 1)),),  # type: ignore[arg-type]
            ),
            correlation_id=uuid4(),
        )

        assert result.ended == 1
        assert len(repository.relationships) == 1, "the edge must survive its own removal"
        assert repository.relationships[0].valid_to is not None
        assert publisher.types() == ["relationship.ended"]

    async def test_a_technology_only_ever_seen_as_removed_is_still_recorded(self) -> None:
        """A vendor reporting current state only tells us LegacyERP was
        retired without ever having said it was running. The claim carries
        the interval, so the edge is written already closed — discarding it
        would lose exactly the history a displacement signal reads.
        """
        repository = FakeGraphRepository()
        derive, _ = self._derive(repository)

        result = await derive.execute(
            DeriveRelationshipsInput(
                WORKSPACE,
                uuid4(),
                (
                    self._tech(  # type: ignore[arg-type]
                        "LegacyERP",
                        removed=True,
                        first_seen=date(2021, 3, 1),
                        last_seen=date(2026, 1, 5),
                    ),
                ),
            ),
            correlation_id=uuid4(),
        )

        assert result.ended == 1
        edge = repository.relationships[0]
        assert edge.valid_from == datetime(2021, 3, 1, tzinfo=UTC)
        assert edge.valid_to == datetime(2026, 1, 5, tzinfo=UTC)

    async def test_a_redelivered_removal_does_not_duplicate_the_edge(self) -> None:
        repository = FakeGraphRepository()
        retired = self._tech("LegacyERP", removed=True, last_seen=date(2026, 1, 5))

        for _ in range(2):
            derive, _ = self._derive(repository)
            await derive.execute(
                DeriveRelationshipsInput(WORKSPACE, uuid4(), (retired,)),  # type: ignore[arg-type]
                correlation_id=uuid4(),
            )

        assert len(repository.relationships) == 2, (
            "two different companies retiring the same technology are two edges"
        )

    async def test_a_repeated_detection_does_not_reopen_a_second_edge(self) -> None:
        repository = FakeGraphRepository()
        entity_id = uuid4()

        for _ in range(2):
            derive, _ = self._derive(repository)
            await derive.execute(
                DeriveRelationshipsInput(WORKSPACE, entity_id, (self._tech("CloudERP"),)),  # type: ignore[arg-type]
                correlation_id=uuid4(),
            )

        assert len(repository.relationships) == 1

    async def test_non_technographic_claims_derive_nothing(self) -> None:
        """Nothing else in the vocabulary yields an edge without inventing
        meaning."""
        repository = FakeGraphRepository()
        derive, publisher = self._derive(repository)

        result = await derive.execute(
            DeriveRelationshipsInput(WORKSPACE, uuid4(), (claim(),)),
            correlation_id=uuid4(),
        )

        assert (result.established, result.ended) == (0, 0)
        assert publisher.events == []

    async def test_the_edge_kind_is_the_one_the_vocabulary_supports(self) -> None:
        repository = FakeGraphRepository()
        derive, _ = self._derive(repository)

        await derive.execute(
            DeriveRelationshipsInput(WORKSPACE, uuid4(), (self._tech("CloudERP"),)),  # type: ignore[arg-type]
            correlation_id=uuid4(),
        )

        assert repository.relationships[0].kind == USES_TECHNOLOGY


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("CloudERP", "clouderp"), ("  Cloud   ERP ", "cloud erp"), ("cloud erp", "cloud erp")],
)
def test_technology_names_reach_one_canonical_key(raw: str, expected: str) -> None:
    assert canonical_technology_key(raw) == expected
