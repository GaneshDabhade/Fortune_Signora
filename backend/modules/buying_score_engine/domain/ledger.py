"""The Contribution Ledger — the authoritative explanation of a score.

**Read the dependency as ledger → score, never score + ledger.** A buying
score is a *projection derived from* its ledger, not a number that happens
to travel with an audit trail. The ledger is the thing that reasons; the
score is what falls out of it. Every reduction the score performs is undone
by reading this object, and that is what makes the reduction safe rather
than lossy.

It is a domain object with behaviour, not a list of rows. Modelled as a
bare sequence, the questions only it can answer — does this reproduce? is
this contested? when does the arithmetic next change? — would drain into a
service and each caller would re-derive them slightly differently. That is
the anemic-model smell, and here it would quietly produce two answers to
*"why is this account scored where it is?"*.

Three properties carry the design:

**It reproduces its own score, with no clock and no configuration.** Sum
the counted entries, divide by the ceiling it carries. Integer arithmetic
throughout — a stored ledger that reproduced only approximately would be an
explanation nobody could rely on.

**Contradiction is preserved, never netted.** Attention is unsigned for
every posture. An expansion reading and a contraction reading both add
attention and the disagreement is recorded as `contested` with the
dissenting signals **named** — because netting them would score a
fought-over account like an inert one, and those are the two most different
accounts in the book.

**Nothing is silently dropped.** A business event already counted through
another signal stays in the ledger with a zero contribution and a stated
reason. A zero with a reason is information; an absent row is a mystery.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from modules.buying_score_engine.domain.scoring_model import PERCENT, Posture
from modules.signal_engine.public import Relevance, SignalType

MAX_SCORE = 100
"""The top of the scale. Saturation is accepted and honest: it means *"as
much attention as we can justify"*, not *"certain to buy"*."""


class LedgerError(ValueError):
    """A ledger was built that cannot be trusted to explain its score."""


@dataclass(frozen=True, slots=True)
class Contribution:
    """One business event's contribution, with every number that produced it.

    The unit is the **business event**, not the signal. A composite
    hypothesis and the constituent it enriches rest on the same grounds read
    two ways; counting both would double-count the evidence, so an event is
    attributed to exactly one signal and the others record why they counted
    nothing.
    """

    business_event_id: UUID
    signal_id: UUID
    signal_type: SignalType
    posture: Posture
    relevance: Relevance

    base_weight: int
    relevance_multiplier: int
    age_band: str
    age_multiplier: int
    #: Points, after all three factors. Integer arithmetic end to end.
    contribution: int

    #: Whether this entry's points count toward the score. `False` means the
    #: business event was already attributed to a higher-weighted signal.
    counted: bool
    #: The sentence a customer reads, rendered from the same fields an
    #: auditor checks — so the explanation and the arithmetic cannot diverge.
    reason: str

    #: When this entry's age band began. Stored because it is the evidence-
    #: derived moment this entry last changed, and score identity is keyed
    #: on the latest such moment rather than on a reading of the clock.
    band_started_at: datetime
    #: When this entry's age band ends, and therefore the next moment its
    #: contribution changes. Stored rather than derived, so a ledger can say
    #: when it goes stale without consulting the model that produced it.
    band_ends_at: datetime

    def __post_init__(self) -> None:
        if self.contribution < 0:
            raise LedgerError(
                f"contribution for signal {self.signal_id} is negative. Attention is unsigned for "
                "every posture: a contraction risk earns attention just as an expansion "
                "opportunity does, and a minus sign here is the netting this module refuses."
            )
        if not self.counted and self.contribution != 0:
            raise LedgerError(
                f"contribution for signal {self.signal_id} is not counted but carries "
                f"{self.contribution} points. An uncounted entry with points is an explanation "
                "that disagrees with its own arithmetic."
            )
        if not self.reason.strip():
            raise LedgerError(
                f"contribution for signal {self.signal_id} has no reason. A number a customer "
                "cannot challenge is exactly the opaque score this module exists to avoid."
            )
        if self.band_ends_at < self.band_started_at:
            raise LedgerError(
                f"contribution for signal {self.signal_id} has a band ending before it begins."
            )


def weigh(base_weight: int, relevance_multiplier: int, age_multiplier: int) -> int:
    """The whole of the arithmetic, in one place, in integers.

    Deliberately not floating point: a stored score must reproduce from its
    ledger **exactly** (AC-51), and accumulated float error would make the
    explanation approximate — which, for the one artifact whose job is to be
    checkable, is the same as useless.
    """
    return base_weight * relevance_multiplier * age_multiplier // (PERCENT * PERCENT)


@dataclass(frozen=True, slots=True)
class ContributionLedger:
    """Every entry that produced a score, and the arithmetic that did it."""

    entries: tuple[Contribution, ...]
    #: The point total that reads as 100, copied from the model in force.
    #: Carried here so the ledger reproduces its score with **no reference
    #: to current configuration** — a historical score explained through
    #: today's ceiling would be a different number wearing the same label.
    ceiling: int

    def __post_init__(self) -> None:
        if self.ceiling <= 0:
            raise LedgerError("a ledger needs a positive ceiling to normalize against.")

        counted = [entry for entry in self.entries if entry.counted]
        seen: set[UUID] = set()
        for entry in counted:
            if entry.business_event_id in seen:
                raise LedgerError(
                    f"business event {entry.business_event_id} is counted twice. The unit of "
                    "contribution is the business event precisely so the same grounds read two "
                    "ways cannot inflate a score."
                )
            seen.add(entry.business_event_id)

    def total(self) -> int:
        """The raw point sum, before normalization."""
        return sum(entry.contribution for entry in self.entries if entry.counted)

    def value(self) -> int:
        """The score this ledger projects. **No clock, no configuration.**"""
        return min(MAX_SCORE, self.total() * MAX_SCORE // self.ceiling)

    def counted_events(self) -> frozenset[UUID]:
        return frozenset(entry.business_event_id for entry in self.entries if entry.counted)

    def contributing_signals(self) -> tuple[UUID, ...]:
        return tuple(sorted({entry.signal_id for entry in self.entries}, key=str))

    def posture_summary(self) -> dict[Posture, int]:
        """Attention by posture — **never summed into the scalar.**

        This is what makes a contested account legible: two accounts can
        score identically and mean opposite things, and the only place that
        difference survives is here.
        """
        summary = {posture: 0 for posture in Posture}
        for entry in self.entries:
            if entry.counted:
                summary[entry.posture] += entry.contribution
        return summary

    @property
    def is_contested(self) -> bool:
        """Whether opposing commercial readings are both live and both count.

        Contradiction is **detected and marked, never resolved**. Deciding
        which reading is true needs evidence this module does not have and
        judgement that belongs to AI Reasoning and to humans.
        """
        summary = self.posture_summary()
        return summary[Posture.EXPANSIONARY] > 0 and summary[Posture.CONTRACTIONARY] > 0

    def dissent(self) -> tuple[UUID, ...]:
        """The outweighed reading's signals, **named rather than counted**.

        A caller told only *"contested"* learns that something disagrees; a
        caller told *which* signals disagree can go and read them. The
        minority is by attention, with ties resolved toward the
        contractionary reading — deterministic, and it errs toward surfacing
        risk rather than burying it.
        """
        if not self.is_contested:
            return ()
        summary = self.posture_summary()
        dissenting = (
            Posture.CONTRACTIONARY
            if summary[Posture.CONTRACTIONARY] <= summary[Posture.EXPANSIONARY]
            else Posture.EXPANSIONARY
        )
        return tuple(
            sorted(
                {
                    entry.signal_id
                    for entry in self.entries
                    if entry.counted and entry.posture is dissenting
                },
                key=str,
            )
        )

    def valid_until(self) -> datetime | None:
        """The next moment this ledger's arithmetic provably changes.

        The earliest band transition across **every** entry, counted or not
        — an uncounted entry can become the counted one when the signal
        currently holding its business event expires.

        `None` means nothing is contributing, so nothing will change without
        a new signal arriving, and a signal arriving publishes an event.
        """
        if not self.entries:
            return None
        return min(entry.band_ends_at for entry in self.entries)

    def basis_at(self) -> datetime | None:
        """The latest moment at which this ledger's composition changed.

        Score identity is keyed on this rather than on a reading of the
        clock, so replaying a workspace's history reproduces byte-identical
        score ids and the established insert-conflict deduplication keeps
        working. `None` for an empty ledger — see `BuyingScore.projected_from`.
        """
        if not self.entries:
            return None
        return max(entry.band_started_at for entry in self.entries)
