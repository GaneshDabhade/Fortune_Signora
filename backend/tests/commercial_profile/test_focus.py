"""The focus's own rules, with no database and no HTTP.

These assert that the module records a statement of intent and **applies it to
nothing** — and, more specifically than in the other three aggregates, that it
carries no ordinal. A rank here is the number a downstream consumer would
multiply by something, and the roadmap's own word for this capability
(*business priorities*) is the reason to check rather than assume.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from modules.commercial_profile.application.declare_focus import (
    DeclareFocus,
    DeclareFocusInput,
    FocusVersionConflictError,
)
from modules.commercial_profile.application.declaring import FocusUnknownProductError
from modules.commercial_profile.domain.catalog import (
    Product,
    ProductCatalog,
    first_catalog,
)
from modules.commercial_profile.domain.focus import (
    MAX_OBJECTIVE,
    CommercialFocus,
    CommercialFocusError,
    first_focus,
)

WORKSPACE = UUID("11111111-1111-4111-8111-111111111111")
ACTOR = UUID("22222222-2222-4222-8222-222222222222")
CORE = UUID("33333333-3333-4333-8333-333333333333")
ENTERPRISE = UUID("44444444-4444-4444-8444-444444444444")
NOW = datetime(2026, 8, 1, tzinfo=UTC)


def _focus(*products: UUID, objective: str = "Land three health systems") -> CommercialFocus:
    return first_focus(WORKSPACE, products, objective, id=uuid4(), by=ACTOR, now=NOW)


class FakeFocusRepository:
    def __init__(self, stored: CommercialFocus | None = None) -> None:
        self.stored = stored
        self.saved: list[CommercialFocus] = []

    async def current(self, workspace_id: UUID) -> CommercialFocus | None:
        return self.stored

    async def save(self, focus: CommercialFocus) -> None:
        self.saved.append(focus)
        self.stored = focus


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
        raise AssertionError("declaring a focus must never write the catalog")


def _declare(focuses: FakeFocusRepository, catalog: FakeCatalogRepository) -> DeclareFocus:
    return DeclareFocus(focuses=focuses, catalog=catalog)


class TestAFocusIsAStatementOfIntent:
    def test_it_names_the_products_being_pushed(self) -> None:
        assert _focus(CORE, ENTERPRISE).products == (CORE, ENTERPRISE)

    def test_the_objective_is_the_customer_s_words(self) -> None:
        assert _focus(CORE).objective == "Land three health systems"

    def test_an_objective_is_optional(self) -> None:
        assert _focus(CORE, objective="").objective == ""

    def test_an_objective_has_a_length_limit(self) -> None:
        with pytest.raises(CommercialFocusError, match=f"{MAX_OBJECTIVE} characters"):
            _focus(CORE, objective="x" * (MAX_OBJECTIVE + 1))

    def test_the_same_product_cannot_be_in_focus_twice(self) -> None:
        with pytest.raises(CommercialFocusError, match="in focus twice"):
            _focus(CORE, CORE)

    def test_an_empty_focus_is_legal(self) -> None:
        # **The one place this differs from the ideal customer**, deliberately.
        # There, an entry saying nothing was refused because leaving the
        # product out said the same thing. Here the aggregate *is* the
        # statement, so an empty one is how a customer retracts a focus — and
        # it has an author and a moment, which is what makes it different
        # from never having said anything.
        focus = _focus(objective="")

        assert (focus.products, focus.objective) == ((), "")


class TestItCarriesNoOrdinal:
    def test_a_focus_has_no_rank_or_position_field(self) -> None:
        # **The field the roadmap's own word invites.** *Business priorities*
        # suggests an ordering; a stored ordinal in the head of the pipeline
        # is one consumer away from a weight in a score, in the module
        # furthest from any evidence that would justify one.
        assert CommercialFocus.__dataclass_fields__.keys() == {
            "id",
            "workspace_id",
            "version",
            "products",
            "objective",
            "created_at",
            "created_by",
            "supersedes",
        }

    def test_reordering_the_same_products_is_the_same_statement(self) -> None:
        # Order is the customer's arrangement and carries no meaning, exactly
        # as in the ideal customer's criteria and the committee's roles.
        assert set(_focus(CORE, ENTERPRISE).products) == set(_focus(ENTERPRISE, CORE).products)


class TestARevisionSupersedesRatherThanEdits:
    def test_it_mints_the_next_version(self) -> None:
        first = _focus(CORE)

        second = first.revise((ENTERPRISE,), "Expand", id=uuid4(), by=ACTOR, now=NOW)

        assert (first.version, second.version) == (1, 2)
        assert second.supersedes == first.id

    def test_the_previous_version_is_unchanged(self) -> None:
        first = _focus(CORE)

        first.revise((), "", id=uuid4(), by=ACTOR, now=NOW)

        assert first.products == (CORE,)

    def test_an_invalid_revision_never_exists(self) -> None:
        first = _focus(CORE)

        with pytest.raises(CommercialFocusError):
            first.revise((CORE, CORE), "", id=uuid4(), by=ACTOR, now=NOW)

    def test_a_stored_focus_starts_at_version_one(self) -> None:
        with pytest.raises(CommercialFocusError, match="version 1 or above"):
            CommercialFocus(
                id=uuid4(),
                workspace_id=WORKSPACE,
                version=0,
                products=(),
                objective="",
                created_at=NOW,
                created_by=ACTOR,
            )


class TestDeclaring:
    async def test_the_first_focus_supersedes_nothing(self) -> None:
        focuses = FakeFocusRepository()

        focus = await _declare(focuses, FakeCatalogRepository(CORE)).execute(
            DeclareFocusInput(
                workspace_id=WORKSPACE,
                products=(CORE,),
                objective="Push Core",
                expected_version=0,
                actor_id=ACTOR,
            )
        )

        assert (focus.version, focus.supersedes) == (1, None)

    async def test_it_records_who_declared_it(self) -> None:
        focuses = FakeFocusRepository()

        focus = await _declare(focuses, FakeCatalogRepository()).execute(
            DeclareFocusInput(
                workspace_id=WORKSPACE,
                products=(),
                objective="",
                expected_version=0,
                actor_id=ACTOR,
            )
        )

        assert focus.created_by == ACTOR

    async def test_a_concurrent_edit_is_refused_rather_than_overwritten(self) -> None:
        focuses = FakeFocusRepository(_focus(CORE))

        with pytest.raises(FocusVersionConflictError) as refusal:
            await _declare(focuses, FakeCatalogRepository(CORE)).execute(
                DeclareFocusInput(
                    workspace_id=WORKSPACE,
                    products=(CORE,),
                    objective="Something else",
                    expected_version=0,
                    actor_id=ACTOR,
                )
            )

        assert (refusal.value.expected, refusal.value.actual) == (0, 1)
        assert focuses.saved == [], "a refused declaration must write nothing"

    async def test_the_refusal_says_what_to_do(self) -> None:
        focuses = FakeFocusRepository(_focus())

        with pytest.raises(FocusVersionConflictError, match="reload"):
            await _declare(focuses, FakeCatalogRepository()).execute(
                DeclareFocusInput(
                    workspace_id=WORKSPACE,
                    products=(),
                    objective="",
                    expected_version=99,
                    actor_id=ACTOR,
                )
            )


class TestAFocusMustNameProductsTheWorkspaceSells:
    async def test_an_unknown_product_is_refused(self) -> None:
        focuses = FakeFocusRepository()

        with pytest.raises(FocusUnknownProductError, match="focus on"):
            await _declare(focuses, FakeCatalogRepository(CORE)).execute(
                DeclareFocusInput(
                    workspace_id=WORKSPACE,
                    products=(ENTERPRISE,),
                    objective="",
                    expected_version=0,
                    actor_id=ACTOR,
                )
            )

        assert focuses.saved == []

    async def test_an_empty_focus_is_accepted_with_no_catalog(self) -> None:
        # Nothing to dangle. Refusing this would mean a workspace could not
        # state that it is pushing nothing until it had declared a product.
        focuses = FakeFocusRepository()

        focus = await _declare(focuses, FakeCatalogRepository()).execute(
            DeclareFocusInput(
                workspace_id=WORKSPACE,
                products=(),
                objective="Still working it out",
                expected_version=0,
                actor_id=ACTOR,
            )
        )

        assert focus.objective == "Still working it out"

    async def test_a_stale_version_is_reported_before_a_stale_product(self) -> None:
        focuses = FakeFocusRepository(_focus())

        with pytest.raises(FocusVersionConflictError):
            await _declare(focuses, FakeCatalogRepository()).execute(
                DeclareFocusInput(
                    workspace_id=WORKSPACE,
                    products=(ENTERPRISE,),
                    objective="",
                    expected_version=0,
                    actor_id=ACTOR,
                )
            )
