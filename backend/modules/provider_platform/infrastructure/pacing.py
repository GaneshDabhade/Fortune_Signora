"""The real pacer: it sleeps.

**The whole adapter, and deliberately so.** Everything that decides *how long*
lives in `domain/pacing.py`, where it can be asserted without a clock; this is
the one line that cannot be.
"""

from __future__ import annotations

import asyncio


class AsyncioPacer:
    """Yields the event loop for the requested interval.

    `asyncio.sleep` rather than a blocking wait: a paced sync must not hold a
    worker's event loop hostage while it waits, or one throttled provider would
    stall every other sync sharing the pool.
    """

    async def wait(self, seconds: float) -> None:
        if seconds <= 0:
            # **Not `sleep(0)`.** That yields to the loop, which is a
            # scheduling decision this has no business making on a path that
            # was told to wait for nothing.
            return
        await asyncio.sleep(seconds)


__all__ = ["AsyncioPacer"]
