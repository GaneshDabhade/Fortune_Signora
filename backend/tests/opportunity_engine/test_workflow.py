"""The Opportunity Engine's domain and use cases, against fakes.

The properties under test are the ones that define the module: the machine
may suggest and nothing more, an opportunity outlives the score that
created it, history is never rewritten, and workflow stores no derived
intelligence of its own.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest

from modules.buying_score_engine.public import BuyingScore
from modules.opportunity_engine.application.qualify import (
    QualifyOpportunity,
    QualifyOpportunityInput,
    QualifyOpportunityResult,
)
from modules.opportunity_engine.application.queries import (
    OpportunityQueries,
    evidence_state,
)
from modules.opportunity_engine.application.transition import (
    MembershipError,
    TransitionOpportunity,
    TransitionOpportunityInput,
    TransitionOpportunityResult,
)
from modules.opportunity_engine.domain.opportunity import (
    MACHINE_AUTHORED,
    EvidenceState,
    Opportunity,
    OpportunityError,
    OpportunityState,
    Qualification,
    Stage,
    allowed_from,
    next_state,
)
from modules.opportunity_engine.domain.policy import (
    DEFAULT_POLICY_VERSION,
    OpportunityPolicy,
    WorkspaceOpportunityPolicy,
)
from modules.opportunity_engine.infrastructure.policy_loader import load_policy
from tests.knowledge_graph.fakes import RecordingPublisher
from tests.opportunity_engine.fakes import (
    COLLEAGUE,
    ENTITY,
    NOW,
    OUTSIDER,
    SELLER,
    WORKSPACE,
    FakeBuyingScoreReader,
    FakeOpportunityRepository,
    FakePolicyRepository,
    FakeWorkspaces,
    make_score,
)

ARTIFACT = load_policy()


def build(
    score: BuyingScore | None = None,
    *,
    policies: FakePolicyRepository | None = None,
    repository: FakeOpportunityRepository | None = None,
    moment: datetime = NOW,
) -> tuple[
    QualifyOpportunity,
    TransitionOpportunity,
    FakeOpportunityRepository,
    FakePolicyRepository,
    RecordingPublisher,
]:
    repository = repository or FakeOpportunityRepository()
    policies = policies or FakePolicyRepository()
    publisher = RecordingPublisher()
    qualify = QualifyOpportunity(
        repository=repository,
        policies=policies,
        scores=FakeBuyingScoreReader(score),
        artifact=ARTIFACT,
        publisher=publisher,
        session=None,  # type: ignore[arg-type]
        clock=lambda: moment,
    )
    transition = TransitionOpportunity(
        repository=repository,
        workspaces=FakeWorkspaces(),
        publisher=publisher,
        session=None,  # type: ignore[arg-type]
        clock=lambda: moment,
    )
    return qualify, transition, repository, policies, publisher


async def open_one(
    qualify: QualifyOpportunity, *, opened_by: UUID | None = None, reason: str = ""
) -> QualifyOpportunityResult:
    return await qualify.execute(
        QualifyOpportunityInput(
            workspace_id=WORKSPACE, entity_id=ENTITY, opened_by=opened_by, reason=reason
        ),
        correlation_id=uuid4(),
    )


async def move(
    transition: TransitionOpportunity,
    opportunity_id: UUID,
    stage: Stage,
    *,
    actor: UUID = SELLER,
    owner: UUID | None = None,
    reason: str = "because",
) -> TransitionOpportunityResult:
    return await transition.execute(
        TransitionOpportunityInput(
            workspace_id=WORKSPACE,
            opportunity_id=opportunity_id,
            stage=stage,
            actor_id=actor,
            owner_id=owner,
            reason=reason,
        ),
        correlation_id=uuid4(),
    )


class TestIntelligenceSuggests:
    """The machine's entire authority over workflow."""

    async def test_a_qualifying_score_opens_a_suggestion_owned_by_nobody(self) -> None:
        qualify, _, repository, _, publisher = build(make_score(value=60))

        result = await open_one(qualify)

        assert result.created
        assert result.opportunity is not None
        assert result.opportunity.qualification is Qualification.AUTOMATIC
        assert result.opportunity.score_at_creation == 60

        state = await repository.current_state(WORKSPACE, result.opportunity.id)
        assert state is not None
        assert state.stage is Stage.TRACKING
        assert state.owner_id is None
        assert state.actor_id is None, "Signora is not a person"
        assert publisher.types() == ["opportunity.created"]

    async def test_tracking_is_the_only_stage_the_machine_may_author(self) -> None:
        assert frozenset({Stage.TRACKING}) == MACHINE_AUTHORED

        with pytest.raises(OpportunityError, match="Intelligence suggests; humans commit"):
            OpportunityState(
                id=uuid4(),
                opportunity_id=uuid4(),
                workspace_id=WORKSPACE,
                sequence=1,
                stage=Stage.ENGAGED,
                owner_id=None,
                actor_id=None,
                reason="nobody decided this",
                occurred_at=NOW,
            )

    async def test_a_score_below_the_threshold_opens_nothing(self) -> None:
        qualify, _, repository, _, publisher = build(
            make_score(value=ARTIFACT.minimum_score - 1)
        )

        result = await open_one(qualify)

        assert not result.created
        assert result.declined is not None and "does not qualify" in result.declined
        assert repository.rows == []
        assert publisher.events == []

    async def test_an_account_with_no_score_opens_nothing(self) -> None:
        qualify, _, repository, _, _ = build(None)

        result = await open_one(qualify)

        assert not result.created
        assert repository.rows == []

    async def test_a_contested_score_qualifies_by_default(self) -> None:
        """A fought-over account is exactly what a seller should look at,
        and M5B already scores it high rather than averaging it away."""
        qualify, _, _, _, _ = build(make_score(value=60, contested=True))

        result = await open_one(qualify)

        assert result.created
        assert result.opportunity is not None
        assert result.opportunity.contested_at_creation

    async def test_a_workspace_may_require_confidence(self) -> None:
        policies = FakePolicyRepository()
        await policies.save(
            WorkspaceOpportunityPolicy(
                id=uuid4(),
                workspace_id=WORKSPACE,
                version=1,
                policy=OpportunityPolicy(
                    version=1,
                    minimum_score=40,
                    contested_qualifies=False,
                    automatic_creation=True,
                ),
                created_at=NOW,
                created_by=SELLER,
            )
        )
        qualify, _, _, _, _ = build(make_score(value=60, contested=True), policies=policies)

        result = await open_one(qualify)

        assert not result.created

    async def test_a_workspace_may_turn_automatic_creation_off(self) -> None:
        policies = FakePolicyRepository()
        await policies.save(
            WorkspaceOpportunityPolicy(
                id=uuid4(),
                workspace_id=WORKSPACE,
                version=1,
                policy=OpportunityPolicy(
                    version=1,
                    minimum_score=40,
                    contested_qualifies=True,
                    automatic_creation=False,
                ),
                created_at=NOW,
                created_by=SELLER,
            )
        )
        qualify, _, _, _, _ = build(make_score(value=90), policies=policies)

        assert not (await open_one(qualify)).created

    async def test_a_human_may_open_one_the_policy_would_decline(self) -> None:
        qualify, _, repository, _, _ = build(make_score(value=1))

        result = await open_one(qualify, opened_by=SELLER)

        assert result.created
        assert result.opportunity is not None
        assert result.opportunity.qualification is Qualification.MANUAL
        state = await repository.current_state(WORKSPACE, result.opportunity.id)
        assert state is not None and state.actor_id == SELLER

    async def test_an_unconfigured_workspace_uses_the_shipped_policy(self) -> None:
        qualify, _, _, _, _ = build(make_score(value=60))

        result = await open_one(qualify)

        assert result.opportunity is not None
        assert result.opportunity.policy_version == DEFAULT_POLICY_VERSION


class TestOneOpenOpportunityPerAccount:
    async def test_a_second_qualifying_score_opens_nothing_new(self) -> None:
        qualify, _, repository, _, publisher = build(make_score(value=60))
        await open_one(qualify)

        again = await open_one(qualify)

        assert not again.created
        assert again.declined is not None and "already exists" in again.declined
        assert len(repository.rows) == 1
        assert len(publisher.events) == 1

    async def test_losing_a_concurrent_race_leaves_exactly_one(self) -> None:
        """Identity is the mechanism working, not an error: exactly one
        opportunity exists, which is what the rule asked for."""
        qualify, _, repository, _, publisher = build(make_score(value=60))
        repository.conflict_on_create = True

        result = await open_one(qualify)

        assert not result.created
        assert repository.rows == []
        assert publisher.events == []

    async def test_a_closed_account_may_be_opened_again_as_a_new_generation(self) -> None:
        qualify, transition, repository, _, _ = build(make_score(value=60))
        first = await open_one(qualify)
        assert first.opportunity is not None
        await move(transition, first.opportunity.id, Stage.CLOSED_LOST)

        second = await open_one(qualify)

        assert second.created
        assert second.opportunity is not None
        assert second.opportunity.generation == 1


class TestHumansCommit:
    async def test_progressing_requires_a_member(self) -> None:
        qualify, transition, _, _, _ = build(make_score(value=60))
        opened = await open_one(qualify)
        assert opened.opportunity is not None

        with pytest.raises(MembershipError, match="not a member"):
            await move(transition, opened.opportunity.id, Stage.ENGAGED, actor=OUTSIDER)

    async def test_assignment_verifies_membership_server_side(self) -> None:
        qualify, transition, _, _, _ = build(make_score(value=60))
        opened = await open_one(qualify)
        assert opened.opportunity is not None

        with pytest.raises(MembershipError, match="not a member"):
            await move(transition, opened.opportunity.id, Stage.ENGAGED, owner=OUTSIDER)

    async def test_engaging_records_the_actor_the_owner_and_the_reason(self) -> None:
        qualify, transition, _, _, publisher = build(make_score(value=60))
        opened = await open_one(qualify)
        assert opened.opportunity is not None

        result = await move(
            transition,
            opened.opportunity.id,
            Stage.ENGAGED,
            owner=COLLEAGUE,
            reason="worth a call this quarter",
        )

        assert result.state.stage is Stage.ENGAGED
        assert result.state.owner_id == COLLEAGUE
        assert result.state.actor_id == SELLER
        assert result.state.reason == "worth a call this quarter"
        assert result.state.sequence == 1
        assert publisher.types() == ["opportunity.created", "opportunity.stage_changed"]

    async def test_an_account_being_worked_can_be_handed_to_a_colleague(self) -> None:
        """The move a real sales team makes constantly: leave, resignation, a
        territory change. It changes no stage, and until LO-04 no screen could
        reach it — a seller going on leave had to close their accounts to get
        them off their name."""
        qualify, transition, repository, _, publisher = build(make_score(value=60))
        opened = await open_one(qualify)
        assert opened.opportunity is not None
        await move(transition, opened.opportunity.id, Stage.ENGAGED, owner=SELLER)

        result = await move(
            transition,
            opened.opportunity.id,
            Stage.ENGAGED,
            owner=COLLEAGUE,
            reason="on leave until March",
        )

        assert result.state.stage is Stage.ENGAGED
        assert result.state.owner_id == COLLEAGUE
        assert result.state.actor_id == SELLER
        assert result.state.sequence == 2
        history = await repository.history(WORKSPACE, opened.opportunity.id)
        assert [s.owner_id for s in history] == [None, SELLER, COLLEAGUE]
        assert publisher.types()[-1] == "opportunity.stage_changed"

    def test_a_handover_is_deliberately_outside_the_stage_table(self) -> None:
        """**Ownership is not a stage**, and the two rules together are what
        say so: a stage cannot become itself, and a hand-over does exactly
        that. Inventing `transferred` as a fifth stage would have made a state
        out of an event and distorted every figure computed from the table."""
        assert Stage.ENGAGED not in allowed_from(Stage.ENGAGED)

        current = OpportunityState(
            id=uuid4(),
            opportunity_id=uuid4(),
            workspace_id=WORKSPACE,
            sequence=1,
            stage=Stage.ENGAGED,
            owner_id=SELLER,
            actor_id=SELLER,
            reason="taking this on",
            occurred_at=NOW,
        )

        handed = next_state(
            current,
            state_id=uuid4(),
            stage=Stage.ENGAGED,
            owner_id=COLLEAGUE,
            actor_id=SELLER,
            reason="moving to their territory",
            occurred_at=NOW,
        )

        assert handed.stage is current.stage
        assert handed.owner_id == COLLEAGUE

    async def test_a_colleague_may_take_over_an_account_somebody_else_holds(self) -> None:
        """Two people believing they own an account is a real thing that
        happens, and the product settles it in the open: the taker is the
        actor, the reason is required, and the previous holder is on the row
        before it. Nothing is silently overwritten."""
        qualify, transition, repository, _, _ = build(make_score(value=60))
        opened = await open_one(qualify)
        assert opened.opportunity is not None
        await move(transition, opened.opportunity.id, Stage.ENGAGED, owner=COLLEAGUE)

        result = await move(
            transition,
            opened.opportunity.id,
            Stage.ENGAGED,
            actor=SELLER,
            owner=SELLER,
            reason="agreed at the pipeline review",
        )

        assert result.state.owner_id == SELLER
        history = await repository.history(WORKSPACE, opened.opportunity.id)
        assert history[-2].owner_id == COLLEAGUE

    async def test_a_state_change_that_changes_nothing_is_refused(self) -> None:
        qualify, transition, _, _, _ = build(make_score(value=60))
        opened = await open_one(qualify)
        assert opened.opportunity is not None
        await move(transition, opened.opportunity.id, Stage.ENGAGED, owner=COLLEAGUE)

        with pytest.raises(OpportunityError, match="already"):
            await move(transition, opened.opportunity.id, Stage.ENGAGED, owner=COLLEAGUE)

    async def test_a_reason_is_always_required(self) -> None:
        qualify, transition, _, _, _ = build(make_score(value=60))
        opened = await open_one(qualify)
        assert opened.opportunity is not None

        with pytest.raises(OpportunityError, match="no reason"):
            await move(transition, opened.opportunity.id, Stage.ENGAGED, reason="   ")

    async def test_history_is_complete_and_never_rewritten(self) -> None:
        qualify, transition, repository, _, _ = build(make_score(value=60))
        opened = await open_one(qualify)
        assert opened.opportunity is not None
        await move(transition, opened.opportunity.id, Stage.ENGAGED, owner=SELLER)
        await move(transition, opened.opportunity.id, Stage.CLOSED_LOST, reason="chose a rival")

        history = await repository.history(WORKSPACE, opened.opportunity.id)

        assert [s.stage for s in history] == [Stage.TRACKING, Stage.ENGAGED, Stage.CLOSED_LOST]
        assert [s.sequence for s in history] == [0, 1, 2]
        assert all(s.reason.strip() for s in history)


class TestStageRules:
    def test_a_won_deal_is_terminal(self) -> None:
        assert allowed_from(Stage.CLOSED_WON) == frozenset()

    def test_a_lost_or_dismissed_opportunity_may_reopen(self) -> None:
        assert Stage.TRACKING in allowed_from(Stage.CLOSED_LOST)
        assert Stage.ENGAGED in allowed_from(Stage.DISMISSED)

    def test_dismissal_is_reachable_without_ever_engaging(self) -> None:
        """`DISMISSED` is feedback about Signora's judgement, so it must be
        available the moment a suggestion appears."""
        assert Stage.DISMISSED in allowed_from(Stage.TRACKING)

    async def test_reopening_is_a_transition_not_a_new_opportunity(self) -> None:
        qualify, transition, repository, _, _ = build(make_score(value=60))
        opened = await open_one(qualify)
        assert opened.opportunity is not None
        await move(transition, opened.opportunity.id, Stage.CLOSED_LOST)

        result = await move(
            transition, opened.opportunity.id, Stage.ENGAGED, reason="they came back"
        )

        assert result.opportunity.id == opened.opportunity.id
        assert len(repository.rows) == 1

    async def test_a_won_deal_cannot_be_reopened(self) -> None:
        qualify, transition, _, _, _ = build(make_score(value=60))
        opened = await open_one(qualify)
        assert opened.opportunity is not None
        await move(transition, opened.opportunity.id, Stage.ENGAGED)
        await move(transition, opened.opportunity.id, Stage.CLOSED_WON, reason="signed")

        with pytest.raises(OpportunityError, match="does not reopen"):
            await move(transition, opened.opportunity.id, Stage.ENGAGED, reason="again")

    def test_advancing_always_requires_an_actor(self) -> None:
        """Structural: there is no machine path to `next_state`, because the
        signature demands a person."""
        import inspect

        parameter = inspect.signature(next_state).parameters["actor_id"]

        assert parameter.default is inspect.Parameter.empty
        assert parameter.annotation == "UUID"


class TestOpportunitiesOutliveTheirScore:
    async def test_an_expiring_score_changes_no_stage(self) -> None:
        """Nothing happening at a company is not evidence a deal is dead."""
        qualify, transition, repository, _, _ = build(make_score(value=60, valid_for_days=10))
        opened = await open_one(qualify)
        assert opened.opportunity is not None
        await move(transition, opened.opportunity.id, Stage.ENGAGED)

        queries = OpportunityQueries(
            repository=repository,
            policies=FakePolicyRepository(),
            scores=FakeBuyingScoreReader(make_score(value=60, valid_for_days=10)),
            artifact=ARTIFACT,
        )
        tracked = await queries.tracked(WORKSPACE, ENTITY, now=NOW + timedelta(days=40))

        assert tracked is not None
        assert tracked.state.stage is Stage.ENGAGED, "workflow must not move on its own"
        assert tracked.evidence_state is EvidenceState.STALE

    def test_a_falling_score_reads_as_cooling(self) -> None:
        opportunity = _opportunity_at(70)

        assert (
            evidence_state(opportunity, make_score(value=50), NOW) is EvidenceState.COOLING
        )

    def test_a_holding_score_reads_as_current(self) -> None:
        opportunity = _opportunity_at(70)

        assert (
            evidence_state(opportunity, make_score(value=68), NOW) is EvidenceState.CURRENT
        )

    def test_no_score_at_all_reads_as_stale(self) -> None:
        assert evidence_state(_opportunity_at(70), None, NOW) is EvidenceState.STALE

    async def test_the_originating_score_is_still_explainable_after_it_is_replaced(
        self,
    ) -> None:
        original = make_score(value=60)
        qualify, _, repository, policies, _ = build(original)
        opened = await open_one(qualify)
        assert opened.opportunity is not None

        # A newer score exists; the reader no longer serves the original as
        # current, but the citation still resolves against it.
        queries = OpportunityQueries(
            repository=repository,
            policies=policies,
            scores=FakeBuyingScoreReader(original),
            artifact=ARTIFACT,
        )
        explanation = await queries.explanation(WORKSPACE, opened.opportunity.id)

        assert explanation is not None
        assert explanation.originating_score is not None
        assert explanation.originating_score.score.id == original.id

    async def test_nothing_in_this_module_closes_an_opportunity(self) -> None:
        """Asserted over the module's own surface: there is no disqualify,
        no auto-close, and no expire."""
        from modules.opportunity_engine.application import qualify as qualify_module
        from modules.opportunity_engine.interface import handlers

        names = set(dir(qualify_module)) | set(dir(handlers))

        assert not {
            name
            for name in names
            if any(word in name.lower() for word in ("disqualify", "close", "expire", "revoke"))
        }


class TestWorkflowStoresNoIntelligence:
    def test_the_aggregate_holds_no_current_score(self) -> None:
        import inspect

        fields = set(inspect.get_annotations(Opportunity, eval_str=True))

        assert "current_score" not in fields
        assert "evidence_state" not in fields
        assert "score_at_creation" in fields, "a historical fact is not a cache"


def _opportunity_at(value: int) -> Opportunity:
    return Opportunity(
        id=uuid4(),
        workspace_id=WORKSPACE,
        entity_id=ENTITY,
        generation=0,
        originating_buying_score_id=uuid4(),
        score_at_creation=value,
        contested_at_creation=False,
        qualification=Qualification.AUTOMATIC,
        policy_version=0,
        created_at=NOW,
        created_by=SELLER,
    )
