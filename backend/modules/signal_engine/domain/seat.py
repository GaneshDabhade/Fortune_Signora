"""Which seat a decision-maker signal is about, and for how long it was held.

**TASK-458.** `new_decision_maker` and `decision_maker_departed` have always
named a *title* — the business event's `facts` carry one and the summary reads
*"Their VP of Engineering departed"*. ⛔ **What they could not say is which
holder, and over what period**, and that is the whole of this module.

### ⛔ No name, ever

[C-221](../../../../docs/LANE_COORDINATION.md) is the specification rather
than a constraint: **a subject, a role and a period — none of which is a
name.** `people` publishes no name to read, and nothing here would have
anywhere to put one.

### Pure, and it does not import `people`

**The application layer resolves affiliations and passes plain values in**, on
exactly the terms `ground()` already takes `declared: frozenset[str]`:
*"passed in rather than read… this module performs no I/O"*. ⚡ **So this file
imports nothing from another module** — `AffiliationView` stays on the
application side of the boundary and `Seat` is this module's own vocabulary
([ADR-0403](../../../../docs/architecture/adr/0403-signal-engine-reads-a-declaration.md)).

### One candidate names the seat; more than one names none

**`people`'s `match_departure` refuses to close an interval when two people
hold the same title at one company** — *"an unmatched departure is
recoverable; a wrongly closed interval is not"*. ⚡ **The same refusal, applied
to a read**: a rationale that picked one of two holders would be asserting
something no evidence supports, and a signal's rationale is the part a
customer is invited to challenge.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Final

#: Where the leadership rules record the seat. `LeadershipAppointed` and
#: `LeadershipDeparted` both write `{"title": …, "seniority": …, "direction":
#: …}`, and the title is the only part a seat can be matched on.
TITLE_FACT: Final = "title"


def fold_title(title: str) -> str:
    """How two titles are compared. **Case and internal space only.**

    ⛔ **Deliberately not a synonym map.** *"VP of Engineering"* and *"VP,
    Engineering"* are one job to a person and two strings here — the same
    limitation `people.match_departure` carries, and for its stated reason:
    deciding two different words mean one thing is a reviewed catalog, not
    code, and inventing one here would put a third vocabulary beside the two
    that already agree to be literal.
    """
    return " ".join(title.split()).casefold()


@dataclass(frozen=True, slots=True)
class Seat:
    """A role held at a company, over a period.

    **The period is the deliverable.** `ended_on = None` means **no departure
    has been observed**, which the People contract is explicit is *not* the
    same claim as *"they still hold it"* — and a rationale that flattened the
    two would be putting a claim in a customer's hands that nothing supports.
    """

    title: str
    seniority: str
    started_on: date
    ended_on: date | None = None

    @property
    def is_open(self) -> bool:
        """**No departure has been observed.** Not *"still held"*."""
        return self.ended_on is None

    @property
    def tenure(self) -> str:
        """The period, in the words a customer would use.

        ⚡ **The open case states the absence rather than implying
        continuation** — [P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md).
        *"Held since March"* quietly asserts they are still there; the
        contract says only that nothing has been observed since.
        """
        if self.ended_on is None:
            return f"held from {_spoken(self.started_on)}, with no departure recorded"
        return f"held from {_spoken(self.started_on)} to {_spoken(self.ended_on)}"


def seat_for(seats: Sequence[Seat], *, title: str) -> Seat | None:
    """The one seat with this title, or **`None` when it cannot be told.**

    ⛔ **`None` covers two different situations and that is deliberate.**
    *Nobody recorded holding this title* and *two people did* both mean the
    rationale may not name a period — and a caller that distinguished them
    would be tempted to pick one of the two.

    ⚡ **This is `match_departure`'s refusal read rather than written.** It
    closes no interval and asserts nothing; it only declines to describe a
    period the evidence does not single out.
    """
    wanted = fold_title(title)
    matches = [seat for seat in seats if fold_title(seat.title) == wanted]
    return matches[0] if len(matches) == 1 else None


def _spoken(when: date) -> str:
    """A date a customer reads, not an ISO string.

    Built by hand rather than with `%-d`, which is glibc-only and would make
    the rendered rationale differ between a developer's machine and a
    container — the hidden input §2 forbids, in its smallest form.
    """
    return f"{when.day} {when:%B %Y}"


__all__ = ["TITLE_FACT", "Seat", "fold_title", "seat_for"]
