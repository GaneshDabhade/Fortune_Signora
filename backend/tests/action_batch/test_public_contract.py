"""The Action Batch contract, before anything implements it.

**Slice 1 of six.** Seven consumers are waiting, and publishing first is what
stops seven approval models being invented while this is built
([P-E](../../../docs/DOMAIN_DISCOVERY_REGISTER.md), [D-121](../../../docs/DECISION_REGISTER.md)).

**A contract with no implementation still has properties worth pinning**, and
the ones below are the ones a consumer would otherwise get wrong.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from modules.action_batch.public import ActionBatchReader, ActionBatchView, ApprovalState

APPLIED = datetime(2026, 8, 6, 12, 0, tzinfo=UTC)
WINDOW = timedelta(hours=1)


def _batch(
    *,
    state: ApprovalState = ApprovalState.APPROVED,
    applied: datetime | None = APPLIED,
    window: timedelta | None = WINDOW,
) -> ActionBatchView:
    return ActionBatchView(
        id=uuid4(),
        workspace_id=uuid4(),
        name="Move 12 accounts to Engaged",
        state=state,
        item_count=12,
        proposed_at=APPLIED - timedelta(minutes=5),
        proposed_by=uuid4(),
        applied_at=applied,
        reversible_for=window,
    )


class TestTheWindowIsAPredicateAndNeverAState:
    def test_it_is_not_settled_inside_the_window(self) -> None:
        assert not _batch().is_settled(now=APPLIED + timedelta(minutes=59))

    def test_it_is_settled_once_the_window_has_elapsed(self) -> None:
        assert _batch().is_settled(now=APPLIED + timedelta(hours=1))

    def test_now_is_a_parameter_so_two_readers_agree(self) -> None:
        """**A stored `is_settled` column would be two representations of one
        fact** (§2), and a scheduler to flip it is machinery P-B refuses. The
        precedent is `Snoozed.until` in `signal_engine`."""
        batch = _batch()

        assert not batch.is_settled(now=APPLIED)
        assert batch.is_settled(now=APPLIED + timedelta(days=1))

    def test_no_field_stores_whether_it_settled(self) -> None:
        assert "is_settled" not in ActionBatchView.__dataclass_fields__
        assert "settled_at" not in ActionBatchView.__dataclass_fields__

    def test_an_action_that_never_applied_is_not_settled(self) -> None:
        """**It has no window to have elapsed.** Reading it as settled would
        say a reversal is no longer possible for something that never
        happened."""
        assert not _batch(state=ApprovalState.PROPOSED, applied=None).is_settled(
            now=APPLIED + timedelta(days=365)
        )

    def test_no_window_declared_means_reversal_was_never_offered(self) -> None:
        """**Different from expired**, and a consumer must not render it as
        *"the window has passed"*."""
        assert not _batch(window=None).is_settled(now=APPLIED + timedelta(days=365))


class TestTheStatesAreDistinctThingsACustomerCanSee:
    def test_withdrawn_and_rejected_are_two_states_and_not_one(self) -> None:
        """One is the proposer changing their mind, the other is a reviewer
        declining. **A customer reading a history needs to tell them apart.**

        ⚠️ **Written first as `WITHDRAWN is not REJECTED` and `mypy --strict`
        refused it** — a non-overlapping identity check, which is a tautology
        the type system can see through. **The real assertion is that the enum
        carries both**, which is what a later collapse into one value would
        break.
        """
        assert len({ApprovalState.WITHDRAWN, ApprovalState.REJECTED}) == 2

    def test_approved_does_not_imply_applied(self) -> None:
        """⚠️ **`APPROVED` with no `applied_at` is a real state**, not an
        inconsistency: approval and application are two moments."""
        pending = _batch(state=ApprovalState.APPROVED, applied=None)

        assert pending.state is ApprovalState.APPROVED
        assert pending.applied_at is None

    def test_the_set_is_closed_at_five(self) -> None:
        assert {s.value for s in ApprovalState} == {
            "proposed",
            "approved",
            "withdrawn",
            "reversed",
            "rejected",
        }


class TestTheContractHoldsNoBusinessSemantics:
    def test_it_publishes_a_count_and_never_the_items(self) -> None:
        """⛔ **ADR-0405's boundary.** What each item *means* belongs to the
        domain that proposed it; publishing the items here would put business
        semantics in the context whose whole boundary is that it holds none."""
        assert "item_count" in ActionBatchView.__dataclass_fields__
        assert "items" not in ActionBatchView.__dataclass_fields__
        assert "payload" not in ActionBatchView.__dataclass_fields__

    def test_the_reader_offers_no_way_to_write(self) -> None:
        """Proposing, approving and reversing are slice 4. **A port that could
        write before the domain exists would let a consumer commit to a
        lifecycle nobody has built.**"""
        published = {name for name in dir(ActionBatchReader) if not name.startswith("_")}

        assert published == {"by_id", "proposed_by"}


class TestItIsAContractAndNotAnImplementation:
    def test_a_fake_satisfies_the_reader(self) -> None:
        """**`mypy --strict` accepting this is the assertion** — if a fake
        cannot stand in, the dependency was never really a boundary."""

        class Fake:
            async def by_id(
                self, workspace_id: UUID, batch_id: UUID
            ) -> ActionBatchView | None:
                return None

            async def proposed_by(
                self, workspace_id: UUID, actor_id: UUID
            ) -> tuple[ActionBatchView, ...]:
                return ()

        reader: ActionBatchReader = Fake()
        assert reader is not None

    def test_the_context_has_no_persistence_application_or_interface_yet(self) -> None:
        """**No table, no endpoint, no events** — P-C: an event exists when a
        consumer appears.

        ⚠️ **Re-aimed by slice 2, which is chartered to add `domain/`.** This
        read `== {"public"}` and pinned *"slice 1 is the contract and nothing
        else"*, which was exactly right for one slice and expires the moment
        the next one lands.

        ⛔ **Re-aimed rather than deleted, and it is strictly stronger here.**
        The property worth keeping was never *"only `public` exists"* — it was
        that **this context still persists nothing, exposes nothing and
        publishes no event**, which is what slices 3 and 4 exist to add and
        what a lane could otherwise smuggle in early. **Naming the three
        forbidden layers asserts that; counting to one only asserted it by
        accident.**
        """
        from pathlib import Path

        import modules.action_batch as context

        present = {p.name for p in Path(context.__file__).parent.iterdir() if p.is_dir()}

        assert present - {"__pycache__"} == {"public", "domain"}
        assert not present & {"infrastructure", "interface", "application"}
