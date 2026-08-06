"""Which open affiliation a departure closes, when nobody knows who left.

**The one genuinely hard question in an anonymous People domain**, and it is
stated here as a rule rather than buried in whichever use case needed it
first — the discipline `knowledge_graph.select_name` set:

> *"the most recently observed claim wins… ties break on provider name"* —
> a rule written down, reported alongside its answer, and **refusing provider
> precedence because provider precedence is a customer policy.**

### The problem, exactly

A provider says *"a VP of Engineering left Acme in September."* **It does not
say which one.** If Acme has two open VP-of-Engineering affiliations, closing
either is a guess, and closing the wrong one writes a false interval into the
record every downstream consumer will cite.

### The rule

> **A departure closes the single open affiliation at that company with that
> title. If there is more than one, it closes none and says so.**

**Refusing is the whole point.** The available alternatives are each a
judgement this module has no standing to make — *close the oldest* assumes
tenure predicts departure, *close the newest* assumes the opposite, and
*close them all* invents a mass exit from one event. **An unmatched departure
is recoverable; a wrongly closed interval is not**, because nothing
downstream can tell it from a real one.

**Title comparison is exact after case and space folding, and nothing more.**
*"VP of Engineering"* and *"VP, Engineering"* are the same job to a human and
two strings here, so a departure under the second leaves the first open. **That
is the same limitation `commercial_profile.evaluation` carries and for the same
reason**: deciding two different words mean one thing is a reviewed catalog,
not code, and inventing one here would put a second vocabulary in the module
that owns none.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Sequence
from uuid import UUID

from modules.people.domain.affiliation import Affiliation


class MatchOutcome(StrEnum):
    """What a departure was able to do. **A category, never a confidence.**

    A number here would invite a threshold, and a threshold would decide when
    to close an interval on a guess — which is the one thing this rule exists
    to refuse.
    """

    MATCHED = "matched"
    """Exactly one open affiliation had that title. It is the one to close."""

    NONE_OPEN = "none_open"
    """**Nobody was recorded as holding that role.** Signora never saw the
    arrival — the person was in post before it started watching, or the
    appointment was never reported. Not an error, and not a departure to
    discard: the fact still happened."""

    AMBIGUOUS = "ambiguous"
    """**Two or more people hold that title at that company.** The departure
    is real and its subject is unknowable from this event. **Nothing is
    closed**, and the candidates travel with the outcome so a consumer can say
    *"one of these two left"* rather than nothing at all."""


@dataclass(frozen=True, slots=True)
class DepartureMatch:
    """The answer, and enough of the working to explain it.

    **`candidates` is populated on every outcome, not only the ambiguous one.**
    A consumer rendering *"we could not tell which of these three"* needs them,
    and a consumer rendering the matched one needs to know it was the only
    candidate rather than the pick of several.
    """

    outcome: MatchOutcome
    candidates: tuple[Affiliation, ...]

    @property
    def closes(self) -> Affiliation | None:
        """The affiliation to end, or ``None`` when the rule refused.

        **`None` on `AMBIGUOUS` is the rule doing its job**, not a failure to
        handle. A caller that treats it as *"nothing happened"* has discarded a
        real departure; a caller that picks from `candidates` has made the
        judgement this module declined to make, and owns it.
        """
        return self.candidates[0] if self.outcome is MatchOutcome.MATCHED else None


def _normalise(title: str) -> str:
    """Case and surrounding space only — **deliberately not a synonym map.**

    Identical to `commercial_profile.evaluation._normalise`, and the
    duplication is two words of code rather than a shared dependency between
    two bounded contexts that must not import each other.
    """
    return " ".join(title.split()).casefold()


def match_departure(
    open_affiliations: Sequence[Affiliation], *, company_id: UUID, title: str
) -> DepartureMatch:
    """Find the affiliation a departure closes.

    **Pure.** No repository, no session, no clock — the caller supplies the
    open affiliations it already holds, so the rule can be replayed, tested
    and explained without a database.

    **Filters on company as well as title**, because the same title is held at
    every company in the workspace and a rule matching on title alone would
    close a VP of Engineering at the wrong account.
    """
    wanted = _normalise(title)
    candidates = tuple(
        affiliation
        for affiliation in open_affiliations
        if affiliation.company_id == company_id
        and affiliation.is_current
        and _normalise(affiliation.title) == wanted
    )

    if not candidates:
        return DepartureMatch(outcome=MatchOutcome.NONE_OPEN, candidates=())
    if len(candidates) > 1:
        return DepartureMatch(outcome=MatchOutcome.AMBIGUOUS, candidates=candidates)
    return DepartureMatch(outcome=MatchOutcome.MATCHED, candidates=candidates)


__all__ = ["DepartureMatch", "MatchOutcome", "match_departure"]
