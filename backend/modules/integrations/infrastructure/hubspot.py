"""Reading a customer's companies out of HubSpot.

**Vendor logic, and nothing else.** Its inputs are an access token, a watermark
and a cursor; its output is raw payloads exactly as HubSpot returned them. It
holds no port, publishes no event, writes no row and knows nothing about how a
record reaches Provider Normalization.

> **Its location is provisional and its behaviour is not.**
> [ADR-0300](../../../../docs/architecture/adr/0300-inbound-customer-systems.md)
> decides *who calls this and where the file lives* — a sibling port here, an
> extended Provider Port in `provider_platform`, or a second ingestion path.
> **All three call something that does exactly this**, so the ruling moves a
> file and rewrites a wrapper. Written here because this module already holds
> the credential and because writing it in a module another lane is assigned
> would be the boundary violation.

**Nothing is stored and nothing is normalized.** The payload is handed on
untouched, because interpreting it is `HubSpotCompanyMapper`'s job and a
fetcher that reshaped anything would put the vendor's contract in two places.

**The properties it asks for come from the mapper.** A CRM returns only what
you request, so a mapper that reads `industry` and a fetcher that never asks
for it produce a claim that silently never appears — no error, no rejection,
just a thinner record. The two are asserted equal by a test.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Final

import httpx

from signora_platform.observability import get_logger

logger = get_logger(__name__)

#: HubSpot's own ceiling for these endpoints. Asking for more is a `400`.
MAX_PAGE_SIZE: Final = 100

READ_TIMEOUT_SECONDS: Final = 30.0

_BASE: Final = "https://api.hubapi.com/crm/v3/objects/companies"


class CrmReadError(Exception):
    """Base for every failure this fetcher surfaces. No httpx escapes it."""


class CrmTransient(CrmReadError):
    """Retry with backoff — a timeout, a 5xx, a dropped connection."""


class CrmRateLimited(CrmTransient):
    """Transient, with the vendor's own wait when it supplied one.

    A subclass rather than a flag, so a caller handling transient failures
    generically still backs off correctly. **Guessing a backoff when the vendor
    stated one is how an integration gets throttled harder.**
    """

    def __init__(self, message: str, retry_after_seconds: float | None = None) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class CrmPermanent(CrmReadError):
    """Do not retry — a rejected credential, a missing scope, a bad request."""


class CrmCredentialRejected(CrmPermanent):
    """The token no longer works.

    **Distinct because the response differs entirely.** A rejected credential
    is a connection that needs renewing or reconnecting, and retrying it burns
    quota to no purpose — while a missing scope needs the customer back.
    """


class CrmPayloadInvalid(CrmPermanent):
    """HubSpot answered, but not with something usable.

    An alert about the integration rather than about one company: the vendor
    changed a shape, or a proxy returned a page where JSON belonged.
    """


@dataclass(frozen=True, slots=True)
class CompanyPage:
    """One page of companies, plus what is needed to fetch the next.

    `next_cursor` and `has_more` are separate rather than inferred from one
    another — the same reasoning the Provider Port already applies, and for the
    same measured reason: a vendor legitimately returns a cursor with no
    further records, and conflating them costs one empty request per sync.
    """

    records: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    next_cursor: str | None = None
    has_more: bool = False


class HubSpotCompanies:
    """Fetches one page of companies, and translates every failure.

    **Pagination is the caller's loop.** An adapter that paginated internally
    would hide the page boundary that rate limiting and backpressure need to
    see — which is the rule the Provider Port states and the reason a sync can
    be paced at all.
    """

    def __init__(
        self,
        properties: frozenset[str],
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        #: Sorted so two runs of one sync request the same thing. **Insertion
        #: order is a hidden input** (§2), and a set's iteration order would
        #: make a recorded request unreproducible.
        self._properties = tuple(sorted(properties))
        self._transport = transport

    async def page(
        self,
        *,
        access_token: str,
        since: datetime | None = None,
        cursor: str | None = None,
        limit: int = MAX_PAGE_SIZE,
    ) -> CompanyPage:
        """One page. `since` requests only what changed after it.

        **Two endpoints, one shape out.** A full listing and an incremental
        read are different HubSpot APIs — `GET /companies` and
        `POST /companies/search` — and which one runs is an implementation
        detail of *this file*. A caller that had to know would be a caller that
        reimplements the choice.
        """
        bounded = max(1, min(limit, MAX_PAGE_SIZE))
        try:
            async with httpx.AsyncClient(
                timeout=READ_TIMEOUT_SECONDS, transport=self._transport
            ) as client:
                response = await (
                    self._changed_since(client, access_token, since, cursor, bounded)
                    if since is not None
                    else self._listing(client, access_token, cursor, bounded)
                )
        except httpx.HTTPError as exc:
            raise CrmTransient(f"could not reach HubSpot: {type(exc).__name__}") from exc

        self._raise_for(response)
        return self._read(response)

    async def _listing(
        self,
        client: httpx.AsyncClient,
        token: str,
        cursor: str | None,
        limit: int,
    ) -> httpx.Response:
        params: dict[str, str] = {
            "limit": str(limit),
            "properties": ",".join(self._properties),
        }
        if cursor is not None:
            params["after"] = cursor
        return await client.get(_BASE, params=params, headers=_auth(token))

    async def _changed_since(
        self,
        client: httpx.AsyncClient,
        token: str,
        since: datetime,
        cursor: str | None,
        limit: int,
    ) -> httpx.Response:
        """**Incremental, so a re-sync is not a full re-read.**

        HubSpot filters on `hs_lastmodifieddate` in epoch milliseconds. The
        watermark is *when Signora last read*, so `GT` rather than `GTE` — a
        record modified in the same millisecond as the previous run's boundary
        was already delivered, and re-delivering it is the duplicate the
        storage layer would then have to absorb.
        """
        body: dict[str, Any] = {
            "limit": limit,
            "properties": list(self._properties),
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "hs_lastmodifieddate",
                            "operator": "GT",
                            "value": str(int(since.timestamp() * 1000)),
                        }
                    ]
                }
            ],
            # Ascending, so a sync interrupted mid-way leaves a watermark that
            # can be resumed from rather than a hole in the middle.
            "sorts": [{"propertyName": "hs_lastmodifieddate", "direction": "ASCENDING"}],
        }
        if cursor is not None:
            body["after"] = cursor
        return await client.post(f"{_BASE}/search", json=body, headers=_auth(token))

    @staticmethod
    def _raise_for(response: httpx.Response) -> None:
        if response.is_success:
            return
        if response.status_code == 401:
            raise CrmCredentialRejected("HubSpot rejected the credential")
        if response.status_code == 403:
            # A working token without a scope. **Not a credential problem** —
            # reconnecting with the same permissions would fail identically.
            raise CrmPermanent("HubSpot refused: the connection lacks a needed permission")
        if response.status_code == 429:
            raise CrmRateLimited(
                "HubSpot rate limit reached",
                _seconds(response.headers.get("retry-after")),
            )
        if response.status_code >= 500:
            raise CrmTransient(f"HubSpot returned {response.status_code}")
        raise CrmPermanent(f"HubSpot refused the request with {response.status_code}")

    @staticmethod
    def _read(response: httpx.Response) -> CompanyPage:
        try:
            payload = response.json()
        except ValueError as exc:
            raise CrmPayloadInvalid("HubSpot returned something that is not JSON") from exc

        if not isinstance(payload, dict):
            raise CrmPayloadInvalid("HubSpot returned a document that is not an object")

        results = payload.get("results")
        if not isinstance(results, list):
            # **Distinct from an empty page.** No results is a fact about a
            # workspace; a missing `results` is a fact about the contract, and
            # collapsing them would make a vendor shape change look like a
            # customer with no companies.
            raise CrmPayloadInvalid("HubSpot returned a page with no results array")

        records = tuple(row for row in results if isinstance(row, dict))
        if len(records) != len(results):
            logger.warning(
                "hubspot page carried entries that were not objects",
                extra={"received": len(results), "usable": len(records)},
            )

        paging = payload.get("paging")
        after = None
        if isinstance(paging, dict):
            nxt = paging.get("next")
            if isinstance(nxt, dict):
                candidate = nxt.get("after")
                after = candidate if isinstance(candidate, str) and candidate else None

        return CompanyPage(records=records, next_cursor=after, has_more=after is not None)


def _auth(token: str) -> dict[str, str]:
    return {"authorization": f"Bearer {token}", "accept": "application/json"}


def _seconds(raw: str | None) -> float | None:
    try:
        return float(raw) if raw is not None else None
    except ValueError:
        return None


__all__ = [
    "MAX_PAGE_SIZE",
    "READ_TIMEOUT_SECONDS",
    "CompanyPage",
    "CrmCredentialRejected",
    "CrmPayloadInvalid",
    "CrmPermanent",
    "CrmRateLimited",
    "CrmReadError",
    "CrmTransient",
    "HubSpotCompanies",
]
