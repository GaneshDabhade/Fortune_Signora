"""The queue, read by state.

The approved Signal Center is *"a triage queue, not a notification list"*, and
the difference is entirely this read: a notification list shows everything that
happened, a queue shows what is still yours to deal with.

## Why state is derived and never stored

A signal's queue state is a function of two things that already exist — the
outcome in force, and what time it is now. Storing it would be a second
representation of a fact the resolution already carries (`CLAUDE.md` §2), and
the two would disagree the first time a snooze elapsed with nobody writing to
the table. **A snoozed signal comes back because the clock moved, not because
something ran.**

That is also what keeps the acceptance criterion honest: *"a snoozed signal
returns at the stated time with its original evidence intact."* The evidence is
intact because returning is a read that stops filtering the signal out —
nothing is regenerated, and the account a seller sees in a fortnight is the one
they postponed rather than a fresh reading that resembles it.

## Deliberately not exported through `public/`

**No other module may read who dismissed what.** The Buying Score Engine is
forbidden from reaching this module's hypotheses at all — *it decides what to
track and never forms hypotheses or weighs them* — and a surface that let any
consumer see a dismissal would be a surface that let one branch on it. Triage
feedback is a customer's account of Signora's judgement; a score that quietly
consumed it would be marking its own work.

This module's `interface/` serves it directly, which is what an interface layer
is for.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from modules.signal_engine.application.ports import ResolutionRepository
from modules.signal_engine.application.queries import SignalQueries
from modules.signal_engine.domain.precision import RulePrecision
from modules.signal_engine.domain.resolution import Resolution, Snoozed
from modules.signal_engine.domain.signal import Signal
from signora_platform.pagination import (
    DEFAULT_PAGE_LIMIT,
    CursorPosition,
    split_overfetched,
)


class QueueState(StrEnum):
    """Where a signal stands in the queue. **Three states, and none stored.**

    **Not a fourth name for `Relevance`.** That says how much a *type* of
    hypothesis matters to a workspace; this says whether *this one* still needs
    somebody. A `primary` signal can be closed and a `contextual` one open.
    """

    #: Nobody has finished with it. Covers *no decision yet*, an assignment
    #: (**routing is not resolving**), and a snooze whose time has come.
    OPEN = "open"
    #: Deliberately set aside, and not yet due. The one state that changes on
    #: its own, because the clock moves.
    SNOOZED = "snoozed"
    #: Actioned or dismissed. **Still readable** — nothing is deleted — but no
    #: longer anybody's to deal with.
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class TriagedSignal:
    """One hypothesis and what has been decided about it.

    **The resolution travels with the signal rather than being looked up
    beside it.** A screen that had to ask a second question to know whether a
    row was open would eventually render one it had not asked about.
    """

    signal: Signal
    state: QueueState
    #: The decision in force, or `None` when nobody has made one.
    #: **`None` means still open and is not the same as a decision to do
    #: nothing** — which is why `Actioned` exists as a distinct outcome.
    resolution: Resolution | None


def state_of(resolution: Resolution | None, now: datetime) -> QueueState:
    """Derive the state. **The only place the rule lives.**

    Reading it from the outcome each time is what makes an elapsed snooze
    return without anything having run.
    """
    if resolution is None:
        return QueueState.OPEN
    if resolution.closes_the_signal:
        return QueueState.CLOSED
    if isinstance(resolution.outcome, Snoozed):
        return QueueState.OPEN if resolution.is_due(now) else QueueState.SNOOZED
    # An assignment. Somebody else owns the decision; nobody has made it.
    return QueueState.OPEN


@dataclass(frozen=True, slots=True)
class TriagePage:
    """One page of the workspace triage queue.

    `has_more` rather than a total, on `AttentionPage`'s precedent and for its
    reason: counting every live signal on every request costs a scan to answer
    a question the caller asks only to decide whether to draw one more button.
    """

    items: tuple[TriagedSignal, ...]
    has_more: bool
    #: The last signal on the raw page, whose keyset the next request resumes
    #: from. `None` only when the page is empty.
    last_signal: Signal | None

    @property
    def next_position(self) -> CursorPosition | None:
        if not self.has_more or self.last_signal is None:
            return None
        return CursorPosition(created_at=self.last_signal.occurred_at, id=self.last_signal.id)


class TriageQueries:
    """Read-only, and scoped to one workspace on every call."""

    def __init__(self, *, signals: SignalQueries, resolutions: ResolutionRepository) -> None:
        self._signals = signals
        self._resolutions = resolutions

    async def queue(
        self,
        workspace_id: UUID,
        entity_id: UUID,
        *,
        state: QueueState | None = None,
        now: datetime | None = None,
    ) -> tuple[TriagedSignal, ...]:
        """Live hypotheses about this account, each with its decision.

        **Live only**, on the terms this module already uses: superseded,
        expired and profile-deactivated hypotheses are excluded before triage
        is considered at all. A hypothesis nobody believes any more is not
        queue work, and resolving it would be asking somebody to decide about
        something Signora has stopped saying.

        **Two reads, not one per signal** — the same shape as
        `live_with_evidence`, and for the same reason: a page of four
        hypotheses must not cost five queries to answer one question.

        `state` filters; **omitting it returns everything, including closed
        rows**, because *"nothing is deleted: every resolution is auditable"*
        and a caller auditing the queue needs to see what left it.
        """
        moment = now or datetime.now(UTC)
        live = await self._signals.signals(workspace_id, entity_id, live_only=True, now=moment)
        if not live:
            return ()

        decisions = await self._resolutions.current_for_signals(
            workspace_id, [signal.id for signal in live]
        )
        triaged = tuple(
            TriagedSignal(
                signal=signal,
                state=state_of(decisions.get(signal.id), moment),
                resolution=decisions.get(signal.id),
            )
            for signal in live
        )
        if state is None:
            return triaged
        return tuple(entry for entry in triaged if entry.state is state)

    async def workspace_queue(
        self,
        workspace_id: UUID,
        *,
        state: QueueState | None = None,
        after: CursorPosition | None = None,
        limit: int = DEFAULT_PAGE_LIMIT,
        now: datetime | None = None,
    ) -> TriagePage:
        """The Signal Center's queue: every live hypothesis in the workspace.

        **The read [C-228](../../../../docs/LANE_COORDINATION.md) found
        missing.** `queue` above answers *"what is outstanding on this
        account"*; the approved screen is *"a triage queue, not a notification
        list"* and asks *"what is outstanding"*. **Same liveness, same
        pairing, same `state_of` — no entity.**

        **Paged, because a queue is unbounded by nature.** An account has four
        hypotheses; a workspace has as many as the pipeline produced, and a
        read that fetched them all would be the unbounded fetch §14 forbids.

        ⚠️ **`state` filters the page, not the query**, and that is a real
        limitation rather than an oversight: queue state is derived from a
        resolution and the clock, so it cannot be a `WHERE` clause without
        storing it — which §2 forbids, and which `queue` already refuses for
        the same reason. **A filtered page can therefore be short.** The
        caller pages on, and `has_more` says whether that is worth doing.
        """
        moment = now or datetime.now(UTC)
        # **Overfetch by one to learn whether another page exists**, rather
        # than counting — a count is a full scan to answer a question asked
        # only to decide whether to draw one more control.
        found = await self._signals.live_page(
            workspace_id, after=after, limit=limit + 1, now=moment
        )
        page, has_more = split_overfetched(list(found), limit=limit)
        if not page:
            return TriagePage(items=(), has_more=has_more, last_signal=None)

        decisions = await self._resolutions.current_for_signals(
            workspace_id, [signal.id for signal in page]
        )
        triaged = tuple(
            TriagedSignal(
                signal=signal,
                state=state_of(decisions.get(signal.id), moment),
                resolution=decisions.get(signal.id),
            )
            for signal in page
        )
        return TriagePage(
            items=triaged if state is None else tuple(e for e in triaged if e.state is state),
            has_more=has_more,
            # **From the last row of the *page*, never of the filtered items.**
            # Resuming from a filtered row would skip every signal the filter
            # removed — the same trap `AttentionPage` documents about ranking.
            last_signal=page[-1],
        )

    async def history(self, workspace_id: UUID, signal_id: UUID) -> tuple[Resolution, ...]:
        """Every decision ever recorded about this signal, oldest first.

        **The audit trail the product promises.** A dismissal somebody
        regretted is still here, which is the whole reason a correction is a
        new record rather than an edit.
        """
        return await self._resolutions.history_for_signal(workspace_id, signal_id)

    async def precision(self, workspace_id: UUID) -> tuple[RulePrecision, ...]:
        """How often each rule was right, for every type anybody has judged.

        **The catalog learning which rules misfire** —
        [447](../../../../docs/architecture/447-signal-center-traceability-audit.md).

        ⛔ **A type nobody has judged is not in the result**, and this method
        does not helpfully add it with zeroes. A rule with no judgements and a
        rule that is always wrong are opposite facts; `0.0` renders them the
        same way and a reader takes the second meaning. **The caller decides
        what *not judged yet* looks like**, which is the only place that
        decision can honestly be made.

        ⚡ **Computed, never stored** — no table, and `Snoozed.until` is this
        module's precedent. A stored figure is stale from the first resolution
        written after it.
        """
        return await self._resolutions.judgements_by_type(workspace_id)


__all__ = ["QueueState", "TriageQueries", "TriagedSignal", "state_of"]
