"""The catalog's own rules, with no database and no HTTP.

**The head of the pipeline records; it does not compute.** These assert that
the only judgements it makes are about the *statement* — that a product is
named, that two are distinguishable, that a revision supersedes rather than
edits — and never about the world.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from modules.commercial_profile.application.ports import ProductCatalogRepository
from modules.commercial_profile.application.publish import (
    CatalogVersionConflictError,
    PublishProductCatalog,
    PublishProductCatalogInput,
)
from modules.commercial_profile.domain.catalog import (
    MAX_NAME,
    Product,
    ProductCatalog,
    first_catalog,
)
from modules.commercial_profile.domain.declaration import CommercialProfileError

WORKSPACE = UUID("11111111-1111-4111-8111-111111111111")
ACTOR = UUID("22222222-2222-4222-8222-222222222222")
NOW = datetime(2026, 8, 1, tzinfo=UTC)


def _product(name: str = "Signora Core", **overrides: object) -> Product:
    return Product(id=overrides.pop("id", uuid4()), name=name, **overrides)  # type: ignore[arg-type]


def _catalog(*products: Product) -> ProductCatalog:
    return first_catalog(WORKSPACE, products, id=uuid4(), by=ACTOR, now=NOW)


class FakeCatalogRepository:
    """A stand-in for persistence. If a fake cannot serve the port, the port
    was never really a boundary (the M5B finding, applied forward)."""

    def __init__(self, stored: ProductCatalog | None = None) -> None:
        self.stored = stored
        self.saved: list[ProductCatalog] = []

    async def current(self, workspace_id: UUID) -> ProductCatalog | None:
        return self.stored

    async def save(self, catalog: ProductCatalog) -> None:
        self.saved.append(catalog)
        self.stored = catalog


def _publish(repository: ProductCatalogRepository) -> PublishProductCatalog:
    return PublishProductCatalog(repository=repository)


class TestAProductIsAStatementSomebodyMade:
    def test_it_needs_a_name(self) -> None:
        with pytest.raises(CommercialProfileError, match="needs a name"):
            Product(id=uuid4(), name="   ")

    def test_a_name_has_a_limit(self) -> None:
        with pytest.raises(CommercialProfileError, match="128 characters"):
            Product(id=uuid4(), name="x" * (MAX_NAME + 1))

    def test_a_description_is_optional(self) -> None:
        # A name alone is a legitimate declaration. Requiring prose would put
        # friction in front of the first thing a customer ever does.
        assert _product().description == ""


class TestTwoProductsMustBeTellableApart:
    def test_the_same_product_cannot_be_listed_twice(self) -> None:
        # A duplicate id would make a later reference to it ambiguous, which
        # is the one thing a stable product identity exists to prevent.
        shared = uuid4()
        with pytest.raises(CommercialProfileError, match="appears twice"):
            _catalog(_product("A", id=shared), _product("B", id=shared))

    def test_two_products_cannot_share_a_name(self) -> None:
        with pytest.raises(CommercialProfileError, match="share a name"):
            _catalog(_product("Signora Core"), _product("Signora Core"))

    def test_names_collide_regardless_of_case_or_padding(self) -> None:
        # A seller choosing between "Core" and "core " could not tell which
        # they picked, so the domain refuses before they have to.
        with pytest.raises(CommercialProfileError, match="share a name"):
            _catalog(_product("Core"), _product(" core "))

    def test_an_empty_catalog_is_legal(self) -> None:
        # "We have stopped selling everything on this list" is a statement a
        # customer is entitled to make, and it has an author and a moment.
        assert _catalog().products == ()


class TestARevisionSupersedesRatherThanEdits:
    def test_it_mints_the_next_version(self) -> None:
        first = _catalog(_product("A"))

        second = first.revise((_product("B"),), id=uuid4(), by=ACTOR, now=NOW)

        assert (first.version, second.version) == (1, 2)
        assert second.supersedes == first.id

    def test_the_previous_version_is_unchanged(self) -> None:
        # Immutability is the point: everything declared later cites a
        # version, and an edited one would make those citations unresolvable.
        first = _catalog(_product("A"))

        first.revise((), id=uuid4(), by=ACTOR, now=NOW)

        assert len(first.products) == 1

    def test_an_invalid_revision_never_exists(self) -> None:
        # Validation happens in the new catalog's construction, so a bad
        # revision cannot reach a variable somebody goes on to save.
        first = _catalog(_product("A"))
        shared = uuid4()

        with pytest.raises(CommercialProfileError):
            first.revise(
                (_product("B", id=shared), _product("C", id=shared)),
                id=uuid4(),
                by=ACTOR,
                now=NOW,
            )

    def test_a_stored_catalog_starts_at_version_one(self) -> None:
        # Version 0 means "nothing declared" and is never a stored row, so a
        # row claiming it would be a workspace that both has and has not
        # declared a catalog.
        with pytest.raises(CommercialProfileError, match="version 1 or above"):
            ProductCatalog(
                id=uuid4(),
                workspace_id=WORKSPACE,
                version=0,
                products=(),
                created_at=NOW,
                created_by=ACTOR,
            )


class TestPublishing:
    async def test_the_first_catalog_supersedes_nothing(self) -> None:
        repository = FakeCatalogRepository()

        catalog = await _publish(repository).execute(
            PublishProductCatalogInput(
                workspace_id=WORKSPACE,
                products=(_product(),),
                expected_version=0,
                actor_id=ACTOR,
            )
        )

        assert (catalog.version, catalog.supersedes) == (1, None)

    async def test_it_records_who_declared_it(self) -> None:
        # A commercial declaration is a decision, and the record of one names
        # its author permanently.
        repository = FakeCatalogRepository()

        catalog = await _publish(repository).execute(
            PublishProductCatalogInput(
                workspace_id=WORKSPACE,
                products=(),
                expected_version=0,
                actor_id=ACTOR,
            )
        )

        assert catalog.created_by == ACTOR

    async def test_a_concurrent_edit_is_refused_rather_than_overwritten(self) -> None:
        # **The failure this exists to prevent**: two colleagues open the
        # page, both save, and the second silently erases the first's work
        # while both are told it worked.
        repository = FakeCatalogRepository(_catalog(_product("A")))

        with pytest.raises(CatalogVersionConflictError) as refusal:
            await _publish(repository).execute(
                PublishProductCatalogInput(
                    workspace_id=WORKSPACE,
                    products=(_product("B"),),
                    expected_version=0,
                    actor_id=ACTOR,
                )
            )

        assert (refusal.value.expected, refusal.value.actual) == (0, 1)
        assert repository.saved == [], "a refused publish must write nothing"

    async def test_the_refusal_says_what_to_do(self) -> None:
        repository = FakeCatalogRepository(_catalog())

        with pytest.raises(CatalogVersionConflictError, match="reload"):
            await _publish(repository).execute(
                PublishProductCatalogInput(
                    workspace_id=WORKSPACE,
                    products=(),
                    expected_version=99,
                    actor_id=ACTOR,
                )
            )

    async def test_declaring_the_first_catalog_twice_is_refused(self) -> None:
        # Version 0 is only sendable by a caller who has never read one. The
        # second such caller has, whether they know it or not.
        repository = FakeCatalogRepository()
        publish = _publish(repository)
        request = PublishProductCatalogInput(
            workspace_id=WORKSPACE,
            products=(),
            expected_version=0,
            actor_id=ACTOR,
        )

        await publish.execute(request)

        with pytest.raises(CatalogVersionConflictError):
            await publish.execute(request)
