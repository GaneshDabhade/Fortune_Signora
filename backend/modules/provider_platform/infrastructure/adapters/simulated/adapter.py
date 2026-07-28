"""The simulated Provider adapter — the one stage production code sees.

Everything left of this is simulation; everything right of it is
production code that cannot tell the difference. The Provider Port is the
seam, and it is the only seam.

**Currently emits DEVELOPMENT FIXTURE payloads.** That fact is carried on
every response and logged on every emission, but it changes nothing about
the adapter's *behaviour*: it satisfies the same contract, raises the same
failure types, and paginates the same way a production adapter will. When
real payloads arrive, only the generators change.
"""

from __future__ import annotations

from datetime import UTC, datetime

from modules.provider_platform.public import (
    ProviderCapability,
    ProviderCapabilityUnsupportedError,
    ProviderDescriptor,
    ProviderName,
    ProviderPayloadInvalidError,
    ProviderPermanentError,
    ProviderRateLimitedError,
    ProviderRecord,
    ProviderRequest,
    ProviderResponse,
    ProviderTransientError,
    ReplayContext,
)
from signora_platform.simulation.delivery import DeliveryPlan
from signora_platform.simulation.faults import FaultKind
from signora_platform.simulation.generators.base import (
    GENERATOR_VERSION,
    PayloadGenerator,
)
from signora_platform.simulation.observability import ReplayRecord, log_payload_emitted


class SimulatedProviderAdapter:
    """Serves scenario events as provider responses.

    Takes a delivery plan and a generator rather than building either, so
    the same adapter serves every provider — a per-provider adapter class
    would duplicate the Port logic five times and let the implementations
    drift.
    """

    def __init__(
        self,
        *,
        provider: ProviderName,
        capabilities: frozenset[ProviderCapability],
        generator: PayloadGenerator,
        plan: DeliveryPlan,
        replay: ReplayRecord,
        rate_limit_per_minute: int | None = 60,
    ) -> None:
        self._descriptor = ProviderDescriptor(
            provider=provider,
            capabilities=capabilities,
            simulated=True,
            rate_limit_per_minute=rate_limit_per_minute,
        )
        self._generator = generator
        self._plan = plan
        self._replay = replay

    def describe(self) -> ProviderDescriptor:
        """No I/O — the platform calls this to validate a request before
        dispatching, and health calls it for every registered provider."""
        return self._descriptor

    async def fetch(self, request: ProviderRequest) -> ProviderResponse:
        if request.capability not in self._descriptor.capabilities:
            raise ProviderCapabilityUnsupportedError(
                self._descriptor.provider,
                f"does not supply {request.capability}",
            )

        if not request.subject:
            # A permanent failure, not an empty page. An empty page is
            # indistinguishable from "no data available", which is how a
            # malformed request stays unnoticed for a month.
            raise ProviderPermanentError(self._descriptor.provider, "no subject supplied")

        page = self._plan.page(cursor=request.cursor, since=request.since)

        # Faults that change how the adapter *responds* are raised here, as
        # the Port's own types. A bespoke simulator exception would put it
        # on a path production never takes, and the retry logic above would
        # be tested against a mock of itself.
        if page.fault is not None:
            self._raise_if_response_fault(page.fault.kind, page.fault.retry_after_seconds)

        records = tuple(
            self._to_record(event, request.capability) for event in page.events[: request.limit]
        )

        for record in records:
            log_payload_emitted(
                self._replay,
                provider=self._descriptor.provider.value,
                event_ref=record.external_id,
            )

        return ProviderResponse(
            provider=self._descriptor.provider,
            records=records,
            next_cursor=page.next_cursor,
            has_more=page.has_more,
            simulated=True,
            replay=ReplayContext(
                scenario=self._replay.scenario,
                seed=self._replay.seed,
                manifest_version=self._replay.manifest_version,
                generator_version=GENERATOR_VERSION,
                clock_mode=self._replay.clock_mode,
                dataset_version=self._replay.dataset_version,
            ),
        )

    def _raise_if_response_fault(self, kind: FaultKind, retry_after: float | None) -> None:
        provider = self._descriptor.provider
        if kind is FaultKind.TIMEOUT:
            raise ProviderTransientError(provider, "request timed out")
        if kind is FaultKind.SERVER_ERROR:
            raise ProviderTransientError(provider, "upstream returned 503")
        if kind is FaultKind.RATE_LIMITED:
            raise ProviderRateLimitedError(
                provider, "rate limit exceeded", retry_after_seconds=retry_after
            )
        if kind is FaultKind.MALFORMED_PAYLOAD:
            raise ProviderPayloadInvalidError(provider, "response body was not usable")

    def _to_record(self, event: object, capability: ProviderCapability) -> ProviderRecord:
        from signora_platform.simulation.scenario import ScenarioEvent

        assert isinstance(event, ScenarioEvent)
        generated = self._generator.generate(event)

        return ProviderRecord(
            provider=self._descriptor.provider,
            capability=capability,
            external_id=generated.external_id,
            # Provider time, never fetch time. Equating them makes every
            # backfill look like a burst of events that happened at once.
            occurred_at=event.occurred_at,
            payload=dict(generated.payload),
        )


def utc_now() -> datetime:
    """Only for adapter-level bookkeeping that is not part of a payload.

    Kept out of `simulation/`, where the wall clock is forbidden — this
    module is an adapter, not the framework.
    """
    return datetime.now(UTC)
