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

from modules.action_batch.public import (
    ActionBatchProposer,
    ActionBatchReader,
    ActionBatchView,
    ApprovalState,
)

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
        """Proposing, approving and reversing were slice 4. **A port that could
        write before the domain exists would let a consumer commit to a
        lifecycle nobody has built.**

        ⚠️ **Still true of the READER after
        [D-235](../../../docs/DECISION_REGISTER.md) ①**: *"what did I propose"*
        and *"propose one"* are different questions, and a consumer needing
        only the first is not handed the second.
        """
        published = {name for name in dir(ActionBatchReader) if not name.startswith("_")}

        assert published == {"by_id", "proposed_by"}

    def test_the_proposer_offers_propose_and_nothing_else(self) -> None:
        """🔴 **The ruling made executable** —
        [D-235](../../../docs/DECISION_REGISTER.md) ①, via
        [C-1504](../../../docs/LANE_COORDINATION.md).

        > ✅ ***"`action_batch/public/` may expose `propose` and nothing else…
        > ⛔ does NOT approve · ⛔ does NOT apply · human approval stays a
        > separate product boundary."***

        ⛔ **This assertion is what stops `approve` arriving later because it
        would be convenient.** ⚡ **Approval is a human decision on a screen,
        not a call in a stack** — and a port that could approve would let a
        domain commit on somebody's behalf, which is the one thing this whole
        context exists to prevent.
        """
        published = {name for name in dir(ActionBatchProposer) if not name.startswith("_")}

        assert published == {"propose"}
        assert "approve" not in published
        assert "apply" not in published
        assert "reverse" not in published


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

    def test_a_fake_satisfies_the_proposer(self) -> None:
        """**`mypy --strict` accepting this is the assertion**, exactly as
        above — a consuming domain must be able to stand a double in."""

        class Fake:
            async def propose(
                self,
                *,
                workspace_id: UUID,
                name: str,
                item_count: int,
                proposed_by: UUID,
                reversible_for: timedelta | None = None,
            ) -> UUID:
                return uuid4()

        proposer: ActionBatchProposer = Fake()
        assert proposer is not None

    def test_the_context_exposes_nothing_and_publishes_only_its_two_events(self) -> None:
        """**No endpoint, no events** — P-C: an event exists when a consumer
        appears.

        ⚠️ **Re-aimed twice, and each time by the slice chartered to add the
        layer it was forbidding.** Slice 1 asserted `== {"public"}`; slice 2
        re-aimed it to name the three forbidden layers; **slice 3 is chartered
        to add persistence, so `infrastructure/` and its port leave the list.**

        ⛔ **Re-aimed rather than deleted, because the property outlives the
        count.** What is worth pinning was never *"which directories exist"* —
        it is that **nothing here is reachable from outside the process and
        nothing here announces itself**, which is what slice 4 adds and what a
        lane could otherwise smuggle in while building the tables. **A
        directory listing asserted that only by accident; this asserts it
        directly.**
        """
        from pathlib import Path

        import modules.action_batch as context

        root = Path(context.__file__).parent
        present = {p.name for p in root.iterdir() if p.is_dir()} - {"__pycache__"}

        # Persistence arrived with slice 3; the worker's handler with slice 5.
        assert "infrastructure" in present

        # ⚠️ **`interface/` now EXISTS, and the assertion is re-aimed rather
        # than deleted** — [TASK-465](../../../docs/BACKLOG.md).
        #
        # ⛔ **What this line was protecting was never the directory**: it was
        # *"an HTTP surface has not arrived"*, and a directory check was the
        # cheapest proxy while the layer was empty. ⚡ **A worker's event handler
        # lives in `interface/` too** — it is an edge, the same as a router —
        # **so the proxy stopped meaning what it said the moment slice 5 landed.**
        #
        # ✅ **And re-aimed once more, exactly as the last version predicted.**
        # 📁 **The apply endpoint arrived** — [TASK-465](../../../docs/BACKLOG.md)'s
        # Definition of Done names it — **so *no router* stopped being true and
        # was replaced rather than deleted.**
        #
        # 🔴 **What still binds is the SHAPE of the edge**: this context has two
        # ways in and no more. ⛔ **A third file here is a second transport** —
        # a GraphQL surface, a second router, a CLI — **and that is an
        # architectural decision** ([§7](../../../CLAUDE.md): *do not introduce
        # a second API paradigm*), **not something a slice adds quietly.**
        interface = root / "interface"
        assert interface.is_dir()
        edges = {p.name for p in interface.iterdir() if p.suffix == ".py"} - {"__init__.py"}
        assert edges == {"handlers.py", "router.py", "schemas.py"}, (
            f"action_batch's interface layer holds {sorted(edges)}. Two edges — an event "
            "handler and one HTTP router — plus the shapes that router puts on the wire. "
            "A third transport is an architectural decision, not a slice."
        )

        # **Events arrived with THIS slice, and the assertion is re-aimed a
        # third time rather than deleted** — the comment above already said
        # slice 4 would add them *inside* `application/`, where a directory
        # check would never look.
        #
        # ⛔ **What is pinned is not *no events* but *exactly the two the
        # domain justifies*.** A batch has six transitions and only two change
        # anything outside this module: it took effect, and it was taken back.
        # **Approval is permission for work that has not happened**, and a
        # subscriber acting on it would act early — so `action_batch.approved`
        # appearing here is the defect this now catches.
        sources = "\n".join(
            p.read_text() for p in root.rglob("*.py") if "__pycache__" not in str(p)
        )

        published = {
            name
            for name in ("ActionBatchApplied", "ActionBatchReversed", "ActionBatchApproved",
                         "ActionBatchRejected", "ActionBatchWithdrawn", "ActionBatchProposed")
            if f"class {name}" in sources
        }
        assert published == {"ActionBatchApplied", "ActionBatchReversed"}, (
            f"action_batch defines {sorted(published)}. Exactly two transitions change "
            "anything outside this module — applied and reversed. P-C: an event exists "
            "when a consumer appears, and nothing consumes an approval."
        )

        # ⚡ **Slice 5's third event is deliberately NOT in the list above.**
        # ⛔ **It is a work trigger, not an integration event**: nothing outside
        # this module subscribes to it, and it exists because §9 forbids
        # publishing straight to Redis. **Asserted separately so the two-event
        # claim keeps meaning what it says.**
        assert "class ActionBatchApplicationRequested" in sources

        # ⛔ **Still no HTTP surface** — 📁 asserted on the ROUTER above, because
        # `interface/` now holds slice 5's worker handler and a directory check
        # stopped meaning *"unreachable from outside the process"* the moment it
        # did.
