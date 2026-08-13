"""Reading and writing a workspace's labels — [TASK-466](../../../../docs/BACKLOG.md).

**Two tables, and no join in any query here.** The vocabulary is read whole
because it is small and bounded (`MAX_VOCABULARY`), and assignments are read
scoped to the accounts the caller already named — 📁 the port's own reason:
*"every account wearing this tag is an unbounded read this use case never
needs."*

### ⚠️ `workspace_id` is in every predicate, and RLS is still the authority

📁 [§8](../../../../CLAUDE.md): *"even with RLS in place, queries must still
explicitly filter by `workspace_id` as defense-in-depth."* ⛔ **Both, always** —
the filter here would not save a caller whose RLS context was never set, and
the policy would not save one whose session belonged to a colleague's request.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.commercial_profile.domain.account_tag import (
    AccountTag,
    TagTone,
    TagVocabulary,
)
from modules.commercial_profile.infrastructure.models import (
    AccountTagAssignmentModel,
    AccountTagModel,
)


class SqlAccountTagRepository:
    """The `AccountTagRepository` port, over Postgres."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def vocabulary(self, workspace_id: UUID) -> TagVocabulary:
        """Every tag the workspace has, ordered by name.

        ⚡ **Ordered in SQL rather than by the caller**, because the design
        renders the vocabulary as a list a person scans and *"whatever order
        the rows came back in"* is a hidden input (§2) — the same set would
        render differently between two requests.
        """
        rows = (
            await self._session.execute(
                select(AccountTagModel)
                .where(AccountTagModel.workspace_id == workspace_id)
                .order_by(AccountTagModel.name)
            )
        ).scalars()
        return TagVocabulary(
            tags=tuple(
                AccountTag(id=row.id, name=row.name, tone=TagTone(row.tone)) for row in rows
            )
        )

    async def create(self, workspace_id: UUID, tag: AccountTag, *, actor_id: UUID) -> None:
        self._session.add(
            AccountTagModel(
                id=tag.id,
                workspace_id=workspace_id,
                name=tag.name,
                tone=tag.tone.value,
                created_by=actor_id,
                updated_by=actor_id,
            )
        )
        await self._session.flush()

    async def rename(self, workspace_id: UUID, tag: AccountTag, *, actor_id: UUID) -> None:
        """Correct a label in place.

        ⛔ **The one `UPDATE` in this module**, and migration `0051` records
        why the grant exists here and nowhere else: a tag is a label a customer
        corrects, not a statement they publish.
        """
        row = (
            await self._session.execute(
                select(AccountTagModel).where(
                    AccountTagModel.workspace_id == workspace_id,
                    AccountTagModel.id == tag.id,
                )
            )
        ).scalar_one()
        row.name = tag.name
        row.tone = tag.tone.value
        row.updated_by = actor_id
        await self._session.flush()

    async def accounts_with(
        self, workspace_id: UUID, tag_id: UUID, *, among: tuple[UUID, ...]
    ) -> frozenset[UUID]:
        if not among:
            # ⛔ **`IN ()` is not valid SQL** and SQLAlchemy renders it as a
            # false predicate — correct, but a round trip to learn nothing.
            return frozenset()
        rows = (
            await self._session.execute(
                select(AccountTagAssignmentModel.account_id).where(
                    AccountTagAssignmentModel.workspace_id == workspace_id,
                    AccountTagAssignmentModel.tag_id == tag_id,
                    AccountTagAssignmentModel.account_id.in_(among),
                )
            )
        ).scalars()
        return frozenset(rows)

    async def assign(
        self, workspace_id: UUID, tag_id: UUID, accounts: tuple[UUID, ...], *, actor_id: UUID
    ) -> None:
        """Write the accounts the batch actually changed.

        ⛔ **A plain `INSERT`, with no conflict clause.** 🔴 `(tag_id,
        account_id)` is the primary key, so a duplicate raises — **and that is
        the behaviour the use case relies on rather than works around.** ⚡ An
        upsert here would let `ApplyTagUseCase` stop scoping its write to
        `changed` without anything failing, which is exactly how the
        attribution on an existing row would start moving to whoever last ran
        a batch.
        """
        self._session.add_all(
            [
                AccountTagAssignmentModel(
                    workspace_id=workspace_id,
                    tag_id=tag_id,
                    account_id=account_id,
                    created_by=actor_id,
                )
                for account_id in accounts
            ]
        )
        await self._session.flush()

    async def unassign(
        self, workspace_id: UUID, tag_id: UUID, accounts: tuple[UUID, ...]
    ) -> None:
        if not accounts:
            return
        await self._session.execute(
            delete(AccountTagAssignmentModel).where(
                AccountTagAssignmentModel.workspace_id == workspace_id,
                AccountTagAssignmentModel.tag_id == tag_id,
                AccountTagAssignmentModel.account_id.in_(accounts),
            )
        )
        await self._session.flush()

    async def tags_for(
        self, workspace_id: UUID, accounts: tuple[UUID, ...]
    ) -> dict[UUID, tuple[UUID, ...]]:
        """Which tags each of these accounts wears.

        ⚡ **The screen's hot read**, and the reason migration `0051` leads its
        index on `account_id`. ⛔ **One query for forty rows, never one per
        row** (§14) — the Companies table renders a page at a time and an
        N+1 here would be a defect at write time rather than a future task.
        """
        if not accounts:
            return {}
        rows = (
            await self._session.execute(
                select(
                    AccountTagAssignmentModel.account_id,
                    AccountTagAssignmentModel.tag_id,
                ).where(
                    AccountTagAssignmentModel.workspace_id == workspace_id,
                    AccountTagAssignmentModel.account_id.in_(accounts),
                )
            )
        ).all()
        held: dict[UUID, list[UUID]] = {}
        for account_id, tag_id in rows:
            held.setdefault(account_id, []).append(tag_id)
        return {account_id: tuple(tag_ids) for account_id, tag_ids in held.items()}
