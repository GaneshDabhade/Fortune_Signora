"""Reading a customer's own system, as a port this module owns.

**The sentence the whole design turns on** ([04-modules.md](../../../../docs/architecture/04-modules.md)):
a *provider* is Signora's supplier and Signora holds the credential; an
*integration* is the **customer's own system** and the customer holds it. The
Provider Port asks a supplier *about one company*. This asks a customer's
system for *the customer's own records*, and **an enumeration has no subject** —
which is the difference that makes this a sibling rather than an extension.

**Ratified as Option A of [ADR-0300](../../../../docs/architecture/adr/0300-inbound-customer-systems.md)
on 2026-08-04**, specified by [409](../../../../docs/architecture/409-inbound-source-port-contract.md),
and built to that contract rather than to a fresh design.

**Defined here because a port belongs to the module that owns the language it
represents** (`CLAUDE.md` §6). *Connected Account*, *grant*, *scope*,
*credential* and *capability* are this module's words. **`integrations` imports
nothing from `provider_platform`**: it declares a contract and does not know
who drives it.

**`ProviderName` stays closed, and that is the point of the whole exercise.**
It means *"a supplier with a ratified qualification record"*, which is a
guarantee worth more than the convenience of one shared enum — so no catalog
slug is ever added to it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from modules.integrations.domain.execution import ExecutionContext
from modules.integrations.domain.catalog import Capability

#: What a source may return in one page. **A ceiling, not a request** — an
#: adapter may return fewer and must never return more.
DEFAULT_PAGE_SIZE = 100


class IntegrationSourceError(Exception):
    """Base for every failure a source adapter surfaces.

    **Mirrors the Provider Port's hierarchy exactly**, so the platform's
    retry decision is the same one it already makes. No vendor exception
    escapes an adapter.
    """


class IntegrationSourceTransientError(IntegrationSourceError):
    """Retry later — a timeout, a 5xx, a dropped connection."""


class IntegrationSourceRateLimitedError(IntegrationSourceTransientError):
    """Transient, with the vendor's own wait when it supplied one.

    A subclass rather than a flag, so a caller handling transient failures
    generically still backs off correctly. **Guessing a backoff when the
    vendor stated one is how an integration gets throttled harder.**
    """

    def __init__(self, message: str, retry_after_seconds: float | None = None) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class IntegrationSourcePermanentError(IntegrationSourceError):
    """Do not retry — a rejected credential, a missing permission, a bad
    request. **The platform stops and alerts rather than resuming later.**"""


class IntegrationCapabilityUnsupportedError(IntegrationSourcePermanentError):
    """This source cannot answer for this capability.

    Permanent by construction: asking again changes nothing, and the honest
    response is that the customer's system does not offer it.
    """


class IntegrationPayloadInvalidError(IntegrationSourceError):
    """The source answered, and not with something usable.

    **An alert about the integration rather than about one record**: the
    vendor changed a shape, or a proxy returned a page where JSON belonged.
    """


@dataclass(frozen=True, slots=True)
class IntegrationFetchRequest:
    """One page's worth of *"give me the customer's records"*.

    **There is no `subject`, and its absence is the whole distinction.** A
    provider is asked about one company, so `ProviderRequest` requires one;
    a source is asked to enumerate, and a subject here would be a field every
    adapter had to ignore.
    """

    #: **Travels with the request rather than being held by the adapter.** A
    #: provider adapter holds Signora's own credential from the composition
    #: root; a customer's credential is per workspace, per connection, and
    #: expires — so it cannot be constructor state.
    context: ExecutionContext
    #: This module's `Capability`, never `ProviderCapability`. **Two
    #: vocabularies with two owners**: one enumerates what suppliers sell, the
    #: other what connecting a customer's system gives Signora, and the type
    #: system keeps them apart.
    capability: Capability
    #: The watermark. `None` requests a full snapshot.
    since: datetime | None = None
    #: Opaque, and interpreted only by the adapter that issued it.
    cursor: str | None = None
    limit: int = DEFAULT_PAGE_SIZE


@dataclass(frozen=True, slots=True)
class IntegrationRecord:
    """One record from a customer's system, exactly as it arrived.

    **It carries no `provider`**, unlike `ProviderRecord` — the slug is on
    `context.integration`, which is one authoritative place, and a record that
    carried its own could disagree with the connection it came from (§2).
    """

    #: The customer's system's own identifier, for deduplication.
    external_id: str
    #: When the described thing happened, **according to the source**. It is
    #: the field a watermark advances on, so it must be the source's and never
    #: the platform's clock — guessing `now()` would make every backfill look
    #: like today.
    occurred_at: datetime
    #: Untrusted and untyped. **Nothing here is validated or reshaped**;
    #: interpreting it is Provider Normalization's job, and a port that
    #: normalised anything would put the vendor's contract in two places.
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class IntegrationPage:
    """One page, plus what is needed to fetch the next.

    `next_cursor` and `has_more` are separate rather than inferred from one
    another, for the reason the Provider Port already gives: **a source
    legitimately returns a cursor with no further records**, and conflating
    them costs one empty request per sync.
    """

    records: tuple[IntegrationRecord, ...] = field(default_factory=tuple)
    next_cursor: str | None = None
    has_more: bool = False


@dataclass(frozen=True, slots=True)
class IntegrationSourceDescriptor:
    """What a source is, and what it can be asked for.

    **Deliberately smaller than `ProviderDescriptor`.** That one carries
    qualification metadata because a provider is a supplier Signora chose and
    assessed; **a source is a system the customer chose, and Signora qualifies
    nothing about it.**
    """

    #: The catalog slug — `"hubspot"`. Never a `ProviderName`.
    integration: str
    capabilities: tuple[Capability, ...]


class IntegrationSourceAdapter(Protocol):
    """A customer's system, as something the platform can read from.

    **Two methods, deliberately**, on the same reasoning the Provider Port
    states: a wider port would need every future source to implement methods
    most of them do not have, and the usual outcome is adapters raising
    `NotImplementedError` — which is a contract that lies.

    **Read-only. `fetch` is the only verb**, and write-back is E2's territory.
    """

    def describe(self) -> IntegrationSourceDescriptor:
        """What this source is and what it answers for. **Not a network
        call** — a descriptor a caller cannot obtain without reaching the
        vendor is a descriptor that fails when the vendor is down."""
        ...

    async def fetch(self, request: IntegrationFetchRequest) -> IntegrationPage:
        """One page of the customer's records.

        **Pagination is the caller's loop.** An adapter that paginated
        internally would hide the page boundary that rate limiting and
        backpressure need to see.

        **A revoked, expired or disconnected connection never reaches here.**
        `ResolveExecutionContext` raises `ConnectionUnusable` before a request
        is built, and that is not an adapter failure — **it is a customer
        decision**, and reporting it as a sync error would file the customer's
        own choice as something the platform got wrong.
        """
        ...


__all__ = [
    "DEFAULT_PAGE_SIZE",
    "IntegrationCapabilityUnsupportedError",
    "IntegrationFetchRequest",
    "IntegrationPage",
    "IntegrationPayloadInvalidError",
    "IntegrationRecord",
    "IntegrationSourceAdapter",
    "IntegrationSourceDescriptor",
    "IntegrationSourceError",
    "IntegrationSourcePermanentError",
    "IntegrationSourceRateLimitedError",
    "IntegrationSourceTransientError",
]
