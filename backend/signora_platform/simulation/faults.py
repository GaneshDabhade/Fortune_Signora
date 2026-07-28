"""Fault injection — turning a healthy response into a realistic failure.

**These are the tests that justify the whole framework.** A real provider
cannot be asked to time out on demand, return a truncated body, or deliver
the same record three times. Without injection, the retry logic, the
backoff, the dead-lettering, and the idempotency ledger are all code that
has never been exercised by the thing it exists to handle.

Two contracts do the work:

**Faults surface through production error semantics.** The framework
declares *what* failed; the adapter raises the Provider Port's own failure
type. A bespoke simulator exception would mean the retry logic above never
sees what it will see in production — testing the mock instead of the code
(20-provider-simulation.md, principle 6).

**Fault selection is seeded.** "Fails 10% of the time" must fail on the
same 10% every run. Otherwise a scenario passes and fails at random, and
within a week nobody trusts the suite.

Deliberately minimal. The simulator is infrastructure, not product: this
covers the failure modes the pipeline must handle and stops there.
"""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Final


class FaultKind(StrEnum):
    """Failure modes the ingestion pipeline is required to survive.

    Each maps to a documented pipeline behaviour, which is why the list is
    short and closed — a fault with no corresponding behaviour to test
    would be simulation for its own sake.
    """

    TIMEOUT = "timeout"
    """Transient. Must retry with backoff."""

    SERVER_ERROR = "server_error"
    """Transient 5xx. Must retry with backoff."""

    RATE_LIMITED = "rate_limited"
    """Transient, with a vendor-supplied wait. Must honour it rather than
    guessing a backoff and being throttled harder."""

    MALFORMED_PAYLOAD = "malformed_payload"
    """Permanent. Normalization must reject it and the event must
    dead-letter with enough context to diagnose the vendor change."""

    PARTIAL_RESPONSE = "partial_response"
    """A short page that still claims more. Exercises the pagination loop
    against a provider that under-delivers."""

    DUPLICATE = "duplicate"
    """The same record delivered N times. At-least-once delivery
    guarantees this in production; it is where platform-owned idempotency
    is exercised rather than assumed."""

    OUT_OF_ORDER = "out_of_order"
    """A record whose `occurred_at` precedes one already delivered."""


DEFAULT_DUPLICATE_COUNT: Final = 2
DEFAULT_RETRY_AFTER_SECONDS: Final = 30.0


class FaultProfileError(ValueError):
    """A scenario declared a fault the injector does not know.

    Raised at **load**, never at injection time: a typo would otherwise
    surface as a scenario that silently never faults — a fault-tolerance
    test that never tests fault tolerance, and looks green forever.
    """


@dataclass(frozen=True, slots=True)
class FaultRule:
    """One declared fault and how often it fires."""

    kind: FaultKind
    #: 0.0–1.0. Evaluated against the seeded generator, so the same events
    #: fault on every run.
    probability: float = 1.0
    #: DUPLICATE only: how many times the record is delivered.
    repeat: int = DEFAULT_DUPLICATE_COUNT
    #: RATE_LIMITED only: the wait the "vendor" reports.
    retry_after_seconds: float = DEFAULT_RETRY_AFTER_SECONDS

    def __post_init__(self) -> None:
        if not 0.0 <= self.probability <= 1.0:
            raise FaultProfileError(f"probability must be between 0 and 1, got {self.probability}")
        if self.repeat < 1:
            raise FaultProfileError(f"repeat must be at least 1, got {self.repeat}")


@dataclass(frozen=True, slots=True)
class FaultProfile:
    """The faults a scenario declares."""

    rules: tuple[FaultRule, ...] = field(default_factory=tuple)

    @classmethod
    def from_declaration(cls, declared: Sequence[Mapping[str, Any]]) -> FaultProfile:
        """Parse a scenario's fault declaration, failing on anything
        unrecognised."""
        rules: list[FaultRule] = []
        for entry in declared:
            raw_kind = str(entry.get("kind", ""))
            try:
                kind = FaultKind(raw_kind)
            except ValueError as exc:
                raise FaultProfileError(
                    f"unknown fault kind '{raw_kind}'. Known kinds: "
                    f"{sorted(k.value for k in FaultKind)}. A typo here would otherwise "
                    "produce a scenario that silently never faults."
                ) from exc
            rules.append(
                FaultRule(
                    kind=kind,
                    probability=float(entry.get("probability", 1.0)),
                    repeat=int(entry.get("repeat", DEFAULT_DUPLICATE_COUNT)),
                    retry_after_seconds=float(
                        entry.get("retry_after_seconds", DEFAULT_RETRY_AFTER_SECONDS)
                    ),
                )
            )
        return cls(rules=tuple(rules))


@dataclass(frozen=True, slots=True)
class InjectedFault:
    """What the injector decided for one event.

    A *decision*, not an exception: the framework declares what failed and
    the adapter raises the Provider Port's own type. Raising here would put
    a simulator exception on the path production never takes.
    """

    kind: FaultKind
    event_sequence: int
    repeat: int = 1
    retry_after_seconds: float | None = None

    def as_log_fields(self) -> dict[str, str | int | float]:
        """Logged distinguishably from a genuine failure. An operator
        debugging a scenario must never wonder whether a failure was
        intentional."""
        fields: dict[str, str | int | float] = {
            "injected_fault": self.kind.value,
            "fault_event_sequence": self.event_sequence,
            "simulated": "true",
        }
        if self.retry_after_seconds is not None:
            fields["fault_retry_after_seconds"] = self.retry_after_seconds
        return fields


class FaultInjector:
    """Decides, deterministically, which events fault and how.

    The generator is seeded per injector instance, so two concurrent
    scenario runs cannot consume each other's randomness and change one
    another's fault pattern.
    """

    def __init__(self, profile: FaultProfile, *, seed: int) -> None:
        self._profile = profile
        self._rng = random.Random(seed)  # noqa: S311 - simulation, not cryptography

    def decide(self, event_sequence: int) -> InjectedFault | None:
        """Whether this event faults, and how.

        Draws once per rule regardless of outcome, so adding a rule does
        not shift the draws of the rules after it — otherwise appending a
        fault to a scenario would silently change which events every
        *other* fault lands on, and every recorded run would become
        incomparable.
        """
        chosen: InjectedFault | None = None

        for rule in self._profile.rules:
            fires = self._rng.random() < rule.probability
            if fires and chosen is None:
                chosen = InjectedFault(
                    kind=rule.kind,
                    event_sequence=event_sequence,
                    repeat=rule.repeat if rule.kind is FaultKind.DUPLICATE else 1,
                    retry_after_seconds=(
                        rule.retry_after_seconds if rule.kind is FaultKind.RATE_LIMITED else None
                    ),
                )

        return chosen
