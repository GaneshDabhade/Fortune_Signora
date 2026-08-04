"""HubSpot, as a source the platform can read from.

**A translation layer, and nothing else.** `HubSpotCompanies` already knows how
to page a customer's companies and how to classify every way that can fail; it
deliberately *"holds no port, publishes no event, writes no row."* This is the
seam between it and `IntegrationSourceAdapter` — **it fetches nothing and
decides nothing**, which is what keeps the fetcher ignorant of connections and
the port ignorant of HubSpot.

**Four responsibilities**, specified in
[409 §3](../../../../docs/architecture/409-inbound-source-port-contract.md):
unwrap the credential · pass the loop parameters through unchanged · lift each
payload into an `IntegrationRecord` · translate the error hierarchy.

**It holds no property list.** `HubSpotCompanies` is constructed with the set
`HubSpotCompanyMapper.translated_properties()` publishes, wired at the
composition root — a second copy here would put the truth in a third place and
defeat the test written to keep the fetcher and the mapper in step.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from modules.integrations.domain.execution import ExecutionContext
from modules.integrations.domain.grant import OAuth2Material
from modules.integrations.domain.source import (
    IntegrationCapabilityUnsupportedError,
    IntegrationFetchRequest,
    IntegrationPage,
    IntegrationPayloadInvalidError,
    IntegrationRecord,
    IntegrationSourceDescriptor,
    IntegrationSourcePermanentError,
    IntegrationSourceRateLimitedError,
    IntegrationSourceTransientError,
)
from modules.integrations.domain.catalog import Capability
from modules.integrations.infrastructure.hubspot import (
    CrmPayloadInvalid,
    CrmPermanent,
    CrmRateLimited,
    CrmTransient,
    HubSpotCompanies,
)

#: The catalog slug this source answers as. **The same string the connection
#: carries**, so a record's origin has one authoritative representation.
HUBSPOT = "hubspot"

#: What HubSpot's companies endpoint can answer for. **One capability, not
#: every capability the catalog lists for HubSpot** — this source reads
#: records, and a source that claimed `CRM_ACTIVITY` would be promising logged
#: calls it never fetches.
_ANSWERS_FOR = (Capability.CRM_RECORDS,)

#: The property HubSpot's own modification timestamp arrives under, **and the
#: same field the fetcher filters on**. Watermark, filter and record timestamp
#: must be one field, or a sync re-reads or silently skips.
_MODIFIED_AT = "hs_lastmodifieddate"


class HubSpotCompanySource:
    """`HubSpotCompanies`, wearing the port."""

    def __init__(self, companies: HubSpotCompanies) -> None:
        self._companies = companies

    def describe(self) -> IntegrationSourceDescriptor:
        return IntegrationSourceDescriptor(integration=HUBSPOT, capabilities=_ANSWERS_FOR)

    async def fetch(self, request: IntegrationFetchRequest) -> IntegrationPage:
        """One page of the customer's companies.

        **The loop parameters pass through one-to-one.** `since`, `cursor` and
        `limit` map straight onto `HubSpotCompanies.page`, which already owns
        *which endpoint runs* — a wrapper that chose would reimplement the
        choice and the two would eventually disagree.
        """
        if request.capability not in _ANSWERS_FOR:
            raise IntegrationCapabilityUnsupportedError(
                f"HubSpot companies cannot answer for {request.capability.value}"
            )

        token = _access_token(request.context)
        try:
            page = await self._companies.page(
                access_token=token,
                since=request.since,
                cursor=request.cursor,
                limit=request.limit,
            )
        except CrmRateLimited as exc:
            # **The vendor's own wait is preserved**, not re-guessed. Guessing
            # a backoff when the vendor stated one is how an integration gets
            # throttled harder.
            raise IntegrationSourceRateLimitedError(
                str(exc), exc.retry_after_seconds
            ) from exc
        except CrmTransient as exc:
            raise IntegrationSourceTransientError(str(exc)) from exc
        except CrmPayloadInvalid as exc:
            raise IntegrationPayloadInvalidError(str(exc)) from exc
        except CrmPermanent as exc:
            # **Catches `CrmCredentialRejected` too, and deliberately last.**
            # Both are permanent for the platform's retry decision — it stops
            # and alerts either way — while the distinction that decides what a
            # customer is told survives on the connection's own health, where
            # reconnecting fixes one and not the other.
            raise IntegrationSourcePermanentError(str(exc)) from exc

        return IntegrationPage(
            records=tuple(_record(raw) for raw in page.records),
            next_cursor=page.next_cursor,
            has_more=page.has_more,
        )


def _access_token(context: ExecutionContext) -> str:
    """**The only place `ExecutionContext` meets a vendor client.**

    Everything above holds a connection; everything below holds a token, and
    neither knows about the other.
    """
    material = OAuth2Material.read(context.credential)
    if material is None:
        # Nothing was asked, and asking would not help. **Permanent**, and the
        # message names no part of the credential (§16).
        raise IntegrationSourcePermanentError(
            "the stored credential is not one this connection can be read with"
        )
    return material.access_token


def _record(raw: dict[str, Any]) -> IntegrationRecord:
    """Lift one HubSpot object into the port's shape.

    **The only place vendor field names appear in this direction**, and the
    payload itself is passed on untouched — nothing is stripped, renamed or
    normalised, because interpreting it is `HubSpotCompanyMapper`'s job.
    """
    external_id = raw.get("id")
    if not isinstance(external_id, str) or not external_id:
        # **A record with no identity cannot be deduplicated**, so it is not a
        # record. Reported as a payload problem about the integration rather
        # than dropped, which would make a shrinking page look like a quiet one.
        raise IntegrationPayloadInvalidError("a HubSpot record arrived with no id")

    properties = raw.get("properties")
    modified = properties.get(_MODIFIED_AT) if isinstance(properties, dict) else None
    occurred_at = _timestamp(modified)
    if occurred_at is None:
        raise IntegrationPayloadInvalidError(
            f"HubSpot record {external_id} carries no readable {_MODIFIED_AT}"
        )

    return IntegrationRecord(
        external_id=external_id, occurred_at=occurred_at, payload=raw
    )


def _timestamp(raw: object) -> datetime | None:
    """HubSpot's modification time, which arrives as ISO-8601 or as epoch
    milliseconds depending on which endpoint answered.

    **Both are read, and neither is guessed.** Defaulting to `now()` for an
    unreadable value would advance the watermark past records nobody has seen
    and make every backfill look like today — which is a silent skip, the class
    [B-004](../../../../docs/BUGS.md) records.
    """
    if isinstance(raw, str) and raw:
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            pass
    # **One epoch conversion, not two.** A string and an int reach the same
    # arithmetic, and writing it twice is two places for the units to drift.
    # `bool` is excluded explicitly because it is an `int` in Python, and
    # `True` would otherwise become 1970.
    if isinstance(raw, bool) or not isinstance(raw, str | int):
        return None
    try:
        return datetime.fromtimestamp(int(raw) / 1000, tz=UTC)
    except (ValueError, OverflowError, OSError):
        return None
