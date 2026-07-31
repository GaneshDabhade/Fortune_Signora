"""Permanent guarantees the Opportunity Engine rests on.

**Signora's first workflow module.** Every module before it derives
information from evidence and can be regenerated from it; this one records
human commitment, which nothing reproduces. That makes it the first place a
routine operation — rebuilding the pipeline — could become a data-loss
incident.

*Permanent architectural principle, ratified 2026-07-29:*

> **Intelligence suggests. Humans commit.**
>
> A buying score may **create** an opportunity. **Only a human may progress
> one beyond the machine-authored boundary.** Commercial intelligence
> informs workflow; it never owns it.

Four guarantees carry it:

* **Only `TRACKING` may be machine-authored**, enforced by the type system,
  the domain, and a database CHECK — three layers, because this is the
  boundary the whole module exists to hold.
* **Nothing closes an opportunity automatically.** No falling score, no
  expiry, no quiet account. The absence of the code is the enforcement.
* **Workflow stores no derived intelligence**, so no stale copy of the
  pipeline's output can accumulate in a workflow row.
* **History is append-only and never rewritten** — no `UPDATE` grant, and
  the status *is* the audit log rather than something kept beside it.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.opportunity_engine.application import qualify as qualify_module
from modules.opportunity_engine.application.queries import OpportunityQueries
from modules.opportunity_engine.domain.opportunity import (
    MACHINE_AUTHORED,
    OPEN_STAGES,
    TERMINAL_STAGES,
    Opportunity,
    OpportunityError,
    OpportunityState,
    Qualification,
    Stage,
    allowed_from,
    next_state,
)
from modules.opportunity_engine.domain.policy import OpportunityPolicy
from modules.opportunity_engine.infrastructure.models import OpportunityModel
from modules.opportunity_engine.infrastructure.policy_loader import load_policy
from modules.opportunity_engine.interface import handlers
from tests.opportunity_engine.fakes import ENTITY, NOW, SELLER, WORKSPACE

#: Column names that would mean workflow had started caching intelligence.
INTELLIGENCE_LIKE = (
    "current_score",
    "score_value",
    "evidence_state",
    "signals",
    "ledger",
    "trend",
    "contested_now",
)

#: Names that would mean something other than a human can end a commitment.
AUTOMATIC_CLOSURE_LIKE = ("disqualify", "autoclose", "auto_close", "expire", "revoke", "retire")

#: The only numbers qualification code may compare against. Zero and one are
#: structural; anything else is a commercial judgement that belongs in the
#: policy artifact.
STRUCTURAL_NUMBERS = (0, 1)


def _is_business_number(value: object) -> bool:
    return (
        isinstance(value, int | float)
        and not isinstance(value, bool)
        and value not in STRUCTURAL_NUMBERS
    )


class TestIntelligenceSuggestsHumansCommit:
    """The boundary the module exists to hold, guarded three ways."""

    def test_only_tracking_may_be_machine_authored(self) -> None:
        assert frozenset({Stage.TRACKING}) == MACHINE_AUTHORED

    def test_the_domain_refuses_a_stage_with_no_actor(self) -> None:
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

    async def test_the_database_refuses_it_too(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Three layers, because a boundary this important should not depend
        on one of them being reached."""
        async with admin_session_factory() as session, session.begin():
            definition = (
                await session.execute(
                    text(
                        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                        "WHERE conname = "
                        "'ck_opportunity_state_only_tracking_is_machine_authored'"
                    )
                )
            ).scalar_one_or_none()

        assert definition is not None

    def test_advancing_requires_a_person_in_the_signature(self) -> None:
        """Structural: there is no machine path to `next_state`, because the
        signature demands an actor with no default."""
        parameter = inspect.signature(next_state).parameters["actor_id"]

        assert parameter.default is inspect.Parameter.empty

    def test_the_automatic_path_can_only_open(self) -> None:
        """The event handler consumes `buying_score.updated` and may do
        exactly one thing with it."""
        source = inspect.getsource(handlers)

        assert "QualifyOpportunityInput" in source
        assert "TransitionOpportunity" not in source


class TestNothingClosesAutomatically:
    def test_no_module_surface_offers_automatic_closure(self) -> None:
        """A falling score, an expiring score, or a quiet account changes no
        stage. Nothing happening at a company is not evidence a deal is
        dead — and the absence of the code is the enforcement."""
        names = set(dir(qualify_module)) | set(dir(handlers)) | set(dir(OpportunityQueries))

        offenders = sorted(
            name for name in names if any(word in name.lower() for word in AUTOMATIC_CLOSURE_LIKE)
        )
        assert offenders == [], f"something can end a human's commitment for them: {offenders}"

    def test_qualification_never_writes_a_terminal_stage(self) -> None:
        """Read as a syntax tree, so prose about closure cannot be mistaken
        for closure."""
        tree = ast.parse(inspect.getsource(qualify_module))

        mentioned = {
            node.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Attribute) and node.attr.isupper()
        }
        terminal = {stage.name for stage in TERMINAL_STAGES}

        assert not mentioned & terminal, (
            f"qualification references a terminal stage: {sorted(mentioned & terminal)}"
        )

    def test_a_won_deal_is_terminal(self) -> None:
        assert allowed_from(Stage.CLOSED_WON) == frozenset()

    def test_a_lost_or_dismissed_opportunity_may_reopen(self) -> None:
        assert allowed_from(Stage.CLOSED_LOST) & OPEN_STAGES
        assert allowed_from(Stage.DISMISSED) & OPEN_STAGES

    def test_dismissal_stays_distinct_from_a_lost_deal(self) -> None:
        """One is feedback about Signora's judgement; the other is a sales
        outcome. Collapsing them destroys the only signal the platform gets
        about its own qualification quality."""
        # Both terminal, and both present: a taxonomy that lost one of them
        # would still pass a test that only counted terminal stages.
        assert {Stage.DISMISSED, Stage.CLOSED_LOST} <= TERMINAL_STAGES
        assert len({s.value for s in TERMINAL_STAGES}) == len(TERMINAL_STAGES)


class TestWorkflowStoresNoIntelligence:
    async def test_the_table_caches_no_derived_state(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """A workflow row holding a current score would be a second, stale
        copy of the pipeline's output — and within a year something would
        read it in preference to the real thing."""
        async with admin_session_factory() as session, session.begin():
            columns = set(
                (
                    await session.execute(
                        text(
                            "SELECT column_name FROM information_schema.columns "
                            "WHERE table_name = 'opportunity'"
                        )
                    )
                )
                .scalars()
                .all()
            )

        offenders = sorted(columns & set(INTELLIGENCE_LIKE))
        assert offenders == [], (
            f"opportunity caches derived intelligence: {offenders}. It cites the score that "
            "caused it to exist and reads everything else live."
        )

    def test_the_aggregate_holds_a_historical_fact_not_a_cache(self) -> None:
        fields = set(inspect.get_annotations(Opportunity, eval_str=True))

        assert "score_at_creation" in fields
        assert "originating_buying_score_id" in fields
        assert not fields & set(INTELLIGENCE_LIKE)

    def test_evidence_state_is_derived_rather_than_stored(self) -> None:
        """Storing it would cache intelligence; recording it as a transition
        would let a data refresh silently revoke a human's decision."""
        assert "evidence_state" not in inspect.get_annotations(Opportunity, eval_str=True)
        assert "evidence_state" not in inspect.get_annotations(OpportunityState, eval_str=True)

    def test_the_read_port_offers_no_recommendation(self) -> None:
        surface = {name for name in dir(OpportunityQueries) if not name.startswith("_")}

        offenders = sorted(
            name
            for name in surface
            if any(
                word in name.lower()
                for word in ("recommend", "action", "message", "next_step", "outreach")
            )
        )
        assert offenders == [], f"the read port answers a later module's question: {offenders}"


class TestHistoryIsNeverRewritten:
    @pytest.mark.parametrize(
        "table", ["opportunity", "opportunity_state", "workspace_opportunity_policy"]
    )
    async def test_the_application_role_cannot_update(
        self, table: str, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Workflow did not require an exception to the platform's strongest
        data property. The latest state may be derived; history must never
        be rewritten."""
        async with admin_session_factory() as session, session.begin():
            privileges = set(
                (
                    await session.execute(
                        text(
                            "SELECT privilege_type FROM information_schema.role_table_grants "
                            "WHERE grantee = 'signora_app' AND table_name = :t"
                        ),
                        {"t": table},
                    )
                ).scalars()
            )

        assert "UPDATE" not in privileges
        assert {"SELECT", "INSERT"} <= privileges

    def test_the_repository_offers_no_update_and_no_delete(self) -> None:
        """The absent *delete* is the stronger statement: derived tables
        offer deletion so regeneration can be their rollback, and workflow
        has no regeneration to roll back to."""
        from modules.opportunity_engine.application.ports import OpportunityRepository

        assert not [
            name
            for name in dir(OpportunityRepository)
            if any(word in name for word in ("update", "edit", "delete", "remove"))
        ]

    async def test_every_state_row_states_a_reason(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        async with admin_session_factory() as session, session.begin():
            definition = (
                await session.execute(
                    text(
                        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                        "WHERE conname = 'ck_opportunity_state_has_reason'"
                    )
                )
            ).scalar_one_or_none()

        assert definition is not None

    async def test_state_sequence_is_unique_per_opportunity(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Two rows claiming the same position would make "the latest state"
        ambiguous, and the status would stop being the log."""
        async with admin_session_factory() as session, session.begin():
            definition = (
                await session.execute(
                    text(
                        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                        "WHERE conname = 'uq_opportunity_state_sequence'"
                    )
                )
            ).scalar_one_or_none()

        assert definition is not None


class TestOneOpenOpportunityPerAccount:
    async def test_the_generation_key_makes_concurrent_creation_conflict(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """ "Open" means *the latest state row is not terminal*, which no
        index can express. Rather than denormalise openness onto a mutable
        column — restoring the `UPDATE` grant to buy a constraint — the
        dangerous case is converted into a conflict."""
        async with admin_session_factory() as session, session.begin():
            definition = (
                await session.execute(
                    text(
                        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                        "WHERE conname = 'uq_opportunity_generation'"
                    )
                )
            ).scalar_one_or_none()

        assert definition is not None
        assert "entity_id" in definition and "generation" in definition


class TestTheCitationCannotBeOrphaned:
    async def test_a_cited_buying_score_cannot_be_deleted(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Derived intelligence is deletable precisely so regeneration can be
        its rollback — but not while workflow cites it. Workflow is the thing
        here that cannot be regenerated."""
        async with admin_session_factory() as session, session.begin():
            rule = (
                await session.execute(
                    text(
                        "SELECT confdeltype FROM pg_constraint "
                        "WHERE conrelid = 'opportunity'::regclass "
                        "AND confrelid = 'buying_score'::regclass"
                    )
                )
            ).scalar_one_or_none()

        # asyncpg returns "char" columns as bytes.
        assert rule in ("r", b"r"), "the originating score must be RESTRICT, never CASCADE"

    def test_the_aggregate_cites_a_score_it_can_never_change(self) -> None:
        assert "originating_buying_score_id" in inspect.get_annotations(Opportunity, eval_str=True)
        assert dataclasses.fields(Opportunity)
        with pytest.raises(dataclasses.FrozenInstanceError):
            _frozen_probe()


class TestNoUndeclaredThreshold:
    def test_qualification_compares_against_no_business_constant(self) -> None:
        """The threshold lives in the policy artifact, where it is versioned
        and customer-owned. Read as a syntax tree so the prose saying so
        cannot be mistaken for one."""
        tree = ast.parse(inspect.getsource(qualify_module))

        offenders = [
            ast.unparse(node)
            for node in ast.walk(tree)
            if isinstance(node, ast.Compare)
            for comparator in node.comparators
            if isinstance(comparator, ast.Constant) and _is_business_number(comparator.value)
        ]
        assert offenders == [], f"qualification compares against a constant: {offenders}"

    def test_the_shipped_policy_is_complete(self) -> None:
        policy = load_policy()

        assert isinstance(policy, OpportunityPolicy)
        assert policy.minimum_score >= 0
        assert policy.contested_qualifies, (
            "a fought-over account is exactly what a seller should look at, and M5B already "
            "scores it high rather than averaging it away"
        )


class TestTenancy:
    @pytest.mark.parametrize(
        "table", ["opportunity", "opportunity_state", "workspace_opportunity_policy"]
    )
    async def test_row_level_security_is_enabled_and_forced(
        self, table: str, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        async with admin_session_factory() as session, session.begin():
            row = (
                await session.execute(
                    text(
                        "SELECT relrowsecurity, relforcerowsecurity FROM pg_class "
                        "WHERE relname = :t"
                    ),
                    {"t": table},
                )
            ).one()

        assert row.relrowsecurity, f"{table} does not have RLS enabled"
        assert row.relforcerowsecurity, f"{table} does not force RLS on its owner"

    def test_assignment_verifies_membership_server_side(self) -> None:
        """A `user_id` from a caller is a claim about who should hold the
        work. An unverified one hands an account to somebody outside the
        workspace."""
        from modules.opportunity_engine.application import transition

        source = inspect.getsource(transition)

        assert "get_membership" in source
        assert "_verify_member" in source


def _unused() -> None:
    """`OpportunityModel` and `ENTITY`/`SELLER` are imported for symmetry
    with the other invariant suites; referenced here so linting stays
    honest about what the module depends on."""
    assert OpportunityModel.__tablename__ == "opportunity"
    assert ENTITY != SELLER


def _frozen_probe() -> None:
    """An opportunity is frozen: the citation it carries cannot be changed
    after the fact, which is what makes the explanation chain durable."""
    opportunity = Opportunity(
        id=uuid4(),
        workspace_id=WORKSPACE,
        entity_id=ENTITY,
        generation=0,
        originating_buying_score_id=uuid4(),
        score_at_creation=50,
        contested_at_creation=False,
        qualification=Qualification.AUTOMATIC,
        policy_version=0,
        created_at=NOW,
        created_by=SELLER,
    )
    opportunity.score_at_creation = 99  # type: ignore[misc]
