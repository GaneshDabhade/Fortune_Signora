"""Establishing whether a HubSpot connection actually works.

**The anticorruption layer for the probe, and it is a translation rather than
a taxonomy.** `HubSpotCompanies` already classifies every way a call can fail;
this maps that classification onto the module's own, and nothing new is
invented. A second error hierarchy here would be the duplicated truth §2
refuses — and the one that drifted would be this one, because it is the copy
nobody exercises.

**The smallest real call the vendor offers.** One company, one property. The
question is whether the door opens, and reading a customer's book of business
to answer it would spend their API quota on Signora's bookkeeping.
"""

from __future__ import annotations

from typing import Final

import httpx

from modules.integrations.application.probe import Reachability
from modules.integrations.application.resolve import ExecutionContext
from modules.integrations.domain.grant import OAuth2Material
from modules.integrations.domain.health import ProbeResult
from modules.integrations.infrastructure.hubspot import (
    CrmCredentialRejected,
    CrmPayloadInvalid,
    CrmPermanent,
    CrmTransient,
    HubSpotCompanies,
)
from signora_platform.observability import get_logger

logger = get_logger(__name__)

#: One record is enough to prove the door opens, and one property is enough to
#: request a record. **`name` rather than the mapper's full set**: a probe that
#: asked for everything a sync asks for would fail differently from a sync for
#: reasons that have nothing to do with the connection.
_PROBE_PROPERTIES: Final = frozenset({"name"})

_PROBE_PAGE_SIZE: Final = 1


class HubSpotReachability:
    """Asks HubSpot one small question and reports what came back."""

    def __init__(self, *, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._companies = HubSpotCompanies(_PROBE_PROPERTIES, transport=transport)

    async def reach(self, context: ExecutionContext) -> Reachability:
        """**Never raises for a failed probe.** A failure is the answer.

        An exception escaping here would make *"the connection is broken"*
        indistinguishable from *"the probe is broken"*, and only one of those
        is something a customer can act on.
        """
        material = OAuth2Material.read(context.credential)
        if material is None:
            # The grant is not OAuth2, or its material is unreadable. **Not a
            # vendor failure** — nothing was asked — but it is conclusive: this
            # connection cannot be used until it is made again. **The reason
            # names no part of the credential** (§16); *why* it is unreadable
            # is not something the customer can act on differently.
            return Reachability(
                ProbeResult.CREDENTIAL_REJECTED,
                "the stored credential is not one this connection can be used with",
            )

        try:
            await self._companies.page(
                access_token=material.access_token, limit=_PROBE_PAGE_SIZE
            )
        except CrmCredentialRejected as exc:
            return Reachability(ProbeResult.CREDENTIAL_REJECTED, str(exc))
        except CrmPayloadInvalid as exc:
            return Reachability(ProbeResult.UNUSABLE_RESPONSE, str(exc))
        except CrmPermanent as exc:
            # A working credential that may not do this. **Ordered after
            # `CrmCredentialRejected` and `CrmPayloadInvalid` because both
            # subclass it** — the general case has to be caught last, or the
            # two distinctions the taxonomy draws are lost here.
            return Reachability(ProbeResult.PERMISSION_MISSING, str(exc))
        except CrmTransient as exc:
            # Includes `CrmRateLimited`, deliberately: both mean *nothing was
            # established*, and a rate limit is the vendor's business rather
            # than the customer's.
            return Reachability(ProbeResult.UNAVAILABLE, str(exc))

        return Reachability(ProbeResult.REACHABLE)
