"""Open an opportunity when an account crosses the tracking threshold.

**This is the machine's entire authority over workflow.** It may open an
opportunity at `TRACKING` — a suggestion that commits nobody — and it may
do nothing else. Progressing, assigning, and closing all require a person,
and there is no code path from here to any of them.

*Intelligence suggests; humans commit* (ratified 2026-07-29).

Three properties shape the flow:

**Creation is automatic; closure never is.** A suggestion costs a glance to
dismiss, while closing something a human is working on destroys their work.
The asymmetry is principled rather than cautious, and it is why this module
has a `Qualify` use case and no `Disqualify` one.

**At most one open opportunity per account.** Without it, auto-creation
would open a new one on every qualifying score. The check is made in the
transaction, and the dangerous case — two concurrent qualifications — is
converted into a unique-index conflict rather than trusted to timing.

**A qualifying score is read, never recomputed.** *Why* the number is what
it is was settled one module upstream and its ledger already explains it.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from modules.buying_score_engine.public import BuyingScore
from modules.opportunity_engine.application.ports import (
    BuyingScoreReader,
    OpportunityPolicyRepository,
    OpportunityRepository,
)
from modules.opportunity_engine.domain.events import OpportunityCreated
from modules.opportunity_engine.domain.opportunity import (
    Opportunity,
    OpportunityState,
    Qualification,
    Stage,
    opening_state,
)
from modules.opportunity_engine.domain.policy import OpportunityPolicy, resolve_policy
from signora_platform.event_bus import EventPublisher
from signora_platform.observability import get_logger

logger = get_logger(__name__)

PRODUCER_MODULE = "opportunity_engine"


@dataclass(frozen=True, slots=True)
class QualifyOpportunityInput:
    workspace_id: UUID
    entity_id: UUID
    #: Set when a human opens an opportunity directly, whatever the score
    #: says. `None` means Signora is suggesting it, and the policy decides.
    opened_by: UUID | None = None
    reason: str = ""


@dataclass(frozen=True, slots=True)
class QualifyOpportunityResult:
    opportunity: Opportunity | None
    created: bool
    #: Why nothing was created, for a caller that needs to say so. `None`
    #: when an opportunity was opened.
    declined: str | None = None


class QualifyOpportunity:
    def __init__(
        self,
        *,
        repository: OpportunityRepository,
        policies: OpportunityPolicyRepository,
        scores: BuyingScoreReader,
        artifact: OpportunityPolicy,
        publisher: EventPublisher,
        session: AsyncSession,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._repository = repository
        self._policies = policies
        # Scores are read through the Buying Score Engine's published port,
        # never recomputed: this module decides what to track, not how much
        # anything matters.
        self._scores = scores
        self._artifact = artifact
        self._publisher = publisher
        self._session = session
        self._clock = clock

    async def execute(
        self,
        request: QualifyOpportunityInput,
        *,
        correlation_id: UUID,
        causation_id: UUID | None = None,
    ) -> QualifyOpportunityResult:
        existing = await self._repository.open_for_entity(request.workspace_id, request.entity_id)
        if existing is not None:
            return QualifyOpportunityResult(
                opportunity=existing,
                created=False,
                declined="an open opportunity already exists for this account",
            )

        score = await self._scores.current(request.workspace_id, request.entity_id)
        if score is None:
            return QualifyOpportunityResult(
                opportunity=None,
                created=False,
                declined="no buying score exists for this account",
            )

        stored = await self._policies.current(request.workspace_id)
        policy, policy_version = resolve_policy(self._artifact, stored)
        manual = request.opened_by is not None

        if not manual:
            if not policy.automatic_creation:
                return QualifyOpportunityResult(
                    opportunity=None,
                    created=False,
                    declined="this workspace has turned off automatic creation",
                )
            if not policy.qualifies(score):
                return QualifyOpportunityResult(
                    opportunity=None,
                    created=False,
                    declined=f"score {score.value} does not qualify under policy v{policy_version}",
                )

        now = self._clock()
        opportunity = Opportunity(
            id=uuid4(),
            workspace_id=request.workspace_id,
            entity_id=request.entity_id,
            generation=await self._repository.generations(
                request.workspace_id, request.entity_id
            ),
            originating_buying_score_id=score.id,
            score_at_creation=score.value,
            contested_at_creation=score.contested,
            qualification=Qualification.MANUAL if manual else Qualification.AUTOMATIC,
            policy_version=policy_version,
            created_at=now,
            created_by=request.opened_by or _SYSTEM,
        )
        opening = opening_state(
            state_id=uuid4(),
            opportunity=opportunity,
            reason=request.reason.strip() or _opening_reason(score, policy_version, manual),
            # None for an automatic suggestion: Signora is not a person, and
            # recording it as one would make the audit trail claim a human
            # decided something nobody decided.
            actor_id=request.opened_by,
            occurred_at=now,
        )

        if not await self._repository.create(opportunity, opening):
            # A concurrent qualification took this generation. Identity is
            # the mechanism working, not an error: exactly one opportunity
            # exists, which is what the rule asked for.
            return QualifyOpportunityResult(
                opportunity=await self._repository.open_for_entity(
                    request.workspace_id, request.entity_id
                ),
                created=False,
                declined="a concurrent qualification opened this account first",
            )

        await self._publisher.publish(
            # See the note in provider_normalization's handler: the platform's
            # PublishableEvent Protocol declares settable members, which frozen
            # domain events cannot satisfy. Raised as a finding, not fixed here.
            [_created_event(opportunity, opening, causation_id)],  # type: ignore[list-item]
            session=self._session,
            producer_module=PRODUCER_MODULE,
            correlation_id=correlation_id,
        )

        logger.info(
            "opportunity opened",
            extra={
                "opportunity_id": str(opportunity.id),
                "entity_id": str(request.entity_id),
                "score_at_creation": opportunity.score_at_creation,
                "contested": opportunity.contested_at_creation,
                "qualification": opportunity.qualification.value,
                "policy_version": policy_version,
            },
        )
        return QualifyOpportunityResult(opportunity=opportunity, created=True)


#: Recorded as the author of an automatically opened opportunity. Distinct
#: from any real user id, so *"who opened this?"* never falsely names a
#: person.
_SYSTEM = UUID("00000000-0000-0000-0000-000000000001")


def _opening_reason(score: BuyingScore, policy_version: int, manual: bool) -> str:
    """The sentence a customer reads, rendered from the facts an auditor
    checks — so the explanation and the record cannot diverge."""
    if manual:
        return f"Opened directly. Commercial attention was {score.value} at the time."
    contested = " Opposing readings were live." if score.contested else ""
    return (
        f"Commercial attention reached {score.value}, which your qualification policy "
        f"(v{policy_version}) treats as worth tracking.{contested}"
    )


def _created_event(
    opportunity: Opportunity, opening: OpportunityState, causation_id: UUID | None
) -> OpportunityCreated:
    return OpportunityCreated(
        event_id=uuid4(),
        workspace_id=opportunity.workspace_id,
        occurred_at=opportunity.created_at,
        opportunity_id=opportunity.id,
        entity_id=opportunity.entity_id,
        originating_buying_score_id=opportunity.originating_buying_score_id,
        score_at_creation=opportunity.score_at_creation,
        contested_at_creation=opportunity.contested_at_creation,
        qualification=opportunity.qualification.value,
        stage=Stage.TRACKING.value,
        policy_version=opportunity.policy_version,
        payload_version=opportunity.payload_version,
        causation_id=causation_id,
    )
