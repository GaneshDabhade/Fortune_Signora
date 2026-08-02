"""SQLAlchemy models for Integrations."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from signora_platform.db.base import AuditMixin, Base, TimestampMixin, WorkspaceScopedMixin


class ConnectedAccountModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """A customer's connection to one of their own systems.

    **Mutable, unlike most of this repository**, and deliberately: a connection
    is not a record of something that *was* true. It is a live relationship
    whose state changes as the customer connects, revokes and reconnects, and
    versioning it would make *"is Salesforce connected?"* a query over history.
    The audit columns carry who last changed it; the operational record of
    *what happened* is the event log's, not this row's.
    """

    __tablename__ = "connected_account"
    __table_args__ = (
        # One connection per account per integration per workspace. Connecting
        # the same Salesforce org twice is a mistake, not a feature — and
        # without this it produces two grants racing to refresh one token.
        UniqueConstraint(
            "workspace_id",
            "integration",
            "external_account_id",
            name="uq_connected_account_identity",
        ),
        Index("ix_connected_account_workspace", "workspace_id", "integration"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    #: A catalog slug, not an enum: a closed enum cannot admit a partner or
    #: customer connector, which is the assumption a marketplace breaks first.
    integration: Mapped[str] = mapped_column(String(64), nullable=False)
    external_account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    endpoint: Mapped[str | None] = mapped_column(String(512), nullable=True)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    connected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class IntegrationGrantModel(Base, WorkspaceScopedMixin, TimestampMixin, AuditMixin):
    """What authorises Signora to act on a connection.

    **Holds no secret material.** `secret_ref` points at a `SecretStore`; the
    material never enters this table, because a row here is backed up,
    replicated and readable by anybody with database access.
    """

    __tablename__ = "integration_grant"
    __table_args__ = (
        Index(
            "ix_integration_grant_account",
            "workspace_id",
            "connected_account_id",
            "revoked_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    connected_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("connected_account.id", ondelete="CASCADE"),
        nullable=False,
    )
    secret_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    scopes: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    refreshable: Mapped[bool] = mapped_column(nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
