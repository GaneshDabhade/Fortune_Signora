"""What a customer does with their own labels — [TASK-466](../../../../docs/BACKLOG.md).

**Eight use cases, and `ApplyTagUseCase` is the one this row exists for.**

⚡ **The port is a Protocol declared here**, in the application layer that
consumes it, rather than in `infrastructure/` — 📁 [§6](../../../../CLAUDE.md):
*"a port belongs to the module that owns the language it represents"*, and
dependencies point inward.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol
from uuid import UUID, uuid4

from modules.commercial_profile.domain.account_tag import (
    AccountTag,
    AccountTagError,
    TagApplication,
    TagBatch,
    TagTone,
    TagVocabulary,
    apply_tag,
)


class AccountTagRepository(Protocol):
    """What persistence has to answer. **Six questions and no more.**

    ⛔ **`remove` is deliberately absent, and it was written and then cut.**
    [TASK-466](../../../../docs/BACKLOG.md) draws no delete control — the
    design's bulk bar offers *Add tag* and the table renders chips — **so a
    `remove` here would have been a method with no caller**, which is the
    class this lane has now found eight times. ⚠️ **Deleting a tag also
    cascades every assignment**, so the first caller should arrive with a
    confirmation designed for it rather than inherit one nobody specified.
    """

    async def vocabulary(self, workspace_id: UUID) -> TagVocabulary: ...

    async def create(self, workspace_id: UUID, tag: AccountTag, *, actor_id: UUID) -> None: ...

    async def rename(self, workspace_id: UUID, tag: AccountTag, *, actor_id: UUID) -> None: ...

    async def tags_for(
        self, workspace_id: UUID, accounts: tuple[UUID, ...]
    ) -> dict[UUID, tuple[UUID, ...]]:
        """⚡ **Which tags each of these accounts wears** — the Companies
        table's Tags column, one query for a page of rows."""
        ...

    async def accounts_with(
        self, workspace_id: UUID, tag_id: UUID, *, among: tuple[UUID, ...]
    ) -> frozenset[UUID]:
        """⚡ **Scoped by `among` deliberately.** The caller always knows which
        accounts it is asking about, and *"every account wearing this tag"* is
        an unbounded read this use case never needs."""
        ...

    async def assign(
        self, workspace_id: UUID, tag_id: UUID, accounts: tuple[UUID, ...], *, actor_id: UUID
    ) -> None: ...

    async def unassign(
        self, workspace_id: UUID, tag_id: UUID, accounts: tuple[UUID, ...]
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class CreateTagInput:
    workspace_id: UUID
    actor_id: UUID
    name: str
    tone: TagTone


class CreateTagUseCase:
    """Add a label to the workspace's vocabulary, or hand back the one that
    already answers to that name.

    ⚡ **Typing an existing name selects it rather than failing**, which is
    what makes the design's *Add tag* control safe to use twice — 📁 and it is
    the caller-side idempotence `TagVocabulary.added` deliberately refuses to
    fake, so *"was it created?"* has one answer per outcome.
    """

    def __init__(self, *, tags: AccountTagRepository) -> None:
        self._tags = tags

    async def execute(self, request: CreateTagInput) -> AccountTag:
        vocabulary = await self._tags.vocabulary(request.workspace_id)
        existing = vocabulary.find(request.name)
        if existing is not None:
            return existing
        tag = AccountTag(id=uuid4(), name=request.name, tone=request.tone)
        # Built through the aggregate so the bound and the fold are enforced
        # by the domain rather than by whichever caller remembered.
        vocabulary.added(tag)
        await self._tags.create(request.workspace_id, tag, actor_id=request.actor_id)
        return tag


@dataclass(frozen=True, slots=True)
class RenameTagInput:
    workspace_id: UUID
    actor_id: UUID
    tag_id: UUID
    name: str
    tone: TagTone


class RenameTagUseCase:
    """Correct a label. **Every account keeps it**, which is the whole reason
    a tag has an id."""

    def __init__(self, *, tags: AccountTagRepository) -> None:
        self._tags = tags

    async def execute(self, request: RenameTagInput) -> AccountTag:
        vocabulary = await self._tags.vocabulary(request.workspace_id)
        current = vocabulary.get(request.tag_id)
        if current is None:
            raise AccountTagError("That tag is not in this workspace.")
        updated = current.renamed(request.name).retoned(request.tone)
        # ⛔ **The uniqueness check runs against the whole vocabulary**, so
        # renaming *At risk* onto an existing *Churn risk* is refused here
        # rather than by an index error the customer would see as a 500.
        vocabulary.replaced(updated)
        await self._tags.rename(request.workspace_id, updated, actor_id=request.actor_id)
        return updated


@dataclass(frozen=True, slots=True)
class ApplyTagInput:
    workspace_id: UUID
    actor_id: UUID
    tag_id: UUID
    accounts: tuple[UUID, ...]


class ApplyTagUseCase:
    """🔴 **The operation the Action Batch applies** — 📁
    [ADR-0405](../../../../docs/architecture/adr/0405-an-action-is-approved-before-it-is-effective.md):
    *"the consuming domain owns performing the operation and implementing the
    inverse."*

    ⚡ **It returns what it CHANGED, not what it was asked to do**, because
    that is the only thing the inverse may read — 📁 `TagApplication`'s own
    reason, and the half [TASK-466](../../../../docs/BACKLOG.md) says is
    normally untested.
    """

    def __init__(self, *, tags: AccountTagRepository) -> None:
        self._tags = tags

    async def execute(self, request: ApplyTagInput) -> TagApplication:
        vocabulary = await self._tags.vocabulary(request.workspace_id)
        if vocabulary.get(request.tag_id) is None:
            raise AccountTagError("That tag is not in this workspace.")
        already = await self._tags.accounts_with(
            request.workspace_id, request.tag_id, among=request.accounts
        )
        application = apply_tag(
            request.tag_id, accounts=request.accounts, already_tagged=already
        )
        # ⛔ **Only the accounts that change are written.** Re-inserting a row
        # that exists would either fail on the primary key or, with an upsert,
        # move `created_by` to whoever ran the batch — losing who first said it.
        if application.changed:
            await self._tags.assign(
                request.workspace_id,
                request.tag_id,
                application.changed,
                actor_id=request.actor_id,
            )
        return application


class ReverseTagApplicationUseCase:
    """Take a batch back. 📁 [TASK-466](../../../../docs/BACKLOG.md): *"a batch
    that applies but cannot be reversed in the window is a defect, not a
    limitation."*

    ⛔ **It takes the `TagApplication` and never a list of accounts**, so a
    caller cannot reverse something the batch did not do. ⚡ **That is the type
    doing the work**: there is no parameter through which *"untag all
    forty-one"* could be expressed.
    """

    def __init__(self, *, tags: AccountTagRepository) -> None:
        self._tags = tags

    async def execute(self, workspace_id: UUID, application: TagApplication) -> None:
        restore = application.inverse()
        if not restore:
            return
        await self._tags.unassign(workspace_id, application.tag_id, restore)


class TagsForAccountsUseCase:
    """Which tags a page of accounts wears.

    ⚡ **The Companies table's Tags column, and the reason it is its own use
    case rather than a field on the accounts list**: 📁 an account is
    `knowledge_graph`'s entity and a tag is this module's, so folding one into
    the other's response would be a cross-module dependency
    ([§5](../../../../CLAUDE.md)) bought for a column. **The screen reads both
    and joins them, which is the boundary working rather than an omission.**
    """

    def __init__(self, *, tags: AccountTagRepository) -> None:
        self._tags = tags

    async def execute(
        self, workspace_id: UUID, accounts: tuple[UUID, ...]
    ) -> dict[UUID, tuple[UUID, ...]]:
        return await self._tags.tags_for(workspace_id, accounts)


class TagBatchStore(Protocol):
    """Where a bulk batch's own payload lives.

    🔴 **A consumer of the Action Batch is forced to have one.** 📁
    `ActionBatchView` publishes *"`item_count` and not the items… what each
    item *means* belongs to the domain that proposed it"* — so the lifecycle
    module knows a batch covers forty-one things and nothing about what.
    """

    async def get(self, workspace_id: UUID, batch_id: UUID) -> TagBatch | None: ...

    async def record_application(
        self, workspace_id: UUID, batch_id: UUID, application: TagApplication
    ) -> None: ...


class ApplyTagBatchUseCase:
    """Run a bulk *Add tag* because its Action Batch was applied.

    ⚡ **Driven by an event, not by a request.** 📁 [§9](../../../../CLAUDE.md):
    inter-module communication defaults to domain events, and the handler
    reads a generic envelope — **this module imports nothing from
    `action_batch`.**

    ⛔ **A batch this module did not propose is not an error.** The Action
    Batch is a shared lifecycle and other domains will use it, so *"not mine"*
    is the ordinary case: **the handler returns and stays silent** rather than
    raising into a retry loop that can never succeed.

    ⚠️ **Idempotent on re-delivery, because it has to be.** 📁 [§9](../../../../CLAUDE.md):
    *"event consumers must be idempotent on `event_id`"* — a second delivery
    of *applied* must not tag anything again, and **must not overwrite the
    record a reversal depends on.**
    """

    def __init__(self, *, tags: AccountTagRepository, batches: TagBatchStore) -> None:
        self._tags = tags
        self._batches = batches

    async def execute(self, workspace_id: UUID, batch_id: UUID, *, actor_id: UUID) -> None:
        batch = await self._batches.get(workspace_id, batch_id)
        if batch is None or batch.is_applied:
            # ⛔ **Both branches are ordinary.** `None` is somebody else's
            # batch; `is_applied` is this event arriving twice.
            return
        application = await ApplyTagUseCase(tags=self._tags).execute(
            ApplyTagInput(
                workspace_id=workspace_id,
                actor_id=actor_id,
                tag_id=batch.tag_id,
                accounts=batch.requested,
            )
        )
        await self._batches.record_application(workspace_id, batch_id, application)


class ReverseTagBatchUseCase:
    """Take a bulk *Add tag* back because its Action Batch was reversed.

    🔴 **It reads what the batch CHANGED and never what it requested.** 📁 If
    three of the forty-one were tagged before the batch, taking it back must
    leave those three — **they were not this batch's doing.**

    ⚠️ **The window is `action_batch`'s to enforce, not this module's.** 📁
    `has_settled` lives there and the aggregate refuses a late reversal, so a
    second implementation of the window here would be *behaviour existing
    twice* (§2) — **and the two would eventually disagree about whether a
    customer may still undo something.**
    """

    def __init__(self, *, tags: AccountTagRepository, batches: TagBatchStore) -> None:
        self._tags = tags
        self._batches = batches

    async def execute(self, workspace_id: UUID, batch_id: UUID) -> None:
        batch = await self._batches.get(workspace_id, batch_id)
        if batch is None or batch.applied is None:
            # ⛔ **Not mine, or never applied.** A batch that never applied has
            # nothing to undo, and reversing it must not reach `requested`.
            return
        await ReverseTagApplicationUseCase(tags=self._tags).execute(
            workspace_id, batch.applied
        )


#: 📁 **The only batch window the design states** —
#: `Fortune Signora Companies.dc.html`: ***"every import is reversible for 24
#: hours as a single named batch."***
#:
#: ⚠️ **It says *import*, and a bulk tag is a different act.** ⛔ **Applying it
#: here is an inference rather than a citation**, and it is named as a constant
#: with this note so a ruling is one edit — 📁
#: [C-1506](../../../../docs/LANE_COORDINATION.md).
#:
#: ⛔ **`None` was the alternative and it is worse**: it means *reversal was
#: never offered*, and [TASK-466](../../../../docs/BACKLOG.md) says in terms
#: that *"a batch that applies but cannot be reversed in the window is a
#: defect, not a limitation."*
REVERSIBLE_FOR = timedelta(hours=24)


class ActionBatchProposer(Protocol):
    """⚡ **`action_batch`'s published write, narrowed to what this module
    uses** — 📁 [D-235](../../../../docs/DECISION_REGISTER.md) ①.

    ⛔ **Restated here as a Protocol rather than imported as one**, so the use
    case below depends on a shape rather than on another module's file — 📁
    [§6](../../../../CLAUDE.md): *dependencies point inward*, and the
    composition root supplies the real adapter.
    """

    async def propose(
        self,
        *,
        workspace_id: UUID,
        name: str,
        item_count: int,
        proposed_by: UUID,
        reversible_for: timedelta | None = None,
    ) -> UUID: ...


class TagBatchRecorder(Protocol):
    """Where this module writes its own half of a proposed batch."""

    async def record(self, workspace_id: UUID, batch: TagBatch, *, actor_id: UUID) -> None: ...


@dataclass(frozen=True, slots=True)
class ProposeTagBatchInput:
    workspace_id: UUID
    actor_id: UUID
    tag_id: UUID
    accounts: tuple[UUID, ...]


class ProposeTagBatchUseCase:
    """🔴 **Ask for a bulk *Add tag*, as one named thing somebody approves.**

    📁 [D-235](../../../../docs/DECISION_REGISTER.md) ①: *"`propose` creates
    the batch and its payload atomically… ⛔ no batch-without-payload state is
    representable."*

    ⚡ **Both writes happen on one session**, which is what makes that true. ⛔
    **Two endpoints called in sequence would make the broken state
    representable** — the first succeeding and the second failing leaves an
    approvable action that applies nothing, which is
    [ADR-0405](../../../../docs/architecture/adr/0405-an-action-is-approved-before-it-is-effective.md)'s
    *no partial state* broken by construction.

    ⛔ **It proposes and does not apply.** 📁 Approval is a human decision on a
    screen; the batch takes effect when somebody accepts it, and
    `action_batch.applied` is what brings the work back here.
    """

    def __init__(
        self,
        *,
        tags: AccountTagRepository,
        batches: TagBatchRecorder,
        proposer: ActionBatchProposer,
    ) -> None:
        self._tags = tags
        self._batches = batches
        self._proposer = proposer

    async def execute(self, request: ProposeTagBatchInput) -> UUID:
        vocabulary = await self._tags.vocabulary(request.workspace_id)
        tag = vocabulary.get(request.tag_id)
        if tag is None:
            raise AccountTagError("That tag is not in this workspace.")

        # ⚡ **De-duplicated BEFORE the count is taken**, so the name a customer
        # approves says how many companies it touches rather than how many rows
        # they clicked. 📁 A table offering *Select all* on top of an existing
        # selection is exactly how a row arrives twice.
        accounts = tuple(dict.fromkeys(request.accounts))
        if not accounts:
            raise AccountTagError("A batch has to name at least one account.")

        batch_id = await self._proposer.propose(
            workspace_id=request.workspace_id,
            # 📁 **The customer's own words**, so a history reads as a record of
            # decisions rather than a list of identifiers.
            name=f"Tag {len(accounts)} companies “{tag.name}”",
            item_count=len(accounts),
            proposed_by=request.actor_id,
            reversible_for=REVERSIBLE_FOR,
        )
        await self._batches.record(
            request.workspace_id,
            TagBatch(batch_id=batch_id, tag_id=request.tag_id, requested=accounts),
            actor_id=request.actor_id,
        )
        return batch_id
