"""The Provider Port — the contract every data provider satisfies.

This is the seam the entire Provider Simulation Framework rests on. A
simulated adapter and a production adapter implement *this*, identically,
and a single contract test suite runs against both
(docs/architecture/20-provider-simulation.md, principle 8).

Two consequences shape everything here:

**The contract belongs to production, not to the simulator.** It is defined
before any adapter exists, so it describes what a real vendor integration
needs rather than what happened to be convenient to simulate. A simulated
adapter that cannot satisfy it is a defect in the adapter, never a licence
to widen the contract.

**Failure is part of the contract.** A port that returns data on success and
raises whatever the vendor SDK raised on failure has not abstracted the
vendor at all — every caller ends up handling httpx, boto, and requests
exceptions. The failure outcomes below are the complete set a caller must
handle, and adapters translate everything into them (CLAUDE.md §15).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable
from uuid import UUID


class ProviderName(StrEnum):
    """Providers with a ratified qualification record.

    Membership here means the provider is *architecturally* recognised, not
    that a generator exists — see docs/architecture/provider-qualification.md
    for per-provider status.
    """

    APOLLO = "apollo"
    BUILTWITH = "builtwith"
    CRUNCHBASE = "crunchbase"
    CORESIGNAL = "coresignal"
    BOMBORA = "bombora"


class ProviderCapability(StrEnum):
    """What a provider can be asked for.

    A provider declares its capabilities rather than the platform hardcoding
    them, so adding a provider does not require editing a dispatch table —
    and asking a provider for something it cannot supply is a typed error
    rather than an empty result that looks like "no data".
    """

    COMPANY_ENRICHMENT = "company_enrichment"
    TECHNOGRAPHICS = "technographics"
    CAPITAL_EVENTS = "capital_events"
    WORKFORCE = "workforce"
    BEHAVIOURAL_INTENT = "behavioural_intent"


# --------------------------------------------------------------- failures


class ProviderError(Exception):
    """Base for every failure a provider adapter may surface.

    A caller catching this has caught everything the port can raise. No
    vendor SDK exception escapes an adapter.
    """

    def __init__(self, provider: ProviderName, message: str) -> None:
        super().__init__(f"[{provider}] {message}")
        self.provider = provider


class ProviderTransientError(ProviderError):
    """Retry with backoff — a timeout, a 5xx, a dropped connection.

    Separated from permanent failures because the correct response differs
    entirely: retrying a permanent failure burns quota to no purpose, and
    giving up on a transient one loses data that was merely late.
    """


class ProviderRateLimitedError(ProviderTransientError):
    """Transient, but with a vendor-supplied wait.

    A subclass rather than a flag: a caller that handles transient failures
    generically still backs off correctly, while one that wants to honour
    `retry_after` can. Guessing a backoff when the vendor stated one is how
    an integration gets throttled harder.
    """

    def __init__(
        self, provider: ProviderName, message: str, retry_after_seconds: float | None = None
    ) -> None:
        super().__init__(provider, message)
        self.retry_after_seconds = retry_after_seconds


class ProviderPermanentError(ProviderError):
    """Do not retry — a 4xx, a rejected credential, an unknown entity."""


class ProviderPayloadInvalidError(ProviderPermanentError):
    """The provider responded, but not with something usable.

    Distinct from a permanent error because it means the *contract* is
    wrong rather than the request: the vendor changed a shape, or the
    payload is truncated. That is an alert about the integration, not about
    one entity.
    """


class ProviderCapabilityUnsupportedError(ProviderPermanentError):
    """The provider was asked for something it does not supply."""


# ------------------------------------------------------------- contracts


@dataclass(frozen=True, slots=True)
class ProviderRequest:
    """One request to one provider.

    `since` drives incremental sync. `cursor` drives pagination. Both are
    opaque to the platform and interpreted only by the adapter — a platform
    that understands a vendor's cursor format has leaked the vendor into
    itself.
    """

    capability: ProviderCapability
    workspace_id: UUID
    correlation_id: UUID
    #: Domain identifier of the subject (a company key, a domain name).
    subject: str
    #: Incremental watermark. None requests a full snapshot.
    since: datetime | None = None
    #: Opaque pagination cursor from a previous response.
    cursor: str | None = None
    #: Maximum records to return. Adapters may return fewer, never more.
    limit: int = 100


@dataclass(frozen=True, slots=True)
class ProviderRecord:
    """One raw record, exactly as the provider returned it.

    `payload` is **untrusted** and deliberately untyped: normalization
    validates it (principle 4). Typing it here would mean the port had
    already interpreted the vendor's shape, which is Provider
    Normalization's job and not the adapter's.
    """

    provider: ProviderName
    capability: ProviderCapability
    #: The provider's own identifier for this record, used for dedup.
    external_id: str
    #: When the described event happened, per the provider — *not* when it
    #: was fetched. The gap between them is what a backfill looks like.
    occurred_at: datetime
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ProviderResponse:
    """A page of records, plus what is needed to fetch the next.

    `next_cursor` and `has_more` are separate rather than inferred from one
    another: a provider legitimately returns a cursor with no further
    records, and conflating them produces an extra empty request per sync
    on every provider that does.
    """

    provider: ProviderName
    records: tuple[ProviderRecord, ...]
    next_cursor: str | None = None
    has_more: bool = False
    #: Set when the response came from simulation. Recorded in ingestion
    #: logs and never in the payload — marking the payload would change its
    #: shape and defeat the identical-contract rule.
    simulated: bool = False
    #: Replay provenance, present only on simulated responses. Carries
    #: scenario, seed, manifest version, generator version, and clock.
    replay: ReplayContext | None = None


@dataclass(frozen=True, slots=True)
class ReplayContext:
    """What makes a simulated run reproducible from its record alone.

    Without generator version in particular, a change in downstream output
    could come from a model change, a prompt change, a dataset change, *or*
    a quietly-updated payload shape — and separating them after the fact is
    impossible.
    """

    scenario: str
    seed: int
    manifest_version: str
    generator_version: str
    clock_mode: str
    dataset_version: str

    def as_log_fields(self) -> dict[str, str | int]:
        return {
            "sim_scenario": self.scenario,
            "sim_seed": self.seed,
            "sim_manifest_version": self.manifest_version,
            "sim_generator_version": self.generator_version,
            "sim_clock_mode": self.clock_mode,
            "sim_dataset_version": self.dataset_version,
        }


@dataclass(frozen=True, slots=True)
class ProviderDescriptor:
    """Static facts about an adapter, readable without calling it.

    Lets the platform validate a request before dispatching it, and lets
    health output report which providers are wired without probing each.
    """

    provider: ProviderName
    capabilities: frozenset[ProviderCapability]
    simulated: bool
    #: Requests per minute the adapter will accept before rate limiting.
    #: Declared so the platform can pace itself rather than discovering the
    #: limit by being throttled.
    rate_limit_per_minute: int | None = None


@runtime_checkable
class ProviderAdapter(Protocol):
    """The port. Implemented identically by simulated and real adapters.

    Deliberately narrow: one describe, one fetch. A wider port would need
    every future vendor to implement methods most of them do not have, and
    the usual outcome is adapters raising NotImplementedError — which is a
    contract that lies.
    """

    def describe(self) -> ProviderDescriptor: ...

    async def fetch(self, request: ProviderRequest) -> ProviderResponse:
        """Fetch one page.

        Raises only ``ProviderError`` subclasses. Pagination is the
        caller's loop, driven by ``next_cursor``/``has_more`` — an adapter
        that paginates internally hides the page boundary that rate
        limiting and backpressure need to see.
        """
        ...


@dataclass(frozen=True, slots=True)
class ProviderRegistry:
    """The adapters available to this process.

    Selection is **configuration only** — the registry is populated at the
    composition root from settings, and no code below it knows whether an
    adapter is simulated (principle 3, and the `if simulated:` prohibition).
    """

    adapters: dict[ProviderName, ProviderAdapter] = field(default_factory=dict)

    def register(self, adapter: ProviderAdapter) -> None:
        descriptor = adapter.describe()
        self.adapters[descriptor.provider] = adapter

    def get(self, provider: ProviderName) -> ProviderAdapter:
        adapter = self.adapters.get(provider)
        if adapter is None:
            raise ProviderPermanentError(provider, "no adapter registered")
        return adapter

    def supporting(self, capability: ProviderCapability) -> tuple[ProviderName, ...]:
        return tuple(
            name
            for name, adapter in sorted(self.adapters.items())
            if capability in adapter.describe().capabilities
        )
