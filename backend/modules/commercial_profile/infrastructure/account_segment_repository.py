"""Reading and writing a workspace's saved groupings — [TASK-1479](../../../../docs/BACKLOG.md) ⓶b.

⚠️ **Named `account_segment_repository.py` and not `segment_repository.py`,
which is taken.** 📁 That file is
[ADR-0041](../../../../docs/architecture/adr/0041-icp-aggregate.md)'s ICP —
a stored **predicate** — and this one is
[ADR-0411](../../../../docs/architecture/adr/0411-customer-organized-account-metadata.md)'s
**enumerated grouping**. 🔴 **Two files one letter apart would be exactly the
confusion [C-1503](../../../../docs/LANE_COORDINATION.md) was raised about**,
and [D-235](../../../../docs/DECISION_REGISTER.md) ② settled the vocabulary
without renaming the older one — so the newer one carries the distinguishing
word.

### ⚠️ `workspace_id` is in every predicate, and RLS is still the authority

📁 [§8](../../../../CLAUDE.md): *"even with RLS in place, queries must still
explicitly filter by `workspace_id` as defense-in-depth."* ⛔ **Both, always** —
the filter would not save a caller whose RLS context was never set, and the
policy would not save one whose session belonged to a colleague's request.
"""

from __future__ import annotations

from typing import Any, cast
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from modules.commercial_profile.domain.account_segment import (
    AccountSegment,
    SegmentAddition,
    SegmentBatch,
    SegmentDirectory,
)
from modules.commercial_profile.infrastructure.models import (
    AccountSegmentBatchModel,
    AccountSegmentMemberModel,
    AccountSegmentModel,
)


class SqlAccountSegmentRepository:
    """The `AccountSegmentRepository` port, over Postgres."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def directory(self, workspace_id: UUID) -> SegmentDirectory:
        """Every segment the workspace has, ordered by name.

        ⚡ **Ordered in SQL rather than by the caller.** The design renders the
        directory as a panel a person scans, and *"whatever order the rows came
        back in"* is a hidden input (§2) — the same set would render
        differently between two requests.
        """
        rows = (
            await self._session.execute(
                select(AccountSegmentModel)
                .where(AccountSegmentModel.workspace_id == workspace_id)
                .order_by(AccountSegmentModel.name)
            )
        ).scalars()
        return SegmentDirectory(
            segments=tuple(
                AccountSegment(id=row.segment_id, name=row.name) for row in rows
            )
        )

    async def create(
        self, workspace_id: UUID, segment: AccountSegment, *, actor_id: UUID
    ) -> None:
        self._session.add(
            AccountSegmentModel(
                segment_id=segment.id,
                workspace_id=workspace_id,
                name=segment.name,
                # ⚡ **Written from the domain's own property**, so the column
                # and the rule cannot disagree about what folding means.
                name_key=segment.key,
                created_by=actor_id,
                updated_by=actor_id,
            )
        )
        await self._session.flush()

    async def rename(
        self, workspace_id: UUID, segment: AccountSegment, *, actor_id: UUID
    ) -> None:
        """Correct a name in place. **The id does not move**, which is what
        keeps every account already in it."""
        row = (
            await self._session.execute(
                select(AccountSegmentModel).where(
                    AccountSegmentModel.workspace_id == workspace_id,
                    AccountSegmentModel.segment_id == segment.id,
                )
            )
        ).scalar_one()
        row.name = segment.name
        row.name_key = segment.key
        row.updated_by = actor_id
        await self._session.flush()

    async def members_among(
        self, workspace_id: UUID, segment_id: UUID, *, among: tuple[UUID, ...]
    ) -> frozenset[UUID]:
        """Which of these accounts are already in the segment.

        ⛔ **Scoped to the accounts the caller named**, never *"everything in
        this segment"* — the design draws a segment with 304 members and a bulk
        action over 41, and reading 304 to decide 41 is an unbounded read the
        use case does not need.
        """
        if not among:
            # ⛔ **`IN ()` is not valid SQL** and SQLAlchemy renders it as a
            # false predicate — correct, but a round trip to learn nothing.
            return frozenset()
        rows = (
            await self._session.execute(
                select(AccountSegmentMemberModel.account_id).where(
                    AccountSegmentMemberModel.workspace_id == workspace_id,
                    AccountSegmentMemberModel.segment_id == segment_id,
                    AccountSegmentMemberModel.account_id.in_(among),
                )
            )
        ).scalars()
        return frozenset(rows)

    async def add(
        self, workspace_id: UUID, segment_id: UUID, accounts: tuple[UUID, ...], *, actor_id: UUID
    ) -> None:
        """Write the accounts the batch actually added.

        ⛔ **A plain `INSERT`, with no conflict clause.** 🔴 `(segment_id,
        account_id)` is the primary key, so a duplicate raises — **and that is
        the behaviour the use case relies on rather than works around.** ⚡ An
        upsert here would let the use case stop scoping its write to `added`
        without anything failing, which is how `added_by` on a row somebody
        curated in June would start moving to whoever last ran a batch.
        """
        if not accounts:
            return
        self._session.add_all(
            [
                AccountSegmentMemberModel(
                    workspace_id=workspace_id,
                    segment_id=segment_id,
                    account_id=account_id,
                    added_by=actor_id,
                )
                for account_id in accounts
            ]
        )
        await self._session.flush()

    async def remove(
        self, workspace_id: UUID, segment_id: UUID, accounts: tuple[UUID, ...]
    ) -> None:
        if not accounts:
            return
        await self._session.execute(
            delete(AccountSegmentMemberModel).where(
                AccountSegmentMemberModel.workspace_id == workspace_id,
                AccountSegmentMemberModel.segment_id == segment_id,
                AccountSegmentMemberModel.account_id.in_(accounts),
            )
        )
        await self._session.flush()

    async def segments_for(
        self, workspace_id: UUID, accounts: tuple[UUID, ...]
    ) -> dict[UUID, tuple[UUID, ...]]:
        """Which segments each of these accounts is in.

        ⚡ **The screen's hot read**, and the reason migration `0055` leads an
        index on `(workspace_id, account_id)`. ⛔ **One query for forty rows,
        never one per row** (§14).
        """
        if not accounts:
            return {}
        rows = (
            await self._session.execute(
                select(
                    AccountSegmentMemberModel.account_id,
                    AccountSegmentMemberModel.segment_id,
                ).where(
                    AccountSegmentMemberModel.workspace_id == workspace_id,
                    AccountSegmentMemberModel.account_id.in_(accounts),
                )
            )
        ).all()
        held: dict[UUID, list[UUID]] = {}
        for account_id, segment_id in rows:
            held.setdefault(account_id, []).append(segment_id)
        return {account_id: tuple(segment_ids) for account_id, segment_ids in held.items()}

    async def counts(self, workspace_id: UUID) -> dict[UUID, int]:
        """How many accounts are in each segment.

        🔴 **Derived on read, never stored.** 📁 The design draws a count beside
        every segment name — *41*, *118*, *212* — and **a stored count is a
        second representation that goes stale the next time anybody adds an
        account** (§2). ⚡ **One grouped query for the whole panel**, which is
        the same N+1 rule `segments_for` follows.

        ⛔ **A segment with no members is absent from this map rather than
        present with `0`**, and the caller must not read absence as *"no such
        segment"* — the directory is what says which segments exist. **Two
        different questions, two different reads.**
        """
        rows = (
            await self._session.execute(
                select(
                    AccountSegmentMemberModel.segment_id,
                    func.count(AccountSegmentMemberModel.account_id),
                )
                .where(AccountSegmentMemberModel.workspace_id == workspace_id)
                .group_by(AccountSegmentMemberModel.segment_id)
            )
        ).all()
        return {segment_id: count for segment_id, count in rows}


class SqlSegmentBatchStore:
    """What one bulk *Add to segment* asked for, and what it added.

    ⚡ **A store rather than a repository method**, on the same reasoning
    `SqlTagBatchStore` records: the repository is asked *"what segments exist
    and who is in them"*, and this is asked *"what did that one batch do?"*
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(self, workspace_id: UUID, batch: SegmentBatch, *, actor_id: UUID) -> None:
        self._session.add(
            AccountSegmentBatchModel(
                batch_id=batch.batch_id,
                workspace_id=workspace_id,
                segment_id=batch.segment_id,
                requested=[str(account) for account in batch.requested],
                # ⛔ **`None`, not `[]`.** The batch has not applied, and the
                # difference is what tells *never approved* from *approved and
                # added nobody*.
                added=None,
                created_by=actor_id,
                updated_by=actor_id,
            )
        )
        await self._session.flush()

    async def get(self, workspace_id: UUID, batch_id: UUID) -> SegmentBatch | None:
        row = (
            await self._session.execute(
                select(AccountSegmentBatchModel).where(
                    AccountSegmentBatchModel.workspace_id == workspace_id,
                    AccountSegmentBatchModel.batch_id == batch_id,
                )
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        requested = tuple(UUID(account) for account in row.requested)
        if row.added is None:
            return SegmentBatch(
                batch_id=row.batch_id, segment_id=row.segment_id, requested=requested
            )
        added = tuple(UUID(account) for account in row.added)
        return SegmentBatch(
            batch_id=row.batch_id,
            segment_id=row.segment_id,
            requested=requested,
            applied=SegmentAddition(
                segment_id=row.segment_id,
                added=added,
                # ⚡ **Derived rather than stored**: everything requested that
                # was not added was already there. 📁 Storing both would be two
                # representations of one partition, and the one nobody writes
                # to is the one that goes wrong.
                unchanged=tuple(account for account in requested if account not in set(added)),
            ),
        )

    async def record_application(
        self, workspace_id: UUID, batch_id: UUID, application: SegmentAddition, *, actor_id: UUID
    ) -> None:
        """Write what running it actually did.

        ⛔ **Conditional on `added IS NULL`**, so a second application cannot
        overwrite the record a reversal depends on. 🔴 **The domain refuses it
        too** — `SegmentBatch.with_application` raises — **and this is the
        second guard, because the domain's answer depends on having read the
        row first and two requests can both read `None`.**
        """
        result = await self._session.execute(
            update(AccountSegmentBatchModel)
            .where(
                AccountSegmentBatchModel.workspace_id == workspace_id,
                AccountSegmentBatchModel.batch_id == batch_id,
                AccountSegmentBatchModel.added.is_(None),
            )
            .values(
                added=[str(account) for account in application.added],
                updated_by=actor_id,
            )
        )
        # `CursorResult` is what an UPDATE returns; the annotation on
        # `execute` is the wider `Result`, which has no `rowcount`.
        if cast("CursorResult[Any]", result).rowcount != 1:
            raise RuntimeError(
                f"Batch {batch_id} has already been applied, or does not belong to this workspace."
            )
        await self._session.flush()
