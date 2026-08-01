"""The product catalog — what a customer sells.

**The first aggregate of the pipeline's new head.** Every module before this
one processed companies; none of them knew what the customer was selling to
them. The catalog is the anchor the later declarations hang off: an ICP is
*"the kind of company that buys **this**"*, a buying committee is *"who
decides about **this**"*, and a priority is a ranking **of these**.

### It records; it does not compute

Nothing here is derived, matched, scored or resolved. A product is a
sentence a customer typed. That is the whole boundary of this module, and
the reason it can sit upstream of a ten-stage pipeline without knowing that
the pipeline exists.

### Versioned and immutable, for the same reason as the signal profile

A catalog is superseded, never edited. The moment anything downstream
records *"this recommendation is about Product X"*, an edited catalog would
make that citation unresolvable — *"which product did you mean?"* would have
no answer, because the answer changed underneath it. `signal_profile`
reached this conclusion first and for the identical reason.

### A product's identity outlives the catalog that contains it

`Product.id` is stable across versions. Revising the catalog mints a new
*catalog* version; it does not mint new products. That is what lets a future
reference survive twelve revisions of the list it lives in.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Final
from uuid import UUID

EMPTY_CATALOG_VERSION: Final = 0
"""The version reported when a workspace has declared nothing.

**Not a stored row.** A new workspace has no catalog, and answering with an
empty one at version 0 means every caller gets the same shape whether or not
anything has been declared — no `None` branch, no 404, and no seeding write
that would tie this module to workspace creation.
"""

MAX_NAME = 128
MAX_DESCRIPTION = 1024


class CommercialProfileError(Exception):
    """Something a customer declared cannot be recorded as stated."""


@dataclass(frozen=True, slots=True)
class Product:
    """One thing the customer sells.

    **Deliberately three fields.** A price, a SKU, a category and a lifecycle
    state were all considered and none is needed to anchor an ICP, a buying
    committee or a priority — which is what this exists for. Each would be a
    field nothing reads, and a field nothing reads is a field nobody keeps
    accurate.
    """

    id: UUID
    name: str
    #: What it does, in the customer's words. Optional, and the reason it
    #: exists at all is that a name alone is not enough context for a human
    #: reading an ICP six months later.
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise CommercialProfileError("a product needs a name.")
        if len(self.name) > MAX_NAME:
            raise CommercialProfileError(
                f"a product name is limited to {MAX_NAME} characters."
            )
        if len(self.description) > MAX_DESCRIPTION:
            raise CommercialProfileError(
                f"a product description is limited to {MAX_DESCRIPTION} characters."
            )


@dataclass(frozen=True, slots=True)
class ProductCatalog:
    """Everything a workspace sells, as declared at one moment.

    Immutable. `revise` returns a **new** catalog naming the one it replaces;
    there is no method that changes this one, and the database agrees — there
    is no `UPDATE` grant on the table.
    """

    id: UUID
    workspace_id: UUID
    version: int
    products: tuple[Product, ...]
    created_at: datetime
    #: Who declared this. A commercial declaration is a decision, and a
    #: customer is entitled to know whose.
    created_by: UUID
    supersedes: UUID | None = None

    def __post_init__(self) -> None:
        if self.version < 1:
            raise CommercialProfileError("a stored catalog is at version 1 or above.")
        if len({product.id for product in self.products}) != len(self.products):
            raise CommercialProfileError(
                "the same product appears twice. A duplicate would make a reference to it "
                "ambiguous, which is the one thing a stable product identity exists to prevent."
            )
        names = [product.name.strip().casefold() for product in self.products]
        if len(set(names)) != len(names):
            raise CommercialProfileError(
                "two products share a name. A seller choosing between them could not tell "
                "which they picked."
            )

    def revise(
        self,
        products: tuple[Product, ...],
        *,
        id: UUID,
        by: UUID,
        now: datetime,
    ) -> ProductCatalog:
        """The next version of this catalog.

        Validation happens in the new catalog's own construction, so an
        invalid revision never exists — not even briefly, and not in a
        variable somebody might go on to save.
        """
        return ProductCatalog(
            id=id,
            workspace_id=self.workspace_id,
            version=self.version + 1,
            products=products,
            created_at=now,
            created_by=by,
            supersedes=self.id,
        )


def first_catalog(
    workspace_id: UUID,
    products: tuple[Product, ...],
    *,
    id: UUID,
    by: UUID,
    now: datetime,
) -> ProductCatalog:
    """The first catalog a workspace declares.

    Separate from `revise` because there is nothing to supersede, and a
    `supersedes=None` branch inside `revise` would be a second meaning for
    one method — *"replace that"* and *"there was nothing"* are different
    statements about the past.
    """
    return ProductCatalog(
        id=id,
        workspace_id=workspace_id,
        version=1,
        products=products,
        created_at=now,
        created_by=by,
        supersedes=None,
    )
