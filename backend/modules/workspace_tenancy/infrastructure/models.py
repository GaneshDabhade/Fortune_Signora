"""SQLAlchemy ORM models for this module's tables.

Deliberately distinct from the domain entities in ``domain/entities.py`` —
mapping between the two happens explicitly in ``repositories.py`` rather
than using the ORM models as the domain model, keeping the domain layer
free of any SQLAlchemy dependency (docs/architecture/15-project-structure.md).
"""

from uuid import UUID

from sqlalchemy import Enum as SqlEnum
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from modules.workspace_tenancy.domain.entities import WorkspaceRole
from signora_platform.db.base import AuditMixin, Base, TimestampMixin


class WorkspaceModel(Base, TimestampMixin, AuditMixin):
    """The tenancy root. Deliberately does not compose
    ``WorkspaceScopedMixin`` — a workspace cannot be scoped to itself. See
    docs/architecture/11-tenancy.md for the RLS policy this table uses
    instead of the standard workspace-scoped policy.
    """

    __tablename__ = "workspace"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)


class MembershipModel(Base, TimestampMixin, AuditMixin):
    """Workspace-owned. Declares ``workspace_id`` explicitly with a foreign
    key to ``workspace.id`` rather than composing the generic
    ``WorkspaceScopedMixin`` — membership rows should be deleted when their
    workspace is deleted, which requires a real FK the shared mixin
    intentionally does not assume for every workspace-owned table (e.g. a
    table referencing an already-deleted workspace for historical/event
    data would not want cascading deletes).
    """

    __tablename__ = "membership"
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_membership_workspace_user"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("workspace.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    # values_callable is required: without it SQLAlchemy persists the Python
    # enum *member name* ("OWNER") rather than its *value* ("owner"), which
    # would not match the PostgreSQL enum labels created in migration 0001.
    role: Mapped[WorkspaceRole] = mapped_column(
        SqlEnum(
            WorkspaceRole,
            name="workspace_role",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
