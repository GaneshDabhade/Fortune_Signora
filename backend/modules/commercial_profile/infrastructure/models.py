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

from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Integer, UniqueConstraint
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
