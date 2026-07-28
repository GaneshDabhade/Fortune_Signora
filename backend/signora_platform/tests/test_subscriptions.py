"""Unit tests for the subscription registry."""

import pytest

from signora_platform.event_bus import (
    DuplicateSubscriptionError,
    EventEnvelope,
    SubscriptionRegistry,
)


async def _handler(envelope: EventEnvelope) -> None:
    return None


@pytest.fixture
def registry() -> SubscriptionRegistry:
    return SubscriptionRegistry()


def test_registers_and_finds_a_subscription(registry: SubscriptionRegistry) -> None:
    registry.subscribe(consumer_name="timeline", event_type="a.b", handler=_handler)

    found = registry.find(consumer_name="timeline", event_type="a.b")

    assert found is not None
    assert found.pool == "default"


def test_rejects_a_duplicate_subscription(registry: SubscriptionRegistry) -> None:
    """A duplicate would mean one event delivered twice to the same handler.
    The idempotency ledger would mask that, hiding the mistake rather than
    surfacing it — so it is rejected at registration."""
    registry.subscribe(consumer_name="timeline", event_type="a.b", handler=_handler)

    with pytest.raises(DuplicateSubscriptionError):
        registry.subscribe(consumer_name="timeline", event_type="a.b", handler=_handler)


def test_same_consumer_may_subscribe_to_different_event_types(
    registry: SubscriptionRegistry,
) -> None:
    registry.subscribe(consumer_name="timeline", event_type="a.b", handler=_handler)
    registry.subscribe(consumer_name="timeline", event_type="c.d", handler=_handler)

    assert len(registry.all()) == 2


def test_different_consumers_may_subscribe_to_the_same_event_type(
    registry: SubscriptionRegistry,
) -> None:
    registry.subscribe(consumer_name="timeline", event_type="a.b", handler=_handler)
    registry.subscribe(consumer_name="signals", event_type="a.b", handler=_handler)

    assert len(registry.for_event_type("a.b")) == 2


def test_unknown_event_type_returns_empty_not_error(registry: SubscriptionRegistry) -> None:
    """Publishing before anyone consumes is how the pipeline is built
    incrementally."""
    assert registry.for_event_type("nobody.listens") == []


def test_filters_by_pool(registry: SubscriptionRegistry) -> None:
    registry.subscribe(consumer_name="a", event_type="x", handler=_handler, pool="graph")
    registry.subscribe(consumer_name="b", event_type="y", handler=_handler, pool="ai_research")

    assert len(registry.for_pool("graph")) == 1
    assert registry.pools() == {"graph", "ai_research"}


def test_find_returns_none_for_unregistered_pair(registry: SubscriptionRegistry) -> None:
    assert registry.find(consumer_name="ghost", event_type="x") is None


def test_clear_resets_the_registry(registry: SubscriptionRegistry) -> None:
    registry.subscribe(consumer_name="a", event_type="x", handler=_handler)

    registry.clear()

    assert registry.all() == []
