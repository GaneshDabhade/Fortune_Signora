"""Shared SQLAlchemy declarative base and column mixins.

Every workspace-owned table's model composes ``TimestampMixin``,
``AuditMixin``, and ``WorkspaceScopedMixin`` — the four mandatory audit/
tenancy columns (``workspace_id``, ``created_at``, ``updated_at``,
``created_by``, ``updated_by``) are never hand-rolled per table.

The one deliberate exception is the ``workspace`` table itself: it is the
tenancy root, not a workspace-owned table, so it composes ``TimestampMixin``
and ``AuditMixin`` but never ``WorkspaceScopedMixin`` — see
docs/architecture/11-tenancy.md.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base shared by every module's SQLAlchemy models."""


class TimestampMixin:
    """``created_at`` / ``updated_at`` audit columns, required on every table."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # onupdate is evaluated by SQLAlchemy on ORM flush, not by a Postgres
    # trigger — PostgreSQL has no built-in "ON UPDATE CURRENT_TIMESTAMP"
    # equivalent, and a trigger-based approach was judged unnecessary
    # operational complexity for a value the ORM can set reliably itself.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class AuditMixin:
    """``created_by`` / ``updated_by`` columns, required on every table.

    These reference a Better Auth user id, not a local ``users`` table —
    Signora does not own the user identity model (ADR-0010), so these are
    plain UUID columns rather than foreign keys.
    """

    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    updated_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)


class WorkspaceScopedMixin:
    """``workspace_id`` column required on every workspace-owned table.

    Composing this mixin is necessary but not sufficient for tenant
    isolation — the owning module's Alembic migration must also enable and
    force Row-Level Security on the table (docs/architecture/11-tenancy.md).
    """

    workspace_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
