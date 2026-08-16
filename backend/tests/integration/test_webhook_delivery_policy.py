"""The webhook retry policy — the window, the backoff, and the parking.

**No database and no network.** The policy is a pure function of
``(first_attempted_at, attempts, now)``, which is what makes the twenty-four
hour window testable at all: the alternative is a test that waits a day, and a
guarantee nobody can afford to verify is not a guarantee.

📁 The design's whole specification, one sentence:

    "Failed webhook deliveries retry with backoff for 24 hours, then park with
     the payload retained."
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from signora_platform.event_bus import dead_letter, webhook_delivery
from signora_platform.event_bus.webhook_delivery import (
    DELIVERY_WINDOW,
    DeliveryState,
    backoff_seconds,
    deadline,
    delivered,
    next_attempt,
)

START = datetime(2026, 8, 16, 9, 0, tzinfo=UTC)


def test_the_window_is_the_designs_twenty_four_hours() -> None:
    """The one number the design states, asserted against the design."""
    assert DELIVERY_WINDOW == timedelta(hours=24)


def test_a_failure_inside_the_window_schedules_another_attempt() -> None:
    decision = next_attempt(first_attempted_at=START, attempts=1, now=START)

    assert decision.state is DeliveryState.PENDING
    assert decision.next_attempt_at == START + timedelta(seconds=5)


def test_a_pending_delivery_always_carries_its_next_attempt() -> None:
    """⛔ A pending row with no scheduled attempt is one nothing will pick up.

    That is the shape that loses deliveries *silently*, so it is asserted
    rather than left to the type.
    """
    for attempts in range(1, 20):
        decision = next_attempt(
            first_attempted_at=START, attempts=attempts, now=START + timedelta(minutes=5)
        )
        if decision.state is DeliveryState.PENDING:
            assert decision.next_attempt_at is not None, attempts


def test_backoff_grows_and_then_caps() -> None:
    assert backoff_seconds(1) == 5
    assert backoff_seconds(2) == 10
    assert backoff_seconds(3) == 20
    assert backoff_seconds(100) == webhook_delivery.MAX_BACKOFF_SECONDS


def test_backoff_is_defensive_about_a_zeroth_attempt() -> None:
    assert backoff_seconds(0) == webhook_delivery.BASE_BACKOFF_SECONDS
    assert backoff_seconds(-3) == webhook_delivery.BASE_BACKOFF_SECONDS


def test_the_delivery_parks_once_the_window_expires() -> None:
    decision = next_attempt(
        first_attempted_at=START, attempts=47, now=START + DELIVERY_WINDOW
    )

    assert decision.state is DeliveryState.PARKED
    assert decision.next_attempt_at is None
    assert "payload is retained" in decision.reason


def test_a_retry_that_would_land_outside_the_window_parks_instead() -> None:
    """⛔ The defect this prevents is visible only to a customer.

    Without it the final backoff is scheduled past the deadline, the row sits
    ``pending`` for up to an hour, and the ``State`` column tells somebody we
    are still trying when the next thing the worker will do is park it.
    """
    just_inside = START + DELIVERY_WINDOW - timedelta(minutes=30)

    decision = next_attempt(first_attempted_at=START, attempts=10, now=just_inside)

    assert decision.state is DeliveryState.PARKED
    assert decision.next_attempt_at is None
    assert "outside the delivery window" in decision.reason


def test_the_window_runs_from_the_first_attempt_not_the_last() -> None:
    """⛔ Otherwise a delivery extends its own deadline by failing.

    An endpoint failing once an hour under a per-attempt window is retried
    forever, one hour at a time, and never parks — so the twenty-four hour
    guarantee would hold for no delivery that actually needed it.
    """
    much_later = START + timedelta(hours=40)

    decision = next_attempt(first_attempted_at=START, attempts=200, now=much_later)

    assert decision.state is DeliveryState.PARKED


def test_success_is_terminal_and_states_its_attempt_count() -> None:
    decision = delivered(attempts=3)

    assert decision.state is DeliveryState.DELIVERED
    assert decision.next_attempt_at is None
    assert "3 attempt(s)" in decision.reason


def test_the_deadline_is_published_rather_than_recomputed() -> None:
    assert deadline(first_attempted_at=START) == START + DELIVERY_WINDOW


@pytest.mark.parametrize(
    "first_attempted_at, now",
    [
        (START.replace(tzinfo=None), START),
        (START, START.replace(tzinfo=None)),
    ],
)
def test_a_naive_timestamp_is_refused_rather_than_compared(
    first_attempted_at: datetime, now: datetime
) -> None:
    """⛔ A naive datetime is UTC on one machine and local time on another.

    The window is the entire policy, so comparing across that difference would
    park deliveries hours early or late depending on where the worker ran.
    """
    with pytest.raises(ValueError, match="timezone-aware"):
        next_attempt(first_attempted_at=first_attempted_at, attempts=1, now=now)


def test_the_platform_policy_is_untouched_and_is_a_different_one() -> None:
    """🔴 The freeze, asserted rather than remembered.

    ``signora_platform`` is frozen (§20a) and the temptation this slice creates
    is to widen ``dead_letter``'s constants until one caller can reach
    twenty-four hours. This fails the moment somebody does — and it also states
    *why* the two differ, which a comment beside the constants could not.
    """
    assert dead_letter.MAX_ATTEMPTS == 5
    assert dead_letter.MAX_BACKOFF_SECONDS == 300

    # ⛔ Five attempts at the platform's cap cannot reach the design's window,
    # which is the whole reason this module exists rather than a parameter.
    reachable = sum(dead_letter.backoff_seconds(n) for n in range(1, dead_letter.MAX_ATTEMPTS + 1))
    assert timedelta(seconds=reachable) < DELIVERY_WINDOW
