"""The buying committee's own rules, with no database and no HTTP.

These assert that the only judgements the module makes are about the
*statement* — that a committee has a seat in it, that two seats are tellable
apart, that it names a product the workspace sells — and never about a person,
a company or a deal. **Nothing here evaluates a committee**, and the last
class asserts there is no way it could.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from modules.commercial_profile.application.declare_committee import (
    CommitteeVersionConflictError,
    DeclareBuyingCommittee,
    DeclareBuyingCommitteeInput,
)
from modules.commercial_profile.application.declaring import (
    CommitteeUnknownProductError,
)
from modules.commercial_profile.domain.catalog import Product, ProductCatalog, first_catalog
from modules.commercial_profile.domain.committee import (
    BuyingCommittee,
    BuyingCommitteeError,
    CommitteePart,
    CommitteeRole,
    MAX_ROLES,
    MAX_TITLE,
    ProductCommittee,
    SEAT_NAMESPACE,
    first_committee,
    seat_id,
)

WORKSPACE = UUID("11111111-1111-4111-8111-111111111111")
ACTOR = UUID("22222222-2222-4222-8222-222222222222")
CORE = UUID("33333333-3333-4333-8333-333333333333")
ENTERPRISE = UUID("44444444-4444-4444-8444-444444444444")
NOW = datetime(2026, 8, 1, tzinfo=UTC)


def _role(
    title: str = "VP of Revenue Operations",
    part: CommitteePart = CommitteePart.ECONOMIC_BUYER,
) -> CommitteeRole:
    return CommitteeRole(title=title, part=part)


def _committee(product_id: UUID = CORE, *roles: CommitteeRole) -> ProductCommittee:
    return ProductCommittee(product_id=product_id, roles=roles or (_role(),))


def _declaration(*committees: ProductCommittee) -> BuyingCommittee:
    return first_committee(WORKSPACE, committees, id=uuid4(), by=ACTOR, now=NOW)


class FakeCommitteeRepository:
    def __init__(self, stored: BuyingCommittee | None = None) -> None:
        self.stored = stored
        self.saved: list[BuyingCommittee] = []

    async def current(self, workspace_id: UUID) -> BuyingCommittee | None:
        return self.stored

    async def save(self, committee: BuyingCommittee) -> None:
        self.saved.append(committee)
        self.stored = committee


class FakeCatalogRepository:
    def __init__(self, *product_ids: UUID) -> None:
        self.stored: ProductCatalog | None = (
            first_catalog(
                WORKSPACE,
                tuple(Product(id=pid, name=str(pid)) for pid in product_ids),
                id=uuid4(),
                by=ACTOR,
                now=NOW,
            )
            if product_ids
            else None
        )

    async def current(self, workspace_id: UUID) -> ProductCatalog | None:
        return self.stored

    async def save(self, catalog: ProductCatalog) -> None:  # pragma: no cover
        raise AssertionError("declaring a committee must never write the catalog")


def _declare(
    committees: FakeCommitteeRepository, catalog: FakeCatalogRepository
) -> DeclareBuyingCommittee:
    return DeclareBuyingCommittee(committees=committees, catalog=catalog)


class TestARoleIsATitleAndAPart:
    def test_it_needs_a_title(self) -> None:
        with pytest.raises(BuyingCommitteeError, match="needs a title"):
            _role(title="   ")

    def test_a_title_has_a_limit(self) -> None:
        with pytest.raises(BuyingCommitteeError, match=f"{MAX_TITLE} characters"):
            _role(title="x" * (MAX_TITLE + 1))

    def test_the_title_is_the_customer_s_words(self) -> None:
        # Not a taxonomy to translate into. "Head of Clinical Informatics" is
        # the answer for one customer and meaningless to every other.
        assert _role("Head of Clinical Informatics").title == ("Head of Clinical Informatics")

    def test_the_five_parts_are_the_whole_vocabulary(self) -> None:
        # **Owned here, answering to no provider.** If this grows it is an
        # ordinary change to this module — but a sixth value should have to
        # justify itself against the sentence a seller would actually say.
        assert {part.value for part in CommitteePart} == {
            "economic_buyer",
            "champion",
            "evaluator",
            "user",
            "gatekeeper",
        }


class TestACommitteeHasToHaveSomebodyInIt:
    def test_one_role_is_enough(self) -> None:
        # The first thing a customer types is rarely the whole committee.
        assert len(_committee().roles) == 1

    def test_an_empty_committee_is_refused(self) -> None:
        # **The one judgement here, and it is about the statement.** It says
        # nothing that leaving the product out does not say already.
        with pytest.raises(BuyingCommitteeError, match="at least one role"):
            ProductCommittee(product_id=CORE, roles=())

    def test_a_committee_has_an_upper_bound(self) -> None:
        with pytest.raises(BuyingCommitteeError, match=f"{MAX_ROLES} roles"):
            _committee(CORE, *[_role(title=f"Role {n}") for n in range(MAX_ROLES + 1)])

    def test_two_roles_cannot_share_a_title(self) -> None:
        with pytest.raises(BuyingCommitteeError, match="share a title"):
            _committee(CORE, _role("CFO"), _role("cfo", CommitteePart.GATEKEEPER))

    def test_the_same_title_may_not_differ_only_by_case_or_padding(self) -> None:
        with pytest.raises(BuyingCommitteeError, match="share a title"):
            _committee(CORE, _role("CFO"), _role("  cfo  "))

    def test_two_roles_may_share_a_part(self) -> None:
        # Two gatekeepers — security and legal — is the ordinary case, not a
        # mistake. Only the title has to be distinguishable.
        committee = _committee(
            CORE,
            _role("Head of Security", CommitteePart.GATEKEEPER),
            _role("General Counsel", CommitteePart.GATEKEEPER),
        )

        assert len(committee.roles) == 2


class TestOneProductHasOneCommittee:
    def test_two_committees_for_one_product_are_refused(self) -> None:
        with pytest.raises(BuyingCommitteeError, match="two committees"):
            _declaration(_committee(CORE), _committee(CORE))

    def test_different_products_may_decide_differently(self) -> None:
        declaration = _declaration(_committee(CORE), _committee(ENTERPRISE))

        assert len(declaration.committees) == 2

    def test_declaring_no_committees_is_a_legal_statement(self) -> None:
        # "We no longer describe a committee for anything" has an author and
        # a moment, which is what makes it different from never having said
        # anything.
        assert _declaration().committees == ()


class TestARevisionSupersedesRatherThanEdits:
    def test_it_mints_the_next_version(self) -> None:
        first = _declaration(_committee())

        second = first.revise((_committee(ENTERPRISE),), id=uuid4(), by=ACTOR, now=NOW)

        assert (first.version, second.version) == (1, 2)
        assert second.supersedes == first.id

    def test_the_previous_version_is_unchanged(self) -> None:
        first = _declaration(_committee())

        first.revise((), id=uuid4(), by=ACTOR, now=NOW)

        assert len(first.committees) == 1

    def test_an_invalid_revision_never_exists(self) -> None:
        first = _declaration(_committee())

        with pytest.raises(BuyingCommitteeError):
            first.revise((_committee(CORE), _committee(CORE)), id=uuid4(), by=ACTOR, now=NOW)

    def test_a_stored_declaration_starts_at_version_one(self) -> None:
        with pytest.raises(BuyingCommitteeError, match="version 1 or above"):
            BuyingCommittee(
                id=uuid4(),
                workspace_id=WORKSPACE,
                version=0,
                committees=(),
                created_at=NOW,
                created_by=ACTOR,
            )


class TestDeclaring:
    async def test_the_first_declaration_supersedes_nothing(self) -> None:
        committees = FakeCommitteeRepository()

        declaration = await _declare(committees, FakeCatalogRepository(CORE)).execute(
            DeclareBuyingCommitteeInput(
                workspace_id=WORKSPACE,
                committees=(_committee(),),
                expected_version=0,
                actor_id=ACTOR,
            )
        )

        assert (declaration.version, declaration.supersedes) == (1, None)

    async def test_it_records_who_declared_it(self) -> None:
        committees = FakeCommitteeRepository()

        declaration = await _declare(committees, FakeCatalogRepository(CORE)).execute(
            DeclareBuyingCommitteeInput(
                workspace_id=WORKSPACE,
                committees=(),
                expected_version=0,
                actor_id=ACTOR,
            )
        )

        assert declaration.created_by == ACTOR

    async def test_a_concurrent_edit_is_refused_rather_than_overwritten(self) -> None:
        committees = FakeCommitteeRepository(_declaration(_committee()))

        with pytest.raises(CommitteeVersionConflictError) as refusal:
            await _declare(committees, FakeCatalogRepository(CORE)).execute(
                DeclareBuyingCommitteeInput(
                    workspace_id=WORKSPACE,
                    committees=(_committee(CORE, _role("CFO")),),
                    expected_version=0,
                    actor_id=ACTOR,
                )
            )

        assert (refusal.value.expected, refusal.value.actual) == (0, 1)
        assert committees.saved == [], "a refused declaration must write nothing"

    async def test_the_refusal_says_what_to_do(self) -> None:
        committees = FakeCommitteeRepository(_declaration())

        with pytest.raises(CommitteeVersionConflictError, match="reload"):
            await _declare(committees, FakeCatalogRepository(CORE)).execute(
                DeclareBuyingCommitteeInput(
                    workspace_id=WORKSPACE,
                    committees=(),
                    expected_version=99,
                    actor_id=ACTOR,
                )
            )


class TestACommitteeMustNameAProductTheWorkspaceSells:
    async def test_an_unknown_product_is_refused(self) -> None:
        committees = FakeCommitteeRepository()

        with pytest.raises(CommitteeUnknownProductError, match="describe who decides about"):
            await _declare(committees, FakeCatalogRepository(CORE)).execute(
                DeclareBuyingCommitteeInput(
                    workspace_id=WORKSPACE,
                    committees=(_committee(ENTERPRISE),),
                    expected_version=0,
                    actor_id=ACTOR,
                )
            )

        assert committees.saved == []

    async def test_the_refusal_names_the_page_it_is_fixed_on(self) -> None:
        # The shared check, distinct refusals: a customer fixing a committee
        # and one fixing an ideal customer are looking at different pages.
        committees = FakeCommitteeRepository()

        with pytest.raises(CommitteeUnknownProductError, match="Add it under Products"):
            await _declare(committees, FakeCatalogRepository()).execute(
                DeclareBuyingCommitteeInput(
                    workspace_id=WORKSPACE,
                    committees=(_committee(),),
                    expected_version=0,
                    actor_id=ACTOR,
                )
            )

    async def test_an_empty_declaration_is_accepted_with_no_catalog(self) -> None:
        # Nothing to dangle.
        committees = FakeCommitteeRepository()

        declaration = await _declare(committees, FakeCatalogRepository()).execute(
            DeclareBuyingCommitteeInput(
                workspace_id=WORKSPACE,
                committees=(),
                expected_version=0,
                actor_id=ACTOR,
            )
        )

        assert declaration.committees == ()

    async def test_a_stale_version_is_reported_before_a_stale_product(self) -> None:
        committees = FakeCommitteeRepository(_declaration())

        with pytest.raises(CommitteeVersionConflictError):
            await _declare(committees, FakeCatalogRepository()).execute(
                DeclareBuyingCommitteeInput(
                    workspace_id=WORKSPACE,
                    committees=(_committee(ENTERPRISE),),
                    expected_version=0,
                    actor_id=ACTOR,
                )
            )


class TestItEvaluatesNobody:
    def test_a_role_carries_no_measure_of_influence(self) -> None:
        # **The field that would turn a declaration into a scoring input.**
        # Asserted on the dataclass rather than trusted to review: a weight,
        # a seniority band or an importance would each make this module hold
        # a judgement about a real deal.
        assert CommitteeRole.__dataclass_fields__.keys() == {"title", "part"}

    def test_a_committee_offers_no_way_to_assess_itself(self) -> None:
        # No `is_complete`, no `coverage`, no `strength`. Whether a committee
        # is missing somebody is a conclusion about a company, and this
        # module has no evidence to reach one from.
        assert [name for name in dir(ProductCommittee) if not name.startswith("_")] == [
            "product_id",
            "roles",
        ]


class TestASeatCanBeCited:
    """**TASK-428 is the consumer the docstring named as the trigger** — a
    committee seat citing a real affiliation — so a seat now has an id.

    Every test here is about the one property that matters: **the same seat
    answers the same id, everywhere and forever**, including for declarations
    written before the field existed.
    """

    def test_the_same_product_and_title_always_give_the_same_id(self) -> None:
        product = uuid4()

        assert seat_id(product, "CFO") == seat_id(product, "CFO")

    def test_it_is_derived_rather_than_stored_so_an_old_declaration_has_one(self) -> None:
        """**The reason the design is a derivation.**

        Every declaration on disk is immutable and none carries an identifier,
        so a minted id could only ever have been assigned going forward. A
        role parsed from a July row answers the same as one built today.
        """
        product = uuid4()
        parsed_from_storage = CommitteeRole(title="CFO", part=CommitteePart.ECONOMIC_BUYER)

        assert parsed_from_storage.seat_id(product) == seat_id(product, "CFO")

    def test_two_products_do_not_share_a_seat(self) -> None:
        assert seat_id(uuid4(), "CFO") != seat_id(uuid4(), "CFO")

    def test_two_seats_on_one_product_differ(self) -> None:
        product = uuid4()

        assert seat_id(product, "CFO") != seat_id(product, "CTO")

    def test_retyping_a_title_differently_cites_the_same_seat(self) -> None:
        """Case and surrounding space are folded, so a customer who retypes a
        title is not creating a second seat."""
        product = uuid4()

        assert seat_id(product, "  chief   financial officer ") == seat_id(
            product, "Chief Financial Officer"
        )

    def test_a_rename_mints_a_new_identity_and_that_is_the_stated_limitation(self) -> None:
        """⚠️ **Asserted rather than left in prose**, because it is the one
        thing a consumer must know: carrying identity across a rename needs
        somebody to say *"same seat, renamed"*, and no editing surface exists
        to say it."""
        product = uuid4()

        assert seat_id(product, "VP Finance") != seat_id(product, "CFO")

    def test_the_namespace_is_pinned(self) -> None:
        """**Changing it re-identifies every seat in every workspace.** A test
        so that a change is a decision rather than an edit."""
        assert str(SEAT_NAMESPACE) == "6f8d2c41-9a3e-5b07-8c14-2d9f7e0a5b63"
