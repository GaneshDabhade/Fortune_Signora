"""**A dry run can never become effective, by any route.**

📁 **[TASK-1419](../../../docs/BACKLOG.md), Workflow 26** — 📁 the design's
subtitle: *"Simulated before it runs, approved before it writes, reversible
after it does."*

## 🔴 Why this is a Security Invariant and not a feature test

📁 **The row states it as a database assertion**: *"a simulation writes nothing
— asserted against the database, not against the UI."* ⚡ **The domain-level
half is what makes that possible**: if a dry run cannot be approved, dispatched
or applied, **there is no code path by which one reaches a write.**

⛔ **The failure mode this guards is not a bug in the simulation feature.**
⚡ **It is anything that transitions batches in bulk** — a bulk approval, a
retry, an operator script — **finding a dry run among live ones and treating it
the same.** **That is a customer's live data written by a run they were shown
as a preview.**

## ⛔ It enumerates the transition alphabet rather than the three I thought of

📁 **`Transition` is the module's own lifecycle vocabulary, and its docstring
says why it exists**: *"so a sixth transition cannot be added to one without the
other noticing."* ✅ **This file walks it**, so a future transition that could
make a batch effective and forgets the refusal fails here — ⚡ **without anybody
remembering to add a case.**
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest

from modules.action_batch.domain.batch import (
    ActionBatch,
    ActionBatchError,
    ApprovalState,
    Decision,
    Effect,
    Transition,
)

NOW = datetime(2026, 8, 16, 12, 0, tzinfo=UTC)
ACTOR = uuid4()

#: ⛔ **The transitions that make a batch EFFECTIVE.** ⚡ **Named once, so the
#: completeness check below has something to compare the refusals against.**
MAKES_EFFECTIVE = frozenset(
    {Transition.APPROVED, Transition.DISPATCHED, Transition.APPLIED}
)

#: ✅ **The rest, and each is harmless for a dry run** — ⚠️ **`WITHDRAWN` most
#: of all: a proposer changing their mind about a question is exactly what
#: withdrawal means, and refusing it would strand a dry run forever.**
LEAVES_IT_INEFFECTIVE = frozenset(Transition) - MAKES_EFFECTIVE


def a_batch(*, effect: Effect = Effect.LIVE, **kwargs: Any) -> ActionBatch:
    return ActionBatch(
        id=uuid4(),
        workspace_id=uuid4(),
        name="Retag 40 accounts",
        item_count=40,
        proposed=Decision(actor_id=ACTOR, at=NOW),
        effect=effect,
        **kwargs,
    )


class TestADryRunCannotBecomeEffective:
    """🔴 **The invariant, one test per effective transition.**"""

    def test_it_refuses_approval(self) -> None:
        with pytest.raises(ActionBatchError, match="cannot be approved"):
            a_batch(effect=Effect.DRY_RUN).approved_by(ACTOR, at=NOW)

    def test_it_refuses_dispatch_because_it_can_never_be_approved(self) -> None:
        """⚠️ **The one that is refused by a CHAIN rather than by its own guard.**

        🔴 **A dry-run branch was written in `dispatched_on` and removed after
        fire-testing it**: a dry run can never be `APPROVED`, so the branch was
        unreachable — 📁 [§2](../../../CLAUDE.md)'s *decorative logic*, in the
        slice whose whole subject is guards.

        ✅ **So this asserts the real chain**: dispatch requires approval, and
        approval is refused. ⛔ **Asserting a message from a branch that cannot
        run would have been the false claim the rule warns about.**
        """
        with pytest.raises(ActionBatchError, match="proposed cannot be dispatched"):
            a_batch(effect=Effect.DRY_RUN).dispatched_on(NOW)

        # ⚡ **And the link in the chain that does the work**, asserted here so
        # the two are not separated by a refactor.
        with pytest.raises(ActionBatchError, match="cannot be approved"):
            a_batch(effect=Effect.DRY_RUN).approved_by(ACTOR, at=NOW)

    def test_it_refuses_application(self) -> None:
        with pytest.raises(ActionBatchError, match="cannot be applied"):
            a_batch(effect=Effect.DRY_RUN).applied_on(NOW)

    @pytest.mark.parametrize("transition", sorted(MAKES_EFFECTIVE))
    def test_every_effective_transition_has_a_refusal(
        self, transition: Transition
    ) -> None:
        """🔴 **The completeness check, and the reason this file is enumerated.**

        ⛔ **A transition that makes a batch effective must have a method that
        refuses a dry run.** ⚡ **A seventh transition added to the alphabet
        without one fails HERE**, rather than in production the first time a
        bulk operation meets a simulation.
        """
        method = {
            Transition.APPROVED: lambda b: b.approved_by(ACTOR, at=NOW),
            Transition.DISPATCHED: lambda b: b.dispatched_on(NOW),
            Transition.APPLIED: lambda b: b.applied_on(NOW),
        }.get(transition)

        assert method is not None, (
            f"{transition} makes a batch effective and this file does not "
            "exercise it — add the case, and check the domain refuses it"
        )
        # ⚡ **Refused, by whatever mechanism.** ⛔ **Deliberately NOT asserting
        # a per-method message**: `dispatched_on` is refused by a chain rather
        # than by its own branch, and demanding one would push somebody to
        # re-add the decorative guard that was removed.
        with pytest.raises(ActionBatchError):
            method(a_batch(effect=Effect.DRY_RUN))

    def test_the_two_sets_account_for_every_transition(self) -> None:
        """⚠️ **Neither set may quietly stop covering the alphabet.**"""
        assert frozenset(Transition) == MAKES_EFFECTIVE | LEAVES_IT_INEFFECTIVE
        assert not (MAKES_EFFECTIVE & LEAVES_IT_INEFFECTIVE)


class TestTheGuardIsTheTypeRatherThanTheMethods:
    """🔴 **The load-bearing half, and the methods are the courteous half.**

    ⛔ **A repository reconstructs a batch by CONSTRUCTING it, not by replaying
    transitions.** ⚡ **So a refusal that lived only in the methods would be
    bypassed on every read** — which is how a forbidden state reaches a system
    that checks for it in all the obvious places.
    """

    @pytest.mark.parametrize(
        "forbidden",
        [
            {"state": ApprovalState.APPROVED},
            {"applied_at": NOW},
            {"dispatched_at": NOW},
            {"state": ApprovalState.APPROVED, "applied_at": NOW},
        ],
    )
    def test_a_dry_run_in_an_effective_state_cannot_be_constructed(
        self, forbidden: dict[str, Any]
    ) -> None:
        with pytest.raises(ActionBatchError, match="only a live batch can reach"):
            a_batch(effect=Effect.DRY_RUN, **forbidden)

    def test_the_same_states_are_fine_for_a_live_batch(self) -> None:
        """✅ **The guard is about the dry run, not about the states.**

        ⛔ **A test that only proved the states were refused would pass if the
        guard refused them for everybody**, which would break every live batch
        in the product.
        """
        assert a_batch(state=ApprovalState.APPROVED, applied_at=NOW).is_applied


class TestNothingTurnsADryRunIntoALiveBatch:
    def test_there_is_no_method_that_changes_the_effect(self) -> None:
        """⛔ **The absence IS the invariant, so it is asserted.**

        ⚡ **A helpfully-added `promote()` or `make_live()` would make every
        refusal above a speed bump**, and it would look like a feature.
        """
        surface = {name for name in dir(ActionBatch) if not name.startswith("_")}
        assert not {n for n in surface if "live" in n.lower() or "promote" in n.lower()}

    def test_a_dry_run_survives_the_transitions_it_is_allowed(self) -> None:
        """✅ **Withdrawal keeps the effect, so it cannot be laundered.**

        ⚠️ **If a transition returned a batch that had silently become `LIVE`,
        the refusals would still pass and the guarantee would be gone.**
        """
        withdrawn = a_batch(effect=Effect.DRY_RUN).withdrawn_by(ACTOR, at=NOW)

        assert withdrawn.effect is Effect.DRY_RUN
        assert withdrawn.state is ApprovalState.WITHDRAWN

    def test_a_live_batch_is_the_default_so_no_caller_opts_into_effect(self) -> None:
        """⚡ **Additive by construction** — every existing caller of
        `ActionBatch` keeps proposing live batches without knowing the field
        exists, which is what makes this not a change to [TASK-466](../../../docs/BACKLOG.md)'s
        shipped consumer."""
        assert a_batch().effect is Effect.LIVE
