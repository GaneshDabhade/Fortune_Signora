"""The Virtual Clock — the only source of time inside the simulation.

**Nothing in `simulation/` calls `datetime.now()`.** A single direct call
reintroduces non-determinism that is very hard to find later, because it
produces a test that fails roughly once a week and passes on re-run. A
structural test asserts this rather than trusting the convention
(docs/architecture/20-provider-simulation.md, stage 3).

Two clocks matter and they are deliberately different:

* **Logical time** — what the simulated world believes. `occurred_at` on a
  payload comes from here.
* **Real time** — when the row was actually written. The outbox records
  this.

The gap between them is not a bug: it is exactly what a backfill looks
like, and the pipeline must handle a large one.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Final

DEFAULT_EPOCH: Final = datetime(2026, 1, 1, tzinfo=UTC)


class ClockMode(StrEnum):
    INSTANT = "instant"
    """No delay. Logical time advances on demand; a scenario completes as
    fast as the pipeline can consume it. The mode CI uses."""

    REALTIME = "realtime"
    """One logical second per real second. Used to watch a scenario behave
    the way a customer's data would."""

    ACCELERATED = "accelerated"
    """Logical time advances faster than real time by a multiplier. Four
    simulated weeks in ninety seconds, which is what makes a temporal
    provider demonstrable at all."""


@dataclass(slots=True)
class VirtualClock:
    """Owns "now" for one simulation run.

    Injected, never global (CLAUDE.md §6). A module-level clock would be
    shared between concurrent scenario runs, and each would advance the
    other's time.
    """

    mode: ClockMode = ClockMode.INSTANT
    epoch: datetime = DEFAULT_EPOCH
    #: Logical seconds per real second. Only meaningful in ACCELERATED.
    multiplier: float = 1.0
    _elapsed: timedelta = field(default=timedelta(), init=False)

    def __post_init__(self) -> None:
        if self.epoch.tzinfo is None:
            raise ValueError("epoch must be timezone-aware; a naive epoch produces naive payloads")
        if self.mode is ClockMode.ACCELERATED and self.multiplier <= 1:
            raise ValueError("accelerated clock requires a multiplier greater than 1")

    @property
    def now(self) -> datetime:
        """Current logical time. The only "now" a generator may use."""
        return self.epoch + self._elapsed

    async def advance(self, delta: timedelta) -> None:
        """Move logical time forward, sleeping if the mode requires it.

        In INSTANT mode this is pure bookkeeping — no sleep, so a
        four-week scenario runs in milliseconds and produces identical
        timestamps regardless of how long generation actually took.
        """
        if delta < timedelta():
            raise ValueError(
                "logical time does not move backwards; emit an earlier occurred_at instead"
            )

        self._elapsed += delta

        if self.mode is ClockMode.REALTIME:
            await asyncio.sleep(delta.total_seconds())
        elif self.mode is ClockMode.ACCELERATED:
            await asyncio.sleep(delta.total_seconds() / self.multiplier)

    def at(self, offset: timedelta) -> datetime:
        """A logical timestamp at a fixed offset from the epoch.

        Used to place an event in the timeline without advancing the clock
        — which is how an out-of-order or late-arriving event is expressed:
        its `occurred_at` precedes events already emitted.
        """
        return self.epoch + offset

    def describe(self) -> dict[str, str | float]:
        """Recorded in every replay context, so a run's timing is
        reproducible from its record."""
        return {
            "mode": self.mode.value,
            "epoch": self.epoch.isoformat(),
            "multiplier": self.multiplier,
        }
