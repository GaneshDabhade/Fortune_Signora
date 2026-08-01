"""SQLAlchemy models for the Commercial Profile."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from signora_platform.db.base import AuditMixin, Base, TimestampMixin, WorkspaceScopedMixin


class ProductCatalogModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """**Customer-authored declaration**, not derived intelligence.

    The second table in the platform that cannot be regenerated from
    anything — `signal_profile` was the first, and both need the operational
    treatment derived tables do not: a pipeline rebuild must leave them
    untouched.

    Immutable and versioned: a revision is a new row naming the one it
    supersedes, enforced by the absent `UPDATE` grant in migration `0019`.
    """

    __tablename__ = "product_catalog"
    __table_args__ = (
        UniqueConstraint("workspace_id", "version", name="uq_product_catalog_version"),
        CheckConstraint("version > 0", name="ck_product_catalog_version_positive"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    #: JSONB because a catalog is read whole and never queried field by
    #: field. The same reasoning as `signal_profile.entries`.
    products: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    supersedes: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("product_catalog.id", ondelete="SET NULL"),
        nullable=True,
    )


class IcpDeclarationModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """Who buys each product — **customer-authored declaration**, like the
    catalog, and regenerable from nothing.

    Its own table rather than a column on `product_catalog`: the two are
    separate aggregates versioned independently, and sharing a row would mint
    a description version every time somebody renamed a product.
    """

    __tablename__ = "icp_declaration"
    __table_args__ = (
        UniqueConstraint("workspace_id", "version", name="uq_icp_declaration_version"),
        CheckConstraint("version > 0", name="ck_icp_declaration_version_positive"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
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
