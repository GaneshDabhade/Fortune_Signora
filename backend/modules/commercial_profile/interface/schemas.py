"""HTTP schemas for the product catalog.

**The first customer-authored write in the product surface.** Every other
endpoint reports what Signora computed or records a decision about it; this
one stores a sentence the customer typed, unchanged.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.commercial_profile.domain.catalog import (
    EMPTY_CATALOG_VERSION,
    MAX_DESCRIPTION,
    MAX_NAME,
    Product,
    ProductCatalog,
)


class ProductRequest(BaseModel):
    """One product, as the customer states it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID = Field(
        description=(
            "**Chosen by the client**, so that sending the same catalog twice produces the "
            "same catalog. A server-minted id would make this endpoint non-idempotent — a "
            "retried save would duplicate every product — and the identity has to be stable "
            "anyway, because everything declared later refers to a product by it."
        )
    )
    name: str = Field(min_length=1, max_length=MAX_NAME)
    description: str = Field(
        default="",
        max_length=MAX_DESCRIPTION,
        description=(
            "What it does, in the customer's own words. Optional — a name alone is enough to "
            "declare a product, and not enough to explain one to a colleague six months later."
        ),
    )

    def to_domain(self) -> Product:
        return Product(id=self.id, name=self.name, description=self.description)


class PublishProductCatalogRequest(BaseModel):
    """A complete statement of what the workspace sells."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    expected_version: int = Field(
        ge=EMPTY_CATALOG_VERSION,
        description=(
            "The version being replaced — **0 when declaring the first catalog.** Sending the "
            "version you read turns a colleague's concurrent edit into a refusal you can act "
            "on instead of an overwrite neither of you sees."
        ),
    )
    products: tuple[ProductRequest, ...] = Field(
        description=(
            "The whole catalog, not a change to it. A version is a complete statement, so a "
            "product absent from this list is one the workspace no longer sells — and the "
            "version that contained it is still readable."
        )
    )


class ProductResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(description="Stable across every revision of the catalog.")
    name: str = Field(description="What the customer calls it.")
    description: str = Field(description="What it does. May be empty.")

    @classmethod
    def from_domain(cls, product: Product) -> "ProductResponse":
        return cls(id=product.id, name=product.name, description=product.description)


class ProductCatalogResponse(BaseModel):
    """What this workspace sells, and who last said so."""

    model_config = ConfigDict(frozen=True)

    version: int = Field(
        description=(
            "**0 when nothing has been declared**, which is the ordinary state of a new "
            "workspace — an empty catalog is an answer, not a 404. Every save increments it, "
            "and the number is what a subsequent save must quote."
        )
    )
    products: tuple[ProductResponse, ...] = Field(
        description="In the order the customer arranged them, which is theirs to decide."
    )
    updated_at: datetime | None = Field(
        description="When this version was declared. Null only at version 0."
    )
    updated_by: UUID | None = Field(
        description=(
            "Who declared it. Null only at version 0. **A commercial declaration is a "
            "decision**, and the record of one names its author permanently — the row is "
            "never edited, so this cannot be reattributed."
        )
    )

    @classmethod
    def empty(cls) -> "ProductCatalogResponse":
        """A workspace that has declared nothing.

        The same shape as a populated catalog rather than an absence, so no
        caller needs a branch for the state every workspace starts in.
        """
        return cls(
            version=EMPTY_CATALOG_VERSION, products=(), updated_at=None, updated_by=None
        )

    @classmethod
    def from_domain(cls, catalog: ProductCatalog) -> "ProductCatalogResponse":
        return cls(
            version=catalog.version,
            products=tuple(ProductResponse.from_domain(p) for p in catalog.products),
            updated_at=catalog.created_at,
            updated_by=catalog.created_by,
        )


__all__ = [
    "ProductCatalogResponse",
    "ProductRequest",
    "ProductResponse",
    "PublishProductCatalogRequest",
]
