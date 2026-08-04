"""Telling a vendor that Signora's access is withdrawn.

**The first `ProviderRevoker`, and it closes the gap the disconnect dialog has
been apologising for.** Until now `NoRevoker` reported failure and the product
said so honestly — *"Signora could not tell HubSpot… you may also want to
remove Signora from your HubSpot settings"* — which was true and left the
customer holding a live credential at the vendor.

**Nothing about this depends on how records will one day arrive**
([ADR-0300](../../../../docs/architecture/adr/0300-inbound-customer-systems.md)).
Revocation is a fact about a *grant*, which this module owns outright.

### Why the endpoints live here rather than beside the acquisition ones

`lib/integrations/providers.ts` holds where a customer is *sent* and where a
code is *exchanged*. Those are acquisition, and `18-authentication.md` reserves
them to the Next tier. **This holds where a grant is *destroyed*, which is
management, and §5 puts management in Python.** The two tables never overlap:
no URL appears in both, and neither tier could use the other's.

### A vendor cannot block a disconnect

Every failure below returns `False` rather than raising. `DisconnectSystem`
records the outcome and continues, because **withdrawing access is what
somebody does in a hurry** and a disconnect that failed because the vendor was
down would hold a security action hostage to the system it protects them from.
"""

from __future__ import annotations

from typing import Final
from urllib.parse import quote
from uuid import UUID

import httpx

from modules.integrations.application.ports import (
    ConnectedAccountRepository,
    GrantStore,
    SecretNotFound,
    SecretStore,
)
from modules.integrations.domain.grant import OAuth2Material
from modules.integrations.infrastructure.vendors import VENDOR_ENDPOINTS, RevocationEndpoint
from signora_platform.observability import get_logger

logger = get_logger(__name__)

#: How long to wait for a vendor to acknowledge. **Short deliberately**: the
#: local disconnect proceeds regardless, and a customer watching a spinner
#: while a dead host times out is the worst version of this.
REVOCATION_TIMEOUT_SECONDS: Final = 5.0


class HttpProviderRevoker:
    """Withdraws Signora's access at the vendor, or reports that it could not.

    **Resolves what it needs rather than being handed it**, because the port is
    `revoke(connected_account_id)` and that is the right shape: a caller
    withdrawing access should not have to know that revocation needs a
    credential, a slug and a URL. The cost is two reads the use case has
    already done, which is cheap and happens once per disconnect.
    """

    def __init__(
        self,
        accounts: ConnectedAccountRepository,
        grants: GrantStore,
        secrets: SecretStore,
        workspace_id: UUID,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._accounts = accounts
        self._grants = grants
        self._secrets = secrets
        self._workspace_id = workspace_id
        self._client = client

    async def revoke(self, connected_account_id: UUID) -> bool:
        account = await self._accounts.get(self._workspace_id, connected_account_id)
        if account is None:
            return False

        vendor = VENDOR_ENDPOINTS.get(account.integration)
        endpoint = vendor.revocation if vendor else None
        if endpoint is None:
            # A system Signora can connect but not revoke at. Logged rather
            # than silent: it is the difference between *we tried and failed*
            # and *nobody ever wrote the adapter*, and only one of those is
            # somebody's next task.
            logger.info(
                "no revocation endpoint for integration",
                extra={
                    "workspace_id": str(self._workspace_id),
                    "integration": account.integration,
                },
            )
            return False

        grant = await self._grants.current_for(self._workspace_id, connected_account_id)
        if grant is None:
            return False

        token = await self._token(grant.secret_ref, endpoint.token_field)
        if token is None:
            return False

        return await self._call(endpoint, token, account.integration)

    async def _token(self, secret_ref: str, field: str) -> str | None:
        """The material the vendor wants, out of an opaque credential.

        **The one place `oauth2` material is read**, and it is an adapter —
        which is exactly where a credential's shape is allowed to be known.
        Everything above holds `Credential` and cannot see inside it.
        """
        try:
            credential = await self._secrets.resolve(secret_ref)
        except SecretNotFound:
            # A grant outliving its material. There is nothing to revoke with,
            # and the disconnect proceeds — the material is already gone.
            return None

        material = OAuth2Material.read(credential)
        if material is None:
            return None
        # Explicit rather than `getattr`: a table typo would otherwise resolve
        # to `None` and read as *this vendor issued no refresh token*, which is
        # a legitimate state and would hide the mistake indefinitely.
        if field == "refresh_token":
            return material.refresh_token
        if field == "access_token":
            return material.access_token
        return None

    async def _call(self, endpoint: RevocationEndpoint, token: str, integration: str) -> bool:
        # `safe=""` so a token containing `/` or `&` cannot escape its own
        # position and turn a path segment into a path, or a query value into
        # a second parameter.
        url = endpoint.url_template.replace("{token}", quote(token, safe=""))
        client = self._client or httpx.AsyncClient(timeout=REVOCATION_TIMEOUT_SECONDS)
        owns_client = self._client is None
        try:
            response = await client.request(endpoint.method, url)
        except httpx.HTTPError as exc:
            # **Never raised.** `DisconnectSystem` catches broadly anyway, and
            # returning here keeps the reason in one log line rather than in a
            # traceback the caller deliberately discards.
            logger.warning(
                "revocation failed at the vendor",
                extra={
                    "workspace_id": str(self._workspace_id),
                    "integration": integration,
                    "reason": type(exc).__name__,
                },
            )
            return False
        finally:
            if owns_client:
                await client.aclose()

        # **A vendor that says the grant is already gone has revoked it.** 404
        # on a token that no longer exists is the outcome the customer wanted,
        # and reporting failure would tell them to go and tidy up something
        # that is already tidy.
        revoked = response.is_success or response.status_code == 404
        if not revoked:
            logger.warning(
                "vendor refused revocation",
                extra={
                    "workspace_id": str(self._workspace_id),
                    "integration": integration,
                    "status_code": response.status_code,
                },
            )
        return revoked


__all__ = ["REVOCATION_TIMEOUT_SECONDS", "HttpProviderRevoker"]
