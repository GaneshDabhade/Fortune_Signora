"""Progress an opportunity. **Always a human act.**

*Intelligence suggests; humans commit* (ratified 2026-07-29). Every path
into this use case requires an `actor_id`, and the domain refuses to build
a non-`TRACKING` state without one — so code that advances an opportunity
without a person does not compile, and a row that recorded one would be
rejected by the database as well.

There is deliberately **no automatic closure anywhere in this module.** A
falling score, an expiring score, or an account going quiet changes no
stage. Nothing happening at a company is not evidence that a deal is dead;
it is evidence that nothing happened, and revoking a seller's decision on
that basis would be the worst failure this module could have.

Assignment verifies membership **server-side, every time**. A `user_id`
supplied by a caller is a claim about who should hold the work, and an
unverified one would hand an account to somebody outside the workspace.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from modules.opportunity_engine.application.ports import OpportunityRepository
from modules.opportunity_engine.domain.events import OpportunityStageChanged
from modules.opportunity_engine.domain.opportunity import (
    Opportunity,
    OpportunityError,
    OpportunityState,
    Stage,
    next_state,
)
from modules.workspace_tenancy.public import WorkspaceQueryPort
from signora_platform.event_bus import EventPublisher
from signora_platform.observability import get_logger

logger = get_logger(__name__)

PRODUCER_MODULE = "opportunity_engine"


class MembershipError(OpportunityError):
    """An opportunity was assigned to somebody outside the workspace."""


class OpportunityNotFound(OpportunityError):
    """No opportunity with that identifier is visible in this workspace.

    **Distinguished from every other failure here so the interface can answer
    404 rather than 422.** A caller naming an opportunity from another
    workspace must get the same answer as one naming an opportunity that was
    never created — anything else lets identifiers be enumerated one status
    code at a time, which is the reasoning behind 404-not-403 applied to a
    resource inside the workspace rather than to the workspace itself.
    """


@dataclass(frozen=True, slots=True)
class TransitionOpportunityInput:
    workspace_id: UUID
    opportunity_id: UUID
    stage: Stage
    #: **Required.** There is no machine path to this use case.
    actor_id: UUID
    reason: str
    #: Who should hold the work now. `None` leaves ownership unchanged.
    owner_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class TransitionOpportunityResult:
    opportunity: Opportunity
    state: OpportunityState


class TransitionOpportunity:
    def __init__(
        self,
        *,
        repository: OpportunityRepository,
        workspaces: WorkspaceQueryPort,
        publisher: EventPublisher,
        session: AsyncSession,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._repository = repository
        # The one approved synchronous cross-module read
        # (05-module-dependencies.md). Membership is a tenancy fact, and
        # this module must not keep its own copy of one.
        self._workspaces = workspaces
        self._publisher = publisher
        self._session = session
        self._clock = clock

    async def execute(
        self,
        request: TransitionOpportunityInput,
        *,
        correlation_id: UUID,
        causation_id: UUID | None = None,
    ) -> TransitionOpportunityResult:
        opportunity = await self._repository.by_id(request.workspace_id, request.opportunity_id)
        if opportunity is None:
            raise OpportunityNotFound(
                f"opportunity {request.opportunity_id} does not exist in this workspace."
            )

        current = await self._repository.current_state(
            request.workspace_id, request.opportunity_id
        )
        if current is None:
            raise OpportunityError(
                f"opportunity {request.opportunity_id} has no state. An opportunity in no state "
                "at all is a bug that looks like data."
            )

        await self._verify_member(request.workspace_id, request.actor_id, "act in")
        owner_id = current.owner_id if request.owner_id is None else request.owner_id
        if owner_id is not None and owner_id != current.owner_id:
            await self._verify_member(request.workspace_id, owner_id, "hold work in")

        state = next_state(
            current,
            state_id=uuid4(),
            stage=request.stage,
            owner_id=owner_id,
            actor_id=request.actor_id,
            reason=request.reason,
            occurred_at=self._clock(),
        )
        await self._repository.append(state)

        await self._publisher.publish(
            # See the note in provider_normalization's handler: the platform's
            # PublishableEvent Protocol declares settable members, which frozen
            # domain events cannot satisfy. Raised as a finding, not fixed here.
            [_changed_event(opportunity, current, state, causation_id)],  # type: ignore[list-item]
            session=self._session,
            producer_module=PRODUCER_MODULE,
            correlation_id=correlation_id,
        )

        logger.info(
            "opportunity progressed",
            extra={
                "opportunity_id": str(opportunity.id),
                "entity_id": str(opportunity.entity_id),
                "previous_stage": current.stage.value,
                "new_stage": state.stage.value,
                "actor_id": str(request.actor_id),
                "sequence": state.sequence,
            },
        )
        return TransitionOpportunityResult(opportunity=opportunity, state=state)

    async def _verify_member(self, workspace_id: UUID, user_id: UUID, verb: str) -> None:
        if await self._workspaces.get_membership(workspace_id, user_id) is None:
            raise MembershipError(
                f"user {user_id} is not a member of this workspace and cannot {verb} it. "
                "Membership is verified server-side on every assignment, never trusted from "
                "the request."
            )


def _changed_event(
    opportunity: Opportunity,
    previous: OpportunityState,
    state: OpportunityState,
    causation_id: UUID | None,
) -> OpportunityStageChanged:
    # `actor_id` is never None here: only TRACKING may be machine-authored,
    # and TRACKING is only ever an opening state.
    assert state.actor_id is not None
    return OpportunityStageChanged(
        event_id=uuid4(),
        workspace_id=opportunity.workspace_id,
        occurred_at=state.occurred_at,
        opportunity_id=opportunity.id,
        entity_id=opportunity.entity_id,
        previous_stage=previous.stage.value,
        new_stage=state.stage.value,
        owner_id=state.owner_id,
        actor_id=state.actor_id,
        reason=state.reason,
        sequence=state.sequence,
        payload_version=opportunity.payload_version,
        causation_id=causation_id,
    )
