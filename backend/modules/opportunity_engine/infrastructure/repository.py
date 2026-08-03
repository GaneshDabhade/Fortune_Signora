"""Persistence for opportunities, their state, and workspace policy.

Neither repository offers an update method, and neither offers a delete.
Immutability is enforced at the database by the absent `UPDATE` grant
(migration 0014); the absent *delete* is the stronger statement, because
derived tables offer deletion precisely so regeneration can be their
rollback, and workflow has no regeneration to roll back to.

Current state is **derived** from the append-only log rather than stored
beside it, so a status and its audit trail cannot disagree.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from modules.opportunity_engine.domain.opportunity import (
    OPEN_STAGES,
    TERMINAL_STAGES,
    Opportunity,
    OpportunityState,
    OwnerScope,
    Qualification,
    Stage,
)
from modules.opportunity_engine.domain.policy import (
    OpportunityPolicy,
    WorkspaceOpportunityPolicy,
)
from modules.opportunity_engine.infrastructure.models import (
    OpportunityModel,
    OpportunityStateModel,
    WorkspaceOpportunityPolicyModel,
)
from signora_platform.pagination import CursorPosition

SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _to_opportunity(row: OpportunityModel) -> Opportunity:
    return Opportunity(
        id=row.id,
        workspace_id=row.workspace_id,
        entity_id=row.entity_id,
        generation=row.generation,
        originating_buying_score_id=row.originating_buying_score_id,
        score_at_creation=row.score_at_creation,
        contested_at_creation=row.contested_at_creation,
        qualification=Qualification(row.qualification),
        policy_version=row.policy_version,
        created_at=row.created_at,
        created_by=row.created_by,
        payload_version=row.payload_version,
    )


def _to_state(row: OpportunityStateModel) -> OpportunityState:
    return OpportunityState(
        id=row.id,
        opportunity_id=row.opportunity_id,
        workspace_id=row.workspace_id,
        sequence=row.sequence,
        stage=Stage(row.stage),
        owner_id=row.owner_id,
        actor_id=row.actor_id,
        reason=row.reason,
        occurred_at=row.occurred_at,
    )


def _to_policy(row: WorkspaceOpportunityPolicyModel) -> WorkspaceOpportunityPolicy:
    return WorkspaceOpportunityPolicy(
        id=row.id,
        workspace_id=row.workspace_id,
        version=row.version,
        policy=OpportunityPolicy.model_validate({**row.policy, "version": row.version}),
        created_at=row.created_at,
        created_by=row.created_by,
        supersedes=row.supersedes,
    )


def _policy_to_json(policy: OpportunityPolicy) -> dict[str, Any]:
    return {
        "minimum_score": policy.minimum_score,
        "contested_qualifies": policy.contested_qualifies,
        "automatic_creation": policy.automatic_creation,
    }


class SqlOpportunityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _latest_sequence(self) -> Any:
        return (
            select(
                OpportunityStateModel.opportunity_id,
                func.max(OpportunityStateModel.sequence).label("sequence"),
            )
            .group_by(OpportunityStateModel.opportunity_id)
            .subquery()
        )

    async def open_for_entity(self, workspace_id: UUID, entity_id: UUID) -> Opportunity | None:
        latest = self._latest_sequence()
        row = (
            await self._session.execute(
                select(OpportunityModel)
                .join(latest, latest.c.opportunity_id == OpportunityModel.id)
                .join(
                    OpportunityStateModel,
                    (OpportunityStateModel.opportunity_id == OpportunityModel.id)
                    & (OpportunityStateModel.sequence == latest.c.sequence),
                )
                .where(
                    OpportunityModel.workspace_id == workspace_id,
                    OpportunityModel.entity_id == entity_id,
                    OpportunityStateModel.stage.in_([s.value for s in OPEN_STAGES]),
                )
                .order_by(OpportunityModel.generation.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        return _to_opportunity(row) if row is not None else None

    async def open_page(
        self,
        workspace_id: UUID,
        *,
        after: CursorPosition | None,
        limit: int,
        scope: OwnerScope = OwnerScope.ALL,
        viewer_id: UUID | None = None,
    ) -> tuple[tuple[Opportunity, OpportunityState], ...]:
        return await self._page(
            workspace_id,
            OPEN_STAGES,
            after=after,
            limit=limit,
            scope=scope,
            viewer_id=viewer_id,
        )

    async def decided_page(
        self, workspace_id: UUID, *, after: CursorPosition | None, limit: int
    ) -> tuple[tuple[Opportunity, OpportunityState], ...]:
        """The opposite half of the same query (**R4-04**).

        **Newest decision first**, which is the one difference from the open
        page and the reason this is not one method with a stage argument. The
        open list is walked oldest-first because attention ordering is applied
        over the page afterwards; a decided list has no ranking to apply, and
        the question it answers — *"wait, what did I just dismiss?"* — is asked
        about the most recent one.
        """
        return await self._page(
            workspace_id, TERMINAL_STAGES, after=after, limit=limit, newest_first=True
        )

    async def _page(
        self,
        workspace_id: UUID,
        stages: frozenset[Stage],
        *,
        after: CursorPosition | None,
        limit: int,
        newest_first: bool = False,
        scope: OwnerScope = OwnerScope.ALL,
        viewer_id: UUID | None = None,
    ) -> tuple[tuple[Opportunity, OpportunityState], ...]:
        latest = self._latest_sequence()
        order = (
            (OpportunityModel.created_at.desc(), OpportunityModel.id.desc())
            if newest_first
            else (OpportunityModel.created_at, OpportunityModel.id)
        )
        statement = (
            select(OpportunityModel, OpportunityStateModel)
            .join(latest, latest.c.opportunity_id == OpportunityModel.id)
            .join(
                OpportunityStateModel,
                (OpportunityStateModel.opportunity_id == OpportunityModel.id)
                & (OpportunityStateModel.sequence == latest.c.sequence),
            )
            .where(
                OpportunityModel.workspace_id == workspace_id,
                OpportunityStateModel.stage.in_([s.value for s in stages]),
            )
            .order_by(*order)
            .limit(limit)
        )
        # **In the query, so the cursor walks the filtered set.** Filtering the
        # returned rows would page over everything and show a short page of
        # *mine*, which is a different list wearing the same name.
        if scope is OwnerScope.MINE:
            statement = statement.where(OpportunityStateModel.owner_id == viewer_id)
        elif scope is OwnerScope.UNASSIGNED:
            statement = statement.where(OpportunityStateModel.owner_id.is_(None))
        if after is not None:
            position = tuple_(OpportunityModel.created_at, OpportunityModel.id)
            statement = statement.where(
                position < (after.created_at, after.id)
                if newest_first
                else position > (after.created_at, after.id)
            )
        rows = (await self._session.execute(statement)).all()
        return tuple((_to_opportunity(row[0]), _to_state(row[1])) for row in rows)

    async def generations(self, workspace_id: UUID, entity_id: UUID) -> int:
        return int(
            (
                await self._session.execute(
                    select(func.count())
                    .select_from(OpportunityModel)
                    .where(
                        OpportunityModel.workspace_id == workspace_id,
                        OpportunityModel.entity_id == entity_id,
                    )
                )
            ).scalar_one()
        )

    async def create(self, opportunity: Opportunity, opening: OpportunityState) -> bool:
        """Both rows or neither. An opportunity in no state at all is not a
        workflow object; it is a bug that looks like data.

        **`created_at` is written from the aggregate, not left to the column
        default.** It is not "when this row was inserted" — it is *when a
        commitment was made*, which the use case decides from its injected
        clock. Omitting it let `server_default now()` win silently, so the
        domain's value was discarded on write and the row's substituted on
        read.

        Invisible in production, where qualification happens at wall-clock now
        and the two agree. It diverges under **historical replay**, which this
        module claims to support: an opportunity qualified against a reading
        from June reported that it opened today, the evidence assembled for
        narration carried that date, and a model faithfully told a customer the
        wrong one.
        """
        statement = (
            insert(OpportunityModel)
            .values(
                {
                    "id": opportunity.id,
                    "workspace_id": opportunity.workspace_id,
                    "entity_id": opportunity.entity_id,
                    "generation": opportunity.generation,
                    "originating_buying_score_id": opportunity.originating_buying_score_id,
                    "score_at_creation": opportunity.score_at_creation,
                    "contested_at_creation": opportunity.contested_at_creation,
                    "qualification": opportunity.qualification.value,
                    "policy_version": opportunity.policy_version,
                    "payload_version": opportunity.payload_version,
                    "created_at": opportunity.created_at,
                    "created_by": opportunity.created_by,
                    "updated_by": opportunity.created_by,
                }
            )
            # A concurrent qualification took this generation. Losing that
            # race is the mechanism working, not an error to report.
            .on_conflict_do_nothing(index_elements=["workspace_id", "entity_id", "generation"])
            .returning(OpportunityModel.id)
        )
        if (await self._session.execute(statement)).scalar_one_or_none() is None:
            return False

        await self.append(opening)
        return True

    async def append(self, state: OpportunityState) -> None:
        self._session.add(
            OpportunityStateModel(
                id=state.id,
                opportunity_id=state.opportunity_id,
                workspace_id=state.workspace_id,
                sequence=state.sequence,
                stage=state.stage.value,
                owner_id=state.owner_id,
                actor_id=state.actor_id,
                reason=state.reason,
                occurred_at=state.occurred_at,
                created_by=state.actor_id or SYSTEM_USER_ID,
                updated_by=state.actor_id or SYSTEM_USER_ID,
            )
        )
        await self._session.flush()

    async def by_id(self, workspace_id: UUID, opportunity_id: UUID) -> Opportunity | None:
        row = (
            await self._session.execute(
                select(OpportunityModel).where(
                    OpportunityModel.workspace_id == workspace_id,
                    OpportunityModel.id == opportunity_id,
                )
            )
        ).scalar_one_or_none()
        return _to_opportunity(row) if row is not None else None

    async def current_state(
        self, workspace_id: UUID, opportunity_id: UUID
    ) -> OpportunityState | None:
        row = (
            await self._session.execute(
                select(OpportunityStateModel)
                .where(
                    OpportunityStateModel.workspace_id == workspace_id,
                    OpportunityStateModel.opportunity_id == opportunity_id,
                )
                .order_by(OpportunityStateModel.sequence.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        return _to_state(row) if row is not None else None

    async def history(
        self, workspace_id: UUID, opportunity_id: UUID
    ) -> tuple[OpportunityState, ...]:
        rows = await self._session.execute(
            select(OpportunityStateModel)
            .where(
                OpportunityStateModel.workspace_id == workspace_id,
                OpportunityStateModel.opportunity_id == opportunity_id,
            )
            .order_by(OpportunityStateModel.sequence)
        )
        return tuple(_to_state(row) for row in rows.scalars())

    async def for_entity(self, workspace_id: UUID, entity_id: UUID) -> tuple[Opportunity, ...]:
        rows = await self._session.execute(
            select(OpportunityModel)
            .where(
                OpportunityModel.workspace_id == workspace_id,
                OpportunityModel.entity_id == entity_id,
            )
            .order_by(OpportunityModel.generation)
        )
        return tuple(_to_opportunity(row) for row in rows.scalars())


class SqlOpportunityPolicyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def current(self, workspace_id: UUID) -> WorkspaceOpportunityPolicy | None:
        """The policy in force: **the highest version.**

        **Not `WHERE supersedes IS NULL`** (`B-001`). On an immutable table the
        row with a null `supersedes` is the *first* version — the new row is
        the one that names its predecessor — so that predicate returned
        version 1 forever and silently ignored every revision a customer made.

        Found by the repository-wide invariant written for `signal_profile`,
        which is the argument for writing that one as a scan rather than a
        per-table assertion: **the same shape was in three modules.**
        """
        row = (
            await self._session.execute(
                select(WorkspaceOpportunityPolicyModel)
                .where(WorkspaceOpportunityPolicyModel.workspace_id == workspace_id)
                .order_by(WorkspaceOpportunityPolicyModel.version.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        return _to_policy(row) if row is not None else None

    async def by_version(
        self, workspace_id: UUID, version: int
    ) -> WorkspaceOpportunityPolicy | None:
        row = (
            await self._session.execute(
                select(WorkspaceOpportunityPolicyModel).where(
                    WorkspaceOpportunityPolicyModel.workspace_id == workspace_id,
                    WorkspaceOpportunityPolicyModel.version == version,
                )
            )
        ).scalar_one_or_none()
        return _to_policy(row) if row is not None else None

    async def save(self, policy: WorkspaceOpportunityPolicy) -> None:
        self._session.add(
            WorkspaceOpportunityPolicyModel(
                id=policy.id,
                workspace_id=policy.workspace_id,
                version=policy.version,
                policy=_policy_to_json(policy.policy),
                supersedes=policy.supersedes,
                created_by=policy.created_by,
                updated_by=policy.created_by,
            )
        )
        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise ValueError(
                f"a policy version {policy.version} already exists for this workspace, or "
                "another current policy is present. Configuration is superseded, never edited."
            ) from exc
