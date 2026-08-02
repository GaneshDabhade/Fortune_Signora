"""How fast the platform may ask a provider for things.

**`ProviderDescriptor.rate_limit_per_minute` has existed since M2.0 and nothing
has ever read it.** Its own docstring states the purpose — *"declared so the
platform can pace itself rather than discovering the limit by being
throttled"* — and the contract suite asserts every adapter declares one. The
declaration was honoured by nobody.

**What that costs is not politeness.** `_drain` fetches up to `MAX_PAGES` pages
back to back, as fast as the network allows. Against an adapter declaring sixty
requests a minute, a single sync can spend its entire quota in seconds and then
receive `ProviderRateLimitedError` — which is *transient*, so the sync fails,
the watermark is deliberately left untouched, and the whole thing is retried
later against a quota that is still exhausted. **The pages already fetched are
not lost, but the requests that bought them are spent twice.**

**A rate limit discovered by being throttled is a rate limit that costs money
to discover**, every time, and the number needed to avoid it was declared on
the adapter all along.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Rates are declared per minute; everything here works in seconds because
#: that is what a caller waits in.
_SECONDS_PER_MINUTE = 60.0


@dataclass(frozen=True, slots=True)
class RequestPace:
    """The minimum spacing between two requests to one provider.

    **A value object rather than a number**, so the two things that are easy
    to get wrong are stated once: an undeclared limit means *no pacing at all*,
    and time already spent counts against the interval.
    """

    #: `None` when the adapter declares no limit — which the contract suite
    #: permits explicitly. **No limit means no waiting**, never a default one:
    #: inventing a rate for a provider that did not state one would slow every
    #: sync to a speed nobody asked for.
    requests_per_minute: int | None

    def __post_init__(self) -> None:
        if self.requests_per_minute is not None and self.requests_per_minute <= 0:
            # A declared limit of zero would mean "never ask", which is not a
            # rate limit — it is a disabled provider, and that is a different
            # decision made somewhere else.
            raise ValueError("a declared rate limit must be positive, or absent")

    @property
    def interval_seconds(self) -> float:
        """How far apart two requests must be. Zero when nothing was declared."""
        if self.requests_per_minute is None:
            return 0.0
        return _SECONDS_PER_MINUTE / self.requests_per_minute

    def delay_after(self, elapsed_seconds: float) -> float:
        """How long to wait before the next request, given how long the last
        one took.

        **Elapsed time counts against the interval.** A provider that took two
        seconds to answer has already spent two seconds of its own spacing;
        waiting the full interval on top would punish a slow provider twice and
        make a sync take far longer than the declared rate requires.

        **Never negative.** A request slower than the interval means the next
        one may go immediately — the limit has already been respected by the
        provider's own latency.
        """
        return max(0.0, self.interval_seconds - max(0.0, elapsed_seconds))


__all__ = ["RequestPace"]
