"""Renewing a grant at the vendor — RFC 6749 §6.

**The same standard and the same endpoint as the authorization-code exchange**,
with `grant_type=refresh_token` in place of `authorization_code`. That is why
this needs no vendor-specific branch: HubSpot, Google, Salesforce and Microsoft
all implement §6 identically, and the only per-vendor fact is the URL, which is
a row in `vendors.py`.

**A renewal is a use of a credential, not an acquisition of one.**
[18-authentication.md](../../../../docs/architecture/18-authentication.md)
reserves the redirect, the consent screen and the authorization-code exchange
to the Next tier; a refresh-token grant is none of the three, which is the
precise reading
[44-integrations.md](../../../../docs/architecture/44-integrations.md) §5
already relies on to keep credential *management* here.

**Where the client credentials come from is not this file's business.** It asks
a `ClientCredentialsStore` and acts on the answer; a vendor it has no
credentials for is one it declines to renew, which is the same refusal
`credentialsFor()` performs at the other tier.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any, Final

import httpx

from modules.integrations.application.refresh import (
    ClientCredentials,
    ClientCredentialsStore,
    RenewedMaterial,
)
from modules.integrations.infrastructure.settings import IntegrationSettings
from modules.integrations.infrastructure.vendors import VENDOR_ENDPOINTS
from signora_platform.observability import get_logger

logger = get_logger(__name__)

#: **Longer than revocation's, and deliberately.** A revocation races a
#: customer watching a dialog; a renewal happens before anything is shown, and
#: giving up early costs a connection that could have been saved.
REFRESH_TIMEOUT_SECONDS: Final = 15.0


class HttpTokenRefresher:
    """Asks a vendor for new material, or reports that it could not.

    **`None` for every failure, never a raise.** A refresh that cannot happen
    leaves the grant exactly as it was, and `RefreshGrant` turns that into a
    `REFUSED` outcome a caller can act on — which is more useful than an
    exception carrying a vendor's status code into a layer that has no idea
    what to do with one.
    """

    def __init__(
        self,
        credentials: ClientCredentialsStore,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._credentials = credentials
        # **A transport rather than a client**, so this always owns the client
        # it opens and always closes it. Accepting a client meant a branch on
        # *did somebody give me this?* — and a branch that only a test takes is
        # a branch nothing verifies.
        self._transport = transport
        self._now: Callable[[], datetime] = now or (lambda: datetime.now(UTC))

    async def renew(self, integration: str, refresh_token: str) -> RenewedMaterial | None:
        vendor = VENDOR_ENDPOINTS.get(integration)
        if vendor is None:
            return None

        client_credentials = self._credentials.for_integration(integration)
        if client_credentials is None:
            # Not configured for this vendor. A legitimate state, and the same
            # refusal the acquisition flow performs when its environment holds
            # no client id — logged at info because it is a deployment fact
            # rather than a fault.
            logger.info(
                "no client credentials configured for integration",
                extra={"integration": integration},
            )
            return None

        try:
            async with httpx.AsyncClient(
                timeout=REFRESH_TIMEOUT_SECONDS, transport=self._transport
            ) as client:
                response = await client.post(
                    vendor.token_url,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "client_id": client_credentials.client_id,
                        "client_secret": client_credentials.client_secret,
                    },
                    headers={"content-type": "application/x-www-form-urlencoded"},
                )
        except httpx.HTTPError as exc:
            logger.warning(
                "grant renewal failed to reach the vendor",
                extra={"integration": integration, "reason": type(exc).__name__},
            )
            return None

        return self._read(response, integration)

    def _read(self, response: httpx.Response, integration: str) -> RenewedMaterial | None:
        if not response.is_success:
            # **A refusal is usually the customer, not an outage.** The
            # commonest 400 here is `invalid_grant`, which means they withdrew
            # Signora at the vendor — so the status is logged and the outcome
            # is left to `RefreshGrant`, which already distinguishes *refused*
            # from *unreadable*.
            logger.warning(
                "vendor refused a grant renewal",
                extra={"integration": integration, "status_code": response.status_code},
            )
            return None

        try:
            payload = response.json()
        except ValueError:
            logger.warning(
                "grant renewal returned something that is not JSON",
                extra={"integration": integration},
            )
            return None

        if not isinstance(payload, dict):
            return None
        access = payload.get("access_token")
        if not isinstance(access, str) or not access:
            # A 200 with no token is the vendor's contract broken. Refusing
            # keeps the old material, which still works until it expires —
            # storing an empty token would end the connection immediately.
            logger.warning(
                "grant renewal carried no access token",
                extra={"integration": integration},
            )
            return None

        refresh = payload.get("refresh_token")
        return RenewedMaterial(
            access_token=access,
            # **Absent means the old one stays valid**, which is Google's
            # behaviour. `RefreshGrant` keeps the previous token when this is
            # `None`; returning an empty string here would look like a new one.
            refresh_token=refresh if isinstance(refresh, str) and refresh else None,
            expires_at=self._expiry(payload.get("expires_in")),
        )

    def _expiry(self, raw: Any) -> datetime | None:
        """`expires_in` is seconds from now (RFC 6749 §5.1).

        Absence means the material does not expire, which is a real state
        rather than a missing value — and it is what `refreshable` without
        `expires_at` already describes on a grant.
        """
        try:
            seconds = int(raw)
        except (TypeError, ValueError):
            return None
        if seconds <= 0:
            return None
        return self._now() + timedelta(seconds=seconds)


class SettingsClientCredentials:
    """Client credentials from the module's own typed configuration.

    **Where §6 already puts a module's configuration** — *a typed Settings
    object owned by the module whose behaviour it governs, constructed only at
    the composition root.* No default, for the same reason `secret_key` has
    none: a defaulted client secret is a known secret, which reads as
    configuration and is not.

    **A vendor with nothing configured returns `None`**, which produces
    `NoTokenRefresher` at the composition root and a product that declines to
    refresh rather than pretending it did.
    """

    def __init__(self, settings: IntegrationSettings) -> None:
        self._settings = settings

    def for_integration(self, integration: str) -> ClientCredentials | None:
        pair = self._settings.client_credentials.get(integration)
        if pair is None:
            return None
        return ClientCredentials(
            client_id=pair.client_id, client_secret=pair.client_secret
        )

    def any_configured(self) -> bool:
        """Whether refreshing is possible at all in this deployment.

        **Read once at the composition root** to choose between a real
        refresher and `NoTokenRefresher`, so a deployment that configured
        nothing gets a wiring that says so rather than one that fails per
        connection.
        """
        return bool(self._settings.client_credentials)


__all__ = ["REFRESH_TIMEOUT_SECONDS", "HttpTokenRefresher", "SettingsClientCredentials"]
