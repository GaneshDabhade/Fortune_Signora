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
from modules.buying_score_engine.interface.handlers import (
    CONSUMER_NAME as SCORE_CONSUMER,
)
from modules.signal_engine.interface.handlers import CONSUMER_NAME as SIGNAL_CONSUMER
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


class TestSignalGenerationIsActuallySubscribed:
    """TASK-901 slice 2 — **the first pipeline stage to consume what it
    declares.**

    `signal_engine` has had a `CONSUMER_NAME`, a handler and a full use case
    since M5 and **no subscription in any deployed process**: the only caller
    of `generate_from_business_event` was `tests/pipeline.py`. That is
    [B-301](../../../docs/BUGS.md)'s shape exactly — every gate green, and a
    capability that runs only inside a test.
    """

    def test_both_business_event_types_reach_the_signal_engine(self) -> None:
        subscriptions.register()

        missing = [
            event_type
            for event_type in subscriptions.SIGNAL_INPUTS
            if registry.find(consumer_name=SIGNAL_CONSUMER, event_type=event_type) is None
        ]

        assert missing == []

    def test_it_consumes_what_its_own_handler_documents(self) -> None:
        """**The list is not free to drift.** The module's handler says it
        subscribes to a detected event and a superseded one; a composition root
        quietly subscribing to one of them would leave superseded business
        events forming no signals, and nothing else would notice."""
        assert subscriptions.SIGNAL_INPUTS == (
            "business_event.detected",
            "business_event.superseded",
        )

    def test_it_runs_in_the_pool_declared_for_it(self) -> None:
        """`intelligence` — *"Business Event, Signal, Buying Score, Opportunity
        Engines"*, declared since M1.1 and until now with no subscriber. A
        pipeline stage sharing the read-model pool would let a projection storm
        delay hypothesis formation."""
        subscriptions.register()

        found = registry.find(
            consumer_name=SIGNAL_CONSUMER, event_type="business_event.detected"
        )

        assert found is not None
        assert found.pool == POOLS["intelligence"].name


class TestBuyingScoreIsActuallySubscribed:
    """TASK-901 slice 3 — **the stage directly downstream of slice 2.**"""

    def test_both_signal_events_reach_the_buying_score_engine(self) -> None:
        """**Both, and the module's own docstring is the argument**: *"a
        strengthened hypothesis arrives as a new signal plus a supersession,
        and a consumer that handled only the first would keep weighing the
        replaced reading alongside the one that replaced it — counting the
        same grounds twice."* Subscribing to `signal.generated` alone would
        double-count, silently, and only on strengthened hypotheses."""
        subscriptions.register()

        missing = [
            event_type
            for event_type in subscriptions.SCORE_INPUTS
            if registry.find(consumer_name=SCORE_CONSUMER, event_type=event_type) is None
        ]

        assert missing == []

    def test_it_consumes_exactly_what_its_trigger_table_maps(self) -> None:
        """**The two lists are one fact and must not drift.** The module maps
        each event type it handles to a `ScoreTrigger`; a subscription to an
        event absent from that table would score with a defaulted trigger, and
        a table entry with no subscription would never fire."""
        from modules.buying_score_engine.interface.handlers import _TRIGGERS

        assert set(subscriptions.SCORE_INPUTS) == set(_TRIGGERS)

    def test_the_pipeline_stages_share_one_pool(self) -> None:
        """`intelligence` — declared for these engines since M1.1. Signals and
        the scores that follow them belong to one flow, and splitting them
        across pools would let a score wait behind unrelated work."""
        subscriptions.register()

        signal = registry.find(
            consumer_name=SIGNAL_CONSUMER, event_type="business_event.detected"
        )
        score = registry.find(consumer_name=SCORE_CONSUMER, event_type="signal.generated")

        assert signal is not None and score is not None
        assert signal.pool == score.pool == POOLS["intelligence"].name

