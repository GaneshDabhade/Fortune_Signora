"""The ideal customer's own rules, with no database and no HTTP.

These assert that the only judgements the module makes are about the
*statement* — that a description says something, that a size range is a range,
that a profile names a product the workspace actually sells — and never about
a company. Nothing here matches anybody against anything, and there is no
method that could.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from modules.commercial_profile.application.declare_icp import (
    DeclareIcp,
    DeclareIcpInput,
    IcpVersionConflictError,
    UnknownProductError,
)
from modules.commercial_profile.domain.catalog import (
    Product,
    ProductCatalog,
    first_catalog,
)
from modules.commercial_profile.domain.icp import (
    MAX_CRITERIA,
    MAX_CRITERION,
    MAX_EMPLOYEES,
    MAX_NOTES,
    EmployeeRange,
    IcpDeclaration,
    IcpError,
    ProductIcp,
    first_declaration,
)

WORKSPACE = UUID("11111111-1111-4111-8111-111111111111")
ACTOR = UUID("22222222-2222-4222-8222-222222222222")
CORE = UUID("33333333-3333-4333-8333-333333333333")
ENTERPRISE = UUID("44444444-4444-4444-8444-444444444444")
NOW = datetime(2026, 8, 1, tzinfo=UTC)


def _profile(product_id: UUID = CORE, **overrides: object) -> ProductIcp:
    stated: dict[str, object] = {"industries": ("Financial services",)}
    stated.update(overrides)
    return ProductIcp(product_id=product_id, **stated)  # type: ignore[arg-type]


def _declaration(*profiles: ProductIcp) -> IcpDeclaration:
    return first_declaration(WORKSPACE, profiles, id=uuid4(), by=ACTOR, now=NOW)


class FakeIcpRepository:
    def __init__(self, stored: IcpDeclaration | None = None) -> None:
        self.stored = stored
        self.saved: list[IcpDeclaration] = []

    async def current(self, workspace_id: UUID) -> IcpDeclaration | None:
        return self.stored

    async def save(self, declaration: IcpDeclaration) -> None:
        self.saved.append(declaration)
        self.stored = declaration


class FakeCatalogRepository:
    """The catalog as the ICP use case sees it — one method, read-only."""

    def __init__(self, *product_ids: UUID) -> None:
        self.stored: ProductCatalog | None = (
            first_catalog(
                WORKSPACE,
                tuple(Product(id=product_id, name=str(product_id)) for product_id in product_ids),
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
        raise AssertionError("declaring an ideal customer must never write the catalog")


def _declare(declarations: FakeIcpRepository, catalog: FakeCatalogRepository) -> DeclareIcp:
    return DeclareIcp(declarations=declarations, catalog=catalog)


class TestADescriptionHasToDescribeSomething:
    def test_one_criterion_is_enough(self) -> None:
        # "Anyone in fintech" is a real answer, and the first thing a customer
        # types is rarely their whole ICP.
        assert _profile().industries == ("Financial services",)

    def test_a_description_with_no_criteria_is_refused(self) -> None:
        # **The one judgement this module makes about a statement.** A profile
        # with nothing in it would describe every company on earth, which is
        # the one thing the customer cannot have meant — and it is
        # indistinguishable from leaving the product out, which they can
        # already do.
        with pytest.raises(IcpError, match="at least one thing"):
            ProductIcp(product_id=CORE)

    def test_size_alone_is_a_description(self) -> None:
        assert _profile(industries=(), employees=EmployeeRange(minimum=200)) is not None

    def test_a_note_alone_is_not(self) -> None:
        # Notes are for a colleague, never parsed. A profile that says only
        # "the usual suspects" narrows nothing a machine can act on.
        with pytest.raises(IcpError, match="at least one thing"):
            ProductIcp(product_id=CORE, notes="the usual suspects")


class TestWhatTheCustomerTypedIsWhatIsStored:
    def test_capitalisation_and_spacing_survive(self) -> None:
        # A module that records has no business tidying somebody's words.
        stated = _profile(industries=("  Financial Services  ", "SaaS"))

        assert stated.industries == ("  Financial Services  ", "SaaS")

    def test_the_same_industry_twice_is_refused(self) -> None:
        with pytest.raises(IcpError, match="same industry is listed twice"):
            _profile(industries=("Fintech", " fintech "))

    def test_the_same_country_twice_is_refused(self) -> None:
        with pytest.raises(IcpError, match="same country is listed twice"):
            _profile(industries=(), countries=("United States", "united states"))

    def test_a_blank_entry_is_refused(self) -> None:
        with pytest.raises(IcpError, match="says nothing"):
            _profile(industries=("Fintech", "   "))

    def test_an_entry_has_a_length_limit(self) -> None:
        with pytest.raises(IcpError, match=f"{MAX_CRITERION} characters"):
            _profile(industries=("x" * (MAX_CRITERION + 1),))

    def test_the_list_has_a_length_limit(self) -> None:
        # Past two dozen the description has stopped narrowing anything, and
        # the field has become a place to paste a spreadsheet column.
        with pytest.raises(IcpError, match=f"{MAX_CRITERIA} industry"):
            _profile(industries=tuple(f"Industry {n}" for n in range(MAX_CRITERIA + 1)))

    def test_a_note_has_a_length_limit(self) -> None:
        with pytest.raises(IcpError, match=f"{MAX_NOTES} characters"):
            _profile(notes="x" * (MAX_NOTES + 1))


class TestSizeIsARangeOfPeople:
    def test_either_bound_may_be_left_out(self) -> None:
        # "Anything over 500" and "under 50" are both real answers.
        assert (
            EmployeeRange(minimum=500).maximum is None and EmployeeRange(maximum=50).minimum is None
        )

    def test_a_range_with_neither_bound_is_refused(self) -> None:
        # Having no size preference is said by leaving size out. A range that
        # constrains nothing would be a second way to say the same thing.
        with pytest.raises(IcpError, match="lower bound, an upper bound, or both"):
            EmployeeRange()

    def test_the_floor_cannot_be_above_the_ceiling(self) -> None:
        with pytest.raises(IcpError, match="cannot be larger than the largest"):
            EmployeeRange(minimum=5000, maximum=50)

    def test_a_negative_size_is_refused(self) -> None:
        with pytest.raises(IcpError, match="cannot be negative"):
            EmployeeRange(minimum=-1)

    def test_an_implausible_size_is_refused(self) -> None:
        # A typo guard, not a business rule — refused where somebody can still
        # see what they meant to type.
        with pytest.raises(IcpError, match="limited to"):
            EmployeeRange(maximum=MAX_EMPLOYEES + 1)

    def test_the_bounds_may_be_equal(self) -> None:
        assert EmployeeRange(minimum=500, maximum=500).minimum == 500


class TestOneProductHasOneIdealCustomer:
    def test_two_profiles_for_one_product_are_refused(self) -> None:
        # Two descriptions of who buys the same thing leave no answer to which
        # one it has.
        with pytest.raises(IcpError, match="described twice"):
            _declaration(_profile(CORE), _profile(CORE, countries=("US",)))

    def test_different_products_may_be_described_differently(self) -> None:
        declaration = _declaration(
            _profile(CORE), _profile(ENTERPRISE, employees=EmployeeRange(minimum=5000))
        )

        assert len(declaration.profiles) == 2

    def test_describing_nobody_is_a_legal_statement(self) -> None:
        # "We no longer describe an ideal customer for anything" has an author
        # and a moment, which is what makes it different from never having
        # said anything.
        assert _declaration().profiles == ()


class TestARevisionSupersedesRatherThanEdits:
    def test_it_mints_the_next_version(self) -> None:
        first = _declaration(_profile())

        second = first.revise((_profile(ENTERPRISE),), id=uuid4(), by=ACTOR, now=NOW)

        assert (first.version, second.version) == (1, 2)
        assert second.supersedes == first.id

    def test_the_previous_version_is_unchanged(self) -> None:
        first = _declaration(_profile())

        first.revise((), id=uuid4(), by=ACTOR, now=NOW)

        assert len(first.profiles) == 1

    def test_an_invalid_revision_never_exists(self) -> None:
        first = _declaration(_profile())

        with pytest.raises(IcpError):
            first.revise((_profile(CORE), _profile(CORE)), id=uuid4(), by=ACTOR, now=NOW)

    def test_a_stored_declaration_starts_at_version_one(self) -> None:
        with pytest.raises(IcpError, match="version 1 or above"):
            IcpDeclaration(
                id=uuid4(),
                workspace_id=WORKSPACE,
                version=0,
                profiles=(),
                created_at=NOW,
                created_by=ACTOR,
            )


class TestDeclaring:
    async def test_the_first_declaration_supersedes_nothing(self) -> None:
        declarations = FakeIcpRepository()

        declaration = await _declare(declarations, FakeCatalogRepository(CORE)).execute(
            DeclareIcpInput(
                workspace_id=WORKSPACE,
                profiles=(_profile(),),
                expected_version=0,
                actor_id=ACTOR,
            )
        )

        assert (declaration.version, declaration.supersedes) == (1, None)

    async def test_it_records_who_described_them(self) -> None:
        declarations = FakeIcpRepository()

        declaration = await _declare(declarations, FakeCatalogRepository(CORE)).execute(
            DeclareIcpInput(
                workspace_id=WORKSPACE,
                profiles=(_profile(),),
                expected_version=0,
                actor_id=ACTOR,
            )
        )

        assert declaration.created_by == ACTOR

    async def test_a_concurrent_edit_is_refused_rather_than_overwritten(self) -> None:
        declarations = FakeIcpRepository(_declaration(_profile()))

        with pytest.raises(IcpVersionConflictError) as refusal:
            await _declare(declarations, FakeCatalogRepository(CORE)).execute(
                DeclareIcpInput(
                    workspace_id=WORKSPACE,
                    profiles=(_profile(countries=("US",)),),
                    expected_version=0,
                    actor_id=ACTOR,
                )
            )

        assert (refusal.value.expected, refusal.value.actual) == (0, 1)
        assert declarations.saved == [], "a refused declaration must write nothing"

    async def test_the_refusal_says_what_to_do(self) -> None:
        declarations = FakeIcpRepository(_declaration())

        with pytest.raises(IcpVersionConflictError, match="reload"):
            await _declare(declarations, FakeCatalogRepository(CORE)).execute(
                DeclareIcpInput(
                    workspace_id=WORKSPACE,
                    profiles=(),
                    expected_version=99,
                    actor_id=ACTOR,
                )
            )


class TestAProfileMustNameAProductTheWorkspaceSells:
    async def test_an_unknown_product_is_refused(self) -> None:
        # The reference would resolve to nothing — a dangling citation, in the
        # module whose whole job is being citable later.
        declarations = FakeIcpRepository()

        with pytest.raises(UnknownProductError, match="Add it under Products first"):
            await _declare(declarations, FakeCatalogRepository(CORE)).execute(
                DeclareIcpInput(
                    workspace_id=WORKSPACE,
                    profiles=(_profile(ENTERPRISE),),
                    expected_version=0,
                    actor_id=ACTOR,
                )
            )

        assert declarations.saved == []

    async def test_a_workspace_with_no_catalog_can_describe_nobody(self) -> None:
        declarations = FakeIcpRepository()

        with pytest.raises(UnknownProductError):
            await _declare(declarations, FakeCatalogRepository()).execute(
                DeclareIcpInput(
                    workspace_id=WORKSPACE,
                    profiles=(_profile(),),
                    expected_version=0,
                    actor_id=ACTOR,
                )
            )

    async def test_an_empty_declaration_is_accepted_with_no_catalog(self) -> None:
        # Nothing to dangle. Refusing this would mean a workspace could not
        # state that it describes nobody until it had declared a product.
        declarations = FakeIcpRepository()

        declaration = await _declare(declarations, FakeCatalogRepository()).execute(
            DeclareIcpInput(
                workspace_id=WORKSPACE,
                profiles=(),
                expected_version=0,
                actor_id=ACTOR,
            )
        )

        assert declaration.profiles == ()

    async def test_a_stale_version_is_reported_before_a_stale_product(self) -> None:
        # **Order matters to the reader.** A caller whose version is stale has
        # a stale product list too, so naming the product would send them to
        # fix the wrong page.
        declarations = FakeIcpRepository(_declaration())

        with pytest.raises(IcpVersionConflictError):
            await _declare(declarations, FakeCatalogRepository()).execute(
                DeclareIcpInput(
                    workspace_id=WORKSPACE,
                    profiles=(_profile(ENTERPRISE),),
                    expected_version=0,
                    actor_id=ACTOR,
                )
            )
