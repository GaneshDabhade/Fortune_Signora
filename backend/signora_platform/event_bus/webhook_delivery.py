"""Outbound webhook delivery — retried across a window, then parked.

**A customer's endpoint is not a handler, and the difference decides the
policy.** An internal event handler that fails five times has a bug; no
further attempt will fix it, so ``dead_letter`` stops after five and is right
to. A customer's endpoint that fails for six hours is *ordinary* — a
deployment, a certificate renewal, a cloud region — and giving up on it after
twenty-five minutes would lose a delivery the customer had every reason to
expect.

So this carries its own policy rather than widening the platform's. That is
not a preference: ``signora_platform`` is frozen (``CLAUDE.md`` §20a), and
reshaping ``dead_letter``'s constants so one caller could reach twenty-four
hours is exactly the "reshaping a platform interface because one module would
find a different shape convenient" the freeze exists to refuse. Adding a
worker pool beside it is the permitted half, and this is that.

**The design gives one sentence and it is the whole specification:**

    "Failed webhook deliveries retry with backoff for 24 hours, then park
     with the payload retained."

    -- ``Fortune Signora Settings.dc.html``, API keys & webhooks

## The bound is a duration, and that is the load-bearing reading

The platform's policy is *attempt-bounded* — ``MAX_ATTEMPTS = 5``. The
design's is *time-bounded* — "for 24 hours". Those are different kinds of
rule, and choosing the wrong one produces a policy that is right today and
silently wrong after any change to the backoff curve.

Bounding by attempts would mean picking a number that happens to land near
twenty-four hours under today's constants. Change ``MAX_BACKOFF`` and the
window moves without anybody editing the number that claims to define it —
a derived fact stored as if it were authoritative, which is the defect
``CLAUDE.md`` §2 names. **So the window is the rule and the attempt count is
whatever the window allows.**

## Park is not dead-letter, and the word is the customer's

``dead_letter`` is the platform's word for an internal event nothing can
process. **Park** is the design's word for a delivery that ran out of window
with its payload intact, and it reaches a screen — the ``State`` column of the
API keys & webhooks table. ADR-0034 puts the customer's vocabulary at the
frontend edge, so the *concept* here is named for what it is; only the string
a customer reads is the design's.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Final

#: 📁 The design's number, and the only one it states.
DELIVERY_WINDOW: Final = timedelta(hours=24)

BASE_BACKOFF_SECONDS: Final = 5
"""Longer than the platform's ``2``, deliberately.

A handler retried after two seconds costs a worker slot. A customer's endpoint
retried after two seconds is a request they did not ask for, against a service
that has had no time to recover — and at scale it is indistinguishable from a
retry storm aimed at them.
"""

MAX_BACKOFF_SECONDS: Final = 3600
"""One hour between attempts at the tail.

The platform caps at five minutes because an internal event delayed longer
than that "looks indistinguishable from the event having been lost". Nothing
here is lost: the row is readable in the table the whole time, with its state
and its next attempt. So the cap can be the one that serves the *endpoint* —
an hour is long enough to let a deployment finish, and short enough that a
recovery inside the window is still delivered inside it.
"""


class DeliveryState(str, Enum):
    """Every state a delivery can be in, and each is observable (§17)."""

    PENDING = "pending"
    """Accepted, not yet attempted, or waiting out a backoff."""

    DELIVERED = "delivered"
    """The endpoint accepted it. Terminal."""

    PARKED = "parked"
    """The window expired. **Terminal, and the payload is retained** — the
    design says so in the same sentence that sets the window, because a parked
    delivery a customer cannot inspect is indistinguishable from one that was
    dropped."""


def backoff_seconds(attempt: int) -> int:
    """Exponential backoff, capped, for the *next* attempt after ``attempt``.

    ``attempt`` is 1-based and counts attempts already made, so the delay after
    the first failure is ``BASE_BACKOFF_SECONDS``. A caller passing ``0`` or a
    negative number gets the base delay rather than a fractional one, which is
    the same defensive shape ``dead_letter.backoff_seconds`` uses.
    """
    scaled: int = BASE_BACKOFF_SECONDS * (2 ** max(attempt - 1, 0))
    return min(scaled, MAX_BACKOFF_SECONDS)


@dataclass(frozen=True, slots=True)
class Attempt:
    """What the worker should do next, and why.

    Frozen because it records a decision that was made at a moment. Recomputing
    it later from a different ``now`` is a *different* decision, and one that
    can be stored and compared is one an operator can explain.
    """

    state: DeliveryState
    next_attempt_at: datetime | None
    """``None`` in every terminal state, and never ``None`` in ``PENDING`` —
    a pending delivery with no scheduled attempt is a row nothing will ever
    pick up, which is the shape that loses deliveries silently."""

    reason: str
    """Why this delivery is where it is, in words an operator can act on."""


def next_attempt(
    *,
    first_attempted_at: datetime,
    attempts: int,
    now: datetime,
) -> Attempt:
    """Decide what happens after a failed attempt.

    **``now`` is a parameter, never ``datetime.now()``.** A policy that reads
    the clock cannot be replayed, and ``CLAUDE.md`` §2 calls an input that
    influences behaviour without being declared an architecture defect —
    "hidden inputs are architecture defects", with assembly timestamps named
    among the ones already removed.

    The window is measured from the **first** attempt rather than from the last
    one, so a delivery cannot extend its own deadline by failing: with a
    per-attempt window, an endpoint failing every hour would be retried
    forever, one hour at a time, and never park.
    """
    if first_attempted_at.tzinfo is None or now.tzinfo is None:
        raise ValueError(
            "webhook delivery timestamps must be timezone-aware; a naive datetime "
            "here compares as UTC on one machine and local time on another, and the "
            "window is the whole policy"
        )

    elapsed = now - first_attempted_at
    if elapsed >= DELIVERY_WINDOW:
        return Attempt(
            state=DeliveryState.PARKED,
            next_attempt_at=None,
            reason=(
                f"the {DELIVERY_WINDOW.total_seconds() / 3600:.0f}-hour delivery window "
                f"expired after {attempts} attempt(s); the payload is retained"
            ),
        )

    delay = timedelta(seconds=backoff_seconds(attempts))
    scheduled = now + delay

    # ⛔ **A retry scheduled past the deadline must not be scheduled.** Without
    # this, the last backoff of a long-failing delivery lands outside the
    # window and the worker wakes only to park it — so the row sits `pending`
    # for up to an hour describing an attempt that will never be made, and the
    # `State` column tells a customer we are still trying when we are not.
    if scheduled - first_attempted_at >= DELIVERY_WINDOW:
        return Attempt(
            state=DeliveryState.PARKED,
            next_attempt_at=None,
            reason=(
                f"the next backoff of {delay.total_seconds():.0f}s would fall outside the "
                f"delivery window; parked after {attempts} attempt(s) with the payload retained"
            ),
        )

    return Attempt(
        state=DeliveryState.PENDING,
        next_attempt_at=scheduled,
        reason=f"attempt {attempts + 1} scheduled in {delay.total_seconds():.0f}s",
    )


def delivered(*, attempts: int) -> Attempt:
    """The endpoint accepted it.

    Separate from :func:`next_attempt` rather than a branch inside it, because
    success is not a retry decision and folding it in would give that function
    two subjects.
    """
    return Attempt(
        state=DeliveryState.DELIVERED,
        next_attempt_at=None,
        reason=f"accepted by the endpoint after {attempts} attempt(s)",
    )


def deadline(*, first_attempted_at: datetime) -> datetime:
    """When this delivery stops being retried.

    Published so the worker, the table and any operator answer the question the
    same way. **Truth has exactly one authoritative representation** (§2), and a
    deadline recomputed in three places eventually disagrees with itself.
    """
    return first_attempted_at + DELIVERY_WINDOW


def utcnow() -> datetime:
    """The one place this module reads a clock.

    Callers pass ``now`` in. This exists so a composition root has somewhere
    honest to get it from, rather than each caller reaching for
    ``datetime.now()`` with a different tzinfo argument.
    """
    return datetime.now(UTC)
