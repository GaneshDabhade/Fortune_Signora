"""Naming a grouping, and putting companies in it — [TASK-1479](../../../../docs/BACKLOG.md) ⓶b.

**[ADR-0411](../../../../docs/architecture/adr/0411-customer-organized-account-metadata.md)'s
third capability**, on the Action Batch lifecycle
[TASK-466](../../../../docs/BACKLOG.md) built and slice ⓶a reused: **propose,
approve, apply, take back.**

⚠️ **These are the *tag* use cases' shape and deliberately so.** ⛔ **Not
copied — the shapes match because the lifecycle is one lifecycle**, and where
the rule genuinely differs (a segment has no tone, a segment's membership is
never edited) the difference is stated rather than inherited.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID, uuid4

# ⚡ **`ActionBatchProposer` and `REVERSIBLE_FOR` are imported rather than
# re-declared.** The proposer is one shape for every consumer of the Action
# Batch, and the window is [C-1506](../../../../docs/LANE_COORDINATION.md)'s
# open number — **so a ruling on it changes one line and not three.**
from modules.commercial_profile.application.tag_use_cases import (
    REVERSIBLE_FOR,
    ActionBatchProposer,
)
from modules.commercial_profile.domain.account_segment import (
    AccountSegment,
    AccountSegmentError,
    SegmentAddition,
    SegmentBatch,
    SegmentDirectory,
    add_to_segment,
)


class AccountSegmentRepository(Protocol):
    """What this module needs of its own storage."""

    async def directory(self, workspace_id: UUID) -> SegmentDirectory: ...

    async def create(
        self, workspace_id: UUID, segment: AccountSegment, *, actor_id: UUID
    ) -> None: ...

    async def rename(
        self, workspace_id: UUID, segment: AccountSegment, *, actor_id: UUID
    ) -> None: ...

    async def members_among(
        self, workspace_id: UUID, segment_id: UUID, *, among: tuple[UUID, ...]
    ) -> frozenset[UUID]: ...

    async def add(
        self,
        workspace_id: UUID,
        segment_id: UUID,
        accounts: tuple[UUID, ...],
        *,
        actor_id: UUID,
    ) -> None: ...

    async def remove(
        self, workspace_id: UUID, segment_id: UUID, accounts: tuple[UUID, ...]
    ) -> None: ...

    async def segments_for(
        self, workspace_id: UUID, accounts: tuple[UUID, ...]
    ) -> dict[UUID, tuple[UUID, ...]]: ...

    async def counts(self, workspace_id: UUID) -> dict[UUID, int]: ...


class SegmentBatchStore(Protocol):
    async def record(
        self, workspace_id: UUID, batch: SegmentBatch, *, actor_id: UUID
    ) -> None: ...

    async def get(self, workspace_id: UUID, batch_id: UUID) -> SegmentBatch | None: ...

    async def record_application(
        self,
        workspace_id: UUID,
        batch_id: UUID,
        application: SegmentAddition,
        *,
        actor_id: UUID,
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class CreateSegmentInput:
    workspace_id: UUID
    actor_id: UUID
    name: str


class CreateSegmentUseCase:
    """Name a new grouping.

    ⚡ **Reads the directory first**, so *"Board reporting set"* typed twice
    selects the existing one rather than raising at the database. 📁 The
    aggregate is what refuses a duplicate, and the unique index on
    `(workspace_id, name_key)` is the second guard — **the domain's answer
    depends on having read, and two requests can both read the same absence.**
    """

    def __init__(self, *, segments: AccountSegmentRepository) -> None:
        self._segments = segments

    async def execute(self, request: CreateSegmentInput) -> AccountSegment:
        directory = await self._segments.directory(request.workspace_id)
        segment = AccountSegment(id=uuid4(), name=request.name)
        # Raises if the name is taken — deliberately, and the caller is what
        # makes *New segment* safe to repeat by asking `find` first.
        directory.added(segment)
        await self._segments.create(request.workspace_id, segment, actor_id=request.actor_id)
        return segment


@dataclass(frozen=True, slots=True)
class RenameSegmentInput:
    workspace_id: UUID
    actor_id: UUID
    segment_id: UUID
    name: str


class RenameSegmentUseCase:
    """Correct a name. **Every account in it stays in it**, because the id does
    not move."""

    def __init__(self, *, segments: AccountSegmentRepository) -> None:
        self._segments = segments

    async def execute(self, request: RenameSegmentInput) -> AccountSegment:
        directory = await self._segments.directory(request.workspace_id)
        existing = directory.get(request.segment_id)
        if existing is None:
            raise AccountSegmentError("That segment is not in this workspace.")
        renamed = existing.renamed(request.name)
        # The aggregate refuses a rename onto another segment's name.
        directory.replaced(renamed)
        await self._segments.rename(request.workspace_id, renamed, actor_id=request.actor_id)
        return renamed


@dataclass(frozen=True, slots=True)
class AddToSegmentInput:
    workspace_id: UUID
    actor_id: UUID
    segment_id: UUID
    accounts: tuple[UUID, ...]


class AddToSegmentUseCase:
    """Put a selection of companies into a grouping.

    🔴 **Writes only what changed.** 📁 The accounts already in the segment are
    not touched — **not as an optimisation, but because `added_by` and
    `added_at` on a row somebody curated in June are facts about June**, and an
    upsert would move them to whoever last ran a batch.
    """

    def __init__(self, *, segments: AccountSegmentRepository) -> None:
        self._segments = segments

    async def execute(self, request: AddToSegmentInput) -> SegmentAddition:
        directory = await self._segments.directory(request.workspace_id)
        if directory.get(request.segment_id) is None:
            raise AccountSegmentError("That segment is not in this workspace.")
        accounts = tuple(dict.fromkeys(request.accounts))
        if not accounts:
            raise AccountSegmentError("A selection has to name at least one account.")

        already_in = await self._segments.members_among(
            request.workspace_id, request.segment_id, among=accounts
        )
        addition = add_to_segment(
            request.segment_id, accounts=accounts, already_in=already_in
        )
        await self._segments.add(
            request.workspace_id,
            request.segment_id,
            addition.added,
            actor_id=request.actor_id,
        )
        return addition


class ReverseSegmentAdditionUseCase:
    """Take back a bulk *Add to segment*.

    ⛔ **Removes `inverse()` and never `requested`.** An account curated into
    the segment before the batch stays in it — **it was not this batch's doing,
    and removing it would delete work the customer never asked to undo.**

    ⚠️ **No re-check of anything, deliberately.** ⛔ A reversal that declined to
    undo part of what it was asked to undo would leave a customer who pressed
    *take it back* with it partly taken back, which is worse than either
    outcome it was choosing between.
    """

    def __init__(self, *, segments: AccountSegmentRepository) -> None:
        self._segments = segments

    async def execute(self, workspace_id: UUID, addition: SegmentAddition) -> None:
        await self._segments.remove(
            workspace_id, addition.segment_id, addition.inverse()
        )


class SegmentsForAccountsUseCase:
    """Which segments each of these accounts is in — the Companies read."""

    def __init__(self, *, segments: AccountSegmentRepository) -> None:
        self._segments = segments

    async def execute(
        self, workspace_id: UUID, accounts: tuple[UUID, ...]
    ) -> dict[UUID, tuple[UUID, ...]]:
        return await self._segments.segments_for(workspace_id, accounts)


class SegmentDirectoryUseCase:
    """The panel: every segment, with how many companies are in each.

    ⚡ **Two reads rather than one join**, and the absence is the point: a
    segment with no members is absent from `counts` and present in the
    directory, so it renders as *"0"* rather than vanishing. 🔴 **A join would
    have made an empty segment disappear from the customer's own panel** —
    [P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md)'s shape, and the one
    a newly created segment is in for as long as it takes to curate it.
    """

    def __init__(self, *, segments: AccountSegmentRepository) -> None:
        self._segments = segments

    async def execute(self, workspace_id: UUID) -> tuple[tuple[AccountSegment, int], ...]:
        directory = await self._segments.directory(workspace_id)
        counts = await self._segments.counts(workspace_id)
        return tuple((segment, counts.get(segment.id, 0)) for segment in directory.segments)


@dataclass(frozen=True, slots=True)
class ProposeSegmentBatchInput:
    workspace_id: UUID
    actor_id: UUID
    segment_id: UUID
    accounts: tuple[UUID, ...]


class ProposeSegmentBatchUseCase:
    """🔴 **Ask for a bulk *Add to segment*, as one named thing somebody
    approves.**

    📁 [D-235](../../../../docs/DECISION_REGISTER.md) ①: *"`propose` creates
    the batch and its payload atomically… ⛔ no batch-without-payload state is
    representable."* ⚡ **Both writes happen on one session**, which is what
    makes that true.

    ⛔ **It proposes and does not apply.** Approval is a human decision on a
    screen, and `action_batch.applied` is what brings the work back here.
    """

    def __init__(
        self,
        *,
        segments: AccountSegmentRepository,
        batches: SegmentBatchStore,
        proposer: ActionBatchProposer,
    ) -> None:
        self._segments = segments
        self._batches = batches
        self._proposer = proposer

    async def execute(self, request: ProposeSegmentBatchInput) -> UUID:
        directory = await self._segments.directory(request.workspace_id)
        segment = directory.get(request.segment_id)
        if segment is None:
            raise AccountSegmentError("That segment is not in this workspace.")

        # ⚡ **De-duplicated BEFORE the count is taken**, so the name a customer
        # approves says how many companies it touches rather than how many rows
        # they clicked.
        accounts = tuple(dict.fromkeys(request.accounts))
        if not accounts:
            raise AccountSegmentError("A batch has to name at least one account.")

        batch_id = await self._proposer.propose(
            workspace_id=request.workspace_id,
            # ⚡ **The customer's own words**, so the approval screen shows the
            # sentence they would say rather than an identifier.
            name=f"Add {len(accounts)} companies to “{segment.name}”",
            item_count=len(accounts),
            proposed_by=request.actor_id,
            reversible_for=REVERSIBLE_FOR,
        )
        await self._batches.record(
            request.workspace_id,
            SegmentBatch(
                batch_id=batch_id, segment_id=request.segment_id, requested=accounts
            ),
            actor_id=request.actor_id,
        )
        return batch_id


class ApplySegmentBatchUseCase:
    """Run an approved batch, and record exactly what it did."""

    def __init__(
        self,
        *,
        segments: AccountSegmentRepository,
        batches: SegmentBatchStore,
    ) -> None:
        self._segments = segments
        self._batches = batches

    async def execute(self, workspace_id: UUID, batch_id: UUID, *, actor_id: UUID) -> None:
        batch = await self._batches.get(workspace_id, batch_id)
        if batch is None:
            # ⛔ **Not an error.** 📁 `action_batch` is a shared lifecycle and
            # every consumer sees every applied event; one that is not this
            # module's is not this module's to refuse.
            return
        if batch.is_applied:
            # ⚡ **Idempotent on a redelivered event**, which the envelope
            # contract says will happen. The store's conditional write is the
            # guard that holds when two deliveries race.
            return

        already_in = await self._segments.members_among(
            workspace_id, batch.segment_id, among=batch.requested
        )
        addition = add_to_segment(
            batch.segment_id, accounts=batch.requested, already_in=already_in
        )
        await self._segments.add(
            workspace_id, batch.segment_id, addition.added, actor_id=actor_id
        )
        await self._batches.record_application(
            workspace_id, batch_id, addition, actor_id=actor_id
        )


class ReverseSegmentBatchUseCase:
    """Take back an applied batch.

    ⛔ **Reads what was ADDED, never what was requested**, which is the whole
    reason the batch keeps its own row.
    """

    def __init__(
        self,
        *,
        segments: AccountSegmentRepository,
        batches: SegmentBatchStore,
    ) -> None:
        self._segments = segments
        self._batches = batches

    async def execute(self, workspace_id: UUID, batch_id: UUID) -> None:
        batch = await self._batches.get(workspace_id, batch_id)
        if batch is None or not batch.is_applied:
            # Nothing ran, so there is nothing to undo. ⚠️ **Not an error**: a
            # reversal arriving for a batch this module never applied is
            # another consumer's batch, or one that was approved and never ran.
            return
        await self._segments.remove(workspace_id, batch.segment_id, batch.to_reverse())


__all__ = [
    "AccountSegmentRepository",
    "AddToSegmentInput",
    "AddToSegmentUseCase",
    "ApplySegmentBatchUseCase",
    "CreateSegmentInput",
    "CreateSegmentUseCase",
    "ProposeSegmentBatchInput",
    "ProposeSegmentBatchUseCase",
    "RenameSegmentInput",
    "RenameSegmentUseCase",
    "ReverseSegmentAdditionUseCase",
    "ReverseSegmentBatchUseCase",
    "SegmentBatchStore",
    "SegmentDirectoryUseCase",
    "SegmentsForAccountsUseCase",
    "REVERSIBLE_FOR",
]
