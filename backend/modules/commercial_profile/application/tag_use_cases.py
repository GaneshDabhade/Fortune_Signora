"""What a customer does with their own labels — [TASK-466](../../../../docs/BACKLOG.md).

**Four use cases, and the third is the one this row exists for.**

⚡ **The port is a Protocol declared here**, in the application layer that
consumes it, rather than in `infrastructure/` — 📁 [§6](../../../../CLAUDE.md):
*"a port belongs to the module that owns the language it represents"*, and
dependencies point inward.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID, uuid4

from modules.commercial_profile.domain.account_tag import (
    AccountTag,
    AccountTagError,
    TagApplication,
    TagTone,
    TagVocabulary,
    apply_tag,
)


class AccountTagRepository(Protocol):
    """What persistence has to answer. **Six questions and no more.**"""

    async def vocabulary(self, workspace_id: UUID) -> TagVocabulary: ...

    async def create(self, workspace_id: UUID, tag: AccountTag, *, actor_id: UUID) -> None: ...

    async def rename(self, workspace_id: UUID, tag: AccountTag, *, actor_id: UUID) -> None: ...

    async def remove(self, workspace_id: UUID, tag_id: UUID) -> None: ...

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
