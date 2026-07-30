"""What an inference cost, in facts rather than currency.

**Deliberately no money anywhere in this file.** Tokens, latency and retry
count are facts about what happened and stay true forever. A price is a
contract term: vendor-specific, time-varying, renegotiable, and different
per account. A dollar figure written onto an inference record would be
correct for about a week and quietly wrong for the rest of the row's life.

Pricing is a table applied *outside* the port, at reporting time, over
stored usage — so a price change re-prices history correctly instead of
leaving a stratum of rows priced at a rate nobody remembers.

This is the same discipline that keeps Provider Normalization from
inventing a confidence score: **record what happened; compute judgements
where the inputs are actually known.**
"""

from __future__ import annotations

from dataclasses import dataclass


class UsageError(ValueError):
    """A usage record was constructed that cannot describe a real call."""


@dataclass(frozen=True, slots=True)
class InferenceUsage:
    """What one call to a model consumed.

    Both scaling triggers in ``docs/architecture/12-scalability.md`` read
    from here, and both are vendor-specific in the raw — normalising them is
    what the port is for.
    """

    input_tokens: int
    output_tokens: int
    #: Wall-clock time for the vendor call, including retries the adapter
    #: performed internally. Integer milliseconds: sub-millisecond precision
    #: on a network call is noise, and quoting it would imply a resolution
    #: the measurement does not have.
    latency_ms: int
    #: How many times the call was retried before this record was written —
    #: the platform's own retry policy, not an adapter's internal one, since
    #: no adapter retries. A rising value is the earliest visible sign of a
    #: rate-limit problem, visible long before it is visible on an invoice
    #: (R-01), and it is recorded on failed calls precisely so a retry storm
    #: is legible in the rows that prove one happened.
    retries: int = 0

    def __post_init__(self) -> None:
        for name, value in (
            ("input_tokens", self.input_tokens),
            ("output_tokens", self.output_tokens),
            ("latency_ms", self.latency_ms),
            ("retries", self.retries),
        ):
            if value < 0:
                raise UsageError(
                    f"{name} cannot be negative (got {value}). Usage records what a call "
                    "consumed, and no call consumes a negative amount of anything."
                )

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens
