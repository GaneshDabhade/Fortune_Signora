"""The ports the Action Batch use cases depend on."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from modules.action_batch.domain.batch import ActionBatch


class ActionBatchRepository(Protocol):
    """Persistence for a batch and the log of what happened to it.

    ⛔ **There is no `update`, and there never will be.** The store is
    append-only in the database (no `UPDATE` grant, migration `0042`) and this
    port refuses one too — a method offering an edit is a method somebody will
    eventually call, and an approval that can be edited is an approval nobody
    can cite (§2).

    **`record` takes the batch *after* the transition**, not an id and a verb.
    The domain has already refused every illegal move by the time anything
    reaches here, so the guards live in one place rather than being
    re-implemented in SQL.
    """

    async def add(self, batch: ActionBatch, *, actor_id: UUID) -> None:
        """Store a newly proposed batch. **Its identity, and nothing else.**

        The proposal is not a transition — it is how a batch begins — so this
        writes no log row.
        """
        ...

    async def record(self, batch: ActionBatch, *, actor_id: UUID) -> None:
        """Append whatever the last transition was.

        Takes the whole aggregate because **which transition happened is
        derived from it**, never passed alongside it: a caller that could name
        the verb independently of the state could name the wrong one.
        """
        ...

    async def get(self, workspace_id: UUID, batch_id: UUID) -> ActionBatch | None:
        """Rebuild a batch by replaying its log. `None` when there is no such
        batch **in this workspace** — a batch in another one is not found
        rather than forbidden, which is the same rule §7 applies to
        workspaces."""
        ...
