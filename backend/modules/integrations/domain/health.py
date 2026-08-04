"""Whether a connection actually works, as distinct from whether it looks right.

**The gap this closes.** Everything the Connection Center reports today is
derived from *records* — a grant exists, it has not expired, its state is
`CONNECTED`. **None of that is evidence that the credential still works.** A
token whose HubSpot user lost a permission is structurally perfect and
completely useless, and it reads as healthy until the first sync fails. The
approved CRM Integrations screen is built around exactly that scenario:
*"Writes are paused — the connected user lost a permission… two fields became
read-only for the integration user at 06:41."*

**`ConnectionState.VALIDATED` was designed for this and has never been
reachable.** Its own docstring says *"a real call succeeded with it… a grant
that authenticates but lacks a scope is the commonest integration failure and
is indistinguishable from healthy until the first sync."* The state was
correct; nothing ever performed the call that earns it.

**A probe is a fact about a moment, so it is immutable and append-only** (§2).
Health is then **derived from the probes**, never stored — the same rule
`Attention` already follows, and for the same reason: a stored health column
would be wrong the moment a credential was revoked without anybody writing a
row.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ProbeResult(StrEnum):
    """What one attempt to use a connection established.

    **The vendor's error taxonomy expressed once, in this module's words.**
    The adapter's `Crm*` hierarchy is the same distinctions at the vendor
    boundary; this is what survives the anticorruption layer, and there is
    deliberately no third vocabulary between them.

    **Ordered by nothing.** These are categories, not degrees — the same
    refusal `MatchStrength` makes in the Knowledge Graph, and for the same
    reason: the moment they compare, somebody adds them up.
    """

    #: The call succeeded. The credential works **and** carries the access the
    #: platform needs, which is more than any record could have told us.
    REACHABLE = "reachable"

    #: The vendor rejected the credential outright. Not recoverable by retry
    #: and not recoverable by refresh — the grant was resolved before this
    #: call, so a refreshable credential had already been refreshed.
    CREDENTIAL_REJECTED = "credential_rejected"

    #: The credential authenticates and lacks something the platform needs.
    #: **Deliberately distinct from a rejection**: reconnecting with the same
    #: permissions would fail identically, so telling a customer to reconnect
    #: would waste their time and leave the connection broken.
    PERMISSION_MISSING = "permission_missing"

    #: The vendor answered with something unusable — a changed shape, a proxy
    #: page where JSON belonged. **An alert about the integration**, not about
    #: the customer's credential.
    UNUSABLE_RESPONSE = "unusable_response"

    #: Nothing was established. A timeout, a 5xx, a rate limit. **Not a
    #: verdict**, and treating it as one is how a dashboard turns a vendor's
    #: bad afternoon into a customer's reconnection.
    UNAVAILABLE = "unavailable"

    @property
    def is_conclusive(self) -> bool:
        """Whether this result settles the question on its own.

        **`UNAVAILABLE` is the whole reason this property exists.** A single
        transient failure says nothing about the connection, so it must never
        change a state or raise an alarm by itself — which is what *"two
        consecutive failures"* protects against.
        """
        return self is not ProbeResult.UNAVAILABLE


@dataclass(frozen=True, slots=True)
class ConnectionProbe:
    """One recorded attempt to use a connection.

    **Immutable, like every record of something that happened** (§2). A probe
    is never corrected: a later probe supersedes it by being later, and the
    history is what makes *"it stopped working at 06:41"* answerable at all.

    **It carries no credential and no vendor payload.** `detail` is the
    adapter's own message about the failure — never a response body, never a
    token, never a header (§16).
    """

    id: UUID
    workspace_id: UUID
    connected_account_id: UUID
    result: ProbeResult
    #: Why, in the adapter's words, or `None` when it succeeded. **Not a
    #: sentence for a customer** — the wording is the presentation layer's, on
    #: the rule `ConnectionView.reason` already follows.
    detail: str | None
    probed_at: datetime

    def __post_init__(self) -> None:
        if self.result is ProbeResult.REACHABLE and self.detail is not None:
            raise ValueError("a reachable probe has nothing to explain")


class ConnectionHealth(StrEnum):
    """What the probes say about a connection, derived and never stored."""

    #: The last probe succeeded.
    HEALTHY = "healthy"

    #: The connection is not working. Either a conclusive failure, or **two
    #: consecutive inconclusive ones** — one transient failure is a vendor
    #: having a moment, and two in a row is a pattern worth a customer's
    #: attention.
    DEGRADED = "degraded"

    #: Nothing has been established, because nothing has been tried.
    #: **Absence, not health** — reporting an unprobed connection as healthy
    #: would be the same lie the record-derived view already tells.
    UNKNOWN = "unknown"


#: How many inconclusive failures in a row constitute a pattern.
#:
#: **A product decision with a number attached**, from the approved screen's
#: *"two consecutive failures pause writes"*. Deliberately not configurable: a
#: per-workspace knob here is a setting nobody knows how to answer, and the
#: same reasoning `EXPIRY_WARNING` records.
CONSECUTIVE_FAILURES_FOR_DEGRADED = 2


def health_from(probes: tuple[ConnectionProbe, ...]) -> ConnectionHealth:
    """The health these probes imply. `probes` newest first.

    **Derived on every read** (§2). The probes are the authoritative record;
    this is a reading of them, and a stored copy would disagree with them the
    first time one was written without the copy being updated.
    """
    # Walk back through any run of inconclusive results to the most recent
    # probe that actually established something. **An inconclusive run shorter
    # than the threshold does not overturn what the last real answer was** —
    # it also does not manufacture one, which is why a lone `UNAVAILABLE` with
    # nothing behind it is `UNKNOWN` rather than `HEALTHY`.
    run = 0
    for probe in probes:
        if probe.result is ProbeResult.REACHABLE:
            return ConnectionHealth.HEALTHY
        if probe.result.is_conclusive:
            return ConnectionHealth.DEGRADED
        run += 1
        if run >= CONSECUTIVE_FAILURES_FOR_DEGRADED:
            return ConnectionHealth.DEGRADED
    return ConnectionHealth.UNKNOWN
