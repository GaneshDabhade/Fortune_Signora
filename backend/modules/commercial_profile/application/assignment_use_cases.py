"""Putting a member on an account, and taking it back.

**[TASK-1479](../../../../docs/BACKLOG.md) slice ⓶.**

**[ADR-0411](../../../../docs/architecture/adr/0411-customer-organized-account-metadata.md)'s
second capability.** The domain decides what a reassignment *is*; this decides
**who may be named** and hands the batch machinery an operation with an
inverse.

### 🔴 The membership check is the point of the whole design

📁 The ruling: *"A reference to a workspace **member**, not free text. A person
who leaves must not leave a dangling string."*

⛔ **A reference that is never verified is free text with a `UUID` type.** So
the assignment refuses a user who is not a member of this workspace, **before
anything is written** — and it asks
[`WorkspaceQueryPort`](../../workspace_tenancy/public/query_port.py), which is
the one approved synchronous cross-module read for exactly this
(`05-module-dependencies.md` line 60, *sync, for workspace scope*).

⚠️ **This module keeps no copy of a membership.** A cached one would be a
second representation of a tenancy fact ([§2](../../../../CLAUDE.md)), and the
copy would be the one that was wrong on the day somebody left.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from modules.action_batch.public import ActionBatchProposer
from modules.commercial_profile.application.tag_use_cases import REVERSIBLE_FOR
from modules.commercial_profile.domain.account_assignment import (
    AccountAssignment,
    AccountRole,
    AssignmentBatch,
    AssignmentError,
    Reassignment,
)
from modules.workspace_tenancy.public.query_port import WorkspaceQueryPort


class AccountAssignmentRepository(Protocol):
    """What this module needs from storage. **Owned here, implemented in
    `infrastructure/`** — a port belongs to the module that owns the language
    it represents (§6)."""

    async def for_accounts(
        self, workspace_id: UUID, account_ids: tuple[UUID, ...]
    ) -> tuple[AccountAssignment, ...]: ...

    async def assign(
        self,
        workspace_id: UUID,
        account_ids: tuple[UUID, ...],
        *,
        role: AccountRole,
        member_user_id: UUID,
        actor_id: UUID,
    ) -> Reassignment: ...

    async def restore(
        self,
        workspace_id: UUID,
        previous: tuple[tuple[UUID, UUID | None], ...],
        *,
        role: AccountRole,
        assigned_to: UUID | None,
        actor_id: UUID,
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class AssignAccountsInput:
    workspace_id: UUID
    account_ids: tuple[UUID, ...]
    role: AccountRole
    member_user_id: UUID
    actor_id: UUID


class NotAWorkspaceMemberError(AssignmentError):
    """The person named is not a member of this workspace.

    ⚠️ **A distinct error rather than a generic refusal**, because the two
    reasons an assignment fails are answered by different people: *"this
    account does not exist"* is the caller's mistake, and *"this person is not
    on your team"* is something the customer can act on — 📁 §10's truthful
    -attribution rule, one layer along.
    """

    def __init__(self, member_user_id: UUID) -> None:
        super().__init__(
            f"{member_user_id} is not a member of this workspace. An account owner is a "
            "reference to a member, so a person who leaves does not leave a dangling "
            "name — which only holds if the reference is checked when it is made."
        )


class AssignAccounts:
    """Put one member on a selection of accounts."""

    def __init__(
        self,
        *,
        repository: AccountAssignmentRepository,
        workspaces: WorkspaceQueryPort,
    ) -> None:
        self._repository = repository
        # The one approved synchronous cross-module read
        # (05-module-dependencies.md). Membership is a tenancy fact, and this
        # module must not keep its own copy of one.
        self._workspaces = workspaces

    async def execute(self, request: AssignAccountsInput) -> Reassignment:
        """Assign, and return **what moved** so the caller can undo exactly it.

        ⛔ **Membership first, and before any write.** Verifying afterwards
        would mean a rejected assignment had already changed rows, and the
        caller would be relying on a transaction rollback to undo something the
        domain should never have accepted.
        """
        if not request.account_ids:
            # ⛔ **Refused rather than answered with an empty result.** *"Assign
            # nobody to nothing"* is a caller defect, and returning a
            # successful no-op would let a broken selection look like a
            # completed action — the shape P-A names one layer up.
            raise AssignmentError(
                "an assignment names no accounts. A selection that resolved to nothing "
                "is a defect in the caller, and reporting success for it would tell "
                "somebody their accounts were assigned."
            )

        membership = await self._workspaces.get_membership(
            request.workspace_id, request.member_user_id
        )
        if membership is None:
            raise NotAWorkspaceMemberError(request.member_user_id)

        return await self._repository.assign(
            request.workspace_id,
            request.account_ids,
            role=request.role,
            member_user_id=request.member_user_id,
            actor_id=request.actor_id,
        )


class ReverseAssignment:
    """Put back exactly what an assignment changed.

    ⛔ **No membership check here, and the omission is deliberate.** The
    previous holders were members when they were assigned; **if one has since
    left, restoring them is still the correct reversal** — the alternative is a
    reversal that silently declines to undo part of what it was asked to undo.

    ⚠️ **A departed member's accounts are a separate question with a separate
    answer**, and answering it inside a reversal would make *undo* mean two
    things.
    """

    def __init__(self, *, repository: AccountAssignmentRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        workspace_id: UUID,
        reassignment: Reassignment,
        *,
        actor_id: UUID,
    ) -> None:
        await self._repository.restore(
            workspace_id,
            reassignment.inverse(),
            role=reassignment.role,
            # ⚡ **The condition travels with the reversal.** Undoing *my*
            # change is a different operation from restoring a past state, and
            # only the first is what a customer pressing *take it back* asked
            # for.
            assigned_to=reassignment.assigned_to,
            actor_id=actor_id,
        )


@dataclass(frozen=True, slots=True)
class ProposeAssignmentBatchInput:
    workspace_id: UUID
    actor_id: UUID
    account_ids: tuple[UUID, ...]
    role: AccountRole
    member_user_id: UUID


class ProposeAssignmentBatch:
    """🔴 **Ask for a bulk owner change, as one named thing somebody approves.**

    ⛔ **It proposes and does not assign.** 📁 ADR-0405:
    *intelligence suggests; humans commit* — **reassigning forty accounts is
    exactly the shape that should be approved before it is effective**, and the
    tag batch established the pattern one capability over.

    ⚡ **Membership is verified HERE, at proposal time, and again when the batch
    applies.** ⚠️ **Not redundant**: a proposal a customer cannot act on is
    worth refusing immediately, and a member who leaves between proposal and
    approval must not be assigned on acceptance. **Two moments, two checks,
    because the answer can differ between them.**
    """

    def __init__(
        self,
        *,
        workspaces: WorkspaceQueryPort,
        proposer: ActionBatchProposer,
    ) -> None:
        self._workspaces = workspaces
        self._proposer = proposer

    async def execute(self, request: ProposeAssignmentBatchInput) -> UUID:
        # ⚡ **De-duplicated BEFORE the count is taken**, so the name a customer
        # approves says how many companies it touches rather than how many rows
        # they clicked — the same reason the tag batch does it.
        accounts = tuple(dict.fromkeys(request.account_ids))
        if not accounts:
            raise AssignmentError("A batch has to name at least one account.")

        membership = await self._workspaces.get_membership(
            request.workspace_id, request.member_user_id
        )
        if membership is None:
            raise NotAWorkspaceMemberError(request.member_user_id)

        return await self._proposer.propose(
            workspace_id=request.workspace_id,
            # 📁 **The customer's own words.** ⛔ Not the member's name — this
            # module holds none, by ADR-0411's own design, and inventing one
            # here would be the duplicated identity the reference exists to
            # avoid.
            name=(
                f"Change the {request.role.value} on {len(accounts)} "
                f"compan{'y' if len(accounts) == 1 else 'ies'}"
            ),
            item_count=len(accounts),
            proposed_by=request.actor_id,
            reversible_for=REVERSIBLE_FOR,
        )


class AssignmentBatchStore(Protocol):
    """Where this module reads and writes its own half of a proposed batch."""

    async def record(
        self, workspace_id: UUID, batch: AssignmentBatch, *, actor_id: UUID
    ) -> None: ...

    async def by_id(
        self, workspace_id: UUID, batch_id: UUID
    ) -> AssignmentBatch | None: ...

    async def record_applied(
        self,
        workspace_id: UUID,
        batch_id: UUID,
        moved: Reassignment,
        *,
        actor_id: UUID,
    ) -> None: ...


class ApplyAssignmentBatch:
    """Assign the accounts the batch named, **because somebody approved it.**

    ⛔ **The accounts come from this module's own row, never from the event.**
    *Events carry identity; ports carry payload* — a replayed `applied` cannot
    act on a selection that has since changed.

    ⚡ **Membership is verified again here.** 📁 It was checked at proposal
    time, and **a member who leaves between proposing and approving must not be
    assigned on acceptance** — two moments, two checks, because the answer can
    differ between them.
    """

    def __init__(
        self,
        *,
        repository: AccountAssignmentRepository,
        batches: AssignmentBatchStore,
        workspaces: WorkspaceQueryPort,
    ) -> None:
        self._repository = repository
        self._batches = batches
        self._workspaces = workspaces

    async def execute(self, workspace_id: UUID, batch_id: UUID, *, actor_id: UUID) -> None:
        batch = await self._batches.by_id(workspace_id, batch_id)
        if batch is None:
            # **A batch this module did not propose is not an error.** Another
            # domain's action is simply not ours.
            return

        membership = await self._workspaces.get_membership(
            workspace_id, batch.member_user_id
        )
        if membership is None:
            raise NotAWorkspaceMemberError(batch.member_user_id)

        moved = await self._repository.assign(
            workspace_id,
            batch.requested,
            role=batch.role,
            member_user_id=batch.member_user_id,
            actor_id=actor_id,
        )
        await self._batches.record_applied(workspace_id, batch_id, moved, actor_id=actor_id)


class ReverseAssignmentBatch:
    """Undo exactly what the batch moved, **because it was taken back.**

    ⚠️ **The reversal window is `action_batch`'s and is not re-checked here.**
    📁 `has_settled` lives there and the aggregate refuses a late reversal, so
    **a second implementation of the window would be behaviour existing twice**
    (§2) — and the two would eventually disagree about whether a customer may
    still undo something.
    """

    def __init__(
        self,
        *,
        repository: AccountAssignmentRepository,
        batches: AssignmentBatchStore,
    ) -> None:
        self._repository = repository
        self._batches = batches

    async def execute(self, workspace_id: UUID, batch_id: UUID, *, actor_id: UUID) -> None:
        batch = await self._batches.by_id(workspace_id, batch_id)
        if batch is None or batch.moved is None:
            # ⛔ **A batch that never applied has nothing to undo**, and that is
            # not a failure — it is the `None` the store deliberately keeps
            # distinct from an empty list.
            return

        await self._repository.restore(
            workspace_id,
            batch.to_reverse(),
            role=batch.role,
            assigned_to=batch.moved.assigned_to,
            actor_id=actor_id,
        )


__all__ = [
    "AccountAssignmentRepository",
    "ApplyAssignmentBatch",
    "AssignmentBatchStore",
    "AssignAccounts",
    "AssignAccountsInput",
    "NotAWorkspaceMemberError",
    "ProposeAssignmentBatch",
    "ProposeAssignmentBatchInput",
    "ReverseAssignment",
    "ReverseAssignmentBatch",
]
