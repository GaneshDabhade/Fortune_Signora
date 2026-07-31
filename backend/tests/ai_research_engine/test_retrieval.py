"""Internal retrieval: the facts research may look at, and nothing else.

**Two kinds of test, deliberately, and the M9 lesson is why.** The real pipeline
is the only honest check that the translation is faithful — a hand-built
explanation is shaped by what is convenient to translate, which is the failure
mode M8's source test names. But *a property a fixture cannot vary is a property
the fixture cannot test*, and the seeded scenario produces no dissent and no
business event cited by two signals. Those are constructed.

Nothing here calls a model, and nothing here reaches a network.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.ai_platform.infrastructure.explanation import (
    BUYING_SCORE,
    CONTRIBUTION,
    OPPORTUNITY,
)
from modules.ai_research_engine.domain.retrieval import (
    BUSINESS_EVENT,
    DISSENTING_SIGNAL,
    RESEARCH_FACT_KINDS,
)
from modules.ai_research_engine.infrastructure.retrieval import (
    PROVIDER_SEPARATOR,
    OpportunityFactSource,
    assemble,
)
from modules.opportunity_engine.public import OpportunityExplanation
from signora_platform.db import tenant_scoped_session
from tests.opportunity_engine.test_opportunity_pipeline import _tracked
from tests.pipeline import opportunities


class TestTheTwoSourcesNeverAddressTheSameThing:
    """**The duplicate-truth guard, made executable.**

    M8 assembles `opportunity`, `buying_score` and `signal_contribution`.
    Research assembles what that omits. If the two sets ever intersected, one
    citation would resolve to two different sentences depending on which module
    assembled it — and both would be correct.
    """

    def test_the_kinds_are_disjoint(self) -> None:
        assert RESEARCH_FACT_KINDS.isdisjoint({OPPORTUNITY, BUYING_SCORE, CONTRIBUTION}), (
            "A research fact kind collides with one the AI Platform's assembler already "
            "emits. Two modules producing the same citation is duplicate truth, and the "
            "reader cannot tell which sentence it was shown."
        )

    def test_every_declared_kind_is_actually_emitted(self) -> None:
        """The positive control. A disjointness rule is satisfied by emitting
        nothing, so the declared set must match what the code can produce."""
        assert RESEARCH_FACT_KINDS == {BUSINESS_EVENT, DISSENTING_SIGNAL}


@pytest.mark.integration
class TestAgainstTheRealPipeline:
    async def test_it_retrieves_the_business_events_beneath_the_score(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The layer M8's assembler stops above, and the reason this exists."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            source = OpportunityFactSource(opportunities(session, workspace_id))
            facts = await source.facts_for(workspace_id, entity_id)

        assert facts, "the seeded account produced no retrievable facts"
        assert {fact.ref.kind for fact in facts} <= RESEARCH_FACT_KINDS
        assert any(fact.ref.kind == BUSINESS_EVENT for fact in facts)
        assert all(fact.workspace_id == workspace_id for fact in facts)

    async def test_every_fact_carries_a_summary_the_pipeline_authored(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Not a model's words. A business event's summary is rendered by the
        detection rule from its own facts, so what a customer reads and what an
        auditor checks cannot diverge."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            source = OpportunityFactSource(opportunities(session, workspace_id))
            facts = await source.facts_for(workspace_id, entity_id)

        assert all(fact.summary.strip() for fact in facts)

    async def test_reading_the_same_account_twice_produces_the_same_facts(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Retrieval feeds derivations whose output is content-addressed. If
        the tuple varied between reads, a finding's identity would vary with
        it — replay would stop being replay."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            source = OpportunityFactSource(opportunities(session, workspace_id))
            first = await source.facts_for(workspace_id, entity_id)
            second = await source.facts_for(workspace_id, entity_id)

        assert first == second

    async def test_an_account_with_no_opportunity_retrieves_nothing(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """An answer, not an absence: research runs on qualified opportunities,
        and an account without one has nothing to research."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            source = OpportunityFactSource(opportunities(session, workspace_id))
            facts = await source.facts_for(workspace_id, uuid4())

        assert facts == ()


async def _explanation(
    session_factory: async_sessionmaker[AsyncSession],
    admin_session_factory: async_sessionmaker[AsyncSession],
) -> tuple[OpportunityExplanation, UUID]:
    """A real explanation, then varied in memory.

    The seeded scenario cannot produce dissent or a shared business event, so
    the cases below are built by *replacing* fields on a genuine explanation
    rather than by inventing one — the structure stays whatever the pipeline
    actually produces.
    """
    workspace_id, user_id, entity_id, _ = await _tracked(
        session_factory, admin_session_factory, "northwind"
    )
    async with tenant_scoped_session(
        session_factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        tracked = await opportunities(session, workspace_id).tracked(workspace_id, entity_id)
        assert tracked is not None
        explanation = await opportunities(session, workspace_id).explanation(
            workspace_id, tracked.opportunity.id
        )
    assert explanation is not None
    return explanation, workspace_id


@pytest.mark.integration
class TestPropertiesTheSeededScenarioCannotVary:
    async def test_an_event_cited_by_two_signals_is_retrieved_once(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Two signals may rest on one business event. Retrieved twice, it
        would be two premises where the pipeline recorded one — the
        corroboration defect in miniature."""
        explanation, _ = await _explanation(session_factory, admin_session_factory)
        score = explanation.originating_score
        assert score is not None and score.signals

        first = score.signals[0]
        assert first.business_events, "the seeded signal cites no business events"
        twin = replace(first, signal=replace(first.signal, id=uuid4()))
        widened = replace(explanation, originating_score=replace(score, signals=(first, twin)))

        facts = assemble(widened)
        events = [fact for fact in facts if fact.ref.kind == BUSINESS_EVENT]
        assert len(events) == len({fact.ref for fact in events})

    async def test_the_order_signals_arrive_in_is_not_a_fact(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Why the final sort is load-bearing**, and not merely tidy.

        Two signals citing two different events produce those events in
        traversal order. Without a canonical order, the same account would
        assemble to two different tuples depending on how the query happened
        to return its signals — a hidden input, and one that would propagate
        into the identity of every finding derived from these facts.
        """
        explanation, _ = await _explanation(session_factory, admin_session_factory)
        score = explanation.originating_score
        assert score is not None and score.signals

        signal = score.signals[0]
        assert signal.business_events
        left = replace(
            signal,
            signal=replace(signal.signal, id=uuid4()),
            business_events=(replace(signal.business_events[0], id=uuid4()),),
        )
        right = replace(
            signal,
            signal=replace(signal.signal, id=uuid4()),
            business_events=(replace(signal.business_events[0], id=uuid4()),),
        )

        forward = assemble(replace(explanation, originating_score=replace(score, signals=(left, right))))
        reverse = assemble(replace(explanation, originating_score=replace(score, signals=(right, left))))

        assert forward == reverse
        assert len(forward) == 2

    async def test_dissent_is_retrieved(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The Buying Score Engine carries outweighed readings through six
        stages so they are not netted away. M8's assembler drops them, so until
        here they are visible to nothing."""
        explanation, _ = await _explanation(session_factory, admin_session_factory)
        score = explanation.originating_score
        assert score is not None and score.signals

        outweighed = replace(score.signals[0], signal=replace(score.signals[0].signal, id=uuid4()))
        contested = replace(explanation, originating_score=replace(score, dissent=(outweighed,)))

        facts = assemble(contested)
        dissenting = [fact for fact in facts if fact.ref.kind == DISSENTING_SIGNAL]
        assert len(dissenting) == 1
        assert dissenting[0].ref.id == outweighed.signal.id

    async def test_a_corroborated_event_names_every_provider_that_agreed(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The fact nothing in the product surfaces today.** Provider
        agreement is what `SupportBasis` derives from, and the reachable chain
        exposes it only on a business event."""
        explanation, _ = await _explanation(session_factory, admin_session_factory)
        score = explanation.originating_score
        assert score is not None and score.signals

        signal = score.signals[0]
        event = replace(
            signal.business_events[0], corroborating_providers=("coresignal", "apollo")
        )
        widened = replace(
            explanation,
            originating_score=replace(
                score, signals=(replace(signal, business_events=(event,)),)
            ),
        )

        facts = assemble(widened)
        attributes = dict(next(f for f in facts if f.ref.kind == BUSINESS_EVENT).attributes)
        assert attributes["provider_count"] == 2
        assert attributes["corroborated"] is True
        assert attributes["providers"] == PROVIDER_SEPARATOR.join(("apollo", "coresignal"))

    async def test_provider_order_out_of_the_pipeline_is_not_a_fact(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Insertion order is a hidden input. Two orderings of one agreement
        must produce one fact, or the same account digests differently."""
        explanation, _ = await _explanation(session_factory, admin_session_factory)
        score = explanation.originating_score
        assert score is not None and score.signals
        signal = score.signals[0]

        def _with(providers: tuple[str, ...]) -> tuple[object, ...]:
            event = replace(signal.business_events[0], corroborating_providers=providers)
            widened = replace(
                explanation,
                originating_score=replace(
                    score, signals=(replace(signal, business_events=(event,)),)
                ),
            )
            return assemble(widened)

        assert _with(("apollo", "coresignal")) == _with(("coresignal", "apollo"))

    async def test_an_uncorroborated_event_says_so(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        explanation, _ = await _explanation(session_factory, admin_session_factory)
        score = explanation.originating_score
        assert score is not None and score.signals
        signal = score.signals[0]

        event = replace(signal.business_events[0], corroborating_providers=("apollo",))
        widened = replace(
            explanation,
            originating_score=replace(
                score, signals=(replace(signal, business_events=(event,)),)
            ),
        )

        attributes = dict(
            next(f for f in assemble(widened) if f.ref.kind == BUSINESS_EVENT).attributes
        )
        assert attributes["provider_count"] == 1
        assert attributes["corroborated"] is False

    async def test_an_explanation_with_no_score_retrieves_nothing(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """An opportunity outlives the score that opened it. Nothing beneath a
        score is reachable without one, and inventing a fact to fill the gap is
        the thing retrieval must never do."""
        explanation, _ = await _explanation(session_factory, admin_session_factory)

        assert assemble(replace(explanation, originating_score=None)) == ()


@pytest.mark.integration
class TestTypedRatherThanRendered:
    async def test_a_date_is_a_date_and_a_count_is_an_int(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """These facts feed deterministic comparison, not a prompt. A count
        compared as text would make `1` and `"1"` equal by accident — the
        type-loss the canonical form tags to prevent."""
        explanation, _ = await _explanation(session_factory, admin_session_factory)
        facts = assemble(explanation)
        attributes = dict(next(f for f in facts if f.ref.kind == BUSINESS_EVENT).attributes)

        assert isinstance(attributes["provider_count"], int)
        assert isinstance(attributes["corroborated"], bool)
        assert isinstance(attributes["occurred_on"], type(datetime.now(UTC).date()))
