"""SQLAlchemy ORM models for this module's tables.

Deliberately distinct from the domain entities in ``domain/entities.py`` —
mapping between the two happens explicitly in ``repositories.py`` rather
than using the ORM models as the domain model, keeping the domain layer
free of any SQLAlchemy dependency (docs/architecture/15-project-structure.md).
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import JSONB
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
    # **The live-membership uniqueness is a partial index in migration 0032.**
    # SQLAlchemy cannot express a partial unique constraint, and a total one
    # here would refuse a legitimate re-join after somebody was removed.

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
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    ended_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    member_email: Mapped[str | None] = mapped_column(String(320), nullable=True)


class InvitationModel(Base, TimestampMixin, AuditMixin):
    """An offer of membership, addressed to an email that may not be a user yet.

    Cascades with its workspace exactly as ``MembershipModel`` does: an
    invitation into an organization that no longer exists is not history worth
    keeping, it is a row nothing can resolve.

    **The live-invitation uniqueness is a partial index in migration 0031**, not
    a constraint here — SQLAlchemy cannot express a partial unique constraint,
    and expressing half of it would be worse than expressing none.
    """

    __tablename__ = "invitation"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("workspace.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invited_email: Mapped[str] = mapped_column(String(320), nullable=False)
    role: Mapped[WorkspaceRole] = mapped_column(
        SqlEnum(
            WorkspaceRole,
            name="workspace_role",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MembershipRoleChangeModel(Base, TimestampMixin, AuditMixin):
    """What somebody was allowed to do, and when it changed.

    **Append-only**, enforced by the grant in migration 0034 rather than by
    convention: `SELECT` and `INSERT`, and no `UPDATE`.
    """

    __tablename__ = "membership_role_change"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("workspace.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    membership_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("membership.id", ondelete="CASCADE"),
        nullable=False,
    )
    previous_role: Mapped[WorkspaceRole] = mapped_column(
        SqlEnum(
            WorkspaceRole,
            name="workspace_role",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    new_role: Mapped[WorkspaceRole] = mapped_column(
        SqlEnum(
            WorkspaceRole,
            name="workspace_role",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )


class SavedViewModel(Base, TimestampMixin, AuditMixin):
    """A named, shared declaration of a query — one row per *version*.

    **The declaration is `JSONB` and this module never reads inside it**
    ([D-091](../../../../docs/DECISION_REGISTER.md)). ⚡ **No GIN index, and
    that is the reason**: an index on the document's keys exists to answer
    questions *about* the declaration, and asking one here is the first step
    to `workspace_tenancy` owning another module's semantics.

    ⛔ **No `is_live` column.** Live is derived from the supersession chain —
    a boolean beside it would be the same fact stored twice, and the two would
    disagree the first time a version landed (§2).
    """

    __tablename__ = "saved_view"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("workspace.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    declaration: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    # `created_by` is AuditMixin's — the author the public contract names is
    # the same fact the audit column already holds, and declaring it twice
    # would be two columns for one truth.
    supersedes: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        # **`SET NULL`, not `CASCADE`.** A superseded version is never deleted
        # in normal operation, but if one ever were, the versions after it must
        # survive: the chain is history, and losing a later reading because an
        # earlier one went is exactly what versioning exists to prevent.
        ForeignKey("saved_view.id", ondelete="SET NULL"),
        nullable=True,
    )
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OnboardingRunModel(Base, TimestampMixin, AuditMixin):
    """One person's run through onboarding, in one workspace — **TASK-469**.

    ⚡ **Every answer column is nullable, and that is the design rather than
    laxity.** *"An abandoned onboarding still produces a customer"* — a
    `NOT NULL` industry would turn the person who left at step 3 into a row
    that cannot be written, which is the opposite of what skippable means.

    ⛔ **No `features` column.** The goals imply them deterministically and the
    aggregate derives them on read (§2, *truth has exactly one authoritative
    representation*). **A stored copy is the one that disagrees** the first
    time the mapping changes — and a customer would then see a home page built
    from a rule the product no longer holds.

    ⚠️ **Each answer carries its provenance in its own column**, because the
    design requires *"every inferred value marked as inferred and
    correctable"*. **One shared provenance would be wrong for three of the
    four company facts the moment a person corrected any one of them.**
    """

    __tablename__ = "onboarding_run"

    workspace_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("workspace.id", ondelete="CASCADE"),
        primary_key=True,
    )
    # **Composite key, not a surrogate id.** A workspace has many members and
    # each arrives once, so *(workspace, person)* is the identity — and it is
    # what stops a second member resuming the first member's run.
    person_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_step: Mapped[str] = mapped_column(String(16), nullable=False)
    # The rail's done marks. **A list of names rather than a count**, because
    # a person can go back: *"Back is always available, never destructive."*
    completed_steps: Mapped[list[str]] = mapped_column(JSONB, nullable=False)

    industry: Mapped[str | None] = mapped_column(String(64), nullable=True)
    industry_provenance: Mapped[str | None] = mapped_column(String(16), nullable=True)
    company_size: Mapped[str | None] = mapped_column(String(16), nullable=True)
    company_size_provenance: Mapped[str | None] = mapped_column(String(16), nullable=True)
    region: Mapped[str | None] = mapped_column(String(32), nullable=True)
    region_provenance: Mapped[str | None] = mapped_column(String(16), nullable=True)
    # An IANA zone. The design's fallback to UTC is *visible*, so the stored
    # value is the real one and the note is the screen's, not a magic string.
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timezone_provenance: Mapped[str | None] = mapped_column(String(16), nullable=True)

    role: Mapped[str | None] = mapped_column(String(32), nullable=True)
    role_provenance: Mapped[str | None] = mapped_column(String(16), nullable=True)
    team_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    team_size_provenance: Mapped[str | None] = mapped_column(String(16), nullable=True)

    # **Ordered**, because the design says the goals order the home page.
    goals: Mapped[list[str]] = mapped_column(JSONB, nullable=False)

    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # ⚡ **Separate from `finished_at` on purpose.** *Left* and *completed* are
    # different facts and the resume banner reads the difference.
    skipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
