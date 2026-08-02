"""Where integration credentials actually live.

**The port's first real implementation, and deliberately a modest one.**
[13-integrations.md](../../../../docs/architecture/13-integrations.md) puts
per-workspace grants in AWS Secrets Manager, and `M14.5` provisions it three
milestones from here. Until then the material lives in its own table,
**encrypted at rest**, behind the same `SecretStore` the vault will implement.

**Encrypted rather than merely separated.** A token in a plain column is a
token in every backup, every replica and every engineer's `psql` session. The
key is injected as configuration and never defaulted: a default would ship a
known key, which is worse than no encryption because it reads as protection.

**Its own table rather than a column on `integration_grant`.** The grant is
lifecycle — read on every connections screen, joined, listed, counted. The
material is read only when a call is about to be made. Separating them means
the common query never touches ciphertext, and a future move to a vault deletes
a table rather than migrating a column out of a hot aggregate.
"""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import String, delete, select
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from modules.integrations.application.ports import SecretNotFound
from modules.integrations.domain.grant import Credential
from signora_platform.db.base import Base, TimestampMixin, WorkspaceScopedMixin


class IntegrationSecretModel(Base, WorkspaceScopedMixin, TimestampMixin):
    """Encrypted credential material, addressed by `secret_ref`."""

    __tablename__ = "integration_secret"

    secret_ref: Mapped[str] = mapped_column(String(255), primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    ciphertext: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    #: Carried so a purge on offboarding can find every secret for a connection
    #: without reading the grants table.
    connected_account_id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), nullable=False)


class EncryptedSecretStore:
    """`SecretStore` backed by an encrypted table."""

    def __init__(self, session: AsyncSession, key: str) -> None:
        self._session = session
        self._fernet = Fernet(key)

    async def resolve(self, secret_ref: str) -> Credential:
        row = (
            await self._session.execute(
                select(IntegrationSecretModel).where(
                    IntegrationSecretModel.secret_ref == secret_ref
                )
            )
        ).scalar_one_or_none()
        if row is None:
            raise SecretNotFound(secret_ref)
        try:
            material = self._fernet.decrypt(row.ciphertext)
        except InvalidToken as exc:
            # A rotated or wrong key is indistinguishable from corruption here,
            # and both mean the same thing to a caller: this credential cannot
            # be used. Surfacing it as "not found" would send an engineer
            # looking for a missing row that is present.
            raise SecretUndecryptable(secret_ref) from exc
        return Credential(kind=row.kind, material=material)

    async def store(
        self, *, secret_ref: str, workspace_id: str, connected_account_id: str, credential: Credential
    ) -> None:
        self._session.add(
            IntegrationSecretModel(
                secret_ref=secret_ref,
                workspace_id=workspace_id,
                connected_account_id=connected_account_id,
                kind=credential.kind,
                ciphertext=self._fernet.encrypt(credential.material),
            )
        )

    async def purge_for(self, connected_account_id: str) -> None:
        """Delete every secret for a connection.

        **Offboarding's half that the grant table cannot do.** Deleting a grant
        row leaves material behind; this is what makes disconnecting actually
        remove the credential rather than merely forget the pointer.
        """
        await self._session.execute(
            delete(IntegrationSecretModel).where(
                IntegrationSecretModel.connected_account_id == connected_account_id
            )
        )


class SecretUndecryptable(SecretNotFound):
    """Material exists and the configured key cannot read it.

    **A subclass, so a caller handling *"this credential cannot be used"* handles
    both without knowing which.** A rotated key and a purged secret are the same
    fact to everything above the adapter: the connection must be made again.
    The distinct type survives for the log line, where the difference is the
    whole diagnosis.
    """
