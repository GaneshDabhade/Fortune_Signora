"""The subscription registry — which consumers receive which event types.

Deliberately declarative and process-local. The registry is populated at
import time by each module's infrastructure layer, then read by both the
relay (to know which queues an event fans out to) and the worker (to know
which handler to invoke).

Keeping the registry in code rather than in a database table is a
deliberate choice: subscriptions are part of the system's *shape*, not its
data. A subscription that exists in one deployed version and not another is
a deployment concern, and code review is the right gate for it.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Final

from signora_platform.event_bus.envelope import EventEnvelope

EventHandler = Callable[[EventEnvelope], Awaitable[None]]
"""A consumer's handler. Receives the full envelope so it has access to
``workspace_id`` (needed to establish RLS context) and the correlation
identifiers, not merely the payload."""

DEFAULT_POOL: Final = "default"


@dataclass(frozen=True)
class Subscription:
    """One consumer's interest in one event type."""

    consumer_name: str
    """Stable identifier, used as half the idempotency key. **Renaming a
    consumer resets its idempotency ledger and will cause every historical
    event to be re-processed on replay** — treat the name as a permanent
    contract, not a label."""

    event_type: str
    handler: EventHandler
    pool: str = DEFAULT_POOL
    """Which worker pool processes this subscription. Pools let a slow,
    expensive stage (AI research) run at low concurrency without starving a
    fast one (normalization) — see docs/architecture/12-scalability.md."""


class DuplicateSubscriptionError(Exception):
    """The same consumer registered twice for the same event type.

    Almost always a copy-paste error. Allowed silently, it would mean one
    event delivered twice to the same handler — which the idempotency ledger
    would then mask, hiding the mistake rather than surfacing it.
    """

    def __init__(self, consumer_name: str, event_type: str) -> None:
        super().__init__(f"Consumer '{consumer_name}' is already subscribed to '{event_type}'.")


@dataclass
class SubscriptionRegistry:
    _subscriptions: list[Subscription] = field(default_factory=list)

    def subscribe(
        self,
        *,
        consumer_name: str,
        event_type: str,
        handler: EventHandler,
        pool: str = DEFAULT_POOL,
    ) -> None:
        for existing in self._subscriptions:
            if existing.consumer_name == consumer_name and existing.event_type == event_type:
                raise DuplicateSubscriptionError(consumer_name, event_type)
        self._subscriptions.append(
            Subscription(
                consumer_name=consumer_name, event_type=event_type, handler=handler, pool=pool
            )
        )

    def for_event_type(self, event_type: str) -> list[Subscription]:
        """Consumers interested in this event type.

        An empty list is a normal, valid outcome — an event with no
        subscribers is relayed and marked done rather than treated as an
        error. Publishing before anyone consumes is how the pipeline is
        built incrementally.
        """
        return [s for s in self._subscriptions if s.event_type == event_type]

    def for_pool(self, pool: str) -> list[Subscription]:
        return [s for s in self._subscriptions if s.pool == pool]

    def find(self, *, consumer_name: str, event_type: str) -> Subscription | None:
        return next(
            (
                s
                for s in self._subscriptions
                if s.consumer_name == consumer_name and s.event_type == event_type
            ),
            None,
        )

    def pools(self) -> set[str]:
        return {s.pool for s in self._subscriptions}

    def all(self) -> list[Subscription]:
        return list(self._subscriptions)

    def clear(self) -> None:
        """Reset the registry. Exists for test isolation; production code
        registers once at import time and never clears."""
        self._subscriptions.clear()


registry: Final = SubscriptionRegistry()
"""The process-wide registry. Modules register against this at import time;
the composition root imports those modules to trigger registration."""
