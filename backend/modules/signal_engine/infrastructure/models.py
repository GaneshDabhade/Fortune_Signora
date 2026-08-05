"""SQLAlchemy models for the Signal Engine."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from signora_platform.db.base import AuditMixin, Base, TimestampMixin, WorkspaceScopedMixin


class SignalProfileModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """**Customer-authored configuration**, not derived intelligence.

    Immutable and versioned: a new profile is a new row naming the one it
    supersedes. It cannot be regenerated from anything, so a rebuild that
    dropped it would destroy customer data (migration 0012).
    """

    __tablename__ = "signal_profile"
    __table_args__ = (
        UniqueConstraint("workspace_id", "version", name="uq_signal_profile_version"),
        CheckConstraint("version > 0", name="ck_signal_profile_version_positive"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    entries: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    supersedes: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("signal_profile.id", ondelete="SET NULL"), nullable=True
    )


class SignalModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """Derived intelligence. Rebuildable from business events, and immutable:
    a hypothesis that gains evidence becomes a new signal naming the one it
    replaces.

    There is deliberately no score, priority, likelihood, or rank column.
    """

    __tablename__ = "signal"
    __table_args__ = (
        CheckConstraint(
            "array_length(contributing_event_ids, 1) >= 1", name="ck_signal_cites_business_events"
        ),
        CheckConstraint(
            "array_length(contributing_event_types, 1) >= 1", name="ck_signal_names_event_types"
        ),
        CheckConstraint("relevance <> 'ignored'", name="ck_signal_relevance_is_held"),
        CheckConstraint("window_end >= window_start", name="ck_signal_window_ordered"),
        CheckConstraint("relevant_until >= occurred_at", name="ck_signal_shelf_life_ordered"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("entity.id", ondelete="CASCADE")
    )
    signal_type: Mapped[str] = mapped_column(String(64), nullable=False)
    relevance: Mapped[str] = mapped_column(String(16), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    relevant_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rationale: Mapped[str] = mapped_column(String(1024), nullable=False)
    contributing_event_ids: Mapped[list[UUID]] = mapped_column(
        ARRAY(PGUUID(as_uuid=True)), nullable=False
    )
    contributing_event_types: Mapped[list[str]] = mapped_column(ARRAY(String(64)), nullable=False)
    constituent_signal_ids: Mapped[list[UUID]] = mapped_column(
        ARRAY(PGUUID(as_uuid=True)), nullable=False, default=list
    )
    catalog_version: Mapped[int] = mapped_column(Integer, nullable=False)
    profile_version: Mapped[int] = mapped_column(Integer, nullable=False)
    payload_version: Mapped[int] = mapped_column(Integer, nullable=False)
    supersedes: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("signal.id", ondelete="SET NULL"), nullable=True
    )


class SignalResolutionModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """How a signal left the queue. **A record beside the signal, never a
    column on it.**

    The signal states what Signora concluded from evidence at a moment; a
    person disagreeing with it later has not changed what was concluded. So
    nothing here writes to `signal`, and the acceptance criterion *"resolution
    never mutates the signal or its evidence"* is a property of the schema
    rather than of the code that writes it.

    **Shaped after `opportunity_state`, deliberately.** That table is this
    concept one level up — an append-only, human-authored decision with an
    explicit `actor_id` and its own `occurred_at`, rather than leaning on the
    audit columns. Two records of the same kind should read the same way.

    **The one difference is stricter, not looser**: `actor_id` is `NOT NULL`
    here with no exemption. `opportunity_state` permits exactly one
    machine-authored stage; **no outcome in this table may be authored by
    Signora**, so the column that would carry the exception does not allow it.
    """

    __tablename__ = "signal_resolution"
    __table_args__ = (
        CheckConstraint(
            "outcome IN ('actioned', 'assigned', 'snoozed', 'dismissed')",
            name="ck_signal_resolution_outcome_known",
        ),
        # **Each payload present exactly when its outcome requires it, and
        # absent otherwise.** Written as an equivalence rather than an
        # implication so both directions hold: a `dismissed` row cannot omit
        # its reason, and an `actioned` row cannot smuggle one in. The domain
        # makes the omission unconstructable; this makes it unstorable, which
        # is what a second writer would eventually need.
        CheckConstraint(
            "(outcome = 'assigned') = (assigned_to IS NOT NULL)",
            name="ck_signal_resolution_assignment_names_somebody",
        ),
        CheckConstraint(
            "(outcome = 'snoozed') = (snoozed_until IS NOT NULL)",
            name="ck_signal_resolution_snooze_states_a_time",
        ),
        CheckConstraint(
            "(outcome = 'dismissed') = (dismissal_reason IS NOT NULL)",
            name="ck_signal_resolution_dismissal_gives_a_reason",
        ),
        CheckConstraint(
            "dismissal_reason IS NULL OR length(trim(dismissal_reason)) > 0",
            name="ck_signal_resolution_reason_is_not_blank",
        ),
        # A snooze that has already elapsed is a no-op wearing the clothes of
        # a decision: the queue would show it handled and return it at once.
        CheckConstraint(
            "snoozed_until IS NULL OR snoozed_until > recorded_at",
            name="ck_signal_resolution_snooze_is_not_already_over",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    signal_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("signal.id", ondelete="CASCADE"), nullable=False
    )
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    assigned_to: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    snoozed_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dismissal_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    #: **Never nullable and never the platform.** Every outcome here is a
    #: human judgement; a machine-authored one would be Signora marking its
    #: own work.
    actor_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    #: When the person decided — **not `created_at`**, which is when the row
    #: reached the database. `opportunity_state.occurred_at` separates the two
    #: for the same reason, and a snooze compares against this one.
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    supersedes: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("signal_resolution.id", ondelete="SET NULL"),
        nullable=True,
    )
    payload_version: Mapped[int] = mapped_column(Integer, nullable=False)
