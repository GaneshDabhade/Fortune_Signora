"""Declaring what the workspace sells.

The module's only write. It takes the catalog a customer means to have and
records it as a new version — it never patches, merges, or reconciles.

### Why the whole catalog arrives, not a change to it

The aggregate is the catalog, so a version is a complete statement. Accepting
*"add this product"* would make the stored version depend on what was there
when the request arrived, which is exactly the lost update two people editing
a list produce — and the one thing versioning is supposed to make visible.

### Why the caller states the version it is replacing

`expected_version` turns a concurrent edit into a **refusal a person can
act on** rather than a silent overwrite. Without it, the second of two
colleagues to press Save would erase the first's work and both would see
success.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from modules.commercial_profile.application.ports import ProductCatalogRepository
from modules.commercial_profile.domain.catalog import (
    Product,
    ProductCatalog,
    first_catalog,
)
from modules.commercial_profile.domain.declaration import (
    UNDECLARED,
    CommercialProfileError,
)


class CatalogVersionConflictError(CommercialProfileError):
    """Somebody else changed the catalog since this caller read it."""

    def __init__(self, *, expected: int, actual: int) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"the catalog is at version {actual}, not {expected}. Somebody else changed it "
            "since you opened this page — reload to see their version before saving yours, "
            "so neither of you loses work."
        )


@dataclass(frozen=True, slots=True)
class PublishProductCatalogInput:
    workspace_id: UUID
    products: tuple[Product, ...]
    #: The version the caller believes it is replacing. `0` declares the
    #: first catalog, and is the only value that may be sent by a caller who
    #: has never read one.
    expected_version: int
    #: Taken from the verified caller by the interface layer. There is no
    #: field a request could use to name somebody else as the author.
    actor_id: UUID


class PublishProductCatalog:
    def __init__(self, *, repository: ProductCatalogRepository) -> None:
        self._repository = repository

    async def execute(self, request: PublishProductCatalogInput) -> ProductCatalog:
        current = await self._repository.current(request.workspace_id)
        actual = current.version if current is not None else UNDECLARED
        if actual != request.expected_version:
            raise CatalogVersionConflictError(expected=request.expected_version, actual=actual)

        now = datetime.now(UTC)
        catalog = (
            first_catalog(
                request.workspace_id,
                request.products,
                id=uuid4(),
                by=request.actor_id,
                now=now,
            )
            if current is None
            else current.revise(request.products, id=uuid4(), by=request.actor_id, now=now)
        )
        await self._repository.save(catalog)
        return catalog
