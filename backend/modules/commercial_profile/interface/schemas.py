"""HTTP schemas for what a customer declares about their own business.

**The customer-authored writes in the product surface.** Every other endpoint
reports what Signora computed or records a decision about it; these store
sentences the customer typed, unchanged.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.commercial_profile.domain.catalog import (
    MAX_DESCRIPTION,
    MAX_NAME,
    Product,
    ProductCatalog,
)
from modules.commercial_profile.domain.declaration import UNDECLARED
from modules.commercial_profile.domain.icp import (
    MAX_CRITERIA,
    MAX_EMPLOYEES,
    MAX_NOTES,
    EmployeeRange,
    IcpDeclaration,
    ProductIcp,
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
        ge=UNDECLARED,
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
    def from_domain(cls, product: Product) -> ProductResponse:
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
    def empty(cls) -> ProductCatalogResponse:
        """A workspace that has declared nothing.

        The same shape as a populated catalog rather than an absence, so no
        caller needs a branch for the state every workspace starts in.
        """
        return cls(version=UNDECLARED, products=(), updated_at=None, updated_by=None)

    @classmethod
    def from_domain(cls, catalog: ProductCatalog) -> ProductCatalogResponse:
        return cls(
            version=catalog.version,
            products=tuple(ProductResponse.from_domain(p) for p in catalog.products),
            updated_at=catalog.created_at,
            updated_by=catalog.created_by,
        )


class EmployeeRangeRequest(BaseModel):
    """How big the companies that buy this are."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    minimum: int | None = Field(
        default=None,
        ge=0,
        le=MAX_EMPLOYEES,
        description="The smallest company worth selling to. Omit for no lower bound.",
    )
    maximum: int | None = Field(
        default=None,
        ge=0,
        le=MAX_EMPLOYEES,
        description="The largest. Omit for no upper bound.",
    )

    def to_domain(self) -> EmployeeRange:
        return EmployeeRange(minimum=self.minimum, maximum=self.maximum)


class ProductIcpRequest(BaseModel):
    """Who buys one product, as the customer describes them."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    product_id: UUID = Field(
        description=(
            "**A product from the catalog**, and one the workspace currently sells. The id "
            "is stable across every revision of the catalog, so this reference survives a "
            "product being renamed or reordered."
        )
    )
    industries: tuple[str, ...] = Field(
        default=(),
        max_length=MAX_CRITERIA,
        description=(
            "The kinds of business that buy this, **in your own words**. Signora records "
            "what you say; nothing here is matched against a fixed list."
        ),
    )
    countries: tuple[str, ...] = Field(
        default=(),
        max_length=MAX_CRITERIA,
        description="Where they are, in your own words.",
    )
    employees: EmployeeRangeRequest | None = Field(
        default=None, description="How big they are. Omit if size does not matter."
    )
    notes: str = Field(
        default="",
        max_length=MAX_NOTES,
        description=("Anything the fields above cannot hold. Read by a colleague, never parsed."),
    )

    def to_domain(self) -> ProductIcp:
        return ProductIcp(
            product_id=self.product_id,
            industries=self.industries,
            countries=self.countries,
            employees=None if self.employees is None else self.employees.to_domain(),
            notes=self.notes,
        )


class DeclareIcpRequest(BaseModel):
    """A complete statement of who buys what this workspace sells."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    expected_version: int = Field(
        ge=UNDECLARED,
        description=(
            "The version being replaced — **0 when describing an ideal customer for the "
            "first time.** Sending the version you read turns a colleague's concurrent "
            "edit into a refusal you can act on instead of an overwrite neither of you sees."
        ),
    )
    profiles: tuple[ProductIcpRequest, ...] = Field(
        description=(
            "Every product you have described, not a change to one. A product absent from "
            "this list has no ideal customer described — and the version that described it "
            "is still readable."
        )
    )


class EmployeeRangeResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    minimum: int | None = Field(description="Null when there is no lower bound.")
    maximum: int | None = Field(description="Null when there is no upper bound.")

    @classmethod
    def from_domain(cls, employees: EmployeeRange) -> EmployeeRangeResponse:
        return cls(minimum=employees.minimum, maximum=employees.maximum)


class ProductIcpResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    product_id: UUID = Field(description="The product this describes the buyer of.")
    industries: tuple[str, ...] = Field(description="As the customer wrote them.")
    countries: tuple[str, ...] = Field(description="As the customer wrote them.")
    employees: EmployeeRangeResponse | None = Field(description="Null when size was not stated.")
    notes: str = Field(description="May be empty.")

    @classmethod
    def from_domain(cls, profile: ProductIcp) -> ProductIcpResponse:
        return cls(
            product_id=profile.product_id,
            industries=profile.industries,
            countries=profile.countries,
            employees=(
                None
                if profile.employees is None
                else EmployeeRangeResponse.from_domain(profile.employees)
            ),
            notes=profile.notes,
        )


class IcpDeclarationResponse(BaseModel):
    """Who buys what this workspace sells, and who last said so."""

    model_config = ConfigDict(frozen=True)

    version: int = Field(
        description=(
            "**0 when nothing has been described**, which is the ordinary state of a new "
            "workspace — an empty description is an answer, not a 404. Every save "
            "increments it, and the number is what a subsequent save must quote."
        )
    )
    profiles: tuple[ProductIcpResponse, ...] = Field(
        description=(
            "One per product described. A product with no entry has no ideal customer "
            "described yet — **never a match, a score or a rank**: this endpoint reports "
            "what the customer stated and nothing Signora concluded."
        )
    )
    updated_at: datetime | None = Field(
        description="When this version was declared. Null only at version 0."
    )
    updated_by: UUID | None = Field(
        description=(
            "Who declared it. Null only at version 0. The row is never edited, so this "
            "cannot be reattributed."
        )
    )

    @classmethod
    def empty(cls) -> IcpDeclarationResponse:
        """A workspace that has described nobody.

        The same shape as a populated declaration rather than an absence, so
        no caller needs a branch for the state every workspace starts in.
        """
        return cls(version=UNDECLARED, profiles=(), updated_at=None, updated_by=None)

    @classmethod
    def from_domain(cls, declaration: IcpDeclaration) -> IcpDeclarationResponse:
        return cls(
            version=declaration.version,
            profiles=tuple(ProductIcpResponse.from_domain(p) for p in declaration.profiles),
            updated_at=declaration.created_at,
            updated_by=declaration.created_by,
        )


__all__ = [
    "DeclareIcpRequest",
    "EmployeeRangeRequest",
    "EmployeeRangeResponse",
    "IcpDeclarationResponse",
    "ProductCatalogResponse",
    "ProductIcpRequest",
    "ProductIcpResponse",
    "ProductRequest",
    "ProductResponse",
    "PublishProductCatalogRequest",
]
