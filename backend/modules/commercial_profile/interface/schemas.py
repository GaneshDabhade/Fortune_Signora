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
from modules.commercial_profile.domain.committee import (
    MAX_ROLES,
    MAX_TITLE,
    BuyingCommittee,
    CommitteePart,
    CommitteeRole,
    ProductCommittee,
)
from modules.commercial_profile.domain.declaration import UNDECLARED
from modules.commercial_profile.domain.focus import MAX_OBJECTIVE, CommercialFocus
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


class CommitteeRoleRequest(BaseModel):
    """One seat at the table, as the customer states it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    title: str = Field(
        min_length=1,
        max_length=MAX_TITLE,
        description=(
            "What they are called, **in your words** — *VP of Revenue Operations*, "
            "*Head of Clinical Informatics*. Never a person's name: this is a template "
            "of roles, and Signora holds no individuals here."
        ),
    )
    part: CommitteePart = Field(
        description=(
            "The part they play in a purchase. Five values, and they are ordinary sales "
            "language rather than a taxonomy to translate into."
        )
    )

    def to_domain(self) -> CommitteeRole:
        return CommitteeRole(title=self.title, part=self.part)


class ProductCommitteeRequest(BaseModel):
    """Who decides about one product."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    product_id: UUID = Field(
        description=(
            "**A product from the catalog**, and one the workspace currently sells. The "
            "id is stable across every revision of the catalog, so this reference "
            "survives a product being renamed."
        )
    )
    roles: tuple[CommitteeRoleRequest, ...] = Field(
        min_length=1,
        max_length=MAX_ROLES,
        description=(
            "At least one. **In no significant order** — the list is the customer's to "
            "arrange, and its order carries no rank, weight or importance."
        ),
    )

    def to_domain(self) -> ProductCommittee:
        return ProductCommittee(
            product_id=self.product_id,
            roles=tuple(role.to_domain() for role in self.roles),
        )


class DeclareBuyingCommitteeRequest(BaseModel):
    """A complete statement of who decides about what this workspace sells."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    expected_version: int = Field(
        ge=UNDECLARED,
        description=(
            "The version being replaced — **0 when declaring a committee for the first "
            "time.** Sending the version you read turns a colleague's concurrent edit "
            "into a refusal you can act on instead of an overwrite neither of you sees."
        ),
    )
    committees: tuple[ProductCommitteeRequest, ...] = Field(
        description=(
            "Every product with a committee, not a change to one. A product absent from "
            "this list has no committee declared — and the version that declared it is "
            "still readable."
        )
    )


class CommitteeRoleResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str = Field(description="As the customer wrote it.")
    part: CommitteePart = Field(description="The part they play in a purchase.")

    @classmethod
    def from_domain(cls, role: CommitteeRole) -> CommitteeRoleResponse:
        return cls(title=role.title, part=role.part)


class ProductCommitteeResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    product_id: UUID = Field(description="The product this committee decides about.")
    roles: tuple[CommitteeRoleResponse, ...] = Field(
        description=(
            "In the order the customer arranged them, which carries no rank or "
            "importance — **this endpoint reports a declaration, never a judgement**."
        )
    )

    @classmethod
    def from_domain(cls, committee: ProductCommittee) -> ProductCommitteeResponse:
        return cls(
            product_id=committee.product_id,
            roles=tuple(CommitteeRoleResponse.from_domain(r) for r in committee.roles),
        )


class BuyingCommitteeResponse(BaseModel):
    """Who decides about what this workspace sells, and who last said so."""

    model_config = ConfigDict(frozen=True)

    version: int = Field(
        description=(
            "**0 when nothing has been declared**, which is the ordinary state of a new "
            "workspace — an empty committee is an answer, not a 404."
        )
    )
    committees: tuple[ProductCommitteeResponse, ...] = Field(
        description="One per product with a committee declared."
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
    def empty(cls) -> BuyingCommitteeResponse:
        """A workspace that has declared no committee."""
        return cls(version=UNDECLARED, committees=(), updated_at=None, updated_by=None)

    @classmethod
    def from_domain(cls, declaration: BuyingCommittee) -> BuyingCommitteeResponse:
        return cls(
            version=declaration.version,
            committees=tuple(
                ProductCommitteeResponse.from_domain(c) for c in declaration.committees
            ),
            updated_at=declaration.created_at,
            updated_by=declaration.created_by,
        )


class DeclareFocusRequest(BaseModel):
    """A complete statement of what the workspace is pushing right now."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    expected_version: int = Field(
        ge=UNDECLARED,
        description=(
            "The version being replaced — **0 when declaring a focus for the first "
            "time.** Sending the version you read turns a colleague's concurrent edit "
            "into a refusal you can act on instead of an overwrite neither of you sees."
        ),
    )
    products: tuple[UUID, ...] = Field(
        description=(
            "The products being pushed, each one the workspace currently sells. **No "
            "order and no rank** — a product is in focus or it is not, and this list "
            "carries nothing a consumer could multiply. An empty list is a legitimate "
            "statement: *we are not pushing anything in particular*."
        )
    )
    objective: str = Field(
        default="",
        max_length=MAX_OBJECTIVE,
        description=(
            "What you are trying to do, in your own words — *land three health "
            "systems*. Read by a colleague, never parsed."
        ),
    )


class CommercialFocusResponse(BaseModel):
    """What this workspace is pushing, and who last said so."""

    model_config = ConfigDict(frozen=True)

    version: int = Field(
        description=(
            "**0 when nothing has been declared**, which is the ordinary state of a new "
            "workspace — an empty focus is an answer, not a 404."
        )
    )
    products: tuple[UUID, ...] = Field(
        description="The products in focus. **Unordered and unranked.**"
    )
    objective: str = Field(description="In the customer's words. May be empty.")
    updated_at: datetime | None = Field(
        description=(
            "When this was declared. Null only at version 0. **This is also the answer "
            "to whether the focus is current** — there is no separate period field, "
            "because it would be free to disagree with this one."
        )
    )
    updated_by: UUID | None = Field(
        description=(
            "Who declared it. Null only at version 0. The row is never edited, so this "
            "cannot be reattributed."
        )
    )

    @classmethod
    def empty(cls) -> CommercialFocusResponse:
        """A workspace that has declared no focus."""
        return cls(
            version=UNDECLARED,
            products=(),
            objective="",
            updated_at=None,
            updated_by=None,
        )

    @classmethod
    def from_domain(cls, focus: CommercialFocus) -> CommercialFocusResponse:
        return cls(
            version=focus.version,
            products=focus.products,
            objective=focus.objective,
            updated_at=focus.created_at,
            updated_by=focus.created_by,
        )


__all__ = [
    "BuyingCommitteeResponse",
    "CommercialFocusResponse",
    "CommitteeRoleRequest",
    "CommitteeRoleResponse",
    "DeclareBuyingCommitteeRequest",
    "DeclareFocusRequest",
    "DeclareIcpRequest",
    "EmployeeRangeRequest",
    "EmployeeRangeResponse",
    "IcpDeclarationResponse",
    "ProductCatalogResponse",
    "ProductCommitteeRequest",
    "ProductCommitteeResponse",
    "ProductIcpRequest",
    "ProductIcpResponse",
    "ProductRequest",
    "ProductResponse",
    "PublishProductCatalogRequest",
]
