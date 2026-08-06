"""How a signal leaves the queue.

**A signal is raised today and never resolved.** The approved Signal Center is
*"a triage queue, not a notification list"* — every signal ends in a decision,
and *"nothing is deleted: every resolution is auditable."* This is that
decision, and it is a **separate record rather than a field on the signal.**

**The signal is immutable and stays immutable.** It records what Signora
concluded from evidence at a moment; a person disagreeing with it later does
not change what was concluded. So a resolution *refers* to a signal and never
edits one — the same shape as a Decision Package naming a score, and for the
same reason: **editing the record would destroy the only account of what a
customer was actually shown.**

## Two things called *ignoring*, and they are not the same

`Relevance.IGNORED` already exists in this module and is **not** this concept.
The distinction is worth stating because the words collide and the facts do
not:

| | `Relevance.IGNORED` | A dismissal here |
|---|---|---|
| **Scope** | A signal **type**, for a workspace | **One signal** |
| **Direction** | Prospective — *"never raise this kind"* | Retrospective — *"this one was wrong"* |
| **Where it lives** | The workspace's profile | This record |
| **Effect** | Never generated — `Signal` refuses it | It existed, was shown, was judged |

**A workspace that dismisses six `hiring_surge` signals has not said it wants
none of them.** Collapsing the two would silently turn feedback about *this
account* into configuration about *every* account, which is a customer's
decision and not an inference this module may make.

## Dismissal is `opportunity_engine`'s concept one level down

`Stage.DISMISSED` means *"we should not have been shown this"* and is
**deliberately distinct from `CLOSED_LOST`** — one is feedback about Signora's
judgement, the other is a sales outcome. A signal-level dismissal is that same
feedback about a smaller unit, so **the vocabulary is reused and not
redefined** (`CLAUDE.md` §4).

## Why the outcomes are four types rather than one type with four flags

*"A dismissal cannot be recorded without a reason"* is an invariant, and a
`reason: str | None` validated in `__post_init__` is a **check** — something a
future caller can pass `None` to and discover at runtime. Four frozen types,
each carrying exactly what its outcome needs, make the omission
**unconstructable**: there is no way to build a `Dismissed` without a reason
because the field has no default (§2, *types should make incorrect architecture
impossible*).

**No outcome may be authored by Signora.** Every one names an actor, and the
platform is not one — *intelligence suggests; humans commit.*
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Final
from uuid import UUID

PAYLOAD_VERSION: Final = 1

#: The longest a reason may be. Long enough for a sentence explaining why the
#: reading was wrong, short enough that nobody pastes a call transcript into
#: the field a rule-precision measure will later read.
MAX_REASON = 500


class ResolutionError(ValueError):
    """**Something the customer described that cannot be recorded** — a
    dismissal with no reason, a snooze that has already elapsed.

    The message is customer copy: it says which part was wrong and why the
    product insists on it. Surfaces as `422`.
    """


class UnreadableOutcomeError(ResolutionError):
    """**Something Signora stored that this build cannot interpret** — an
    outcome discriminator it does not know.

    **A subclass rather than a sibling**, so every `except ResolutionError`
    still catches it while the handler's MRO walk finds this type's own row
    first and answers `500`.

    **The distinction is which of us was wrong**, and it is `B-103`'s exactly:
    one class carrying both meanings told a seller *"your request was refused"*
    for a bug in ours. That row was fixed in `ai_research_engine` hours before
    this file reproduced the same shape — which is the argument for the
    repository-wide invariant that row's fix deliberately did not write.
    """


@dataclass(frozen=True, slots=True)
class DismissalReason:
    """Why this signal should not have been raised, in a person's own words.

    **A value object rather than a `str`**, so the emptiness check happens once
    at the only place a reason can come into existence. A caller cannot reach
    `Dismissed` with whitespace by taking a different route.

    **Deliberately free text and not a closed set.** A vocabulary of dismissal
    reasons is a product decision about what the platform believes can be wrong
    with its own judgement, and inventing one inside an implementation slice
    would be exactly the *"architecture arriving in a feature"* §20e forbids. A
    closed set may well be right later; it is not this slice's to declare.
    """

    text: str

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ResolutionError(
                "a dismissal with no reason is indistinguishable from one nobody explained, "
                "and the reason is the only part of a dismissal a rule can learn from."
            )
        if len(self.text) > MAX_REASON:
            raise ResolutionError(
                f"a dismissal reason is at most {MAX_REASON} characters; this one is "
                f"{len(self.text)}."
            )


@dataclass(frozen=True, slots=True)
class Actioned:
    """Somebody did something about it. **The queue's success case.**

    Deliberately carries nothing. *What* they did happens in a CRM, a call or
    an inbox — none of which Signora can see — and inventing a field to hold it
    would be asking the customer to restate work the platform cannot verify.
    """


@dataclass(frozen=True, slots=True)
class Assigned:
    """Somebody else owns the decision now.

    **Still open.** Assigning is routing, not resolving, and a queue that
    treated it as an ending would lose every signal handed to a colleague.
    """

    to: UUID


@dataclass(frozen=True, slots=True)
class Snoozed:
    """Not now, but not wrong — *"snoozed signals return at the stated time
    with their original evidence intact."*

    **The evidence is intact because nothing about the signal is touched.**
    Returning is a read that stops filtering this resolution out, not a
    regeneration, so the account a customer sees in a fortnight is the one they
    postponed rather than a fresh reading that happens to resemble it.
    """

    until: datetime


@dataclass(frozen=True, slots=True)
class Dismissed:
    """*"We should not have been shown this."* Feedback about Signora's
    judgement, and the only outcome that says the platform was wrong.

    `reason` has **no default**, which is what makes the acceptance criterion a
    property of the type rather than a rule somebody has to remember.
    """

    reason: DismissalReason


#: What a signal can become. **Closed by construction**: a fifth outcome is a
#: product decision about what triage means, and `mypy` refuses an unhandled
#: member at every match site rather than letting one fall through a default.
Outcome = Actioned | Assigned | Snoozed | Dismissed

#: The outcomes after which a signal is no longer in the queue. `Assigned` is
#: deliberately absent — it moves the decision, it does not make it.
CLOSING: Final = (Actioned, Dismissed)


#: The name of each outcome, and **the only place these four words are
#: decided.** They are this module's ubiquitous language for *how a signal left
#: the queue* (§4), so they belong to the domain rather than to either of the
#: two edges that spell them out: the column `SignalResolutionModel.outcome`
#: stores one, and `signal.resolved` publishes one. **Those must never be able
#: to disagree** — a stored `dismissed` and a published `Dismissed` would be
#: one fact with two representations, and the bus is where the second one
#: becomes somebody else's vocabulary (§2).
ACTIONED: Final = "actioned"
ASSIGNED: Final = "assigned"
SNOOZED: Final = "snoozed"
DISMISSED: Final = "dismissed"


def discriminator(outcome: Outcome) -> str:
    """What this outcome is called, in one word.

    **Exhaustive by construction.** `Outcome` is a closed union, so `mypy`
    refuses this function if a fifth member is ever added without a branch —
    which is the point of the union being closed, and it now protects the
    published contract as well as the column.
    """
    match outcome:
        case Actioned():
            return ACTIONED
        case Assigned():
            return ASSIGNED
        case Snoozed():
            return SNOOZED
        case Dismissed():
            return DISMISSED


@dataclass(frozen=True, slots=True)
class Resolution:
    """One person's decision about one signal, and when they made it.

    **Immutable, like everything that records a fact** (§2). Changing your mind
    is a *new* resolution naming the one it supersedes — so the queue can show
    what is true now while the history of how it got there stays readable, and
    a dismissal somebody regretted cannot quietly cease to exist.
    """

    id: UUID
    workspace_id: UUID
    signal_id: UUID
    outcome: Outcome
    #: **Never optional and never the platform.** Every outcome here is a human
    #: judgement; a machine-authored one would be Signora marking its own work.
    actor_id: UUID
    recorded_at: datetime
    #: The earlier resolution this replaces. `None` on the first.
    supersedes: UUID | None = None
    payload_version: int = PAYLOAD_VERSION

    def __post_init__(self) -> None:
        # **No identifier in any of these messages.** They were written when
        # nothing mapped `ResolutionError` to a status code, and naming the
        # resolution was free; registering the mapping in `interface/errors.py`
        # is what turned them into customer copy, and the Security Invariant
        # caught it in the same run. A UUID on a seller's screen is noise they
        # cannot use — the id is already on the correlation id, the log line
        # and the row the reader is looking at (R4-03).
        if self.recorded_at.tzinfo is None:
            raise ResolutionError(
                "A decision must be timestamped with a timezone. A queue that returns "
                "snoozed work at a stated time cannot be built on a naive datetime."
            )
        if isinstance(self.outcome, Snoozed):
            if self.outcome.until.tzinfo is None:
                raise ResolutionError("A snooze must state when it ends, with a timezone.")
            if self.outcome.until <= self.recorded_at:
                raise ResolutionError(
                    f"A snooze until {self.outcome.until.isoformat()} has already elapsed, "
                    "so the signal would come straight back. Choose a time in the future."
                )

    @property
    def closes_the_signal(self) -> bool:
        """Whether the signal has left the queue.

        **Derived from the outcome rather than stored beside it** — a boolean
        column would be a second representation of a fact the outcome already
        carries, and the two would eventually disagree (§2).
        """
        return isinstance(self.outcome, CLOSING)

    def is_due(self, now: datetime) -> bool:
        """Whether a snoozed signal has come back.

        Answers `False` for every other outcome: nothing else is waiting, and a
        method that returned `True` for an `Actioned` signal would put finished
        work back in front of a person.
        """
        return isinstance(self.outcome, Snoozed) and self.outcome.until <= now


__all__ = [
    "ACTIONED",
    "ASSIGNED",
    "CLOSING",
    "DISMISSED",
    "MAX_REASON",
    "SNOOZED",
    "Actioned",
    "Assigned",
    "DismissalReason",
    "Dismissed",
    "Outcome",
    "Resolution",
    "ResolutionError",
    "Snoozed",
    "UnreadableOutcomeError",
    "discriminator",
]
