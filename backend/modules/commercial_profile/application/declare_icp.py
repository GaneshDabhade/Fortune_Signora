"""Describing who buys what the workspace sells.

The second write in the module, and the same discipline as the first: it takes
the description a customer means to have and records it as a new version. It
never patches, merges, reconciles — or matches anybody against the result.

### Why the whole description arrives, not a change to it

The aggregate is the declaration, so a version is a complete statement.
Accepting *"describe this one product"* would make the stored version depend
on what was there when the request arrived, which is exactly the lost update
two people editing the same page produce.

### Why a product must already be in the catalog

A profile cites a product id, and everything read later resolves that id
against the catalog. Accepting one for a product the workspace does not sell
would store a reference that resolves to nothing — a dangling citation, in the
module whose whole job is being citable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from modules.commercial_profile.application.ports import (
    IcpDeclarationRepository,
    ProductCatalogRepository,
)
from modules.commercial_profile.domain.declaration import (
    UNDECLARED,
    CommercialProfileError,
)
from modules.commercial_profile.domain.icp import (
    IcpDeclaration,
    ProductIcp,
    first_declaration,
)


class IcpVersionConflictError(CommercialProfileError):
    """Somebody else changed the description since this caller read it."""

    def __init__(self, *, expected: int, actual: int) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"your ideal customer is at version {actual}, not {expected}. Somebody else "
            "changed it since you opened this page — reload to see their version before "
            "saving yours, so neither of you loses work."
        )


class UnknownProductError(CommercialProfileError):
    """A profile names a product the workspace does not currently sell."""

    def __init__(self, product_id: UUID) -> None:
        self.product_id = product_id
        super().__init__(
            "you cannot describe who buys a product you have not said you sell. Add it "
            "under Products first, then describe its ideal customer."
        )


@dataclass(frozen=True, slots=True)
class DeclareIcpInput:
    workspace_id: UUID
    profiles: tuple[ProductIcp, ...]
    #: The version the caller believes it is replacing. `0` declares the first
    #: description, and is the only value that may be sent by a caller who has
    #: never read one.
    expected_version: int
    #: Taken from the verified caller by the interface layer. There is no
    #: field a request could use to name somebody else as the author.
    actor_id: UUID


class DeclareIcp:
    def __init__(
        self,
        *,
        declarations: IcpDeclarationRepository,
        catalog: ProductCatalogRepository,
    ) -> None:
        self._declarations = declarations
        self._catalog = catalog

    async def execute(self, request: DeclareIcpInput) -> IcpDeclaration:
        current = await self._declarations.current(request.workspace_id)
        actual = current.version if current is not None else UNDECLARED
        # **Version before products, deliberately.** A stale caller's product
        # list is stale too, so telling them their catalog is wrong would send
        # them to fix the wrong page.
        if actual != request.expected_version:
            raise IcpVersionConflictError(expected=request.expected_version, actual=actual)

        catalog = await self._catalog.current(request.workspace_id)
        sold = {product.id for product in catalog.products} if catalog else set[UUID]()
        for profile in request.profiles:
            if profile.product_id not in sold:
                raise UnknownProductError(profile.product_id)

        now = datetime.now(UTC)
        declaration = (
            first_declaration(
                request.workspace_id,
                request.profiles,
                id=uuid4(),
                by=request.actor_id,
                now=now,
            )
            if current is None
            else current.revise(request.profiles, id=uuid4(), by=request.actor_id, now=now)
        )
        await self._declarations.save(declaration)
        return declaration
