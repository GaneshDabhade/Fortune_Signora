"""What the deployed worker actually consumes.

**Nothing asserted this, and that is how [B-301](../../../docs/BUGS.md) shipped.**
Timeline was promoted to `main` with its domain, its projection table, its
repository, its read API and its feed component all built and tested — and
**no subscription registering its handler in the deployed worker.** Every gate
was green: the module's unit tests drive `ProjectEvent` directly, and the
integration tests drive the handler directly. A customer running the promoted
build would have seen an account timeline that stayed empty forever.

The gap is structural rather than careless. `apps/worker/subscriptions.py` is a
composition root, and **a composition root is the one file no module's own
suite covers** — each module tests its own half and assumes the wiring. So the
assertion belongs here, at the level that owns the wiring, and it is written
against `PROJECTIONS` rather than a hand-written list so that adding a rule
without a subscription fails immediately.
"""

from __future__ import annotations

import pytest

from apps.worker import subscriptions
from apps.worker.pools import POOLS
from modules.timeline.domain.projection import PROJECTIONS
from modules.timeline.interface.handlers import CONSUMER_NAME as TIMELINE_CONSUMER
from signora_platform.event_bus import registry

pytestmark = pytest.mark.integration


class TestTimelineIsActuallySubscribed:
    def test_every_event_timeline_projects_has_a_consumer(self) -> None:
        """**The regression.** A projection rule with no subscription is a rule
        that never runs outside a test."""
        subscriptions.register()
        missing = [
            event_type
            for event_type in PROJECTIONS
            if registry.find(consumer_name=TIMELINE_CONSUMER, event_type=event_type) is None
        ]
        assert missing == []

    def test_it_subscribes_to_nothing_it_cannot_project(self) -> None:
        """The other direction, and it matters as much. A subscription for an
        event with no rule wakes a worker to do nothing, and the projection
        silently returns `False` — indistinguishable from working."""
        subscriptions.register()
        subscribed = {
            s.event_type
            for pool in POOLS.values()
            for s in registry.for_pool(pool.name)
            if s.consumer_name == TIMELINE_CONSUMER
        }
        assert subscribed == set(PROJECTIONS)

    def test_the_consumer_name_is_the_module_s_own(self) -> None:
        """Registered under the name the module declares, not one the
        composition root invented. A divergence here would give the projection
        two idempotency ledgers and re-project everything on the next replay."""
        assert TIMELINE_CONSUMER == "timeline.project"

    def test_registering_twice_is_safe(self) -> None:
        """`register()` runs at import, and both the worker and the relay
        import this module. A duplicate raises, so the guard has to hold."""
        subscriptions.register()
        subscriptions.register()
        assert (
            registry.find(consumer_name=TIMELINE_CONSUMER, event_type="signal.generated")
            is not None
        )


class TestEverySubscriptionRoutesSomewhere:
    def test_every_subscription_names_a_declared_pool(self) -> None:
        """The relay reads `(event_type → consumer, pool)` to choose a queue.
        A subscription naming a pool no process runs is an event that is
        relayed, queued, and never picked up."""
        subscriptions.register()
        declared = set(POOLS)
        for pool in registry.pools():
            assert pool in declared, f"subscription routes to undeclared pool {pool!r}"
