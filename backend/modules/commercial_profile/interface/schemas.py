"""HTTP schemas for what a customer declares about their own business.

**The customer-authored writes in the product surface.** Every other endpoint
reports what Signora computed or records a decision about it; these store
sentences the customer typed, unchanged.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.commercial_profile.application.segment_queries import SegmentSummary
from modules.commercial_profile.domain.account_assignment import (
    AccountAssignment,
    AccountRole,
    Reassignment,
)
from modules.commercial_profile.domain.account_segment import (
    AccountSegment,
    SegmentAddition,
)
from modules.commercial_profile.domain.account_tag import (
    MAX_TAG_NAME,
    AccountTag,
    TagApplication,
    TagTone,
    TagVocabulary,
)
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
from modules.commercial_profile.domain.competitors import (
    MAX_COMPETITORS,
    Competitor,
    DeclaredCompetitors,
)
from modules.commercial_profile.domain.competitors import (
    MAX_NAME as MAX_COMPETITOR_NAME,
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
from modules.commercial_profile.domain.target_accounts import (
    MAX_ACCOUNTS,
    TargetAccount,
    TargetAccountList,
)
from modules.commercial_profile.domain.target_accounts import (
    MAX_NAME as MAX_ACCOUNT_NAME,
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


class TargetAccountRequest(BaseModel):
    """One company the customer wants watched."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID = Field(
        description=(
            "**Chosen by the client and stable across every revision.** It is what lets "
            "a consumer tell a *rename* from a *remove and re-add* — different "
            "instructions about spending money — and what makes saving the same list "
            "twice produce the same list."
        )
    )
    name: str = Field(
        min_length=1,
        max_length=MAX_ACCOUNT_NAME,
        description=(
            "The company, **as you would say it**. Signora does not ask for a domain or "
            "a registration number: working out which company you mean is our job, not "
            "yours."
        ),
    )

    def to_domain(self) -> TargetAccount:
        return TargetAccount(id=self.id, name=self.name)


class DeclareTargetAccountsRequest(BaseModel):
    """A complete statement of which companies this workspace watches."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    expected_version: int = Field(
        ge=UNDECLARED,
        description=(
            "The version being replaced — **0 when declaring the first list.** Sending "
            "the version you read turns a colleague's concurrent edit into a refusal "
            "you can act on instead of an overwrite neither of you sees."
        ),
    )
    accounts: tuple[TargetAccountRequest, ...] = Field(
        max_length=MAX_ACCOUNTS,
        description=(
            "The whole list, not a change to it. A company absent from this list is one "
            "you no longer want watched — and the version that contained it is still "
            "readable. **No order and no rank**: nothing here says one account matters "
            "more than another."
        ),
    )


class TargetAccountResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(description="Stable across every revision of the list.")
    name: str = Field(description="As the customer typed it. Never resolved.")

    @classmethod
    def from_domain(cls, account: TargetAccount) -> TargetAccountResponse:
        return cls(id=account.id, name=account.name)


class TargetAccountListResponse(BaseModel):
    """Which companies this workspace watches, and who last said so."""

    model_config = ConfigDict(frozen=True)

    version: int = Field(
        description=(
            "**0 when nothing has been declared**, which is the ordinary state of a new "
            "workspace. Every save increments it, and **the same number travels on the "
            "event that tells Signora the list changed** — so it is part of a published "
            "contract rather than only this endpoint's bookkeeping."
        )
    )
    accounts: tuple[TargetAccountResponse, ...] = Field(
        description=(
            "In the order the customer arranged them, which carries no rank. **Never a "
            "status**: whether Signora has looked at an account yet, and what it found, "
            "belong to other parts of the product."
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
    def empty(cls) -> TargetAccountListResponse:
        """A workspace that has named no companies."""
        return cls(version=UNDECLARED, accounts=(), updated_at=None, updated_by=None)

    @classmethod
    def from_domain(cls, declaration: TargetAccountList) -> TargetAccountListResponse:
        return cls(
            version=declaration.version,
            accounts=tuple(TargetAccountResponse.from_domain(a) for a in declaration.accounts),
            updated_at=declaration.created_at,
            updated_by=declaration.created_by,
        )


class CompetitorRequest(BaseModel):
    """One technology the customer competes against."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID = Field(
        description=(
            "**Chosen by the client and stable across every revision.** It is what lets "
            "a consumer tell a *rename* from a *remove and re-add*, and what makes "
            "saving the same list twice produce the same list."
        )
    )
    name: str = Field(
        min_length=1,
        max_length=MAX_COMPETITOR_NAME,
        description=(
            "The competing product, **as you would say it**. Signora does not ask for a "
            "vendor or a website: working out which technology you mean is our job, not "
            "yours."
        ),
    )

    def to_domain(self) -> Competitor:
        return Competitor(id=self.id, name=self.name)


class DeclareCompetitorsRequest(BaseModel):
    """A complete statement of who this workspace competes against."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    expected_version: int = Field(
        ge=UNDECLARED,
        description=(
            "The version being replaced — **0 when declaring the first list.** Sending "
            "the version you read turns a colleague's concurrent edit into a refusal "
            "you can act on instead of an overwrite neither of you sees."
        ),
    )
    competitors: tuple[CompetitorRequest, ...] = Field(
        max_length=MAX_COMPETITORS,
        description=(
            "The whole list, not a change to it. A technology absent from this list is "
            "one you no longer consider a rival — and the version that contained it is "
            "still readable. **No order, no rank and no threat level**: Signora records "
            "who you are up against and grades none of them."
        ),
    )


class CompetitorResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(description="Stable across every revision of the list.")
    name: str = Field(description="As the customer typed it. Never resolved.")

    @classmethod
    def from_domain(cls, entry: Competitor) -> CompetitorResponse:
        return cls(id=entry.id, name=entry.name)


class DeclaredCompetitorsResponse(BaseModel):
    """Who this workspace competes against, and who last said so."""

    model_config = ConfigDict(frozen=True)

    version: int = Field(
        description=(
            "**0 when nothing has been declared**, which is the ordinary state of a new "
            "workspace. Every save increments it."
        )
    )
    competitors: tuple[CompetitorResponse, ...] = Field(
        description=(
            "In the order the customer arranged them, which carries no rank. **Never a "
            "score**: how much a competitor moves an account is decided elsewhere, from "
            "a reviewed model a customer can read."
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
    def empty(cls) -> DeclaredCompetitorsResponse:
        """A workspace that has named no competitors.

        **Distinct from a workspace that declared an empty list**, which reads
        version 1 — *"we do not track competitors"* is a statement with an
        author, and version 0 is the absence of one.
        """
        return cls(version=UNDECLARED, competitors=(), updated_at=None, updated_by=None)

    @classmethod
    def from_domain(cls, declaration: DeclaredCompetitors) -> DeclaredCompetitorsResponse:
        return cls(
            version=declaration.version,
            competitors=tuple(CompetitorResponse.from_domain(c) for c in declaration.competitors),
            updated_at=declaration.created_at,
            updated_by=declaration.created_by,
        )


__all__ = [
    "BuyingCommitteeResponse",
    "CompetitorRequest",
    "CompetitorResponse",
    "DeclareCompetitorsRequest",
    "DeclaredCompetitorsResponse",
    "DeclareTargetAccountsRequest",
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
    "TargetAccountListResponse",
    "TargetAccountRequest",
    "TargetAccountResponse",
    "ProductIcpResponse",
    "ProductRequest",
    "ProductResponse",
    "PublishProductCatalogRequest",
]


class SegmentSummaryResponse(BaseModel):
    """One segment, as a list reads it.

    **Purpose-built, never the domain object.** Nothing here exposes a version
    id, a transition sequence or a `supersedes` pointer — those are how the
    module keeps its promises, not something a customer asked about.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID
    name: str = Field(description="What the customer calls this segment.")
    state: str = Field(
        description=(
            "draft, published or archived. Derived from the latest lifecycle "
            "transition rather than stored, so it cannot disagree with the log."
        )
    )
    version: int = Field(
        description=(
            "Which published version is in force. A draft that has never been "
            "published has no version and does not appear here yet."
        )
    )
    product_ids: list[UUID] = Field(
        description=(
            "Which products this segment buys. Ids rather than names — the "
            "catalog owns names, and a product removed from it must still "
            "leave this row readable."
        )
    )
    last_changed_at: datetime = Field(
        description="A publication or a lifecycle move, whichever happened later."
    )
    last_changed_by: UUID

    @classmethod
    def from_domain(cls, summary: SegmentSummary) -> SegmentSummaryResponse:
        return cls(
            id=summary.id,
            name=summary.name,
            state=summary.state.value,
            version=summary.version,
            product_ids=list(summary.product_ids),
            last_changed_at=summary.last_changed_at,
            last_changed_by=summary.last_changed_by,
        )


class AccountTagResponse(BaseModel):
    """One label in the workspace's vocabulary."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    name: str = Field(description="**As the customer typed it**, never the folded form.")
    tone: str = Field(
        description=(
            "The design's chip token — `risk`, `warn`, `pos` or `neutral`. **`ai` is not "
            "among them**: that tone is reserved for what Signora itself inferred, and a "
            "customer's own label must not be able to wear it."
        )
    )

    @classmethod
    def from_domain(cls, tag: AccountTag) -> AccountTagResponse:
        return cls(id=tag.id, name=tag.name, tone=tag.tone.value)


class AccountTagVocabularyResponse(BaseModel):
    """Every tag the workspace has, in name order."""

    model_config = ConfigDict(frozen=True)

    tags: list[AccountTagResponse]

    @classmethod
    def from_domain(cls, vocabulary: TagVocabulary) -> AccountTagVocabularyResponse:
        return cls(tags=[AccountTagResponse.from_domain(tag) for tag in vocabulary.tags])


class CreateAccountTagRequest(BaseModel):
    """Add a label, or select the one that already answers to that name."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1, max_length=MAX_TAG_NAME)
    tone: TagTone = Field(
        description=(
            "**Chosen by the customer.** Nothing in the platform can derive it: "
            '"Champion lost" is a risk and "Expansion" is positive because a person '
            "judged them so."
        )
    )


class RenameAccountTagRequest(BaseModel):
    """Correct a label. **Every account keeps the tag** — the id does not move."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1, max_length=MAX_TAG_NAME)
    tone: TagTone


class ApplyAccountTagRequest(BaseModel):
    """Put one tag on several accounts at once."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    accounts: list[UUID] = Field(
        min_length=1,
        description=(
            "**The accounts the customer selected.** Duplicates are tolerated and counted "
            "once — a table that offered *Select all* twice must not report two changes "
            "for one row, and must not try to reverse it twice."
        ),
    )


class AccountTagApplicationResponse(BaseModel):
    """What the batch actually did, account by account.

    **`changed` is what a reversal operates on, and `unchanged` is what makes the
    confirmation truthful** — *"38 tagged, 3 already had it"* rather than
    *"41 tagged"*.
    """

    model_config = ConfigDict(frozen=True)

    tag_id: UUID
    changed: list[UUID]
    unchanged: list[UUID]
    applied_count: int
    total_count: int

    @classmethod
    def from_domain(cls, application: TagApplication) -> AccountTagApplicationResponse:
        return cls(
            tag_id=application.tag_id,
            changed=list(application.changed),
            unchanged=list(application.unchanged),
            applied_count=application.applied_count,
            total_count=application.total_count,
        )


class ProposedTagBatchResponse(BaseModel):
    """The batch somebody is now asked to approve.

    ⛔ **An id and a count, never a state.** 📁 The approval lifecycle is the
    Action Batch's and is read from its own endpoint — **two representations of
    where a batch stands would eventually disagree** ([§2](../../../../CLAUDE.md)).
    """

    model_config = ConfigDict(frozen=True)

    batch_id: UUID
    item_count: int = Field(
        description=(
            "**Companies, not clicks.** The selection is de-duplicated before the count is "
            "taken, so the sentence a customer approves says how many companies it touches."
        )
    )


class AccountTagAssignmentsResponse(BaseModel):
    """Which tags each of the requested accounts wears.

    **Keyed by account, and an account with none is simply absent** — a caller
    asking about forty accounts gets rows for the ones that have tags, and the
    screen renders nothing for the rest. An empty list per account would say the
    same thing in more bytes.
    """

    model_config = ConfigDict(frozen=True)

    assignments: dict[UUID, list[UUID]]


class AccountAssignmentResponse(BaseModel):
    """Who holds one role on one account.

    ⛔ **A `user_id` and no name.** The screen resolves it against the member
    list it already has — 📁 ADR-0411 stores a reference precisely so a name is
    never duplicated here, and a name on this response would be the second
    representation §2 forbids, stale the day somebody changes theirs.
    """

    model_config = ConfigDict(frozen=True)

    account_id: UUID
    role: AccountRole
    member_user_id: UUID

    @classmethod
    def from_domain(cls, assignment: AccountAssignment) -> AccountAssignmentResponse:
        return cls(
            account_id=assignment.account_id,
            role=assignment.role,
            member_user_id=assignment.member_user_id,
        )


class AccountAssignmentListResponse(BaseModel):
    """Every assignment on the accounts the caller asked about."""

    model_config = ConfigDict(frozen=True)

    assignments: list[AccountAssignmentResponse]

    @classmethod
    def from_domain(
        cls, assignments: tuple[AccountAssignment, ...]
    ) -> AccountAssignmentListResponse:
        return cls(
            assignments=[
                AccountAssignmentResponse.from_domain(assignment)
                for assignment in assignments
            ]
        )


class AssignAccountsRequest(BaseModel):
    """Put one member on a selection of accounts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    account_ids: list[UUID] = Field(min_length=1)
    role: AccountRole
    member_user_id: UUID


class ReassignmentResponse(BaseModel):
    """What the assignment changed — **and what would undo it.**

    ⚡ **`changed` counts accounts that actually moved**, so the confirmation a
    seller reads is the truth rather than the size of their selection. 📁 The
    same distinction `AccountTagBatch` draws between `requested` and `changed`,
    and the reason both exist.
    """

    model_config = ConfigDict(frozen=True)

    role: AccountRole
    changed: int
    unchanged: int

    @classmethod
    def from_domain(cls, reassignment: Reassignment) -> ReassignmentResponse:
        return cls(
            role=reassignment.role,
            changed=len(reassignment.previous),
            unchanged=len(reassignment.unchanged),
        )


# ── Segments (TASK-1479 ⓶b, ADR-0411's third capability) ────────────────────


class CreateAccountSegmentRequest(BaseModel):
    """Name a new saved grouping."""

    name: str = Field(min_length=1, max_length=60)


class RenameAccountSegmentRequest(BaseModel):
    name: str = Field(min_length=1, max_length=60)


class AccountSegmentResponse(BaseModel):
    """One saved grouping.

    ⛔ **No `rule` and no `kind`.** The design draws a Dynamic kind and it is
    not built ([C-1511](../../../../docs/LANE_COORDINATION.md)); **a field
    reporting `"static"` for every row would be a vocabulary this response
    cannot yet contrast with anything**, which is a promise rather than a fact.
    """

    segment_id: UUID
    name: str

    @classmethod
    def from_domain(cls, segment: AccountSegment) -> AccountSegmentResponse:
        return cls(segment_id=segment.id, name=segment.name)


class AccountSegmentEntry(BaseModel):
    """One row of the Segments panel: a grouping and how many companies are in
    it.

    ⚡ **`account_count` is derived on read.** A stored count is a second
    representation that goes stale the next time anybody adds an account.
    """

    segment_id: UUID
    name: str
    account_count: int


class AccountSegmentDirectoryResponse(BaseModel):
    """Every saved grouping the workspace has, with its count.

    ⛔ **A segment with nobody in it is present with `0`, never absent.** 📁
    [P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md): an empty result and
    an absent one are different facts, and **a newly named segment is in the
    empty state for as long as it takes somebody to curate it** — vanishing
    from the panel in that window would look like the creation had failed.
    """

    segments: list[AccountSegmentEntry]


class AddToAccountSegmentRequest(BaseModel):
    account_ids: list[UUID] = Field(min_length=1)


class AccountSegmentAdditionResponse(BaseModel):
    """What a bulk *Add to segment* actually did.

    ⚠️ **Two numbers, because one would have to lie.** *"38 added, 3 already
    there"* is a sentence the customer can check against the table in front of
    them; *"41 updated"* is one they can disprove by looking.
    """

    segment_id: UUID
    added: int
    unchanged: int

    @classmethod
    def from_domain(cls, addition: SegmentAddition) -> AccountSegmentAdditionResponse:
        return cls(
            segment_id=addition.segment_id,
            added=addition.added_count,
            unchanged=len(addition.unchanged),
        )


class AccountSegmentMembership(BaseModel):
    """Which segments one account is in."""

    account_id: UUID
    segment_ids: list[UUID]


class AccountSegmentMembershipList(BaseModel):
    """The Companies read: segment membership for the accounts on screen.

    ⛔ **An account in no segment is ABSENT from this list**, not present with
    an empty array — the screen asked about forty accounts and this answers
    only about the ones with something to say. **The caller must not read an
    absent account as an unread one**, which is why the request names its
    accounts and the response never widens beyond them.
    """

    memberships: list[AccountSegmentMembership]


class ProposedSegmentBatchResponse(BaseModel):
    """The id of a batch that has been proposed and **not applied.**

    ⛔ **The only field, deliberately.** 📁 `ActionBatchView` is what publishes
    a batch's state, and a second copy of it here would be the representation
    that drifts — **the one nobody updates when the batch is approved.**
    """

    batch_id: UUID
