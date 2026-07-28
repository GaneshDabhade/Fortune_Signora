"""Delivery — pacing events into pages, the way a real integration does.

Three modes exercise genuinely different pipeline paths and are not
interchangeable:

* **Snapshot** — every record, every time. Tests dedup and merge.
* **Incremental** — only records after a watermark. Tests watermark
  handling, and catches the off-by-one that silently drops or re-sends the
  boundary record.
* **Scheduled poll** — repeated incremental fetches. Tests that a sync
  which finds nothing new is a no-op rather than a re-ingest.

**Webhook delivery is deliberately absent.** It requires the real inbound
HTTP route including signature verification, which does not exist yet;
building against a route that does not exist means testing a mock of our
own code (20-provider-simulation.md, principle 7). It arrives with the
route.

Pagination lives here rather than inside an adapter: the platform's loop
drives it, and an adapter that paginated internally would hide the page
boundary that rate limiting and backpressure need to see.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Final

from signora_platform.simulation.faults import FaultInjector, FaultKind, InjectedFault
from signora_platform.simulation.scenario import ScenarioEvent

DEFAULT_PAGE_SIZE: Final = 50


class DeliveryMode(StrEnum):
    SNAPSHOT = "snapshot"
    INCREMENTAL = "incremental"
    SCHEDULED_POLL = "scheduled_poll"


@dataclass(frozen=True, slots=True)
class DeliveryPage:
    """One page, plus what the caller needs to fetch the next.

    `next_cursor` and `has_more` are independent, mirroring the Provider
    Port: a provider legitimately returns a cursor with no further records,
    and conflating them costs an extra empty request per sync.
    """

    events: tuple[ScenarioEvent, ...]
    next_cursor: str | None
    has_more: bool
    fault: InjectedFault | None = None


class DeliveryPlan:
    """Turns a timeline into pages, applying watermark and fault decisions.

    Holds no connection and performs no I/O — it decides *what* would be
    delivered. The adapter turns that into Provider Port calls, which is
    what keeps this provider-agnostic and independently testable.
    """

    def __init__(
        self,
        events: tuple[ScenarioEvent, ...],
        *,
        mode: DeliveryMode = DeliveryMode.SNAPSHOT,
        page_size: int = DEFAULT_PAGE_SIZE,
        injector: FaultInjector | None = None,
    ) -> None:
        if page_size < 1:
            raise ValueError("page_size must be at least 1; a zero-size page never terminates")
        self._events = events
        self._mode = mode
        self._page_size = page_size
        self._injector = injector

    def page(self, *, cursor: str | None = None, since: datetime | None = None) -> DeliveryPage:
        """Produce one page.

        `since` is honoured only in incremental modes. A snapshot ignoring
        the watermark is the point of a snapshot — it is how a re-sync
        exercises dedup.
        """
        selected = self._select(since)
        offset = self._decode(cursor)
        window = selected[offset : offset + self._page_size]

        fault = None
        if self._injector is not None and window:
            fault = self._injector.decide(window[0].sequence)
            window = self._apply(window, fault)

        consumed = offset + self._page_size
        has_more = consumed < len(selected)

        return DeliveryPage(
            events=window,
            # A cursor is returned whenever a position exists, including
            # when nothing follows — matching providers that do the same.
            next_cursor=str(consumed) if selected else None,
            has_more=has_more,
            fault=fault,
        )

    def _select(self, since: datetime | None) -> tuple[ScenarioEvent, ...]:
        if self._mode is DeliveryMode.SNAPSHOT or since is None:
            return self._events
        # Strictly after the watermark. Inclusive would re-deliver the
        # boundary record on every sync — a duplicate the platform absorbs,
        # but one that hides a real watermark bug behind idempotency.
        return tuple(event for event in self._events if event.occurred_at > since)

    @staticmethod
    def _decode(cursor: str | None) -> int:
        if cursor is None:
            return 0
        try:
            offset = int(cursor)
        except ValueError as exc:
            raise ValueError(f"malformed delivery cursor: {cursor!r}") from exc
        if offset < 0:
            raise ValueError(f"delivery cursor must not be negative: {offset}")
        return offset

    @staticmethod
    def _apply(
        window: tuple[ScenarioEvent, ...], fault: InjectedFault | None
    ) -> tuple[ScenarioEvent, ...]:
        """Apply the faults that change *what* is delivered.

        Timeout, 5xx, rate limiting, and malformed payloads change how the
        adapter *responds* and are handled there — the injector's decision
        is carried on the page for the adapter to act on.
        """
        if fault is None:
            return window
        if fault.kind is FaultKind.DUPLICATE:
            # The simulator deliberately does not deduplicate. That is the
            # platform's job, and doing it here would hide whether the
            # platform actually does it.
            return tuple(event for event in window for _ in range(fault.repeat))
        if fault.kind is FaultKind.PARTIAL_RESPONSE:
            return window[: max(1, len(window) // 2)]
        if fault.kind is FaultKind.OUT_OF_ORDER:
            return tuple(reversed(window))
        return window
