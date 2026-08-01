"""Declaring what the workspace is pushing right now.

The fourth write in the module, and the same discipline as the first three: it
takes the focus a customer means to have and records it as a new version. It
never patches, merges, reconciles — and it applies the focus to nothing.

### Why the whole focus arrives, not a change to it

The aggregate is the declaration, so a version is a complete statement.
Accepting *"add this product to the focus"* would make the stored version
depend on what was there when the request arrived, which is exactly the lost
update two people editing the same page produce.

### Why a product must already be in the catalog

A focus cites product ids, and everything read later resolves them against the
catalog. The shared rule in `declaring.py`, because all three product-citing
declarations need the identical guarantee.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from modules.commercial_profile.application.declaring import (
    FocusUnknownProductError,
    sold_products,
)
from modules.commercial_profile.application.ports import (
    CommercialFocusRepository,
    ProductCatalogRepository,
)
from modules.commercial_profile.domain.declaration import (
    UNDECLARED,
    CommercialProfileError,
)
from modules.commercial_profile.domain.focus import CommercialFocus, first_focus


class FocusVersionConflictError(CommercialProfileError):
    """Somebody else changed the focus since this caller read it."""

    def __init__(self, *, expected: int, actual: int) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"your focus is at version {actual}, not {expected}. Somebody else changed "
            "it since you opened this page — reload to see their version before saving "
            "yours, so neither of you loses work."
        )


@dataclass(frozen=True, slots=True)
class DeclareFocusInput:
    workspace_id: UUID
    products: tuple[UUID, ...]
    objective: str
    #: The version the caller believes it is replacing. `0` declares the first
    #: focus, and is the only value that may be sent by a caller who has never
    #: read one.
    expected_version: int
    #: Taken from the verified caller by the interface layer. There is no
    #: field a request could use to name somebody else as the author.
    actor_id: UUID


class DeclareFocus:
    def __init__(
        self,
        *,
        focuses: CommercialFocusRepository,
        catalog: ProductCatalogRepository,
    ) -> None:
        self._focuses = focuses
        self._catalog = catalog

    async def execute(self, request: DeclareFocusInput) -> CommercialFocus:
        current = await self._focuses.current(request.workspace_id)
        actual = current.version if current is not None else UNDECLARED
        # **Version before products**, as everywhere in this module: a stale
        # caller's product list is stale too, so telling them their catalog is
        # wrong would send them to fix the wrong page.
        if actual != request.expected_version:
            raise FocusVersionConflictError(expected=request.expected_version, actual=actual)

        sold = await sold_products(self._catalog, request.workspace_id)
        for product_id in request.products:
            if product_id not in sold:
                raise FocusUnknownProductError(product_id)

        now = datetime.now(UTC)
        focus = (
            first_focus(
                request.workspace_id,
                request.products,
                request.objective,
                id=uuid4(),
                by=request.actor_id,
                now=now,
            )
            if current is None
            else current.revise(
                request.products,
                request.objective,
                id=uuid4(),
                by=request.actor_id,
                now=now,
            )
        )
        await self._focuses.save(focus)
        return focus
