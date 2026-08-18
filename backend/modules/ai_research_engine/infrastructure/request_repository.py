"""Storing a research request and reading a completed run back.

Two adapters, matching the two ports. They live together because they share
one session and one workspace scope, and apart from `repository.py` because
that one only ever writes.

**Nothing is updated.** `signora_app` holds no `UPDATE` grant on either request
table, so the absence of an update method here is a second lock rather than the
only one. Progress is an append: the current state is the highest `sequence`,
which cannot invert the way a `supersedes IS NULL` predicate does (`B-001`).

**Every query names `workspace_id` explicitly**, even though RLS is the
authoritative control. Defence in depth, per CLAUDE.md §8 — and the reader here
runs on an API request's session where a filter is the thing an engineer can
see while reviewing.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from modules.ai_platform.public import AIVendor, EvidenceRef, GroundedStatement
from modules.ai_research_engine.domain.request import (
    IN_FLIGHT,
    ResearchRequest,
    ResearchRequestState,
    ResearchStatus,
)
from modules.ai_research_engine.domain.research import (
    PAYLOAD_VERSION,
    ResearchFinding,
    ResearchSynthesis,
    ResearchTask,
)
from modules.ai_research_engine.infrastructure.models import (
    ResearchFindingModel,
    ResearchSynthesisModel,
    ResearchTaskModel,
)
from modules.ai_research_engine.infrastructure.repository import (
    SYSTEM_USER_ID,
    attributes_of,
    cited_of,
)
from modules.ai_research_engine.infrastructure.request_models import (
    ResearchRequestModel,
    ResearchRequestStateModel,
)

#: Statuses a request has not finished in, as the strings the column holds.
#: Derived from the domain's own set rather than written out, so a status added
#: without classifying it cannot silently read as finished here.
IN_FLIGHT_VALUES: tuple[str, ...] = tuple(sorted(s.value for s in IN_FLIGHT))


class SqlResearchRequestRepository:
    """A request and its append-only history."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def open(self, request: ResearchRequest, state: ResearchRequestState) -> None:
        self._session.add(
            ResearchRequestModel(
                id=request.id,
                workspace_id=request.workspace_id,
                entity_id=request.entity_id,
                opportunity_id=request.opportunity_id,
                requested_by=request.requested_by,
                requested_at=request.requested_at,
                generation=request.generation,
                # Audit attribution is the requester, not the system: this is
                # the one row in the module a human authored.
                created_by=request.requested_by,
                updated_by=request.requested_by,
            )
        )
        self._session.add(self._state_row(state, entity_id=request.entity_id))
        await self._session.flush()

    async def record(self, state: ResearchRequestState) -> None:
        entity_id = await self._session.scalar(
            select(ResearchRequestModel.entity_id).where(
                ResearchRequestModel.workspace_id == state.workspace_id,
                ResearchRequestModel.id == state.request_id,
            )
        )
        if entity_id is None:
            raise LookupError(
                f"research request {state.request_id} does not exist in this workspace, so a "
                "state for it would be history belonging to nothing."
            )
        self._session.add(self._state_row(state, entity_id=entity_id))
        await self._session.flush()

    async def generations(self, workspace_id: UUID, entity_id: UUID) -> int:
        return (
            await self._session.scalar(
                select(func.count())
                .select_from(ResearchRequestModel)
                .where(
                    ResearchRequestModel.workspace_id == workspace_id,
                    ResearchRequestModel.entity_id == entity_id,
                )
            )
        ) or 0

    async def by_id(
        self, workspace_id: UUID, request_id: UUID
    ) -> tuple[ResearchRequest, ResearchRequestState] | None:
        row = await self._session.scalar(
            select(ResearchRequestModel).where(
                ResearchRequestModel.workspace_id == workspace_id,
                ResearchRequestModel.id == request_id,
            )
        )
        if row is None:
            return None
        state = await self._current_state(workspace_id, request_id)
        if state is None:
            return None
        return _request(row), state

    async def in_flight_for(
        self, workspace_id: UUID, entity_id: UUID
    ) -> tuple[ResearchRequest, ResearchRequestState] | None:
        """The unfinished request for this account.

        **The newest unfinished state**, and the ordering is load-bearing:
        history is append-only, so a request that has begun running still has
        its `requested` row sitting behind it. Reading either one would answer
        the question; reading the *latest* is what makes the status shown match
        the status the domain will transition from.
        """
        state_row = await self._session.scalar(
            select(ResearchRequestStateModel)
            .where(
                ResearchRequestStateModel.workspace_id == workspace_id,
                ResearchRequestStateModel.entity_id == entity_id,
                ResearchRequestStateModel.status.in_(IN_FLIGHT_VALUES),
            )
            .order_by(ResearchRequestStateModel.sequence.desc())
            .limit(1)
        )
        if state_row is None:
            return None
        # An account whose newest request has settled still has old in-flight
        # rows in its history — they belong to a finished request. Confirming
        # against the *current* state is what stops a completed run reading as
        # one still in progress.
        current = await self._current_state(workspace_id, state_row.request_id)
        if current is None or current.status not in IN_FLIGHT:
            return None
        request_row = await self._session.scalar(
            select(ResearchRequestModel).where(
                ResearchRequestModel.workspace_id == workspace_id,
                ResearchRequestModel.id == state_row.request_id,
            )
        )
        if request_row is None:
            return None
        return _request(request_row), current

    async def latest_for(
        self, workspace_id: UUID, entity_id: UUID
    ) -> tuple[ResearchRequest, ResearchRequestState] | None:
        row = await self._session.scalar(
            select(ResearchRequestModel)
            .where(
                ResearchRequestModel.workspace_id == workspace_id,
                ResearchRequestModel.entity_id == entity_id,
            )
            .order_by(ResearchRequestModel.generation.desc())
            .limit(1)
        )
        if row is None:
            return None
        state = await self._current_state(workspace_id, row.id)
        if state is None:
            return None
        return _request(row), state

    async def recent(
        self, workspace_id: UUID, *, limit: int
    ) -> tuple[tuple[ResearchRequest, ResearchRequestState], ...]:
        """Every account's latest ask, newest first — one query, not N+1.

        **The current state is the highest `sequence`**, exactly as
        `_current_state` reads it for one request. Asking that per request
        would be one round trip per row for a list; a window function ranks
        every request's history once and keeps the top of each.

        ⚡ **Ordered by when it was ASKED, not by when it last moved.** A run
        that failed at 04:00 and one requested at 09:00 are two different
        answers to *"what has Signora been doing?"*, and ordering by the state
        would put a long-finished request above a fresh one every time its
        history gained a row.
        """
        ranked = (
            select(
                ResearchRequestStateModel,
                func.row_number()
                .over(
                    partition_by=ResearchRequestStateModel.request_id,
                    order_by=ResearchRequestStateModel.sequence.desc(),
                )
                .label("rank"),
            )
            .where(ResearchRequestStateModel.workspace_id == workspace_id)
            .subquery()
        )
        # **The subquery mapped back to the entity**, so the row this method
        # returns is built by `_state` — the same function `by_id`,
        # `latest_for` and `in_flight_for` all go through. A second hand-rolled
        # mapping here would be a second place for a column rename to break.
        current = aliased(ResearchRequestStateModel, ranked)
        rows = (
            await self._session.execute(
                select(ResearchRequestModel, current)
                .join(ranked, ranked.c.request_id == ResearchRequestModel.id)
                .where(
                    ResearchRequestModel.workspace_id == workspace_id,
                    ranked.c.rank == 1,
                )
                .order_by(ResearchRequestModel.requested_at.desc())
                .limit(limit)
            )
        ).all()
        return tuple((_request(request), _state(state)) for request, state in rows)

    async def _current_state(
        self, workspace_id: UUID, request_id: UUID
    ) -> ResearchRequestState | None:
        row = await self._session.scalar(
            select(ResearchRequestStateModel)
            .where(
                ResearchRequestStateModel.workspace_id == workspace_id,
                ResearchRequestStateModel.request_id == request_id,
            )
            .order_by(ResearchRequestStateModel.sequence.desc())
            .limit(1)
        )
        return None if row is None else _state(row)

    def _state_row(
        self, state: ResearchRequestState, *, entity_id: UUID
    ) -> ResearchRequestStateModel:
        return ResearchRequestStateModel(
            id=uuid4(),
            workspace_id=state.workspace_id,
            request_id=state.request_id,
            entity_id=entity_id,
            sequence=state.sequence,
            status=state.status.value,
            occurred_at=state.occurred_at,
            task_id=state.task_id,
            detail=state.detail,
            created_by=SYSTEM_USER_ID,
            updated_by=SYSTEM_USER_ID,
        )


class SqlResearchArtifactReader:
    """Reading one completed run back, whole.

    Three queries rather than a join: the rows have different shapes and
    different cardinalities, and a join would return the synthesis once per
    finding for a reader that then has to undo it.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def by_task(
        self, workspace_id: UUID, task_id: UUID
    ) -> tuple[ResearchTask, tuple[ResearchFinding, ...], ResearchSynthesis] | None:
        task_row = await self._session.scalar(
            select(ResearchTaskModel).where(
                ResearchTaskModel.workspace_id == workspace_id,
                ResearchTaskModel.id == task_id,
            )
        )
        if task_row is None:
            return None
        synthesis_row = await self._session.scalar(
            select(ResearchSynthesisModel).where(
                ResearchSynthesisModel.workspace_id == workspace_id,
                ResearchSynthesisModel.task_id == task_id,
            )
        )
        if synthesis_row is None:
            return None
        finding_rows = (
            await self._session.scalars(
                select(ResearchFindingModel)
                .where(
                    ResearchFindingModel.workspace_id == workspace_id,
                    ResearchFindingModel.task_id == task_id,
                )
                # The derivation name, so the order a customer reads findings
                # in is stable across requests. Insertion order is not a fact
                # about the account, and a list that reshuffled between polls
                # would look like the answer changing.
                .order_by(ResearchFindingModel.derivation)
            )
        ).all()
        return (
            _task(task_row),
            tuple(_finding(row) for row in finding_rows),
            _synthesis(synthesis_row),
        )


    async def source_counts(
        self, workspace_id: UUID, task_ids: tuple[UUID, ...]
    ) -> Mapping[UUID, int]:
        """How many distinct sources each run read — one query for all of them.

        **`unnest` then `count(distinct)`**, because a source cited by two
        findings is one source. A run that compared six business events across
        four derivations read six things, and reporting twenty-two would be
        counting the comparisons rather than the evidence.

        ⚡ **A task with no findings is absent from the mapping rather than
        `0`.** `NOTHING_TO_RESEARCH` is a real outcome, and the caller's own
        `.get` decides how to say so — a `0` written here would be this adapter
        answering a product question.
        """
        if not task_ids:
            return {}
        # `joins_implicitly` is the truthful description rather than a warning
        # suppressed: a set-returning function in `FROM` that reads a column of
        # another `FROM` item is an implicit LATERAL in PostgreSQL, so each row
        # is unnested against its own citations and never against every other
        # finding's.
        source = func.unnest(ResearchFindingModel.cited).column_valued(
            "source", joins_implicitly=True
        )
        rows = (
            await self._session.execute(
                select(
                    ResearchFindingModel.task_id,
                    func.count(distinct(source)),
                )
                .where(
                    ResearchFindingModel.workspace_id == workspace_id,
                    ResearchFindingModel.task_id.in_(task_ids),
                )
                .group_by(ResearchFindingModel.task_id)
            )
        ).all()
        return {task_id: count for task_id, count in rows}


def _request(row: ResearchRequestModel) -> ResearchRequest:
    return ResearchRequest(
        id=row.id,
        workspace_id=row.workspace_id,
        entity_id=row.entity_id,
        opportunity_id=row.opportunity_id,
        requested_by=row.requested_by,
        requested_at=row.requested_at,
        generation=row.generation,
    )


def _state(row: ResearchRequestStateModel) -> ResearchRequestState:
    return ResearchRequestState(
        request_id=row.request_id,
        workspace_id=row.workspace_id,
        sequence=row.sequence,
        status=ResearchStatus(row.status),
        occurred_at=row.occurred_at,
        task_id=row.task_id,
        detail=row.detail,
    )


def _task(row: ResearchTaskModel) -> ResearchTask:
    return ResearchTask(
        id=row.id,
        workspace_id=row.workspace_id,
        correlation_id=row.correlation_id,
        subject=EvidenceRef(kind=row.subject_kind, id=row.subject_id),
        opportunity_id=row.opportunity_id,
        requested_at=row.requested_at,
    )


def _finding(row: ResearchFindingModel) -> ResearchFinding:
    return ResearchFinding(
        id=row.id,
        workspace_id=row.workspace_id,
        task_id=row.task_id,
        subject=EvidenceRef(kind=row.subject_kind, id=row.subject_id),
        derivation=row.derivation,
        derivation_version=row.derivation_version,
        attributes=attributes_of(row.attributes),
        cited=cited_of(row.cited),
        created_at=row.created_at,
    )


def _synthesis(row: ResearchSynthesisModel) -> ResearchSynthesis:
    return ResearchSynthesis(
        id=row.id,
        workspace_id=row.workspace_id,
        task_id=row.task_id,
        statements=tuple(_statement(entry) for entry in row.statements),
        finding_ids=tuple(row.finding_ids),
        prompt_name=row.prompt_name,
        prompt_version=row.prompt_version,
        prompt_fingerprint=row.prompt_fingerprint,
        model=row.model,
        vendor=AIVendor(row.vendor),
        evidence_digest=row.evidence_digest,
        inference_id=row.inference_id,
        created_at=row.created_at,
    )


def _statement(entry: dict[str, Any]) -> GroundedStatement:
    return GroundedStatement(text=entry["text"], evidence=tuple(entry["evidence"]))


__all__ = [
    "PAYLOAD_VERSION",
    "SqlResearchArtifactReader",
    "SqlResearchRequestRepository",
]
