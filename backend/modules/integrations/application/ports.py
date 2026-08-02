"""The ports Integrations depends on.

Each belongs to this module because it is this module's language
(`CLAUDE.md` §6), and each is implemented in its own infrastructure.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from modules.integrations.domain.connection import ConnectedAccount
from modules.integrations.domain.grant import Credential, IntegrationGrant


class ConnectedAccountRepository(Protocol):
    """Where a workspace's connections live."""

    async def get(self, workspace_id: UUID, account_id: UUID) -> ConnectedAccount | None: ...

    async def list_for_workspace(self, workspace_id: UUID) -> list[ConnectedAccount]:
        """Every connection a workspace has, in any state.

        **Including unusable ones, deliberately.** A revoked Salesforce is the
        single most important row on a connections screen, and a list that
        quietly omitted it would leave a customer believing their data was
        flowing.
        """
        ...

    async def save(self, account: ConnectedAccount) -> None: ...


class GrantStore(Protocol):
    """Where grants live. **Lifecycle facts only — never secret material.**"""

    async def current_for(
        self, workspace_id: UUID, connected_account_id: UUID
    ) -> IntegrationGrant | None:
        """The live grant for a connection, or `None` if it has never had one."""
        ...

    async def save(self, grant: IntegrationGrant) -> None: ...


class SecretStore(Protocol):
    """Resolves a `secret_ref` into usable material.

    **The seam the eventual vault arrives behind.** `13-integrations.md` puts
    per-workspace grants in AWS Secrets Manager, and `M14.5` provisions it three
    milestones after this one — so the port exists now and its production
    implementation lands later, without any type above it changing.

    **It is also what keeps tokens out of Postgres.** A grant row is backed up,
    replicated and readable by anybody with database access; a `secret_ref` in
    one is a pointer, and a bearer token in one is an incident.
    """

    async def resolve(self, secret_ref: str) -> Credential:
        """The material behind `secret_ref`.

        Raises `SecretNotFound` if the reference has no material — which is a
        real state rather than a bug: a grant row can outlive the secret it
        points at when a vault entry is purged on offboarding.
        """
        ...


class SecretNotFound(Exception):
    """A grant references material the store does not hold."""
