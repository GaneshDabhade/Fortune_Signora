"""Naming a grouping and filling it — [TASK-1479](../../../docs/BACKLOG.md) ⓶b.

⚡ **Written before the slice was offered, which is the change [B-201](../../../docs/BUGS.md)
bought.** ⓶a shipped its batch lifecycle at 61% and the gap was only visible
from a repository-wide run; **these are the same paths for segments, covered
before anybody had to find them missing.**
"""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID, uuid4

import pytest

from modules.commercial_profile.application.segment_use_cases import (
    AccountSegmentRepository,
    AddToSegmentInput,
    AddToSegmentUseCase,
    ApplySegmentBatchUseCase,
    CreateSegmentInput,
    CreateSegmentUseCase,
    ProposeSegmentBatchInput,
    ProposeSegmentBatchUseCase,
    RenameSegmentInput,
    RenameSegmentUseCase,
    ReverseSegmentAdditionUseCase,
    ReverseSegmentBatchUseCase,
    SegmentDirectoryUseCase,
    SegmentsForAccountsUseCase,
)
from modules.commercial_profile.domain.account_segment import (
    AccountSegment,
    AccountSegmentError,
    SegmentAddition,
    SegmentBatch,
    SegmentDirectory,
    add_to_segment,
)


class _Segments:
    """A fake with real membership, so *what changed* is decided by the same
    rule the database would decide it by."""

    def __init__(
        self,
        *,
        segments: tuple[AccountSegment, ...] = (),
        members: dict[UUID, set[UUID]] | None = None,
    ) -> None:
        self._segments = segments
        self._members = members or {}
        self.created: list[AccountSegment] = []
        self.renamed: list[AccountSegment] = []
        self.added: list[tuple[UUID, tuple[UUID, ...]]] = []
        self.removed: list[tuple[UUID, tuple[UUID, ...]]] = []

    async def directory(self, workspace_id: UUID) -> SegmentDirectory:
        return SegmentDirectory(segments=self._segments)

    async def create(
        self, workspace_id: UUID, segment: AccountSegment, *, actor_id: UUID
    ) -> None:
        self.created.append(segment)
        self._segments = (*self._segments, segment)

    async def rename(
        self, workspace_id: UUID, segment: AccountSegment, *, actor_id: UUID
    ) -> None:
        self.renamed.append(segment)

    async def members_among(
        self, workspace_id: UUID, segment_id: UUID, *, among: tuple[UUID, ...]
    ) -> frozenset[UUID]:
        return frozenset(self._members.get(segment_id, set())) & frozenset(among)

    async def add(
        self,
        workspace_id: UUID,
        segment_id: UUID,
        accounts: tuple[UUID, ...],
        *,
        actor_id: UUID,
    ) -> None:
        self.added.append((segment_id, accounts))
        self._members.setdefault(segment_id, set()).update(accounts)

    async def remove(
        self, workspace_id: UUID, segment_id: UUID, accounts: tuple[UUID, ...]
    ) -> None:
        self.removed.append((segment_id, accounts))
        self._members.setdefault(segment_id, set()).difference_update(accounts)

    async def segments_for(
        self, workspace_id: UUID, accounts: tuple[UUID, ...]
    ) -> dict[UUID, tuple[UUID, ...]]:
        held: dict[UUID, list[UUID]] = {}
        for segment_id, members in self._members.items():
            for account in members & set(accounts):
                held.setdefault(account, []).append(segment_id)
        return {account: tuple(ids) for account, ids in held.items()}

    async def counts(self, workspace_id: UUID) -> dict[UUID, int]:
        # ⚡ **Absent rather than zero**, exactly as the SQL `GROUP BY` behaves
        # — which is the behaviour the directory use case has to compensate for.
        return {
            segment_id: len(members)
            for segment_id, members in self._members.items()
            if members
        }


class _Proposer:
    def __init__(self) -> None:
        self.proposals: list[dict[str, object]] = []

    async def propose(
        self,
        *,
        workspace_id: UUID,
        name: str,
        item_count: int,
        proposed_by: UUID,
        reversible_for: timedelta | None = None,
    ) -> UUID:
        batch_id = uuid4()
        self.proposals.append(
            {"name": name, "item_count": item_count, "reversible_for": reversible_for}
        )
        return batch_id


class _Batches:
    def __init__(self, batch: SegmentBatch | None = None) -> None:
        self._batch = batch
        self.recorded: list[SegmentBatch] = []
        self.applications: list[SegmentAddition] = []

    async def record(self, workspace_id: UUID, batch: SegmentBatch, *, actor_id: UUID) -> None:
        self.recorded.append(batch)
        self._batch = batch

    async def get(self, workspace_id: UUID, batch_id: UUID) -> SegmentBatch | None:
        if self._batch is None or self._batch.batch_id != batch_id:
            return None
        return self._batch

    async def record_application(
        self,
        workspace_id: UUID,
        batch_id: UUID,
        application: SegmentAddition,
        *,
        actor_id: UUID,
    ) -> None:
        self.applications.append(application)
        assert self._batch is not None
        self._batch = self._batch.with_application(application)


def _repository(segments: _Segments) -> AccountSegmentRepository:
    return segments


class TestNamingAGrouping:
    async def test_a_new_name_is_created(self) -> None:
        segments = _Segments()

        created = await CreateSegmentUseCase(segments=_repository(segments)).execute(
            CreateSegmentInput(workspace_id=uuid4(), actor_id=uuid4(), name="Board reporting set")
        )

        assert segments.created == [created]
        assert created.name == "Board reporting set"

    async def test_a_name_already_in_use_is_refused_rather_than_selected(self) -> None:
        """⚠️ **The contrast with *Add tag* is the design's, not a preference.**

        📁 *Add tag* returns the existing tag because the control is meant to
        be pressed twice. ⛔ ***New segment* opens a naming affordance**, and a
        customer who types a name they already used has made a mistake worth
        telling them about.
        """
        existing = AccountSegment(id=uuid4(), name="Board reporting set")
        segments = _Segments(segments=(existing,))

        with pytest.raises(AccountSegmentError):
            await CreateSegmentUseCase(segments=_repository(segments)).execute(
                CreateSegmentInput(
                    workspace_id=uuid4(), actor_id=uuid4(), name="board REPORTING set"
                )
            )

        assert segments.created == []

    async def test_renaming_keeps_the_id(self) -> None:
        existing = AccountSegment(id=uuid4(), name="Board reporting set")
        segments = _Segments(segments=(existing,))

        renamed = await RenameSegmentUseCase(segments=_repository(segments)).execute(
            RenameSegmentInput(
                workspace_id=uuid4(),
                actor_id=uuid4(),
                segment_id=existing.id,
                name="Quarterly pack",
            )
        )

        assert renamed.id == existing.id
        assert segments.renamed == [renamed]

    async def test_renaming_something_that_is_not_here_is_refused(self) -> None:
        with pytest.raises(AccountSegmentError):
            await RenameSegmentUseCase(segments=_repository(_Segments())).execute(
                RenameSegmentInput(
                    workspace_id=uuid4(), actor_id=uuid4(), segment_id=uuid4(), name="Anything"
                )
            )

    async def test_renaming_onto_another_segment_s_name_is_refused(self) -> None:
        first = AccountSegment(id=uuid4(), name="Board reporting set")
        second = AccountSegment(id=uuid4(), name="Competitive watch")
        segments = _Segments(segments=(first, second))

        with pytest.raises(AccountSegmentError):
            await RenameSegmentUseCase(segments=_repository(segments)).execute(
                RenameSegmentInput(
                    workspace_id=uuid4(),
                    actor_id=uuid4(),
                    segment_id=second.id,
                    name="Board reporting set",
                )
            )

        assert segments.renamed == []


class TestPuttingCompaniesIn:
    async def test_only_what_changed_is_written(self) -> None:
        """🔴 **Not an optimisation.** `added_by` and `added_at` on a row
        somebody curated in June are facts about June, and an upsert would move
        them to whoever last pressed this."""
        segment = AccountSegment(id=uuid4(), name="Board reporting set")
        already, fresh = uuid4(), uuid4()
        segments = _Segments(segments=(segment,), members={segment.id: {already}})

        addition = await AddToSegmentUseCase(segments=_repository(segments)).execute(
            AddToSegmentInput(
                workspace_id=uuid4(),
                actor_id=uuid4(),
                segment_id=segment.id,
                accounts=(already, fresh),
            )
        )

        assert segments.added == [(segment.id, (fresh,))]
        assert addition.unchanged == (already,)

    async def test_a_segment_that_is_not_here_is_refused(self) -> None:
        with pytest.raises(AccountSegmentError):
            await AddToSegmentUseCase(segments=_repository(_Segments())).execute(
                AddToSegmentInput(
                    workspace_id=uuid4(),
                    actor_id=uuid4(),
                    segment_id=uuid4(),
                    accounts=(uuid4(),),
                )
            )

    async def test_an_empty_selection_is_refused(self) -> None:
        segment = AccountSegment(id=uuid4(), name="Board reporting set")

        with pytest.raises(AccountSegmentError):
            await AddToSegmentUseCase(
                segments=_repository(_Segments(segments=(segment,)))
            ).execute(
                AddToSegmentInput(
                    workspace_id=uuid4(), actor_id=uuid4(), segment_id=segment.id, accounts=()
                )
            )

    async def test_the_reversal_removes_only_what_was_added(self) -> None:
        segment, already, fresh = uuid4(), uuid4(), uuid4()
        segments = _Segments(members={segment: {already, fresh}})
        addition = SegmentAddition(segment_id=segment, added=(fresh,), unchanged=(already,))

        await ReverseSegmentAdditionUseCase(segments=_repository(segments)).execute(
            uuid4(), addition
        )

        assert segments.removed == [(segment, (fresh,))]


class TestThePanel:
    async def test_a_segment_with_nobody_in_it_reports_zero_rather_than_vanishing(
        self,
    ) -> None:
        """🔴 **The state every segment passes through**, between being named
        and being curated. ⛔ **A join would have made it disappear from the
        customer's own panel in exactly that window** —
        [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md), where the customer
        is looking.
        """
        empty = AccountSegment(id=uuid4(), name="Board reporting set")
        filled = AccountSegment(id=uuid4(), name="Competitive watch")
        segments = _Segments(segments=(empty, filled), members={filled.id: {uuid4(), uuid4()}})

        panel = await SegmentDirectoryUseCase(segments=_repository(segments)).execute(uuid4())

        assert panel == ((empty, 0), (filled, 2))

    async def test_membership_comes_back_for_the_accounts_asked_about(self) -> None:
        segment, account, elsewhere = uuid4(), uuid4(), uuid4()
        segments = _Segments(members={segment: {account, elsewhere}})

        held = await SegmentsForAccountsUseCase(segments=_repository(segments)).execute(
            uuid4(), (account,)
        )

        assert held == {account: (segment,)}


class TestTheBatchLifecycle:
    def _segment(self) -> AccountSegment:
        return AccountSegment(id=uuid4(), name="Board reporting set")

    async def test_the_proposal_is_named_in_the_customer_s_words(self) -> None:
        segment = self._segment()
        proposer = _Proposer()

        await ProposeSegmentBatchUseCase(
            segments=_repository(_Segments(segments=(segment,))),
            batches=_Batches(),
            proposer=proposer,
        ).execute(
            ProposeSegmentBatchInput(
                workspace_id=uuid4(),
                actor_id=uuid4(),
                segment_id=segment.id,
                accounts=(uuid4(), uuid4()),
            )
        )

        name = str(proposer.proposals[0]["name"])
        assert "Board reporting set" in name
        assert "2" in name

    async def test_the_count_is_of_companies_and_not_of_clicks(self) -> None:
        segment = self._segment()
        repeated = uuid4()
        proposer = _Proposer()

        await ProposeSegmentBatchUseCase(
            segments=_repository(_Segments(segments=(segment,))),
            batches=_Batches(),
            proposer=proposer,
        ).execute(
            ProposeSegmentBatchInput(
                workspace_id=uuid4(),
                actor_id=uuid4(),
                segment_id=segment.id,
                accounts=(repeated, uuid4(), repeated),
            )
        )

        assert proposer.proposals[0]["item_count"] == 2

    async def test_a_reversal_window_travels_with_the_proposal(self) -> None:
        segment = self._segment()
        proposer = _Proposer()

        await ProposeSegmentBatchUseCase(
            segments=_repository(_Segments(segments=(segment,))),
            batches=_Batches(),
            proposer=proposer,
        ).execute(
            ProposeSegmentBatchInput(
                workspace_id=uuid4(),
                actor_id=uuid4(),
                segment_id=segment.id,
                accounts=(uuid4(),),
            )
        )

        assert proposer.proposals[0]["reversible_for"] is not None

    async def test_a_segment_that_is_not_here_cannot_be_proposed(self) -> None:
        proposer = _Proposer()

        with pytest.raises(AccountSegmentError):
            await ProposeSegmentBatchUseCase(
                segments=_repository(_Segments()),
                batches=_Batches(),
                proposer=proposer,
            ).execute(
                ProposeSegmentBatchInput(
                    workspace_id=uuid4(),
                    actor_id=uuid4(),
                    segment_id=uuid4(),
                    accounts=(uuid4(),),
                )
            )

        assert proposer.proposals == []

    async def test_an_empty_selection_cannot_be_proposed(self) -> None:
        segment = self._segment()

        with pytest.raises(AccountSegmentError):
            await ProposeSegmentBatchUseCase(
                segments=_repository(_Segments(segments=(segment,))),
                batches=_Batches(),
                proposer=_Proposer(),
            ).execute(
                ProposeSegmentBatchInput(
                    workspace_id=uuid4(), actor_id=uuid4(), segment_id=segment.id, accounts=()
                )
            )

    async def test_applying_writes_the_members_and_records_what_moved(self) -> None:
        segment = self._segment()
        already, fresh = uuid4(), uuid4()
        segments = _Segments(segments=(segment,), members={segment.id: {already}})
        batch = SegmentBatch(
            batch_id=uuid4(), segment_id=segment.id, requested=(already, fresh)
        )
        batches = _Batches(batch)

        await ApplySegmentBatchUseCase(
            segments=_repository(segments), batches=batches
        ).execute(uuid4(), batch.batch_id, actor_id=uuid4())

        assert segments.added == [(segment.id, (fresh,))]
        assert batches.applications[0].added == (fresh,)

    async def test_another_domain_s_batch_is_ignored_rather_than_refused(self) -> None:
        """⛔ **Not an error.** Every consumer of `action_batch.applied` sees
        every one of them, and raising would dead-letter a tag batch on this
        module's queue."""
        segments = _Segments()
        batches = _Batches(None)

        await ApplySegmentBatchUseCase(
            segments=_repository(segments), batches=batches
        ).execute(uuid4(), uuid4(), actor_id=uuid4())

        assert segments.added == []

    async def test_a_redelivered_apply_changes_nothing(self) -> None:
        """⚡ **Idempotent**, which the envelope contract says is required — a
        redelivery is normal, not exceptional."""
        segment = self._segment()
        account = uuid4()
        segments = _Segments(segments=(segment,))
        batch = SegmentBatch(batch_id=uuid4(), segment_id=segment.id, requested=(account,))
        batches = _Batches(batch)
        apply = ApplySegmentBatchUseCase(segments=_repository(segments), batches=batches)

        await apply.execute(uuid4(), batch.batch_id, actor_id=uuid4())
        await apply.execute(uuid4(), batch.batch_id, actor_id=uuid4())

        assert segments.added == [(segment.id, (account,))]
        assert len(batches.applications) == 1

    async def test_reversing_removes_what_the_batch_added_and_not_what_it_asked(self) -> None:
        segment = self._segment()
        already, fresh = uuid4(), uuid4()
        segments = _Segments(segments=(segment,), members={segment.id: {already, fresh}})
        batch = SegmentBatch(
            batch_id=uuid4(),
            segment_id=segment.id,
            requested=(already, fresh),
            applied=add_to_segment(
                segment.id, accounts=(already, fresh), already_in=frozenset({already})
            ),
        )

        await ReverseSegmentBatchUseCase(
            segments=_repository(segments), batches=_Batches(batch)
        ).execute(uuid4(), batch.batch_id)

        assert segments.removed == [(segment.id, (fresh,))]

    async def test_reversing_a_batch_that_never_applied_writes_nothing(self) -> None:
        segment = self._segment()
        segments = _Segments(segments=(segment,))
        batch = SegmentBatch(batch_id=uuid4(), segment_id=segment.id, requested=(uuid4(),))

        await ReverseSegmentBatchUseCase(
            segments=_repository(segments), batches=_Batches(batch)
        ).execute(uuid4(), batch.batch_id)

        assert segments.removed == []

    async def test_reversing_another_domain_s_batch_writes_nothing(self) -> None:
        segments = _Segments()

        await ReverseSegmentBatchUseCase(
            segments=_repository(segments), batches=_Batches(None)
        ).execute(uuid4(), uuid4())

        assert segments.removed == []
