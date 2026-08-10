"""The store is append-only, and the aggregate is rebuilt by replaying it.

**[TASK-463](../../../docs/BACKLOG.md), slice 3 of six**
([455 §5](../../../docs/architecture/455-context-definitions-r02-r03.md)).

**What is asserted here is the mapping, not the database.** That the tables
carry no `UPDATE` grant, force RLS and are classified is asserted by the
Security Invariants suite, which is driven by `tenancy_policy.py` — registering
the two names is what earns those checks, and restating them here would be the
duplicated truth §2 forbids.

**What that suite cannot see is whether the code round-trips**, and the
refusals below are the substance: a log that could not have been produced
legally must fail loudly rather than rebuild an aggregate that is quietly
wrong.
"""

from __future__ import annotations

import importlib.util
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType
from uuid import UUID, uuid4

import pytest

from modules.action_batch.domain.batch import (
    ActionBatch,
    ActionBatchError,
    ApprovalState,
    Decision,
    Transition,
)
from modules.action_batch.infrastructure.models import (
    ActionBatchModel,
    ActionBatchTransitionModel,
)
from modules.action_batch.infrastructure.repository import _history, _replay

MIGRATION = (
    Path(__file__).resolve().parents[2] / "migrations" / "versions" / "0042_action_batch.py"
)


def _migration_source() -> str:
    return MIGRATION.read_text()


def _migration_module(path: Path = MIGRATION, name: str = "migration_0042") -> ModuleType:
    """Loaded by path, because `0042_action_batch` is not an importable name."""
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


#: 🔴 **The migration that CURRENTLY defines the transition constraint** —
#: [TASK-465](../../../docs/BACKLOG.md).
#:
#: ⚠️ **`0042` is not updated to match, and that is the rule rather than an
#: oversight.** 📁 [§2](../../../CLAUDE.md): *a record of what was true then must
#: not be rewritten to match now.* **`0042` created the table with five
#: transitions and that is what it did**; `0048` widened the alphabet to seven.
#: ⛔ **Rewriting `0042`'s tuple would make the repository lie about its own
#: history and would break any deployment replaying the chain.**
CURRENT_CONSTRAINT = MIGRATION.parent / "0048_action_batch_dispatch.py"


PROPOSED = datetime(2026, 8, 7, 9, 0, tzinfo=UTC)
DECIDED = PROPOSED + timedelta(minutes=5)
APPLIED = PROPOSED + timedelta(minutes=10)
WINDOW = timedelta(hours=1)

WORKSPACE = uuid4()
PROPOSER = uuid4()
APPROVER = uuid4()


def _batch(*, window: timedelta | None = WINDOW) -> ActionBatch:
    return ActionBatch(
        id=uuid4(),
        workspace_id=WORKSPACE,
        name="Move 12 accounts to Engaged",
        item_count=12,
        proposed=Decision(actor_id=PROPOSER, at=PROPOSED),
        reversible_for=window,
    )


def _row(batch: ActionBatch) -> ActionBatchModel:
    """The opening row, as `add` would have written it."""
    return ActionBatchModel(
        id=batch.id,
        workspace_id=batch.workspace_id,
        name=batch.name,
        item_count=batch.item_count,
        proposed_by=batch.proposed.actor_id,
        proposed_at=batch.proposed.at,
        reversible_for=batch.reversible_for,
        created_by=PROPOSER,
        updated_by=PROPOSER,
    )


def _log(batch: ActionBatch) -> list[ActionBatchTransitionModel]:
    """The log rows, as successive `record` calls would have written them."""
    return [
        ActionBatchTransitionModel(
            id=uuid4(),
            workspace_id=batch.workspace_id,
            batch_id=batch.id,
            sequence=index,
            transition=transition.value,
            actor_id=actor_id,
            occurred_at=occurred_at,
            created_by=PROPOSER,
            updated_by=PROPOSER,
        )
        for index, (transition, actor_id, occurred_at) in enumerate(_history(batch))
    ]


class TestTheHistoryIsDerivedFromTheAggregate:
    """**Never tracked beside it**, which is what makes `record` idempotent."""

    def test_a_proposed_batch_has_nothing_to_record(self) -> None:
        """The proposal is how a batch begins, not something that happened to
        it — so it lives on the batch row and not in the log."""
        assert _history(_batch()) == ()

    def test_each_transition_extends_the_history_by_exactly_one(self) -> None:
        batch = _batch()
        approved = batch.approved_by(APPROVER, at=DECIDED)
        applied = approved.applied_on(APPLIED)
        reversed_ = applied.reversed_by(APPROVER, at=APPLIED + timedelta(minutes=1))

        assert len(_history(approved)) == 1
        assert len(_history(applied)) == 2
        assert len(_history(reversed_)) == 3

    def test_the_position_is_a_property_of_the_aggregate_not_of_the_store(self) -> None:
        """**This is what makes re-recording collide rather than duplicate.**
        The same aggregate always yields the same length, so a second `record`
        writes the same `sequence` and `uq_action_batch_transition_sequence`
        refuses it. A `max(sequence) + 1` would happily store the fact twice.
        """
        applied = _batch().approved_by(APPROVER, at=DECIDED).applied_on(APPLIED)

        assert len(_history(applied)) - 1 == 1
        assert len(_history(applied)) - 1 == 1

    def test_application_is_the_one_transition_with_no_actor(self) -> None:
        applied = _batch().approved_by(APPROVER, at=DECIDED).applied_on(APPLIED)
        recorded = {transition: actor for transition, actor, _ in _history(applied)}

        assert recorded[Transition.APPROVED] == APPROVER
        assert recorded[Transition.APPLIED] is None

    @pytest.mark.parametrize(
        ("leave", "expected"),
        [
            ("approved_by", Transition.APPROVED),
            ("rejected_by", Transition.REJECTED),
            ("withdrawn_by", Transition.WITHDRAWN),
        ],
    )
    def test_which_decision_it_was_comes_from_the_state(
        self, leave: str, expected: Transition
    ) -> None:
        """`_decide` is the only thing that leaves `PROPOSED` and it sets state
        and decision together, so the transition never has to be passed
        alongside the aggregate — where a caller could name the wrong one."""
        decided = getattr(_batch(), leave)(APPROVER, at=DECIDED)

        assert _history(decided)[-1][0] is expected

    def test_a_reversal_does_not_rewrite_the_approval_that_preceded_it(self) -> None:
        """⚠️ **This is a defect the round-trip caught, and it is the reason
        the derivation is not simply `state`.**

        **A reversal overwrites `state` with `REVERSED`**, so reading the
        decision off the current state recorded the approval *as* a reversal —
        two reversals in the log and no approval anywhere. **The batch would
        have replayed as something that was never approved**, which is the one
        thing an approval record exists to prove.

        ⛔ **Nothing is stored to fix it.** Only an approved batch can be
        applied and only an applied one reversed, so the approval is entailed
        by `applied_at` — and §2 prefers deriving it to keeping a second copy
        that could disagree.
        """
        reversed_ = (
            _batch()
            .approved_by(APPROVER, at=DECIDED)
            .applied_on(APPLIED)
            .reversed_by(APPROVER, at=APPLIED + timedelta(minutes=30))
        )

        recorded = [transition for transition, _, _ in _history(reversed_)]

        assert recorded == [Transition.APPROVED, Transition.APPLIED, Transition.REVERSED]


class TestReplayGoesThroughTheDomain:
    def test_a_proposed_batch_round_trips(self) -> None:
        batch = _batch()

        rebuilt = _replay(_row(batch), _log(batch))

        assert rebuilt == batch

    @pytest.mark.parametrize(
        "leave", ["approved_by", "rejected_by", "withdrawn_by"]
    )
    def test_every_decision_round_trips(self, leave: str) -> None:
        batch = getattr(_batch(), leave)(APPROVER, at=DECIDED)

        assert _replay(_row(batch), _log(batch)) == batch

    def test_an_applied_batch_round_trips_and_stays_approved(self) -> None:
        """**`APPLIED` is not a state.** An applied batch is still `APPROVED`,
        and `applied_at` is what says it ran — so a store that made it a state
        would lose who approved it."""
        batch = _batch().approved_by(APPROVER, at=DECIDED).applied_on(APPLIED)

        rebuilt = _replay(_row(batch), _log(batch))

        assert rebuilt == batch
        assert rebuilt.state is ApprovalState.APPROVED
        assert rebuilt.applied_at == APPLIED

    def test_a_reversal_round_trips(self) -> None:
        batch = (
            _batch()
            .approved_by(APPROVER, at=DECIDED)
            .applied_on(APPLIED)
            .reversed_by(APPROVER, at=APPLIED + timedelta(minutes=30))
        )

        rebuilt = _replay(_row(batch), _log(batch))

        assert rebuilt == batch
        assert rebuilt.state is ApprovalState.REVERSED

    def test_replay_is_deterministic_however_long_afterwards_it_runs(self) -> None:
        """⚡ **Because no domain method reads a clock** (§2, *hidden inputs*).
        A reversal recorded inside its window replays years later and is still
        inside it, since `now` is the moment it was recorded at rather than the
        moment of the read.
        """
        batch = (
            _batch()
            .approved_by(APPROVER, at=DECIDED)
            .applied_on(APPLIED)
            .reversed_by(APPROVER, at=APPLIED + timedelta(minutes=30))
        )
        row, log = _row(batch), _log(batch)

        assert _replay(row, log) == _replay(row, log) == batch

    def test_a_window_that_was_never_offered_survives_the_round_trip(self) -> None:
        """`None` means reversal was never offered, which is a different answer
        from *expired* — and a store that flattened them would tell a customer
        the wrong one."""
        batch = _batch(window=None).approved_by(APPROVER, at=DECIDED).applied_on(APPLIED)

        rebuilt = _replay(_row(batch), _log(batch))

        assert rebuilt.reversible_for is None
        assert not rebuilt.is_settled(now=APPLIED + timedelta(days=365))


class TestAnImpossibleLogIsRefusedRatherThanRebuilt:
    """⛔ **The reason replay goes through the domain at all.** Setting fields
    directly would let persistence construct aggregates the domain refuses, and
    the defect would surface wherever the aggregate was later used rather than
    where it was read."""

    def test_a_second_decision_is_refused(self) -> None:
        batch = _batch().approved_by(APPROVER, at=DECIDED)
        log = _log(batch)
        duplicate = _log(batch)[0]
        duplicate.sequence = 1
        duplicate.transition = Transition.REJECTED.value

        with pytest.raises(ActionBatchError, match="leaves the proposed state exactly once"):
            _replay(_row(batch), [*log, duplicate])

    def test_an_application_with_no_approval_is_refused(self) -> None:
        """An `applied` row against a batch nobody approved would be a change
        performed on nobody's authority."""
        batch = _batch()
        orphan = ActionBatchTransitionModel(
            id=uuid4(),
            workspace_id=batch.workspace_id,
            batch_id=batch.id,
            sequence=0,
            transition=Transition.APPLIED.value,
            actor_id=None,
            occurred_at=APPLIED,
            created_by=PROPOSER,
            updated_by=PROPOSER,
        )

        with pytest.raises(ActionBatchError, match="did not take effect"):
            _replay(_row(batch), [orphan])

    def test_an_attributed_transition_with_no_actor_is_refused(self) -> None:
        """⚠️ **The table's CHECK permits `NULL` only for `applied`**, so this
        row cannot be written today. **Asserted anyway, and it is not
        decorative**: the guard is the only thing standing between a relaxed
        constraint and an approval attributed to nobody, and a guard nothing
        exercises is one nobody would notice removing.
        """
        batch = _batch().approved_by(APPROVER, at=DECIDED)
        log = _log(batch)
        log[0].actor_id = None

        with pytest.raises(ActionBatchError, match="names no actor"):
            _replay(_row(batch), log)


class TestTheStoredShapeMatchesTheDomain:
    def test_the_migration_constrains_exactly_the_transitions_the_domain_has(self) -> None:
        """**The migration is a frozen historical artifact and may not import
        live code**, so its tuple is a copy — and a copy nothing checks is the
        duplicated truth §2 forbids. This is the check."""
        migration = _migration_module(CURRENT_CONSTRAINT, "migration_0048")

        assert set(migration.TRANSITIONS) == {t.value for t in Transition}
        # ⚡ **Three unattributed now** — [TASK-465](../../../docs/BACKLOG.md).
        # ⛔ **Compared as a SET against the enum rather than named literally**,
        # so a fourth reaches the migration's constraint by failing here.
        assert set(migration.UNATTRIBUTED) == {t.value for t in Transition if not t.is_attributed}

    def test_the_migration_withholds_update_on_both_tables(self) -> None:
        """⛔ **The grant and the policy are both withheld, never one.** A
        policy without a grant is decorative; a grant without a policy is a
        tenancy hole."""
        source = _migration_source()

        assert "GRANT SELECT, INSERT, DELETE ON" in source
        assert "UPDATE" not in source.split("def upgrade()")[1]

    def test_the_model_derives_its_constraint_from_the_enum(self) -> None:
        """A sixth transition reaches the model's CHECK automatically."""
        from modules.action_batch.infrastructure import models

        for transition in Transition:
            assert f"transition = '{transition.value}'" in models._KNOWN_TRANSITIONS
        for transition in Transition:
            listed = f"'{transition.value}'" in models._UNATTRIBUTED_LIST
            assert listed is (not transition.is_attributed), transition

    def test_no_column_stores_the_state_or_the_window_having_elapsed(self) -> None:
        """**Both derive** (§2). A stored `state` beside the log is the copy
        that eventually disagrees with the record an audit cites, and a stored
        `is_settled` needs a scheduler [P-B] refuses."""
        columns = set(ActionBatchModel.__table__.columns.keys())

        assert not columns & {"state", "applied_at", "is_settled", "settled_at", "reversed_at"}

    def test_the_batch_row_carries_no_hint_of_what_the_items_are(self) -> None:
        """This context coordinates lifecycle and never learns business
        semantics ([D-126](../../../docs/DECISION_REGISTER.md))."""
        columns = set(ActionBatchModel.__table__.columns.keys())

        assert not columns & {"payload", "operation", "inverse", "entity_type", "items"}
        assert "item_count" in columns

    def test_every_transition_names_a_method_the_aggregate_has(self) -> None:
        """**The alphabet and the behaviour cannot drift**, because a sixth
        member with no method fails here rather than at the first replay."""
        verbs = {
            Transition.APPROVED: "approved_by",
            Transition.REJECTED: "rejected_by",
            Transition.WITHDRAWN: "withdrawn_by",
            # ⚡ **Slice 5's two** — [TASK-465](../../../docs/BACKLOG.md).
            # **This guard is what made me add them here rather than only to
            # the enum**, which is exactly what it was written for.
            Transition.DISPATCHED: "dispatched_on",
            Transition.APPLIED: "applied_on",
            Transition.APPLICATION_FAILED: "failed_to_apply",
            Transition.REVERSED: "reversed_by",
        }

        assert set(verbs) == set(Transition)
        for transition, method in verbs.items():
            assert callable(getattr(ActionBatch, method)), transition


class TestTheRepositoryOffersNoEdit:
    def test_there_is_no_update_method_anywhere_on_it(self) -> None:
        """⛔ **Enforced, not documented.** A method offering an edit is a
        method somebody will eventually call, and the database's missing
        `UPDATE` grant would then surface as a runtime failure in a request
        rather than as a design this module refused."""
        from modules.action_batch.infrastructure.repository import SqlActionBatchRepository

        methods = {m for m in dir(SqlActionBatchRepository) if not m.startswith("_")}

        assert methods == {"add", "record", "get"}
        assert not [m for m in methods if m.startswith(("update", "edit", "set", "delete"))]

    def test_the_port_and_the_implementation_agree(self) -> None:
        from modules.action_batch.application.ports import ActionBatchRepository
        from modules.action_batch.infrastructure.repository import SqlActionBatchRepository

        port = {m for m in dir(ActionBatchRepository) if not m.startswith("_")}
        implementation = {m for m in dir(SqlActionBatchRepository) if not m.startswith("_")}

        assert port == implementation

    @pytest.mark.asyncio
    async def test_recording_a_batch_that_has_not_transitioned_is_refused(self) -> None:
        """A proposal is written by `add`; asking `record` for one would append
        a log row for something that is not a transition.

        **The fake session refuses every call**, so the test also proves
        nothing was written before the guard fired.
        """

        class _Session:
            def add(self, _: object) -> None:
                raise AssertionError("nothing should be written")

            async def flush(self) -> None:
                raise AssertionError("nothing should be flushed")

        from modules.action_batch.infrastructure.repository import SqlActionBatchRepository

        repository = SqlActionBatchRepository(_Session())  # type: ignore[arg-type]

        with pytest.raises(ActionBatchError, match="no transition to record"):
            await repository.record(_batch(), actor_id=uuid4())


class TestTheTablesAreClassified:
    """**Registration is what earns the Security Invariants**, which are driven
    by these sets rather than by naming tables inline. Asserted here so the
    slice fails if the classification is dropped — §8 requires it *in the same
    change* that creates the table."""

    def test_both_tables_are_tenant_owned(self) -> None:
        from tests.security_invariants.tenancy_policy import TENANT_OWNED_TABLES

        assert {"action_batch", "action_batch_transition"} <= TENANT_OWNED_TABLES

    def test_both_tables_are_immutable(self) -> None:
        from tests.security_invariants.tenancy_policy import IMMUTABLE_TENANT_TABLES

        assert {"action_batch", "action_batch_transition"} <= IMMUTABLE_TENANT_TABLES

    def test_the_model_tablenames_are_the_ones_registered(self) -> None:
        """⚠️ **The classification is by string**, so a rename that missed the
        policy file would leave a table with no invariants and nothing would
        say so."""
        from tests.security_invariants.tenancy_policy import TENANT_OWNED_TABLES

        assert ActionBatchModel.__tablename__ in TENANT_OWNED_TABLES
        assert ActionBatchTransitionModel.__tablename__ in TENANT_OWNED_TABLES


def test_the_actor_column_is_nullable_only_because_application_has_no_actor() -> None:
    """**The one nullable attribution in the module, and it is argued.**
    Application is performed on the authority of the approval already recorded;
    inventing a second actor would attribute the write to whoever flushed it."""
    columns = ActionBatchTransitionModel.__table__.columns

    assert columns["actor_id"].nullable
    assert not columns["occurred_at"].nullable

    # ⚡ **Three unattributed transitions now, and the argument is unchanged**
    # — [TASK-465](../../../docs/BACKLOG.md). **A worker is not an actor**:
    # dispatch and failure happen on the authority of the approval already
    # recorded, and naming the approver as the author of a background failure
    # would put a false name in a history somebody may have to defend.
    unattributed = {Transition.DISPATCHED, Transition.APPLIED, Transition.APPLICATION_FAILED}
    assert {t for t in Transition if not t.is_attributed} == unattributed
    assert all(t.is_attributed for t in Transition if t not in unattributed)


def test_the_batch_id_is_carried_and_the_workspace_is_never_a_foreign_key() -> None:
    """No foreign key leaves this context — `workspace_id` is carried, not
    constrained, exactly as everywhere."""
    foreign = {
        fk.column.table.name for fk in ActionBatchTransitionModel.__table__.foreign_keys
    }

    assert foreign == {"action_batch"}
    assert not ActionBatchModel.__table__.foreign_keys


def test_a_uuid_is_a_uuid_everywhere_it_is_stored() -> None:
    """Guards the mapping rather than the schema: a column typed as text would
    round-trip a string and compare unequal to the aggregate it came from."""
    batch = _batch().approved_by(APPROVER, at=DECIDED)
    rebuilt = _replay(_row(batch), _log(batch))

    assert isinstance(rebuilt.id, UUID)
    assert isinstance(rebuilt.proposed.actor_id, UUID)
    assert rebuilt.decided is not None
    assert isinstance(rebuilt.decided.actor_id, UUID)
