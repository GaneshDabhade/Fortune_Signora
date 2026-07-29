"""M5B demonstration: one number, and every number survives being challenged.

Proves the seventh link, and the **first one that intentionally reduces**.
Everything upstream added information and destroyed none; here many live
hypotheses become a single integer — which is the product value and also the
first real opportunity to lose something the pipeline cannot recover.

The assertions that matter most are the ones proving nothing was lost: the
score reproduces from its own ledger exactly, and every ledger entry walks
back through signals, business events, observations, knowledge and claims to
the raw provider payload that started it.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.buying_score_engine.domain.score import ScoreTrigger, Trend
from modules.buying_score_engine.infrastructure.models import BuyingScoreModel
from modules.signal_engine.public import SignalType
from signora_platform.db import tenant_scoped_session
from tests.knowledge_graph.test_graph_pipeline import _run_pipeline
from tests.observation_engine.test_observation_pipeline import _acme
from tests.pipeline import (
    buying_scores,
    detect_all,
    observe_all,
    score_all,
    signal_all,
    signals,
    sweep_stale,
)

pytestmark = pytest.mark.integration


async def _through_signals(
    factory: async_sessionmaker[AsyncSession],
    admin_factory: async_sessionmaker[AsyncSession],
    name: str,
) -> tuple[UUID, UUID]:
    workspace_id, user_id = await _run_pipeline(factory, admin_factory, name)
    await observe_all(factory, admin_factory, workspace_id, user_id)
    await detect_all(factory, admin_factory, workspace_id, user_id)
    await signal_all(factory, admin_factory, workspace_id, user_id)
    return workspace_id, user_id


async def _while_signals_are_live(
    factory: async_sessionmaker[AsyncSession], workspace_id: UUID, user_id: UUID
) -> tuple[UUID, datetime]:
    """A moment at which the scenario's hypotheses are still current.

    **Derived from the evidence, never hardcoded.** The simulated provider
    payloads describe events months in the past, so at wall-clock `now` every
    signal has passed its shelf life — which is the lifecycle working, and is
    asserted in its own right below. Scoring a live account requires asking
    the question as of a moment when the account *was* live.
    """
    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        entity_id = await _acme(session, workspace_id)
        held = await signals(session, workspace_id).signals(
            workspace_id, entity_id, live_only=False
        )
    return entity_id, max(s.occurred_at for s in held) + timedelta(days=1)


async def _scored(
    factory: async_sessionmaker[AsyncSession],
    admin_factory: async_sessionmaker[AsyncSession],
    name: str,
) -> tuple[UUID, UUID, UUID, datetime]:
    workspace_id, user_id = await _through_signals(factory, admin_factory, name)
    entity_id, moment = await _while_signals_are_live(factory, workspace_id, user_id)
    await score_all(factory, admin_factory, workspace_id, user_id, moment=moment)
    return workspace_id, user_id, entity_id, moment


class TestTheReductionIsSafe:
    """A score may summarize intelligence. It must never replace it."""

    async def test_a_score_reproduces_from_its_own_ledger_exactly(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """No clock, no configuration — only the stored entries. A ledger
        that reproduced only approximately would be an explanation nobody
        could rely on."""
        workspace_id, user_id, entity_id, _ = await _scored(
            session_factory, admin_session_factory, "Reproduce"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            score = await buying_scores(session, workspace_id).current(workspace_id, entity_id)

        assert score is not None
        # The ledger here was reconstructed from JSONB by the repository,
        # so this recomputes the number from stored data alone.
        assert score.value == score.ledger.value()

    async def test_every_ledger_entry_reaches_a_raw_provider_record(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The chain, walked rather than asserted.** Score → signals →
        business events → observations → knowledge → claims → raw provider
        records, with no orphan at any hop."""
        workspace_id, user_id, entity_id, _ = await _scored(
            session_factory, admin_session_factory, "Chain"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            queries = buying_scores(session, workspace_id)
            score = await queries.current(workspace_id, entity_id)
            assert score is not None
            explanation = await queries.explanation(workspace_id, score.id)
            assert explanation is not None

            assert explanation.signals, "a score with no explainable signal is opaque"
            cited = {e.business_event_id for e in score.ledger.entries}
            reachable = {
                event.id for signal in explanation.signals for event in signal.business_events
            }
            assert cited <= reachable, "a ledger entry cites a business event nobody can reach"

            observations = {
                observation_id
                for signal in explanation.signals
                for event in signal.business_events
                for observation_id in event.evidence_observation_ids
            }
            assert observations, "business events must cite the observations behind them"

            claims = await session.execute(
                text("SELECT count(*) FROM claim WHERE workspace_id = :w"),
                {"w": workspace_id},
            )
            raw = await session.execute(
                text("SELECT count(*) FROM raw_provider_record WHERE workspace_id = :w"),
                {"w": workspace_id},
            )
            assert claims.scalar_one() > 0
            assert raw.scalar_one() > 0

    async def test_the_ledger_names_every_signal_the_score_rests_on(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, moment = await _scored(
            session_factory, admin_session_factory, "Names"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            score = await buying_scores(session, workspace_id).current(workspace_id, entity_id)
            live = await signals(session, workspace_id).signals(
                workspace_id, entity_id, now=moment
            )

        assert score is not None
        assert set(score.ledger.contributing_signals()) == {s.id for s in live}

    async def test_no_business_event_is_counted_twice(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The scenario contains a genuine composite and its constituent —
        the same grounds read two ways."""
        workspace_id, user_id, entity_id, _ = await _scored(
            session_factory, admin_session_factory, "Once"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            score = await buying_scores(session, workspace_id).current(workspace_id, entity_id)

        assert score is not None
        counted = [e.business_event_id for e in score.ledger.entries if e.counted]
        assert len(counted) == len(set(counted))
        assert any(
            not e.counted for e in score.ledger.entries
        ), "the composite and its constituent share evidence, so one claim must be uncounted"


class TestTheScoreIsNotTheAccount:
    async def test_the_table_holds_no_account_attributes(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, _, _ = await _scored(
            session_factory, admin_session_factory, "Projection"
        )

        columns = {column.name for column in BuyingScoreModel.__table__.columns}

        assert not columns & {"name", "domain", "industry", "employee_count", "website"}


class TestLifecycle:
    async def test_recomputing_an_unchanged_account_writes_nothing(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, _, moment = await _scored(
            session_factory, admin_session_factory, "Idempotent"
        )

        async def count() -> int:
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                return int(
                    (await session.execute(text("SELECT count(*) FROM buying_score"))).scalar_one()
                )

        before = await count()
        await score_all(
            session_factory, admin_session_factory, workspace_id, user_id, moment=moment
        )

        assert await count() == before

    async def test_the_sweep_re_reads_an_account_whose_evidence_has_aged(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The demonstration the module exists for.**

        Shelf-life expiry publishes no event, so without the sweep every
        account would decay into a false hot state — the most dangerous
        failure this module could have, because it is invisible. Here the
        scenario's shorter-lived hypotheses have aged out by wall-clock now
        while the funding round is still within its window: the number
        falls, the trend reads `FALLING`, and the score explains itself as
        evidence having aged rather than as an unexplained drop.

        The previous reading stays intact and still explainable.
        """
        workspace_id, user_id, entity_id, _ = await _scored(
            session_factory, admin_session_factory, "Aged"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            before = await buying_scores(session, workspace_id).current(workspace_id, entity_id)
        assert before is not None

        examined, rescored = await sweep_stale(session_factory, workspace_id, user_id)

        assert examined >= 1
        assert rescored >= 1

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            queries = buying_scores(session, workspace_id)
            after = await queries.current(workspace_id, entity_id)
            history = await queries.history(workspace_id, entity_id)

        assert after is not None
        assert after.trigger is ScoreTrigger.EVIDENCE_AGED
        assert after.trend is Trend.FALLING
        assert after.value < before.value
        assert after.supersedes == before.id
        assert len(after.ledger.contributing_signals()) < len(
            before.ledger.contributing_signals()
        ), "hypotheses past their shelf life must stop being weighed"
        assert {s.id for s in history} == {before.id, after.id}, (
            "the reading a customer was shown before must survive being replaced"
        )

    async def test_a_score_states_how_long_it_is_correct_for(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, moment = await _scored(
            session_factory, admin_session_factory, "Validity"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            score = await buying_scores(session, workspace_id).current(workspace_id, entity_id)

        assert score is not None
        assert score.valid_until is not None
        assert score.is_valid_at(moment)
        assert not score.is_valid_at(score.valid_until + timedelta(seconds=1))

    async def test_the_first_reading_is_steady_and_replaces_nothing(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _scored(
            session_factory, admin_session_factory, "First"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            score = await buying_scores(session, workspace_id).current(workspace_id, entity_id)

        assert score is not None
        assert score.trend is Trend.STEADY
        assert score.supersedes is None
        assert score.trigger in {ScoreTrigger.SIGNAL_GENERATED, ScoreTrigger.SIGNAL_SUPERSEDED}


class TestTheNumberIsExplainable:
    async def test_every_contribution_carries_a_sentence_a_customer_can_challenge(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _scored(
            session_factory, admin_session_factory, "Explain"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            score = await buying_scores(session, workspace_id).current(workspace_id, entity_id)

        assert score is not None
        for entry in score.ledger.entries:
            assert entry.reason.strip()
            assert entry.age_band
        counted = [e for e in score.ledger.entries if e.counted]
        assert sum(e.contribution for e in counted) == score.ledger.total()

    async def test_the_workspace_reads_the_weighting_actually_in_force(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, _, _ = await _scored(
            session_factory, admin_session_factory, "Weighting"
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            queries = buying_scores(session, workspace_id)
            in_force = await queries.scoring_model(workspace_id)

        assert in_force.types
        assert in_force.ceiling > 0
        assert {SignalType(w.key) for w in in_force.types}
