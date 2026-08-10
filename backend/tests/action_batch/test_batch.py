"""The Action Batch's lifecycle — proposal, approval, withdrawal, and the
window that actually refuses a late reversal.

**Slice 2 of six.** Slice 1 published a contract with no implementation; this
is the aggregate behind it.

**What these tests are mostly about is the refusals.** The golden path is four
lines. Every interesting property of this context is a transition it declines
to record — because a lifecycle that accepts anything is a lifecycle no audit
can cite, and because the reversal guard is the only thing that makes the
window more than a comment.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from modules.action_batch.domain.batch import (
    ActionBatch,
    ActionBatchError,
    ApplicationProgress,
    ApprovalState,
    Decision,
    Transition,
    has_settled,
)

PROPOSED_AT = datetime(2026, 8, 7, 9, 0, tzinfo=UTC)
WINDOW = timedelta(hours=24)


def _proposed(*, window: timedelta | None = WINDOW, items: int = 12) -> ActionBatch:
    return ActionBatch(
        id=uuid4(),
        workspace_id=uuid4(),
        name="Move 12 accounts to Engaged",
        item_count=items,
        proposed=Decision(actor_id=uuid4(), at=PROPOSED_AT),
        reversible_for=window,
    )


def _applied(*, window: timedelta | None = WINDOW) -> ActionBatch:
    batch = _proposed(window=window)
    return batch.approved_by(uuid4(), at=PROPOSED_AT + timedelta(minutes=5)).applied_on(
        PROPOSED_AT + timedelta(minutes=10)
    )


class TestTheNamedUnit:
    def test_a_batch_is_proposed_and_nothing_has_happened_yet(self) -> None:
        batch = _proposed()

        assert batch.state is ApprovalState.PROPOSED
        assert batch.decided is None
        assert not batch.is_applied

    def test_a_batch_with_no_name_cannot_be_shown_to_an_approver(self) -> None:
        with pytest.raises(ActionBatchError, match="cannot be shown"):
            ActionBatch(
                id=uuid4(),
                workspace_id=uuid4(),
                name="   ",
                item_count=1,
                proposed=Decision(actor_id=uuid4(), at=PROPOSED_AT),
            )

    def test_an_empty_batch_is_a_decision_that_changes_nothing(self) -> None:
        with pytest.raises(ActionBatchError, match="nothing to\napprove|nothing to approve"):
            _proposed(items=0)

    def test_a_zero_window_is_not_a_window_and_none_is_how_you_say_never(self) -> None:
        """The two are different answers a customer is told differently, so the
        type refuses the one that would blur them."""
        with pytest.raises(ActionBatchError, match="is not a window"):
            _proposed(window=timedelta(0))

        assert _proposed(window=None).reversible_for is None


class TestLeavingProposedHappensExactlyOnce:
    def test_approval_records_who_and_when(self) -> None:
        at = PROPOSED_AT + timedelta(minutes=5)
        actor = uuid4()

        batch = _proposed().approved_by(actor, at=at)

        assert batch.state is ApprovalState.APPROVED
        assert batch.decided == Decision(actor_id=actor, at=at)

    def test_approving_does_not_mutate_the_proposal_it_came_from(self) -> None:
        """Every transition is a new value — an approval that can be edited is
        an approval nobody can cite."""
        original = _proposed()

        original.approved_by(uuid4(), at=PROPOSED_AT + timedelta(minutes=5))

        assert original.state is ApprovalState.PROPOSED
        assert original.decided is None

    @pytest.mark.parametrize("verb", ["approved_by", "rejected_by", "withdrawn_by"])
    def test_a_decided_batch_cannot_be_decided_again(self, verb: str) -> None:
        decided = _proposed().approved_by(uuid4(), at=PROPOSED_AT + timedelta(minutes=1))

        with pytest.raises(ActionBatchError, match="already approved"):
            getattr(decided, verb)(uuid4(), at=PROPOSED_AT + timedelta(minutes=2))

    def test_rejection_and_withdrawal_are_different_outcomes(self) -> None:
        """One is a reviewer declining, the other is the proposer changing
        their mind, and a customer reading a history needs to tell them
        apart."""
        at = PROPOSED_AT + timedelta(minutes=5)

        assert _proposed().rejected_by(uuid4(), at=at).state is ApprovalState.REJECTED
        assert _proposed().withdrawn_by(uuid4(), at=at).state is ApprovalState.WITHDRAWN

    def test_a_decision_cannot_predate_the_proposal(self) -> None:
        with pytest.raises(ActionBatchError, match="before it was proposed"):
            _proposed().approved_by(uuid4(), at=PROPOSED_AT - timedelta(seconds=1))


class TestApplicationIsNotApproval:
    def test_approved_with_no_applied_at_is_a_real_state(self) -> None:
        """Approval and application are two moments, and the gap between them
        is what slice 5 makes visible."""
        batch = _proposed().approved_by(uuid4(), at=PROPOSED_AT + timedelta(minutes=5))

        assert batch.state is ApprovalState.APPROVED
        assert not batch.is_applied

    def test_only_an_approved_batch_can_take_effect(self) -> None:
        withdrawn = _proposed().withdrawn_by(uuid4(), at=PROPOSED_AT + timedelta(minutes=1))

        with pytest.raises(ActionBatchError, match="did not take effect"):
            withdrawn.applied_on(PROPOSED_AT + timedelta(minutes=2))

    def test_one_approval_cannot_be_applied_twice(self) -> None:
        """Two applications of one approval means the change was performed
        twice — a defect to surface, not a timestamp to overwrite."""
        applied = _applied()

        with pytest.raises(ActionBatchError, match="already took effect"):
            applied.applied_on(PROPOSED_AT + timedelta(minutes=20))

    def test_a_batch_cannot_take_effect_before_it_was_proposed(self) -> None:
        """Reachable despite the approval guard: approve at T+5, then apply at
        T−1. A clock skew that would otherwise write a history reading
        backwards."""
        approved = _proposed().approved_by(uuid4(), at=PROPOSED_AT + timedelta(minutes=5))

        with pytest.raises(ActionBatchError, match="before it was proposed"):
            approved.applied_on(PROPOSED_AT - timedelta(seconds=1))

    def test_application_attributes_no_actor(self) -> None:
        """The write is performed on the authority of the approval already
        recorded; a second actor here would attribute it to whoever flushed
        it."""
        applied = _applied()

        assert applied.decided is not None
        assert applied.reversal is None


class TestTheWindowRefusesALateReversal:
    """**This is the class that stops `has_settled` being decorative.**

    A predicate nothing enforces describes a window that does not exist, and
    the comment beside it would be a false claim (§2).
    """

    def test_a_reversal_inside_the_window_is_recorded(self) -> None:
        applied = _applied()
        actor = uuid4()
        at = PROPOSED_AT + timedelta(hours=1)

        reversed_batch = applied.reversed_by(actor, at=at)

        assert reversed_batch.state is ApprovalState.REVERSED
        assert reversed_batch.reversal == Decision(actor_id=actor, at=at)

    def test_a_reversal_after_the_window_is_refused(self) -> None:
        applied = _applied()
        assert applied.applied_at is not None
        too_late = applied.applied_at + WINDOW + timedelta(seconds=1)

        assert applied.is_settled(now=too_late)
        with pytest.raises(ActionBatchError, match="window closed"):
            applied.reversed_by(uuid4(), at=too_late)

    def test_the_boundary_instant_is_settled_and_therefore_refused(self) -> None:
        """`>=`, not `>`. The window is *for* 24 hours, not *through* the
        instant it ends."""
        applied = _applied()
        assert applied.applied_at is not None
        exactly = applied.applied_at + WINDOW

        assert applied.is_settled(now=exactly)
        with pytest.raises(ActionBatchError, match="window closed"):
            applied.reversed_by(uuid4(), at=exactly)

    def test_something_that_never_applied_cannot_be_reversed(self) -> None:
        approved = _proposed().approved_by(uuid4(), at=PROPOSED_AT + timedelta(minutes=5))

        with pytest.raises(ActionBatchError, match="never took effect"):
            approved.reversed_by(uuid4(), at=PROPOSED_AT + timedelta(minutes=6))

    def test_no_window_declared_is_refused_as_never_offered_not_as_expired(self) -> None:
        """The two produce the same `is_settled` answer and are not the same
        situation — so the refusal distinguishes them even though the
        predicate cannot."""
        applied = _applied(window=None)
        at = PROPOSED_AT + timedelta(minutes=20)

        assert not applied.is_settled(now=at)
        with pytest.raises(ActionBatchError, match="never offered"):
            applied.reversed_by(uuid4(), at=at)

    def test_a_batch_is_reversed_once(self) -> None:
        applied = _applied()
        once = applied.reversed_by(uuid4(), at=PROPOSED_AT + timedelta(hours=1))

        with pytest.raises(ActionBatchError, match="already been reversed"):
            once.reversed_by(uuid4(), at=PROPOSED_AT + timedelta(hours=2))


class TestTheWindowIsComputedInExactlyOnePlace:
    def test_the_aggregate_and_the_published_view_give_the_same_answer(self) -> None:
        """**The point of the shared function, asserted rather than trusted.**

        `ActionBatchView.is_settled` and `ActionBatch.is_settled` both call
        `has_settled`. If either ever restates the rule, this fails.
        """
        from modules.action_batch.public import ActionBatchView

        applied = _applied()
        assert applied.applied_at is not None
        view = ActionBatchView(
            id=applied.id,
            workspace_id=applied.workspace_id,
            name=applied.name,
            state=applied.state,
            item_count=applied.item_count,
            proposed_at=applied.proposed.at,
            proposed_by=applied.proposed.actor_id,
            applied_at=applied.applied_at,
            reversible_for=applied.reversible_for,
        )

        for offset in (timedelta(0), WINDOW - timedelta(seconds=1), WINDOW, WINDOW * 2):
            now = applied.applied_at + offset
            assert view.is_settled(now=now) == applied.is_settled(now=now)

    def test_never_applied_and_no_window_both_answer_false(self) -> None:
        now = datetime(2026, 12, 1, tzinfo=UTC)

        assert not has_settled(None, WINDOW, now=now)
        assert not has_settled(PROPOSED_AT, None, now=now)


_LATER = PROPOSED_AT + timedelta(minutes=10)


def _approved() -> ActionBatch:
    """⚡ **Approved and NOT applied** — the state this slice exists for.

    ⛔ **Deliberately not `_applied()`**, which this file already defines and
    which applies the batch: **the gap between the two moments is the whole
    subject here**, so a helper that closed it would make every assertion below
    vacuous.
    """
    return _proposed().approved_by(uuid4(), at=PROPOSED_AT + timedelta(minutes=5))


class TestApplicationProgress:
    """**The gap between approval and application, made visible** —
    [TASK-465](../../../docs/BACKLOG.md), slice 5.

    🔴 **The row's risk in one sentence**: *"a customer told **applied** before
    the work finishes."* ⛔ **And [P-A], which
    [455](../../../docs/architecture/455-context-definitions-r02-r03.md) applies
    to this slice by name**: *a batch that is still running and one that failed
    to start must never render alike.*
    """

    def test_an_approved_batch_has_not_started(self) -> None:
        batch = _approved()

        assert batch.progress is ApplicationProgress.NOT_STARTED

    def test_dispatch_is_accepted_and_is_not_applied(self) -> None:
        # 🔴 **The whole row.** §14: a handler answers once the request is
        # durably accepted — and *accepted* is not *done*.
        batch = _approved().dispatched_on(_LATER)

        assert batch.progress is ApplicationProgress.ACCEPTED
        assert batch.applied_at is None

    def test_a_batch_that_never_dispatched_cannot_fail_to_apply(self) -> None:
        # ⚡ **It has not started.** Collapsing the two would tell somebody the
        # work broke when nothing ever asked it to run.
        with pytest.raises(ActionBatchError, match="has not started"):
            _approved().failed_to_apply("the worker refused", at=_LATER)

    def test_a_failure_states_its_reason_or_is_refused(self) -> None:
        dispatched = _approved().dispatched_on(_LATER)

        with pytest.raises(ActionBatchError, match="stated reason"):
            dispatched.failed_to_apply("   ", at=_LATER)

    def test_failed_and_accepted_are_different_states(self) -> None:
        # 🔴 **P-A, executably.** The dispatched batch is still stamped
        # `dispatched_at`, so reporting progress off that alone would leave a
        # customer waiting for work that has stopped.
        dispatched = _approved().dispatched_on(_LATER)
        failed = dispatched.failed_to_apply("the provider refused the write", at=_LATER)

        assert dispatched.progress is ApplicationProgress.ACCEPTED
        assert failed.progress is ApplicationProgress.FAILED
        assert failed.dispatched_at is not None
        assert failed.failure == "the provider refused the write"

    def test_applying_after_dispatch_reports_applied(self) -> None:
        applied = _approved().dispatched_on(_LATER).applied_on(_LATER)

        assert applied.progress is ApplicationProgress.APPLIED

    def test_a_batch_is_dispatched_once(self) -> None:
        # ⛔ **Two dispatches of one approval is the change performed twice.**
        dispatched = _approved().dispatched_on(_LATER)

        with pytest.raises(ActionBatchError, match="already dispatched"):
            dispatched.dispatched_on(_LATER)

    def test_only_an_approved_batch_is_dispatched(self) -> None:
        with pytest.raises(ActionBatchError, match="cannot be dispatched"):
            _proposed().dispatched_on(_LATER)

    def test_a_completed_application_cannot_be_recorded_as_a_failure(self) -> None:
        # ⛔ **Denying a change that really happened** is worse than any state
        # this could otherwise be in.
        applied = _approved().dispatched_on(_LATER).applied_on(_LATER)

        with pytest.raises(ActionBatchError, match="took effect"):
            applied.failed_to_apply("too late", at=_LATER)

    def test_dispatch_and_failure_name_no_actor(self) -> None:
        """⚡ **A worker is not an actor.**

        ⛔ **Attributing a background failure to whoever approved the batch
        hours earlier would put a false name in a history somebody may have to
        defend** — the same reasoning `applied_on` already carries.
        """
        assert not Transition.DISPATCHED.is_attributed
        assert not Transition.APPLICATION_FAILED.is_attributed
        assert not Transition.APPLIED.is_attributed
        assert Transition.APPROVED.is_attributed
        assert Transition.REVERSED.is_attributed
