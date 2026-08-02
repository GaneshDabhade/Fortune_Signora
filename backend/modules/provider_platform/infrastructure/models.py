"""SQLAlchemy models for the Provider Platform.

Infrastructure layer only — never imported by `domain/`, `application/`,
or `public/` (CLAUDE.md §8).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from signora_platform.db.base import AuditMixin, Base, TimestampMixin, WorkspaceScopedMixin


class ProviderSyncModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    __tablename__ = "provider_sync"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    capability: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    records_received: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pages_fetched: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_kind: Mapped[str | None] = mapped_column(String(32), nullable=True)
    failure_message: Mapped[str | None] = mapped_column(String(1024), nullable=True)


class ProviderWatermarkModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """Separate from the sync so resetting it — the standard recovery from
    a bad run — does not require editing or deleting sync history."""

    __tablename__ = "provider_watermark"
    __table_args__ = (
        # **`subject` is part of the key** (B-004). Without it a workspace
        # watching two accounts shares one position between them, and the
        # second account's sync silently starts from the first's.
        UniqueConstraint(
            "workspace_id",
            "provider",
            "capability",
            "subject",
            name="uq_provider_watermark_subject",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    capability: Mapped[str] = mapped_column(String(64), nullable=False)
    #: Opaque to the platform and interpreted only by the adapter
    #: ([ADR-0036](../../../docs/architecture/adr/0036-target-account-contract.md)
    #: §5) — a company name as the customer typed it. Empty on rows written
    #: before the column existed; those match no real subject and are inert.
    subject: Mapped[str] = mapped_column(String(512), nullable=False)
    position: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RawProviderRecordModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """Raw records, stored before interpretation.

    The unique constraint is what makes a re-sync idempotent at the storage
    layer: a snapshot re-delivering everything must not duplicate rows.
    Deduplication is on `(workspace, provider, external_id, occurred_at)` —
    a provider legitimately reports the same subject at different times,
    and collapsing those would erase the history the pipeline reads.
    """

    __tablename__ = "raw_provider_record"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "provider",
            "external_id",
            "occurred_at",
            name="uq_raw_provider_record_identity",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    sync_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("provider_sync.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    capability: Mapped[str] = mapped_column(String(64), nullable=False)
    external_id: Mapped[str] = mapped_column(String(512), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
