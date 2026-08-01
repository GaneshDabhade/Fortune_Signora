"""What this module needs from the outside, in its own vocabulary.

Two ports, and they are split along the same line the tables are: one stores
what a run *produced*, the other what a person *asked for*. An artifact is
written once and never touched again; a request accumulates history. Folding
them into one repository would put an append-only writer and a history reader
behind a single name and lose exactly the distinction that keeps the artifact
immutable.

Retrieval already has its own port in `domain/retrieval.py`, where it belongs —
it represents this module's language. These are storage, which is machinery
rather than vocabulary, so they live here.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from modules.ai_research_engine.domain.request import (
    ResearchRequest,
    ResearchRequestState,
)
from modules.ai_research_engine.domain.research import (
    ResearchFinding,
    ResearchSynthesis,
    ResearchTask,
)


class ResearchRepository(Protocol):
    """Stores one completed run. **There is no update, and no partial save.**

    A task, its findings and its synthesis describe one run and are written
    together: a task whose findings are missing looks like a run that found
    nothing, and a synthesis whose findings are missing cites rows that do not
    exist.
    """

    async def save(
        self,
        task: ResearchTask,
        findings: tuple[ResearchFinding, ...],
        synthesis: ResearchSynthesis,
    ) -> None: ...


class ResearchArtifactReader(Protocol):
    """Reading back one completed run.

    Separate from `ResearchRepository` rather than a method on it, because
    writing an artifact and reading one are wanted by different callers: the
    worker writes and never reads, the API reads and must never be able to
    write. A single port would hand each of them the other's capability.
    """

    async def by_task(
        self, workspace_id: UUID, task_id: UUID
    ) -> tuple[ResearchTask, tuple[ResearchFinding, ...], ResearchSynthesis] | None: ...


class ResearchRequestRepository(Protocol):
    """A request and its history. **Append-only, like the workflow it mirrors.**

    There is no `update`, and the app role holds no `UPDATE` grant on either
    table — so a status that could be quietly rewritten is unrepresentable
    here and rejected by the database as well.

    Every read returns the request **with its current state**, never one
    without the other. A request whose status a caller has to fetch separately
    is one a caller can forget to fetch, and the two things this module is
    asked are *"is it running?"* and *"is there something to read?"* — both of
    which are answered by the state.
    """

    async def open(self, request: ResearchRequest, state: ResearchRequestState) -> None:
        """Record the ask and its first state, in one unit of work."""
        ...

    async def record(self, state: ResearchRequestState) -> None:
        """Append the next state. Never replaces the one before it."""
        ...

    async def by_id(
        self, workspace_id: UUID, request_id: UUID
    ) -> tuple[ResearchRequest, ResearchRequestState] | None: ...

    async def in_flight_for(
        self, workspace_id: UUID, entity_id: UUID
    ) -> tuple[ResearchRequest, ResearchRequestState] | None:
        """The unfinished request for this account, if there is one."""
        ...

    async def latest_for(
        self, workspace_id: UUID, entity_id: UUID
    ) -> tuple[ResearchRequest, ResearchRequestState] | None:
        """The most recent request for this account, finished or not."""
        ...

    async def generations(self, workspace_id: UUID, entity_id: UUID) -> int:
        """How many requests this account has had.

        The next request takes this as its generation, and the unique
        constraint decides which of two simultaneous askers gets it — the same
        device, and the same method name, as `OpportunityRepository`.
        """
        ...
