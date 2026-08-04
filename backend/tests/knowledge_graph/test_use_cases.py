"""The graph's use cases, tested against fakes.

No database, no event bus, no provider. If any of these needed one, the
Clean Architecture boundary would have leaked — so the absence of
infrastructure here is itself part of what is being asserted.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

import pytest

from modules.knowledge_graph.application.queries import AccountIdentity, ClaimSet, GraphQueries
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
    IdentityBinding,
    IdentityState,
)
from modules.knowledge_graph.public import MatchStrength
from modules.provider_normalization.public import ClaimAttribute, ClaimView
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
        assert publisher.types() == [
            "entity.created",
            "entity.identity_bound",
            "entity.evidence_attached",
        ]

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
        assert publisher.types() == ["entity.identity_bound", "entity.evidence_attached"]

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
        # The identity did not change, but the evidence is still new — and
        # announcing it is the whole reason `entity.evidence_attached`
        # exists. A consumer watching only for identity changes would never
        # see a nightly re-sync's claims, which is most of the evidence the
        # pipeline ever receives.
        assert publisher.types() == ["entity.evidence_attached"]

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
        assert publisher.types() == ["entity.identity_bound", "entity.evidence_attached"]

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


class TestHowCurrentTheEvidenceIs:
    """*"How old is what I am looking at?"* — A4.

    A seller reading a score has no way to tell *"nothing is happening here"*
    from *"nothing has reached us since March"*, and those demand opposite
    actions. These assert the answer is the newest thing known about the
    **account**, not about its name.
    """

    def _entity_with(self, *bindings: tuple[str, str]) -> tuple[FakeGraphRepository, Entity]:
        repository = FakeGraphRepository()
        entity = Entity.create(workspace_id=WORKSPACE, kind=EntityKind.COMPANY, now=NOW)
        repository.entities[entity.id] = entity
        for provider, external_id in bindings:
            repository.bindings.append(
                bound_binding(
                    entity, provider=provider, external_id=external_id, domain="acme.example"
                )
            )
        return repository, entity

    async def _identity(
        self, repository: FakeGraphRepository, entity: Entity, claims: list[ClaimView]
    ) -> AccountIdentity:
        queries = GraphQueries(repository=repository, claims=FakeClaimReader(claims))
        return (await queries.identities(WORKSPACE, (entity.id,)))[entity.id]

    async def test_it_reports_the_newest_evidence_of_any_kind(self) -> None:
        """**Not the newest *name*.** A company's legal name is claimed once
        and almost never again, so an identity dated by its name would tell a
        seller *"March"* about an account somebody read headcount for this
        morning — the exact false alarm this line exists to prevent.
        """
        repository, entity = self._entity_with(("apollo", "acme-corp"))

        identity = await self._identity(
            repository,
            entity,
            [
                claim(
                    attribute=ClaimAttribute.LEGAL_NAME,
                    value="Acme Corp",
                    observed_at=datetime(2026, 1, 5, tzinfo=UTC),
                ),
                claim(
                    attribute=ClaimAttribute.EMPLOYEE_COUNT,
                    observed_at=datetime(2026, 7, 20, tzinfo=UTC),
                ),
            ],
        )

        assert identity.last_observed_at == datetime(2026, 7, 20, tzinfo=UTC)
        assert identity.observed_at == datetime(2026, 1, 5, tzinfo=UTC)

    async def test_the_provider_that_looked_most_recently_wins(self) -> None:
        """Two sources reading the same company is the ordinary case, and
        *"how current is this?"* is answered by whichever looked last — not
        by whichever the name happened to come from."""
        repository, entity = self._entity_with(("apollo", "acme-corp"), ("coresignal", "acme-cs"))

        identity = await self._identity(
            repository,
            entity,
            [
                claim(provider="apollo", observed_at=datetime(2026, 2, 1, tzinfo=UTC)),
                claim(
                    provider="coresignal",
                    external_id="acme-cs",
                    observed_at=datetime(2026, 6, 1, tzinfo=UTC),
                ),
            ],
        )

        assert identity.last_observed_at == datetime(2026, 6, 1, tzinfo=UTC)

    async def test_an_account_nobody_has_reported_on_says_so_with_absence(self) -> None:
        """**Absent, never epoch zero and never `now`.** Either substitute
        would be a claim Signora cannot support, and the screen renders this
        as *"No evidence collected yet"* — which is the answer that should
        stop a seller trusting the score above it."""
        repository, entity = self._entity_with(("apollo", "acme-corp"))

        identity = await self._identity(repository, entity, [])

        assert identity.last_observed_at is None

    async def test_another_accounts_evidence_does_not_make_this_one_look_fresh(self) -> None:
        """The failure that would be invisible on screen: a page full of
        accounts all reporting the freshest reading in the workspace."""
        repository, entity = self._entity_with(("apollo", "acme-corp"))

        identity = await self._identity(
            repository,
            entity,
            [
                claim(observed_at=datetime(2026, 2, 1, tzinfo=UTC)),
                claim(external_id="globex", observed_at=datetime(2026, 9, 1, tzinfo=UTC)),
            ],
        )

        assert identity.last_observed_at == datetime(2026, 2, 1, tzinfo=UTC)


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


class TestFindingAnAccountByName:
    """*"Show me Databricks."* — A1, and the question a ranked list cannot answer.

    These state what a customer would notice, and one thing they would not
    notice until it cost them: that a blank box does not return the whole
    workspace.
    """

    def _named(self, *names: tuple[str, str, str]) -> tuple[FakeGraphRepository, dict[str, UUID]]:
        """`(provider, external_id, legal_name)` per source, one entity each."""
        repository = FakeGraphRepository()
        claims: list[ClaimView] = []
        ids: dict[str, UUID] = {}
        for provider, external_id, legal_name in names:
            entity = Entity.create(workspace_id=WORKSPACE, kind=EntityKind.COMPANY, now=NOW)
            repository.entities[entity.id] = entity
            repository.bindings.append(
                bound_binding(
                    entity, provider=provider, external_id=external_id, domain=f"{external_id}.example"
                )
            )
            ids[legal_name] = entity.id
            claims.append(
                claim(
                    provider=provider,
                    external_id=external_id,
                    attribute=ClaimAttribute.LEGAL_NAME,
                    value=legal_name,
                )
            )
        self._claims = claims
        return repository, ids

    def _queries(self, repository: FakeGraphRepository) -> GraphQueries:
        return GraphQueries(repository=repository, claims=FakeClaimReader(self._claims))

    async def test_a_partial_name_reaches_the_account(self) -> None:
        repository, ids = self._named(("apollo", "dbx", "Databricks, Inc."))

        found = await self._queries(repository).find_accounts(WORKSPACE, "databr", limit=10)

        assert [identity.entity_id for identity in found] == [ids["Databricks, Inc."]]
        assert found[0].name == "Databricks, Inc."

    async def test_a_company_is_found_under_the_name_it_used_to_have(self) -> None:
        """**The behaviour, not a defect.** Matching claims rather than the
        displayed name means the old name still finds it — which is exactly
        what somebody who has not heard about the rename types. The result is
        then shown under the *current* name, so nobody is misled about what it
        is called today."""
        repository, ids = self._named(("apollo", "nw", "Northwind Traders"))
        self._claims.append(
            claim(
                provider="apollo",
                external_id="nw",
                attribute=ClaimAttribute.LEGAL_NAME,
                value="Northwind Group",
                observed_at=datetime(2026, 6, 1, tzinfo=UTC),
            )
        )

        found = await self._queries(repository).find_accounts(WORKSPACE, "Traders", limit=10)

        assert [identity.entity_id for identity in found] == [ids["Northwind Traders"]]
        assert found[0].name == "Northwind Group", "shown under what it is called now"

    async def test_a_blank_search_finds_nothing_rather_than_everything(self) -> None:
        """**The failure that would look like a feature.** An empty pattern
        matches every claim in the workspace, so a search box that sent one on
        the first keystroke would dump the customer's whole book of business
        and call it a result."""
        repository, _ = self._named(("apollo", "dbx", "Databricks, Inc."))
        queries = self._queries(repository)

        assert await queries.find_accounts(WORKSPACE, "", limit=10) == ()
        assert await queries.find_accounts(WORKSPACE, "   ", limit=10) == ()

    async def test_no_match_is_an_empty_answer_not_an_error(self) -> None:
        repository, _ = self._named(("apollo", "dbx", "Databricks, Inc."))

        assert await self._queries(repository).find_accounts(WORKSPACE, "zzz", limit=10) == ()

    async def test_two_sources_naming_one_company_return_it_once(self) -> None:
        """A match is found per *identity*; a customer is looking for an
        account. Two providers on one company is the ordinary case and must
        not read as two search results."""
        repository = FakeGraphRepository()
        entity = Entity.create(workspace_id=WORKSPACE, kind=EntityKind.COMPANY, now=NOW)
        repository.entities[entity.id] = entity
        for provider, external_id in (("apollo", "acme-a"), ("coresignal", "acme-c")):
            repository.bindings.append(
                bound_binding(entity, provider=provider, external_id=external_id, domain="acme.example")
            )
        self._claims = [
            claim(
                provider=provider,
                external_id=external_id,
                attribute=ClaimAttribute.LEGAL_NAME,
                value="Acme Corporation",
            )
            for provider, external_id in (("apollo", "acme-a"), ("coresignal", "acme-c"))
        ]

        found = await self._queries(repository).find_accounts(WORKSPACE, "acme", limit=10)

        assert [identity.entity_id for identity in found] == [entity.id]

    async def test_an_identity_that_resolved_to_nothing_is_not_a_result(self) -> None:
        """An ambiguous identity binds to no entity, so there is no account to
        send anybody to. Inventing one would be the merge this module exists
        to refuse."""
        repository = FakeGraphRepository()
        entity = Entity.create(workspace_id=WORKSPACE, kind=EntityKind.COMPANY, now=NOW)
        repository.entities[entity.id] = entity
        repository.bindings.append(
            IdentityBinding(
                id=uuid4(),
                workspace_id=WORKSPACE,
                provider="apollo",
                provider_external_id="ambiguous",
                state=IdentityState.AMBIGUOUS,
                entity_id=None,
                decision_id=uuid4(),
                created_at=NOW,
            )
        )
        self._claims = [
            claim(
                provider="apollo",
                external_id="ambiguous",
                attribute=ClaimAttribute.LEGAL_NAME,
                value="Acme Corporation",
            )
        ]

        assert await self._queries(repository).find_accounts(WORKSPACE, "acme", limit=10) == ()
