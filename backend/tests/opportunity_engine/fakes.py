"""Test doubles and builders for the Opportunity Engine.

Buying scores are built directly rather than computed, so a workflow test
states the intelligence it is about instead of arranging the signals that
would produce it. What M6 does with a score is the subject here; how M5B
arrives at one is tested where it belongs.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from modules.buying_score_engine.public import (
    BuyingScore,
    BuyingScoreExplanation,
    Contribution,
    ContributionLedger,
    Posture,
    ScoreTrigger,
    Trend,
)
from modules.opportunity_engine.domain.opportunity import Opportunity, OpportunityState
from modules.opportunity_engine.domain.policy import WorkspaceOpportunityPolicy
from modules.signal_engine.public import Relevance, SignalType
from modules.workspace_tenancy.public import MembershipView

WORKSPACE = UUID("33333333-3333-4333-8333-333333333333")
ENTITY = UUID("44444444-4444-4444-8444-444444444444")
SELLER = UUID("55555555-5555-4555-8555-555555555555")
COLLEAGUE = UUID("66666666-6666-4666-8666-666666666666")
OUTSIDER = UUID("77777777-7777-4777-8777-777777777777")
NOW = datetime(2026, 3, 1, tzinfo=UTC)


def _ledger_for(value: int, contested: bool) -> ContributionLedger:
    """A real ledger that reproduces `value` exactly.

    Built rather than faked because M5B refuses any score whose value
    disagrees with its ledger — a fake that sidestepped that would be
    testing M6 against a score that could not exist.

    Ceiling 100 so points and score coincide, which keeps these fixtures
    readable: a test asking for 60 gets 60.
    """
    contractionary = max(1, value // 4) if contested and value > 1 else 0
    entries = [
        _contribution(value - contractionary, Posture.EXPANSIONARY),
    ]
    if contractionary:
        entries.append(_contribution(contractionary, Posture.CONTRACTIONARY))
    return ContributionLedger(
        entries=tuple(e for e in entries if e.contribution > 0), ceiling=100
    )


def _contribution(points: int, posture: Posture) -> Contribution:
    return Contribution(
        business_event_id=uuid4(),
        signal_id=uuid4(),
        signal_type=SignalType.EXPANSION_OPPORTUNITY
        if posture is Posture.EXPANSIONARY
        else SignalType.CONTRACTION_RISK,
        posture=posture,
        relevance=Relevance.PRIMARY,
        base_weight=points,
        relevance_multiplier=100,
        age_band="fresh",
        age_multiplier=100,
        contribution=points,
        counted=True,
        reason="fixture evidence",
        band_started_at=NOW,
        band_ends_at=NOW + timedelta(days=90),
    )


def make_score(
    *,
    value: int = 60,
    contested: bool = False,
    valid_for_days: int = 30,
    score_id: UUID | None = None,
    computed_at: datetime = NOW,
) -> BuyingScore:
    """A score whose ledger genuinely reproduces it.

    `contested` and the dissent are read **from the ledger** rather than
    asserted beside it, exactly as the real projection does — so no fixture
    can hand M6 a score that disagrees with its own explanation.
    """
    ledger = _ledger_for(value, contested)
    return BuyingScore(
        id=score_id or uuid4(),
        workspace_id=WORKSPACE,
        entity_id=ENTITY,
        value=ledger.value(),
        trend=Trend.STEADY,
        delta=0,
        ledger=ledger,
        contested=ledger.is_contested,
        dissenting_signal_ids=ledger.dissent(),
        computed_at=computed_at,
        valid_until=computed_at + timedelta(days=valid_for_days),
        basis_at=computed_at,
        trigger=ScoreTrigger.SIGNAL_GENERATED,
        scoring_model_version=0,
        model_artifact_version=1,
        profile_version=0,
    )


class FakeOpportunityRepository:
    def __init__(self) -> None:
        self.rows: list[Opportunity] = []
        self.states: list[OpportunityState] = []
        #: Set to simulate losing a concurrent qualification race.
        self.conflict_on_create = False

    def _latest(self, opportunity_id: UUID) -> OpportunityState | None:
        states = [s for s in self.states if s.opportunity_id == opportunity_id]
        return max(states, key=lambda s: s.sequence) if states else None

    async def open_for_entity(
        self, workspace_id: UUID, entity_id: UUID
    ) -> Opportunity | None:
        for opportunity in sorted(self.rows, key=lambda o: o.generation, reverse=True):
            if opportunity.workspace_id != workspace_id or opportunity.entity_id != entity_id:
                continue
            state = self._latest(opportunity.id)
            if state is not None and state.is_open:
                return opportunity
        return None

    async def generations(self, workspace_id: UUID, entity_id: UUID) -> int:
        return len(
            [
                o
                for o in self.rows
                if o.workspace_id == workspace_id and o.entity_id == entity_id
            ]
        )

    async def create(self, opportunity: Opportunity, opening: OpportunityState) -> bool:
        if self.conflict_on_create:
            return False
        taken = {(o.workspace_id, o.entity_id, o.generation) for o in self.rows}
        if (opportunity.workspace_id, opportunity.entity_id, opportunity.generation) in taken:
            return False
        self.rows.append(opportunity)
        self.states.append(opening)
        return True

    async def append(self, state: OpportunityState) -> None:
        self.states.append(state)

    async def by_id(self, workspace_id: UUID, opportunity_id: UUID) -> Opportunity | None:
        return next(
            (
                o
                for o in self.rows
                if o.workspace_id == workspace_id and o.id == opportunity_id
            ),
            None,
        )

    async def current_state(
        self, workspace_id: UUID, opportunity_id: UUID
    ) -> OpportunityState | None:
        return self._latest(opportunity_id)

    async def history(
        self, workspace_id: UUID, opportunity_id: UUID
    ) -> tuple[OpportunityState, ...]:
        return tuple(
            sorted(
                (s for s in self.states if s.opportunity_id == opportunity_id),
                key=lambda s: s.sequence,
            )
        )

    async def for_entity(
        self, workspace_id: UUID, entity_id: UUID
    ) -> tuple[Opportunity, ...]:
        return tuple(
            sorted(
                (
                    o
                    for o in self.rows
                    if o.workspace_id == workspace_id and o.entity_id == entity_id
                ),
                key=lambda o: o.generation,
            )
        )


class FakePolicyRepository:
    def __init__(self) -> None:
        self.rows: list[WorkspaceOpportunityPolicy] = []

    async def current(self, workspace_id: UUID) -> WorkspaceOpportunityPolicy | None:
        live = [p for p in self.rows if p.workspace_id == workspace_id and p.supersedes is None]
        return live[0] if live else None

    async def by_version(
        self, workspace_id: UUID, version: int
    ) -> WorkspaceOpportunityPolicy | None:
        return next(
            (p for p in self.rows if p.workspace_id == workspace_id and p.version == version),
            None,
        )

    async def save(self, policy: WorkspaceOpportunityPolicy) -> None:
        self.rows.append(policy)


class FakeBuyingScoreReader:
    """Satisfies `BuyingScoreReader` — read-only, and read live."""

    def __init__(self, score: BuyingScore | None) -> None:
        self.score = score

    async def current(self, workspace_id: UUID, entity_id: UUID) -> BuyingScore | None:
        return self.score

    async def explanation(
        self, workspace_id: UUID, score_id: UUID
    ) -> BuyingScoreExplanation | None:
        if self.score is None or self.score.id != score_id:
            return None
        return BuyingScoreExplanation(score=self.score, signals=(), dissent=())


class FakeWorkspaces:
    """Satisfies `WorkspaceQueryPort`. Everyone but `OUTSIDER` is a member."""

    async def workspace_exists(self, workspace_id: UUID) -> bool:
        return workspace_id == WORKSPACE

    async def get_membership(
        self, workspace_id: UUID, user_id: UUID
    ) -> MembershipView | None:
        if workspace_id != WORKSPACE or user_id == OUTSIDER:
            return None
        return MembershipView(workspace_id=workspace_id, user_id=user_id, role="member")
