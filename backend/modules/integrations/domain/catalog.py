"""What Signora understands how to connect to, and what each connection gives.

**Reviewed static knowledge a domain expert owns** — the same category as the
Signal Catalog, and the reason it is a table here rather than an inference
anywhere (`CLAUDE.md` §2, least-powerful author). Adding a system is a row.

**A capability is the stable concept; a vendor merely implements one.** That is
the rule the AI Platform holds for models and Provider Platform holds for
providers, and it is what lets Salesforce be replaced by HubSpot without a
customer-facing word changing: both supply `CRM_ACTIVITY`, and the screen talks
about what a customer gets rather than about who supplies it.

**Nothing here claims a capability the platform cannot execute.** `live` is that
rule made checkable: a capability whose consuming pipeline exists reads `True`,
and one waiting on an unbuilt module reads `False`. A Connection Center that
promised meeting intelligence Signora cannot yet produce would be the product
asserting something untrue — the failure [C-017](../../../../docs/LANE_COORDINATION.md)
proposes as a permanent principle.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final


class Capability(StrEnum):
    """What connecting a system gives Signora.

    Engineering's words. The Connection Center turns them into a customer's,
    which is where [ADR-0034](../../../../docs/architecture/adr/0034-ubiquitous-language.md)
    puts the translation.
    """

    #: Activity recorded in a CRM — calls, emails, meetings logged against an
    #: account. An observation source.
    CRM_ACTIVITY = "crm_activity"
    #: Meetings booked with an account. **Arguably the strongest buying signal
    #: the product can carry**, and the cheapest to obtain.
    MEETINGS = "meetings"
    #: Whether an account is engaging with email. An observation source.
    EMAIL_ENGAGEMENT = "email_engagement"
    #: Delivering what Signora concludes into a team's own channels.
    MESSAGE_DELIVERY = "message_delivery"


#: Capabilities the pipeline can actually act on today.
#:
#: **Inbound capabilities are live**: Observation Engine and Business Event
#: Engine are built and running, so evidence arriving from a customer's system
#: reaches a conclusion. **`MESSAGE_DELIVERY` is not**: its consumers —
#: Recommendation Engine and Revenue Intelligence Platform — are deferred and
#: unbuilt, so Signora has nothing to deliver.
LIVE_CAPABILITIES: Final[frozenset[Capability]] = frozenset(
    {Capability.CRM_ACTIVITY, Capability.MEETINGS, Capability.EMAIL_ENGAGEMENT}
)


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    """One system Signora understands."""

    #: The stable identifier. **A slug, never an enum member** — a closed
    #: vocabulary cannot admit a partner-published connector, which is the
    #: first assumption an ecosystem breaks.
    slug: str
    capabilities: tuple[Capability, ...]
    #: Whether a customer can connect it **right now**. Distinct from whether
    #: Signora understands it: the catalog is what the product knows, and this
    #: is what it can currently do about it.
    connectable: bool

    @property
    def live_capabilities(self) -> tuple[Capability, ...]:
        """Only what the platform can act on. What the screen may promise."""
        return tuple(c for c in self.capabilities if c in LIVE_CAPABILITIES)


CATALOG: Final[dict[str, CatalogEntry]] = {
    "salesforce": CatalogEntry("salesforce", (Capability.CRM_ACTIVITY,), connectable=False),
    "hubspot": CatalogEntry("hubspot", (Capability.CRM_ACTIVITY,), connectable=False),
    "google_calendar": CatalogEntry(
        "google_calendar", (Capability.MEETINGS,), connectable=False
    ),
    "outlook_calendar": CatalogEntry(
        "outlook_calendar", (Capability.MEETINGS,), connectable=False
    ),
    "google_workspace": CatalogEntry(
        "google_workspace",
        (Capability.EMAIL_ENGAGEMENT, Capability.MEETINGS),
        connectable=False,
    ),
    "microsoft_365": CatalogEntry(
        "microsoft_365",
        (Capability.EMAIL_ENGAGEMENT, Capability.MEETINGS),
        connectable=False,
    ),
    "slack": CatalogEntry("slack", (Capability.MESSAGE_DELIVERY,), connectable=False),
}
"""The systems Signora understands, and the six the product expects first.

**Every entry is `connectable=False` today, and that is the truthful state**
rather than a placeholder: no acquisition path exists yet, because the OAuth
flow belongs at the frontend edge and has not been built. The catalog says what
the product understands; it does not pretend the button works.

**Slack is listed and supplies only a capability that is not live.** It is here
because the product expects it, and its one capability waits on a module that
does not exist — which is precisely the case `live_capabilities` exists to keep
off a customer's screen.
"""


def entry_for(slug: str) -> CatalogEntry | None:
    """The catalog entry for `slug`, or `None` if Signora does not know it.

    `None` rather than a raise: a connection can outlive a catalog entry that
    was withdrawn, and a customer's existing Salesforce must keep rendering
    after Signora stops offering new Salesforce connections.
    """
    return CATALOG.get(slug)
