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
    #: The customer's own account and opportunity records, enumerated rather
    #: than asked about one at a time. **What [E1](../../../../docs/architecture/401-epic-e1-crm-read.md)
    #: reads**, and deliberately not `CRM_ACTIVITY`, which is logged calls and
    #: emails and remains exactly what it always was.
    CRM_RECORDS = "crm_records"


#: Capabilities the pipeline can actually act on today.
#:
#: **Inbound capabilities are live**: Observation Engine and Business Event
#: Engine are built and running, so evidence arriving from a customer's system
#: reaches a conclusion. **`MESSAGE_DELIVERY` is not**: its consumers —
#: Recommendation Engine and Revenue Intelligence Platform — are deferred and
#: unbuilt, so Signora has nothing to deliver.
#: **`CRM_RECORDS` is deliberately absent.** The port that would read it exists
#: as of 2026-08-04, and **nothing drives it yet** — the runner is
#: [409](../../../../docs/architecture/409-inbound-source-port-contract.md)
#: step 4, in `provider_platform`. Advertising it now would be the Connection
#: Center promising a capability the pipeline cannot deliver, which is the one
#: thing `LIVE_CAPABILITIES` exists to prevent. **It joins this set when the
#: runner lands, and not before.**
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
"""The systems Signora understands, and the two that ship first.

**Day One is one CRM and one calendar** (ruled 2026-08-02). Not breadth — the
launch set exists to deliver real value and to prove the architecture, and both
are better served by two integrations that work than by seven that are listed.

**HubSpot is the first CRM, and Salesforce is the second.** Signora's ICP is
mid-market to upper-mid-market, $20M–$1B ARR
([PRODUCT_DIFFERENTIATORS.md](../../../../PRODUCT_DIFFERENTIATORS.md)), and
HubSpot dominates the lower half of that band where first design partners are
most likely to come from. It is also the materially simpler acquisition: a plain
authorization-code flow against a single host, with no per-org `instance_url`,
no sandbox/production divergence and no API-version pinning — so the first slice
validates *acquisition* rather than Salesforce's object model.

**Salesforce second is the architecture's own test.** *"Would adding a second
CRM require configuration or architectural change?"* is a question worth
answering with evidence rather than confidence, and it is answered cheaply the
moment the first one works.

> **The counter-argument, stated rather than buried:** a named RevOps function
> skews toward Salesforce, and if the first design partners are upper-mid-market
> then Salesforce-first is correct. That is a fact about the sales pipeline
> rather than about the code, and it is the product owner's to overturn.

**Google Calendar is the first calendar.** Microsoft Graph's permission model is
heavier for the same signal, and Google Workspace is the more common in this
band. A meeting booked with an account remains the strongest buying signal the
product can carry, and the cheapest to obtain.

**Slack is deferred, and the catalog already refuses to advertise it.** Its only
capability is delivering conclusions that no built module produces.


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


@dataclass(frozen=True, slots=True)
class ActivationStep:
    """One step a workspace must take before Signora can say anything.

    **The declaration, not the progress.** Whether the step is *done* is derived
    from the connections a workspace actually has; this is the reviewed static
    knowledge of what the steps are and what order they come in — the same
    category as `CATALOG` itself, and owned by the same domain expert.
    """

    capability: Capability
    #: Lower is earlier. **An integer a source declares rather than a position
    #: in a list**, so a system added later lands where it belongs without
    #: anything downstream knowing the set in advance.
    priority: int
    #: Whether Signora can produce anything without it. A blocking step that is
    #: missing is why a workspace has no conclusions; a non-blocking one merely
    #: makes them weaker.
    blocking: bool


#: The steps this module owns, in the order a customer meets them.
#:
#: **Both are blocking**: a CRM is the account and deal record everything scores
#: against, and meetings are what the scoring is largely made of. Neither is
#: something Signora can substitute for.
ACTIVATION_STEPS: Final[tuple[ActivationStep, ...]] = (
    ActivationStep(Capability.CRM_ACTIVITY, priority=100, blocking=True),
    ActivationStep(Capability.MEETINGS, priority=200, blocking=True),
)


def activation_registry() -> tuple[ActivationStep, ...]:
    """The steps this module may currently ask a customer to take.

    **The catalog's own rule, applied to a second reader.** A step is published
    only when its capability is live *and* some system in the catalog supplies
    it — the same test `live_capabilities` already applies to the Connection
    Center, for the same reason: asking somebody to connect a calendar Signora
    cannot act on is the product promising what the pipeline cannot deliver.

    **It can legitimately return nothing**, and that is not a defect to paper
    over — a catalog that supplies no live capability means a misconfigured or
    partly-deployed platform, and the surfaces that read this say so rather
    than rendering an empty list of things to do.
    """
    supplied = {
        capability for entry in CATALOG.values() for capability in entry.live_capabilities
    }
    return tuple(
        sorted(
            (step for step in ACTIVATION_STEPS if step.capability in supplied),
            key=lambda step: step.priority,
        )
    )
