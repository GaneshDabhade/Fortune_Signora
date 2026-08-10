"""SQLAlchemy models for the Action Batch context.

**`infrastructure/` only.** `domain/`, `application/` and `public/` never import
this file, so the aggregate stays free of the tables it happens to be stored in.

**Two tables, and neither is ever updated** — see migration `0042`, which argues
the shape. The identity is written once; every lifecycle event afterwards is a
new row in the log.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Interval,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from modules.action_batch.domain.batch import Transition
from signora_platform.db.base import AuditMixin, Base, TimestampMixin, WorkspaceScopedMixin

#: The alphabet, derived from the domain rather than restated. A sixth
#: transition added to the enum reaches the constraint automatically.
_KNOWN_TRANSITIONS = " OR ".join(f"transition = '{t.value}'" for t in Transition)
#: ⚡ **Derived from the enum, so a transition added there reaches the
#: constraint automatically** — [TASK-465](../../../../docs/BACKLOG.md) added
#: two and this needed no edit beyond the plural.
_UNATTRIBUTED_LIST = ", ".join(f"'{t.value}'" for t in Transition if not t.is_attributed)


class ActionBatchModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """What a batch **is**, which never changes.

    **No `state` column and no `applied_at` column.** Both derive from the
    transition log, and a stored copy would be the second representation §2
    forbids — the one that eventually disagrees with the record an audit cites.
    """

    __tablename__ = "action_batch"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_action_batch_has_a_name"),
        CheckConstraint("item_count >= 1", name="ck_action_batch_covers_something"),
        CheckConstraint(
            "reversible_for IS NULL OR reversible_for > interval '0'",
            name="ck_action_batch_window_is_a_window",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(length=200), nullable=False)
    item_count: Mapped[int] = mapped_column(Integer(), nullable=False)
    proposed_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    proposed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    #: `NULL` means reversal was never offered — not that it expired.
    reversible_for: Mapped[timedelta | None] = mapped_column(Interval(), nullable=True)


class ActionBatchTransitionModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """One thing that happened to a batch. **Append-only.**

    `sequence` is unique per batch, which is what makes the log an ordering
    rather than a bag: replay depends on it, and two writers racing to record
    the same position collide instead of silently interleaving.
    """

    __tablename__ = "action_batch_transition"
    __table_args__ = (
        UniqueConstraint("batch_id", "sequence", name="uq_action_batch_transition_sequence"),
        CheckConstraint("sequence >= 0", name="ck_action_batch_transition_sequence_non_negative"),
        CheckConstraint(
            _KNOWN_TRANSITIONS, name="ck_action_batch_transition_is_a_known_transition"
        ),
        CheckConstraint(
            f"actor_id IS NOT NULL OR transition IN ({_UNATTRIBUTED_LIST})",
            name="ck_action_batch_transition_only_application_is_unattributed",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    batch_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("action_batch.id", ondelete="CASCADE"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(Integer(), nullable=False)
    #: ⚡ **32, widened by migration `0048`** — `application_failed` is 18, and
    #: ⛔ **a column width must not decide a domain verb's name**
    #: ([TASK-465](../../../../docs/BACKLOG.md)).
    transition: Mapped[str] = mapped_column(String(length=32), nullable=False)
    #: `NULL` only for `applied`, enforced above.
    actor_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    #: ⛔ **Why an application failed, and NULL for every other transition** —
    #: [TASK-465](../../../../docs/BACKLOG.md). ⚡ **Stored rather than derived**:
    #: it is the one thing about a failure the aggregate cannot recompute, and
    #: 📁 [P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md) needs it to say
    #: more than *something went wrong*.
    reason: Mapped[str | None] = mapped_column(Text(), nullable=True)
