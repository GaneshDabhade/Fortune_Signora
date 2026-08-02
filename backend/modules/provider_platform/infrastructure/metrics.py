"""The Provider Platform's own operational metrics.

Module-owned, not added to `PipelineMetrics`. A module owns everything required
to realize its behaviour, and the platform composes modules rather than becoming
the owner of their internals (`CLAUDE.md` §2) — the same reasoning that put
`AISettings` and the AI Platform's own counter inside their module.

**`SyncReporter` — the port this implements — lives in `application/ports.py`**,
beside the other contracts `RunProviderSync` consumes. Only the adapter is here,
because only the adapter knows OpenTelemetry exists.

### Why a counter when every sync is already a row

**`provider_sync` cannot answer a platform-wide question.** It is
workspace-owned with forced RLS, and every runtime identity is scoped to one
workspace — by design, and permanently. So *"what is the sync failure rate right
now"* and *"is polling volume growing"* are **unanswerable from the table**,
because answering them means reading across every tenant, which is precisely
what the tenancy model exists to prevent.

That is not a duplicated truth (§2): the row records **what happened to one
workspace's sync**, and these record **how the platform as a whole is
behaving**. Only one of them can be read by an operator, and only the other can
be cited to a customer.

### Each instrument names the decision that needs it

**[12-scalability.md](../../../../docs/architecture/12-scalability.md) states
the extraction trigger for this module:** *"if provider count and polling volume
grow to the point where its scheduling/quota logic needs an independent
deployment and on-call surface."* **That trigger is unmeasurable today** — and
§17 is explicit that stage latency, throughput and error rate exist *because*
the scaling triggers depend on them.

**The sharpest of the three is contract failure.** `SyncFailureKind.CONTRACT`
means a provider's payload stopped matching what the adapter expects — an
integration that has silently started dropping data rather than one that is
down. Today it is a log line and a tenant-scoped row, and **nothing aggregates
it**, so the first sign would be a customer asking why an account went quiet.

**Nothing here is a spend figure.** Operational facts and commercial policy stay
separate (§10, ratified 2026-07-30): a price is a contract term that changes
without the code changing, so cost is applied at reporting time over these
counts and never written beside them.
"""

from __future__ import annotations

from typing import Final

from opentelemetry import metrics

from modules.provider_platform.domain.provider import ProviderName
from modules.provider_platform.domain.sync import SyncFailureKind

_METER_NAME: Final = "signora.provider_platform"

SYNC_DURATION: Final = "signora.provider.sync_duration_ms"
RECORDS_RECEIVED: Final = "signora.provider.records_received"
SYNC_FAILURES: Final = "signora.provider.sync_failures"


class SyncMetrics:
    """The real instruments, constructed once per process.

    Passed explicitly rather than reached for as a module global, so a test
    asserts on a real instance instead of into global state — the same choice
    `PipelineMetrics` made and for the same reason.
    """

    def __init__(self, meter: metrics.Meter) -> None:
        self._duration = meter.create_histogram(
            SYNC_DURATION,
            unit="ms",
            description="Wall time of one provider sync, start to terminal state",
        )
        self._records = meter.create_counter(
            RECORDS_RECEIVED,
            unit="1",
            description="Records received from providers",
        )
        self._failures = meter.create_counter(
            SYNC_FAILURES,
            unit="1",
            description="Provider syncs that ended in a failure, by kind",
        )

    def sync_completed(self, *, provider: ProviderName, duration_ms: int, records: int) -> None:
        # **Provider is an attribute, never a separate metric name.** One
        # instrument per decision; a metric per vendor would make "is polling
        # volume growing" a query nobody can write without knowing the vendor
        # list, and the vendor list changes.
        attributes = {"provider": provider.value}
        self._duration.record(duration_ms, attributes)
        self._records.add(records, attributes)

    def sync_failed(
        self, *, provider: ProviderName, kind: SyncFailureKind, duration_ms: int
    ) -> None:
        # **Duration is recorded on failure too.** A sync that failed after
        # four minutes and one that failed instantly are different incidents,
        # and a latency series that silently excluded failures would look
        # healthiest exactly when a provider had started timing out.
        self._duration.record(duration_ms, {"provider": provider.value})
        self._failures.add(1, {"provider": provider.value, "kind": kind.value})


def build_sync_metrics() -> SyncMetrics:
    return SyncMetrics(metrics.get_meter(_METER_NAME))


__all__ = [
    "RECORDS_RECEIVED",
    "SYNC_DURATION",
    "SYNC_FAILURES",
    "SyncMetrics",
    "build_sync_metrics",
]
