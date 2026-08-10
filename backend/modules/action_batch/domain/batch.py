"""One named unit of work, from proposal to reversal — and the window as a
predicate rather than a state.

**Slice 2 of six** ([455 §5](../../../../docs/architecture/455-context-definitions-r02-r03.md)),
ratified by
[ADR-0405](../../../../docs/architecture/adr/0405-an-action-is-approved-before-it-is-effective.md).

> ## **This context coordinates lifecycle. Business domains own business behaviour.**

**Nothing here knows what an action *means*.** There is no payload, no
operation, no inverse and no validation of the change itself — only who
proposed it, who decided, when it took effect, and whether it can still be
taken back. ⛔ **The moment this module needs to know what an item *is* in
order to answer a question, the boundary has been crossed**
([D-126](../../../../docs/DECISION_REGISTER.md)).

### Every transition is a new value, and every one is attributed

**An approval that can be edited is an approval nobody can cite** — §2,
*immutability is the default for anything that records a fact*. So no method
mutates: each returns a new `ActionBatch`, and **each demands an `actor_id`
with no default**, which is the shape §2 already names as making the
requirement a property of the type rather than a rule somebody remembers.

### Time is an argument, never a reading

**No method calls `datetime.now()`.** A clock read inside a domain method is
a hidden input (§2) — the same declared inputs would produce different
results, which defeats replay and every regression test that depends on one.
`now` is passed in, always.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Final
from uuid import UUID


class ActionBatchError(ValueError):
    """A lifecycle transition was asked for that this context cannot record."""


class ApprovalState(StrEnum):
    """Where an action stands in its lifecycle.

    **Five states, and every one is a different thing a customer can see.**
    Whether the reversible window has elapsed is **not** among them — see
    `has_settled`, which computes it.
    """

    PROPOSED = "proposed"
    """Assembled and waiting for a decision. **Nothing has happened yet**, and
    a consumer must not describe it as pending *execution*."""

    APPROVED = "approved"
    """Somebody decided it should happen. ⚠️ **Not the same as done** — the
    action is effective from here, and `applied_at` is what says it ran."""

    WITHDRAWN = "withdrawn"
    """Taken back **before** approval, by whoever proposed it. A decision that
    was never made, rather than one that was reversed."""

    REVERSED = "reversed"
    """Undone **after** it took effect, inside the reversible window.
    ⛔ **The inverse is performed by the consuming domain**, never here — this
    context records that a reversal happened."""

    REJECTED = "rejected"
    """Somebody decided it should not happen. **Distinct from `WITHDRAWN`**:
    one is the proposer changing their mind, the other is a reviewer
    declining, and a customer reading a history needs to tell them apart."""


class Transition(StrEnum):
    """What happened to a batch — the lifecycle alphabet, named once.

    **Added by slice 3, because persistence had to name these and infrastructure
    may not invent domain vocabulary** (§4). Every member is a verb
    `ActionBatch` already has a method for, and `test_batch.py` asserts that
    correspondence executably rather than trusting it — so a sixth transition
    cannot be added to one without the other noticing.

    ⚠️ **Not the same set as `ApprovalState`, and the difference is the point.**
    `APPLIED` is not a state: an applied batch is still `APPROVED`, and
    `applied_at` is what says it ran. `PROPOSED` is not a transition: it is how
    a batch begins, so it is recorded on the batch itself rather than in its
    log.
    """

    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    DISPATCHED = "dispatched"
    APPLIED = "applied"
    APPLICATION_FAILED = "application_failed"
    REVERSED = "reversed"

    @property
    def is_attributed(self) -> bool:
        """Whether this transition names an actor.

        **Application is the only one that does not**, on the authority of the
        approval already recorded — which is why `applied_on` takes no
        `actor_id`. Stated here so the database constraint and the repository
        derive from one rule rather than restating it twice (§2).
        """
        return self not in _UNATTRIBUTED_TRANSITIONS


#: ⛔ **The transitions performed on the authority of an approval already
#: recorded**, rather than by a person deciding again. **Application is the
#: original one**; ⚡ **dispatch and failure joined it in slice 5 for the same
#: reason** — *a worker is not an actor*, and attributing a background failure
#: to whoever approved the batch hours earlier would put a false name in a
#: history somebody may have to defend.
_UNATTRIBUTED_TRANSITIONS: Final = frozenset(
    {Transition.DISPATCHED, Transition.APPLIED, Transition.APPLICATION_FAILED}
)


class ApplicationProgress(StrEnum):
    """How far the *work* has got, which is a different question from approval.

    🔴 **Derived, never stored** — the same rule this module already applies to
    `state` itself, which is *"derived by replaying the log"* rather than kept
    in a column that a reversal once overwrote.

    📁 **The gap this makes visible was named here before slice 5 existed**:
    *"`APPROVED` with no `applied_at` is a real state, not an inconsistency:
    approval and application are two moments, and the gap between them is what
    slice 5 makes visible."*
    """

    NOT_STARTED = "not_started"
    """Approved, and nothing has been asked to run yet."""

    ACCEPTED = "accepted"
    """⚡ **Durably accepted and not yet done.** 📁 The row's risk in one word:
    *"a customer told **applied** before the work finishes"* — **the response to
    an apply request means THIS**, and a screen that says *applied* here is the
    defect the row names."""

    APPLIED = "applied"
    """The work finished."""

    FAILED = "failed"
    """⛔ **It did not run, and somebody must be told why.**
    📁 [P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md), which
    [455](../../../../docs/architecture/455-context-definitions-r02-r03.md)
    applies to this slice by name: **a batch that is *still running* and one
    that *failed to start* must never render alike.** ⚠️ **Collapsing this into
    `ACCEPTED` is exactly that failure** — a customer would wait for something
    that is never coming."""


def has_settled(
    applied_at: datetime | None,
    reversible_for: timedelta | None,
    *,
    now: datetime,
) -> bool:
    """Whether the reversible window has elapsed.

    > **A predicate, never a stored state** — ADR-0405 §2.

    **The one executable statement of the rule.** `ActionBatch.is_settled` and
    the published `ActionBatchView.is_settled` both call this rather than
    restating it — §2, *behaviour exists exactly once*, and a window computed
    in two places is a window that will eventually disagree with itself about
    whether a customer may still undo something.

    **A stored `is_settled` column would be two representations of one fact**
    and a scheduler to flip it is machinery
    [P-B](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md) exists to refuse. The
    precedent is `Snoozed.until` in `signal_engine`, which
    [447](../../../../docs/architecture/447-signal-center-traceability-audit.md)
    named *"the pattern R-03 should copy."*

    **Two different things both answer `False`**, and they are not the same
    situation:

    | | |
    |---|---|
    | **Never applied** | There is no window to have elapsed |
    | **No window declared** | Reversal was never offered, rather than expired |

    Neither is *"still reversible"* on its own — `ActionBatch.reversed_by`
    is what distinguishes them, and it refuses each with its own reason.
    """
    if applied_at is None or reversible_for is None:
        return False
    return now >= applied_at + reversible_for


@dataclass(frozen=True, slots=True)
class Decision:
    """Who decided something, and when. **Both required.**

    ⚠️ **`actor_id` has no default and never will.** *"Intelligence suggests;
    humans commit"* is the discipline `MACHINE_AUTHORED` already makes
    structural one module over, and an approval whose actor is optional is an
    approval that can be recorded with nobody attached to it.
    """

    actor_id: UUID
    at: datetime


@dataclass(frozen=True, slots=True)
class ActionBatch:
    """A named unit of work, its approval, and its reversal window.

    **The aggregate is richer than the published `ActionBatchView`, and
    deliberately.** The view carries what a consumer renders; this carries the
    decision record — who approved, who withdrew, who reversed and when. The
    view derives from this, never the other way round (§2, *truth has exactly
    one authoritative representation*).
    """

    id: UUID
    workspace_id: UUID
    #: What the customer called it. **Their words** — a history reads as a
    #: record of decisions rather than a list of identifiers.
    name: str
    #: How many things it covers. **A count, never the payload**: what each
    #: item *means* belongs to the domain that proposed it.
    item_count: int
    #: Who proposed it, and when. **The one decision every batch has.**
    proposed: Decision
    state: ApprovalState = ApprovalState.PROPOSED
    #: The decision that left `PROPOSED` — an approval, a rejection or a
    #: withdrawal. `None` while none has been taken.
    decided: Decision | None = None
    #: ⚡ **When the application was durably ACCEPTED** — the moment a handler
    #: may answer, and 📁 slice 5's whole subject: *"a handler responds once the
    #: request is durably accepted, never after the work."*
    dispatched_at: datetime | None = None
    #: When it became effective. **`APPROVED` with no `applied_at` is a real
    #: state**, not an inconsistency: approval and application are two
    #: moments, and the gap between them is what slice 5 makes visible.
    applied_at: datetime | None = None
    #: ⛔ **Why the work did not run, verbatim.** **Set exactly when the
    #: progress is `FAILED` and never otherwise** — a failure with no reason is
    #: a state a customer can see and nobody can act on.
    failure: str | None = None
    #: How long a reversal remains possible after it applied. `None` means
    #: **reversal was never offered**, which is not the same as expired.
    reversible_for: timedelta | None = None
    #: Who reversed it, and when.
    reversal: Decision | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ActionBatchError(
                "an action batch with no name cannot be shown to the person asked to "
                "approve it. A unit of work nobody can identify is not a unit of work."
            )
        if self.item_count < 1:
            raise ActionBatchError(
                f"an action batch covering {self.item_count} items has nothing to "
                "approve. An empty batch is a proposal that was never assembled, and "
                "recording one would put a decision in the history that changed nothing."
            )
        if self.reversible_for is not None and self.reversible_for <= timedelta(0):
            raise ActionBatchError(
                f"a reversible window of {self.reversible_for} is not a window. Use "
                "`None` to say reversal was never offered — the two are different "
                "answers and a customer is told them differently."
            )

    @property
    def is_applied(self) -> bool:
        """Whether it actually took effect. **Not the same as `APPROVED`.**"""
        return self.applied_at is not None

    def is_settled(self, *, now: datetime) -> bool:
        """Whether the reversible window has elapsed. See `has_settled`."""
        return has_settled(self.applied_at, self.reversible_for, now=now)

    def approved_by(self, actor_id: UUID, *, at: datetime) -> ActionBatch:
        """Somebody decided it should happen.

        **Only from `PROPOSED`.** Approving an approved batch is a duplicate
        submission rather than a second approval, and recording it would put
        two approvals in a history that must be citable.
        """
        return self._decide(ApprovalState.APPROVED, actor_id, at, verb="approved")

    def rejected_by(self, actor_id: UUID, *, at: datetime) -> ActionBatch:
        """A reviewer decided it should not happen."""
        return self._decide(ApprovalState.REJECTED, actor_id, at, verb="rejected")

    def withdrawn_by(self, actor_id: UUID, *, at: datetime) -> ActionBatch:
        """The proposer took it back, **before** anybody decided.

        ⚠️ **Withdrawal after approval is not this** — that is a reversal, and
        it has a window. The distinction is the customer-visible one between
        *"I changed my mind"* and *"undo what already happened"*.
        """
        return self._decide(ApprovalState.WITHDRAWN, actor_id, at, verb="withdrawn")

    def applied_on(self, moment: datetime) -> ActionBatch:
        """It took effect. **Records that it ran; it does not run anything.**

        ⛔ **No `actor_id`.** Application is performed by the consuming domain
        on the authority of the approval already recorded — inventing a second
        actor here would attribute the write to whoever happened to flush it.
        """
        if self.state is not ApprovalState.APPROVED:
            raise ActionBatchError(
                f"an action batch that is {self.state.value} did not take effect. Only "
                "an approved batch can be applied, because approval is the authority "
                "the write is performed on."
            )
        if self.applied_at is not None:
            raise ActionBatchError(
                f"this batch already took effect at {self.applied_at} and cannot take "
                f"effect again at {moment}. Two applications of one approval means the "
                "change was performed twice, which is a defect to surface rather than "
                "a timestamp to overwrite."
            )
        if moment < self.proposed.at:
            raise ActionBatchError(
                f"a batch cannot take effect at {moment}, before it was proposed at "
                f"{self.proposed.at}."
            )
        return replace(self, applied_at=moment)

    def dispatched_on(self, moment: datetime) -> ActionBatch:
        """The application was **durably accepted**. ⛔ **Nothing has run yet.**

        🔴 **This is what an apply request records before it answers**, and the
        reason the answer is honest: 📁 §14 — *"a handler responds once the
        request has been durably accepted"* — and the row's own risk, *"a
        customer told applied before the work finishes."*

        ⛔ **No `actor_id`**, for the same reason `applied_on` takes none: the
        authority is the approval already recorded.
        """
        if self.state is not ApprovalState.APPROVED:
            raise ActionBatchError(
                f"an action batch that is {self.state.value} cannot be dispatched for "
                "application. Approval is the authority the work is performed on, and "
                "dispatching without it would queue work nobody agreed to."
            )
        if self.dispatched_at is not None:
            raise ActionBatchError(
                f"this batch was already dispatched at {self.dispatched_at}. Dispatching "
                "it again would run the same approved change twice, which is a defect "
                "to surface rather than a job to enqueue."
            )
        if self.applied_at is not None:  # pragma: no cover — unreachable via applied_on
            raise ActionBatchError("a batch that already took effect cannot be dispatched")
        return replace(self, dispatched_at=moment)

    def failed_to_apply(self, reason: str, *, at: datetime) -> ActionBatch:
        """The work did not run, and the customer is told why.

        ⛔ **Only after a dispatch.** ⚡ **A batch that was never dispatched has
        not failed — it has not started**, and 📁 [P-A] is precisely that the
        two must not render alike.

        ⚠️ **`reason` is required and non-empty.** **A failure nobody can act on
        is worse than a spinner**, because it ends the wait without ending the
        question.
        """
        if not reason.strip():
            raise ActionBatchError(
                "a failed application with no stated reason tells a customer only that "
                "waiting is pointless. The reason is the whole of what this state is for."
            )
        if self.dispatched_at is None:
            raise ActionBatchError(
                "a batch that was never dispatched has not failed to apply — it has not "
                "started. P-A: still running and failed to start must never render alike, "
                "and neither must not-started and failed."
            )
        if self.applied_at is not None:
            raise ActionBatchError(
                f"this batch took effect at {self.applied_at}. Recording a failure over a "
                "completed application would deny a change that really happened."
            )
        if at < self.dispatched_at:
            raise ActionBatchError(
                f"a batch cannot fail at {at}, before it was dispatched at "
                f"{self.dispatched_at}."
            )
        return replace(self, failure=reason.strip())

    @property
    def progress(self) -> ApplicationProgress:
        """How far the WORK has got. ⛔ **Derived, never stored** (§2).

        ⚡ **Order matters and it is the P-A rule in code**: a failure is
        reported ahead of acceptance, because a batch that was dispatched and
        then failed is still `dispatched_at`-stamped — **and reporting it as
        *accepted* would leave somebody waiting for work that has stopped.**
        """
        if self.applied_at is not None:
            return ApplicationProgress.APPLIED
        if self.failure is not None:
            return ApplicationProgress.FAILED
        if self.dispatched_at is not None:
            return ApplicationProgress.ACCEPTED
        return ApplicationProgress.NOT_STARTED

    def reversed_by(self, actor_id: UUID, *, at: datetime) -> ActionBatch:
        """Undone after it took effect, **inside the window**.

        **This is the guard that makes `has_settled` load-bearing.** Without
        it the predicate would describe a window nothing enforced — which is
        the Decorative Logic §2 names, and the comment beside it would be a
        false claim.
        """
        if not self.is_applied:
            raise ActionBatchError(
                f"an action batch that is {self.state.value} and never took effect "
                "cannot be reversed. Taking back something that has not happened is a "
                "withdrawal, and it is a different thing a customer is told differently."
            )
        if self.state is ApprovalState.REVERSED:
            raise ActionBatchError(
                "this batch has already been reversed. The consuming domain performs "
                "the inverse once; recording a second reversal would claim it ran twice."
            )
        if self.reversible_for is None:
            raise ActionBatchError(
                "reversal was never offered for this batch, so there is nothing to "
                "reverse it within. A batch with no window is not an expired one."
            )
        if self.is_settled(now=at):
            raise ActionBatchError(
                f"the reversible window closed at "
                f"{self.applied_at + self.reversible_for if self.applied_at else None} "
                f"and it is {at}. The window is the promise the customer was shown, and "
                "honouring it after it lapses would make it meaningless."
            )
        return replace(self, state=ApprovalState.REVERSED, reversal=Decision(actor_id, at))

    def _decide(
        self, outcome: ApprovalState, actor_id: UUID, at: datetime, *, verb: str
    ) -> ActionBatch:
        """The one place a batch leaves `PROPOSED`.

        **Three verbs, one transition rule** — they differ in what they record
        and in nothing else, so the guard exists once rather than three times.
        """
        if self.state is not ApprovalState.PROPOSED:
            raise ActionBatchError(
                f"an action batch that is already {self.state.value} cannot be {verb}. "
                "A batch leaves the proposed state exactly once, and the record of how "
                "it left is the thing an audit cites."
            )
        if at < self.proposed.at:
            raise ActionBatchError(
                f"a batch cannot be {verb} at {at}, before it was proposed at "
                f"{self.proposed.at}."
            )
        return replace(self, state=outcome, decided=Decision(actor_id, at))


__all__ = [
    "ActionBatch",
    "ActionBatchError",
    "ApprovalState",
    "Decision",
    "Transition",
    "has_settled",
]
