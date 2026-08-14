"""SQLAlchemy models for the Commercial Profile.

**Every table here holds a customer-authored declaration** — a statement
somebody typed about their own business, regenerable from nothing. That is a
data category `signal_profile` opened and this module fills: a pipeline
rebuild regenerates everything through buying scores and **must leave all of
these untouched**.

Each **declaration** is immutable and versioned: a revision is a new row naming
the one it supersedes, enforced by the absent `UPDATE` grant in its migration.

⚠️ **Amended 2026-08-13 ([TASK-466](../../../../docs/BACKLOG.md)), because that
sentence said *every table here* and stopped being true.** 📁
[ADR-0411](../../../../docs/architecture/adr/0411-customer-organized-account-metadata.md)
adds a second kind of customer authorship to this module: **a label, not a
statement.** `AccountTagModel` carries an `UPDATE` grant and no version chain —
⚡ **a customer renaming *At risk* to *Churn risk* is correcting their own
filing, and versioning it would keep a history nobody would ever cite** while
making a rename a write of four rows. **The two kinds are named here rather
than left for a reader to infer from a grant.**
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from signora_platform.db.base import AuditMixin, Base, TimestampMixin, WorkspaceScopedMixin


class DeclarationModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """What every declaration table in this module has in common.

    **Introduced with the third table, not the first.** Two examples would
    have been a guess at the shape; three make it visible. It carries only
    what is genuinely identical — an identity and a version — because
    `supersedes` points at each table's own primary key and cannot be shared.

    Its real job is giving `latest()` a type to stand on, so *"the row in
    force is the highest version"* is expressed **once** for the whole module
    rather than copied into each repository. That rule is subtle enough that
    `signal_profile` has it backwards today.
    """

    __abstract__ = True

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    #: Monotonic per workspace. Everything declared later cites it, and
    #: without it a historical declaration cannot be explained.
    version: Mapped[int] = mapped_column(Integer, nullable=False)


class ProductCatalogModel(DeclarationModel):
    """What the customer sells."""

    __tablename__ = "product_catalog"
    __table_args__ = (
        UniqueConstraint("workspace_id", "version", name="uq_product_catalog_version"),
        CheckConstraint("version > 0", name="ck_product_catalog_version_positive"),
    )

    #: JSONB because a catalog is read whole and never queried field by
    #: field. The same reasoning as `signal_profile.entries`.
    products: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    supersedes: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("product_catalog.id", ondelete="SET NULL"),
        nullable=True,
    )


class IcpDeclarationModel(DeclarationModel):
    """Who buys each product.

    Its own table rather than a column on `product_catalog`: the two are
    separate aggregates versioned independently, and sharing a row would mint
    a description version every time somebody renamed a product.
    """

    __tablename__ = "icp_declaration"
    __table_args__ = (
        UniqueConstraint("workspace_id", "version", name="uq_icp_declaration_version"),
        CheckConstraint("version > 0", name="ck_icp_declaration_version_positive"),
    )

    #: JSONB for the same reason as `product_catalog.products`: a declaration
    #: is read whole and never queried field by field. **Nothing joins on a
    #: product id inside it** — resolving one is the reader's job, and a
    #: relational shape here would invite a query that matched companies.
    profiles: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    supersedes: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("icp_declaration.id", ondelete="SET NULL"),
        nullable=True,
    )


class BuyingCommitteeModel(DeclarationModel):
    """Who decides about each product.

    A third table rather than a field on the ideal customer, and the reason is
    the same one that separated the first two: **a committee and an ICP change
    on different days.** Somebody adds a security reviewer to the committee
    without touching who the product is for, and folding them together would
    mint a version of both every time either moved.
    """

    __tablename__ = "buying_committee"
    __table_args__ = (
        UniqueConstraint("workspace_id", "version", name="uq_buying_committee_version"),
        CheckConstraint("version > 0", name="ck_buying_committee_version_positive"),
    )

    committees: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    supersedes: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("buying_committee.id", ondelete="SET NULL"),
        nullable=True,
    )


class TargetAccountListModel(DeclarationModel):
    """The companies a customer wants watched.

    **The only declaration in this module anything downstream reads.** It is
    still customer-authored and still regenerable from nothing: a pipeline
    rebuild replays everything the providers returned, and must not invent the
    list that asked for it.
    """

    __tablename__ = "target_account_list"
    __table_args__ = (
        UniqueConstraint("workspace_id", "version", name="uq_target_account_list_version"),
        CheckConstraint("version > 0", name="ck_target_account_list_version_positive"),
    )

    #: JSONB, read whole, like every other declaration here. **Nothing joins
    #: on a name inside it** — matching a name to a company is the Knowledge
    #: Graph's, and a relational shape here would invite the query that does
    #: it in the wrong module.
    accounts: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    supersedes: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("target_account_list.id", ondelete="SET NULL"),
        nullable=True,
    )


class CommercialFocusModel(DeclarationModel):
    """What the workspace is pushing right now.

    **The fastest-changing of the four**, which is why it is its own table: a
    catalog moves quarterly and a focus every planning cycle, and one shared
    version would fill the catalog's audit history with somebody else's
    changes.
    """

    __tablename__ = "commercial_focus"
    __table_args__ = (
        UniqueConstraint("workspace_id", "version", name="uq_commercial_focus_version"),
        CheckConstraint("version > 0", name="ck_commercial_focus_version_positive"),
    )

    #: A list of product ids, read whole. **No ordinal, no position** — a
    #: product is in focus or it is not, and a stored rank here is the column
    #: a future consumer would multiply by something.
    products: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False, default="")
    supersedes: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("commercial_focus.id", ondelete="SET NULL"),
        nullable=True,
    )


class SegmentModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """A named customer segment. **Identity, and nothing else.**

    Deliberately not a `DeclarationModel`: that base carries a `version`, and
    this row has none. Content is versioned; identity is not, which is what
    makes a citation from an opportunity resolvable after eleven revisions
    (migration 0031, ADR-0041).
    """

    __tablename__ = "icp_segment"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)


class SegmentVersionModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """One published statement about a segment. **Never a draft.**"""

    __tablename__ = "icp_segment_version"
    __table_args__ = (
        UniqueConstraint("segment_id", "version", name="uq_icp_segment_version_number"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    segment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("icp_segment.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    #: Read and written whole, never queried field by field — the same
    #: reasoning as the catalog's `products`. **The product set is not in
    #: here**: it is a relationship, and burying it in JSON would make
    #: *"which segments buy Revenue Cloud?"* a scan.
    criteria: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    supersedes: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("icp_segment_version.id", ondelete="SET NULL"),
        nullable=True,
    )


class SegmentProductModel(Base, WorkspaceScopedMixin):
    """Which products a segment buys, **versioned with the content it belongs to.**

    No foreign key to a product, because products have no table — they live
    inside `product_catalog`'s versioned document. A removed product therefore
    leaves this row intact and the screen resolves it against the current
    catalog, exactly as `keptForCatalog` already does.
    """

    __tablename__ = "icp_segment_product"

    version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("icp_segment_version.id", ondelete="CASCADE"),
        primary_key=True,
    )
    product_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class SegmentStateModel(Base, WorkspaceScopedMixin):
    """Append-only lifecycle. **The status is the audit log**, not something
    kept beside it — `opportunity_state`'s shape, for the same reason."""

    __tablename__ = "icp_segment_state"
    __table_args__ = (
        UniqueConstraint("segment_id", "sequence", name="uq_icp_segment_state_sequence"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    segment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("icp_segment.id", ondelete="CASCADE"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    #: No default. A lifecycle change nobody is attributable for is one nobody
    #: can explain.
    actor_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class DeclaredCompetitorsModel(DeclarationModel):
    """Which technologies the workspace competes against.

    **The sixth, and the first that is about a risk rather than an ambition.**
    Still customer-authored and still regenerable from nothing: a pipeline
    rebuild replays what the providers returned and must not invent the list
    that made one of those technologies matter.
    """

    __tablename__ = "declared_competitors"
    __table_args__ = (
        UniqueConstraint("workspace_id", "version", name="uq_declared_competitors_version"),
        CheckConstraint("version > 0", name="ck_declared_competitors_version_positive"),
    )

    #: JSONB, read whole, like every other declaration here — and for the
    #: reason the watch list gives out loud. **Nothing joins on a name inside
    #: it**: matching *"Salesforce"* to a technology is the Knowledge Graph's
    #: job, and a relational shape here would invite the query that does it in
    #: the wrong module. **No column holds a weight**, which is the property
    #: this table most needs to keep.
    competitors: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    supersedes: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("declared_competitors.id", ondelete="SET NULL"),
        nullable=True,
    )


class AccountTagModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """One label in a workspace's vocabulary — migration `0051`.

    **Deliberately not a `DeclarationModel`**, for the reason the module
    docstring now records: that base carries a `version` and this row has none.
    A tag is a label a customer corrects, not a statement they publish.

    ⚡ **Uniqueness is `(workspace_id, lower(name))` and lives in the index
    rather than here**, because SQLAlchemy's `UniqueConstraint` cannot express
    a functional index — 📁 the constraint is created in the migration and is
    the only place two concurrent renames can be arbitrated.
    """

    __tablename__ = "account_tag"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(40), nullable=False)
    #: The design's chip token — `risk`, `warn`, `pos`, `neutral`. **Stored as
    #: the token the stylesheet already uses**, so the screen renders it with
    #: no mapping table between the two.
    tone: Mapped[str] = mapped_column(String(8), nullable=False)


class AccountTagAssignmentModel(Base, WorkspaceScopedMixin):
    """Which account wears which tag — migration `0051`.

    **A join row and nothing else.** Removing a tag from an account is a
    `DELETE`, not a state column somebody has to remember to filter on — which
    is what keeps *"the tags on these forty rows"* a single indexed read.

    ⛔ **No `TimestampMixin`**: `updated_at` on a row that can never be updated
    is a column that would only ever equal `created_at`, and §2 calls a field
    with one possible value the decorative class.
    """

    __tablename__ = "account_tag_assignment"

    tag_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("account_tag.id", ondelete="CASCADE"), primary_key=True
    )
    #: ⛔ **No foreign key**, and the omission is the module boundary: an
    #: account is `knowledge_graph`'s entity, and a constraint across it would
    #: make this module's schema depend on another module's (§5).
    account_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class AccountTagBatchModel(Base, WorkspaceScopedMixin, TimestampMixin):
    """What one bulk tag batch asked for, and what it changed — migration `0052`.

    ⚡ **The half the Action Batch deliberately does not hold.** 📁
    `ActionBatchView` publishes *"`item_count` and not the items"*, so the
    lifecycle module knows a batch covers forty-one things and nothing about
    what they are.

    ⛔ **`changed` is nullable and the null is load-bearing**: `None` means *not
    yet applied*, `[]` means *applied and changed nothing* — which is a real
    outcome when every selected account already carried the tag. **A reversal
    reads `changed` and never `requested`.**

    ⛔ **No `AuditMixin`.** That mixin carries `updated_by`, and the only write
    after the insert is the applied-handler recording `changed` — **which is
    the batch's own approver, already held by `action_batch`.** A second copy
    here would be a fact with two representations (§2).
    """

    __tablename__ = "account_tag_batch"

    #: ⛔ **The Action Batch's id, and not a local one.** A batch has one
    #: identity, and minting a second here would make *"which batch is this?"*
    #: a join rather than a fact.
    batch_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tag_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("account_tag.id", ondelete="CASCADE"), nullable=False
    )
    requested: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    changed: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)


class AccountAssignmentModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """Who holds which role on which account — migration `0053`.

    **`(workspace_id, account_id, role)` is the identity**, so a second owner
    is refused by the schema rather than by a query somebody remembers to
    write.

    ⚡ **`TimestampMixin` here, unlike the tag join row beside it**, and the
    difference is real rather than inconsistency: an assignment **can** be
    updated — reassigning an account is a correction to who is responsible —
    so `updated_at` carries a value that differs from `created_at` and is not
    the decorative class §2 names.
    """

    __tablename__ = "account_assignment"

    #: ⛔ **No foreign key**, and the omission is the module boundary: an
    #: account is `knowledge_graph`'s entity (§5).
    account_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    role: Mapped[str] = mapped_column(String(length=8), primary_key=True)
    #: ⛔ **No foreign key either, and for a stronger reason than the account's.**
    #: A constraint would prove the *user* exists; what has to be true is that
    #: they are a member of *this workspace*, which only
    #: `WorkspaceQueryPort.get_membership` can answer.
    member_user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)


class AccountAssignmentBatchModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """One bulk owner change — migration `0054`.

    ⛔ **`moved` is nullable and the null is load-bearing**: `NULL` means the
    batch has not applied, `[]` means it applied and every account already had
    that member. **Collapsing them would make *never approved* and *approved
    and changed nothing* the same row**, and only the first is still waiting
    for somebody.
    """

    __tablename__ = "account_assignment_batch"

    batch_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    role: Mapped[str] = mapped_column(String(length=8), nullable=False)
    member_user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    requested: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    #: ⚡ **`[account, prior]` pairs**, `prior` null where nobody held it — the
    #: condition the reversal needs and cannot recompute later.
    moved: Mapped[list[list[str | None]] | None] = mapped_column(JSONB, nullable=True)


class AccountSegmentModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """One named, saved grouping — migration `0055`.

    ⚡ **Two representations of the name and only one is shown.** `name` is what
    the customer typed; `name_key` is `account_tag.fold`'s output and is what
    the unique index is on. ⛔ **A `lower(name)` constraint would not be the
    rule** — `lower("STRASSE")` and `lower("straße")` differ where the customer
    means one segment, and `casefold` is the function that does not.
    """

    __tablename__ = "account_segment"

    segment_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(length=60), nullable=False)
    #: ⛔ **Never rendered.** What uniqueness is decided on, and nothing else.
    name_key: Mapped[str] = mapped_column(String(length=60), nullable=False)


class AccountSegmentMemberModel(Base, WorkspaceScopedMixin):
    """Which accounts are in which segment — migration `0055`.

    ⛔ **No `UPDATE` grant, and none is needed**: an account is in a segment or
    it is removed from it, and there is no field on this row a customer can
    change. Registered in `IMMUTABLE_TENANT_TABLES` for that reason.
    """

    __tablename__ = "account_segment_member"

    segment_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    #: ⛔ **No foreign key**, and the omission is the module boundary: an
    #: account is `knowledge_graph`'s entity (§5).
    account_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    added_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class AccountSegmentBatchModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """One bulk *Add to segment* — migration `0056`.

    ⛔ **`added` is nullable and the null is load-bearing**, on exactly the
    terms `AccountAssignmentBatchModel` states: `NULL` means not applied, `[]`
    means applied and every selected account was already in the segment.
    """

    __tablename__ = "account_segment_batch"

    batch_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    segment_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    requested: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    #: ⚡ **What the reversal removes**, and never `requested`.
    added: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
