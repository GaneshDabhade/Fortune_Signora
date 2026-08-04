"""SQLAlchemy models for the Commercial Profile.

**Every table here holds a customer-authored declaration** — a statement
somebody typed about their own business, regenerable from nothing. That is a
data category `signal_profile` opened and this module fills: a pipeline
rebuild regenerates everything through buying scores and **must leave all of
these untouched**.

Each is immutable and versioned: a revision is a new row naming the one it
supersedes, enforced by the absent `UPDATE` grant in its migration.
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
