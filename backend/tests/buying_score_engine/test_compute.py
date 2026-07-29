"""The use case, the sweep, and the read surface, against fakes.

What is under test is the module's contract with the rest of the pipeline:
an unchanged account writes nothing, an account with no evidence gets no
reading at all, ageing is what the sweep responds to, and a customer's own
weighting is honoured without ever letting them redefine what a signal
means.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from modules.buying_score_engine.application.compute import (
    ComputeBuyingScore,
    ComputeBuyingScoreInput,
    ComputeBuyingScoreResult,
)
from modules.buying_score_engine.application.queries import BuyingScoreQueries
from modules.buying_score_engine.application.sweep import SweepStaleScores
from modules.buying_score_engine.domain.score import ScoreTrigger, Trend
from modules.buying_score_engine.domain.scoring_model import Posture
from modules.buying_score_engine.domain.workspace_model import (
    ScoringOverrides,
    WorkspaceScoringModel,
    resolve_model,
)
from modules.buying_score_engine.infrastructure.model_loader import load_scoring_model
from modules.signal_engine.infrastructure.catalog_loader import load_catalog
from modules.signal_engine.public import Signal, SignalType
from tests.buying_score_engine.fakes import (
    ENTITY,
    WORKSPACE,
    FakeScoreRepository,
    FakeScoringModelRepository,
    FakeSignalQueries,
    make_signal,
)
from tests.knowledge_graph.fakes import RecordingPublisher

NOW = datetime(2026, 3, 1, tzinfo=UTC)
ARTIFACT = load_scoring_model()
CATALOG = load_catalog()


def build(
    signals: Sequence[Signal],
    *,
    models: FakeScoringModelRepository | None = None,
    moment: datetime = NOW,
    repository: FakeScoreRepository | None = None,
) -> tuple[ComputeBuyingScore, FakeScoreRepository, FakeScoringModelRepository, RecordingPublisher]:
    repository = repository or FakeScoreRepository()
    models = models or FakeScoringModelRepository()
    publisher = RecordingPublisher()
    compute = ComputeBuyingScore(
        repository=repository,
        models=models,
        signals=FakeSignalQueries(tuple(signals), CATALOG),
        artifact=ARTIFACT,
        publisher=publisher,
        session=cast(AsyncSession, None),
        clock=lambda: moment,
    )
    return compute, repository, models, publisher


async def run(
    compute: ComputeBuyingScore, trigger: ScoreTrigger = ScoreTrigger.SIGNAL_GENERATED
) -> ComputeBuyingScoreResult:
    return await compute.execute(
        ComputeBuyingScoreInput(workspace_id=WORKSPACE, entity_id=ENTITY, trigger=trigger),
        correlation_id=uuid4(),
    )


class TestComputing:
    async def test_a_score_is_produced_with_its_ledger_and_announced(self) -> None:
        signal = make_signal(signal_type=SignalType.ACTIVE_EVALUATION, events=(uuid4(),))
        compute, repository, _, publisher = build((signal,))

        result = await run(compute)

        assert result.changed
        assert result.score is not None
        assert result.score.value == result.score.ledger.value()
        assert len(repository.rows) == 1

        published = publisher.events[0]
        assert published.event_type == "buying_score.updated"
        payload = published.to_payload()
        assert payload["score"] == result.score.value
        assert payload["contested"] is False
        assert payload["source_signal_ids"] == [str(signal.id)]

    async def test_an_account_with_no_evidence_gets_no_reading_at_all(self) -> None:
        """A zero is a statement, and Signora has not made one."""
        compute, repository, _, publisher = build(())

        result = await run(compute)

        assert not result.changed
        assert result.score is None
        assert repository.rows == []
        assert publisher.events == []

    async def test_recomputing_an_unchanged_account_writes_and_announces_nothing(self) -> None:
        signal = make_signal(signal_type=SignalType.ACTIVE_EVALUATION, events=(uuid4(),))
        compute, repository, _, publisher = build((signal,))

        await run(compute)
        again = await run(compute)

        assert not again.changed
        assert len(repository.rows) == 1
        assert len(publisher.events) == 1

    async def test_new_evidence_supersedes_the_previous_reading(self) -> None:
        first_signal = make_signal(signal_type=SignalType.ACTIVE_EVALUATION, events=(uuid4(),))
        compute, repository, _, _ = build((first_signal,))
        first = await run(compute)

        compute2, repository, _, publisher = build(
            (first_signal, make_signal(signal_type=SignalType.BUDGET_UNLOCKED, events=(uuid4(),))),
            repository=repository,
        )
        second = await run(compute2, ScoreTrigger.SIGNAL_GENERATED)

        assert second.changed
        assert second.score is not None and first.score is not None
        assert second.score.supersedes == first.score.id
        assert second.score.trend is Trend.RISING
        assert len(repository.rows) == 2

    async def test_a_contested_account_publishes_its_dissent(self) -> None:
        expansion = make_signal(
            signal_type=SignalType.EXPANSION_OPPORTUNITY, events=(uuid4(),)
        )
        contraction = make_signal(signal_type=SignalType.CONTRACTION_RISK, events=(uuid4(),))
        compute, _, _, publisher = build((expansion, contraction))

        result = await run(compute)

        assert result.score is not None and result.score.contested
        payload = publisher.events[0].to_payload()
        assert payload["contested"] is True
        assert payload["dissenting_signal_ids"] == [str(contraction.id)]


class TestCustomerWeighting:
    async def test_a_workspace_weighting_changes_the_number(self) -> None:
        signal = make_signal(signal_type=SignalType.ACTIVE_EVALUATION, events=(uuid4(),))
        models = FakeScoringModelRepository()
        compute, _, _, _ = build((signal,))
        default = await run(compute)

        await models.save(
            WorkspaceScoringModel(
                id=uuid4(),
                workspace_id=WORKSPACE,
                version=1,
                overrides=ScoringOverrides(
                    base_weights={SignalType.ACTIVE_EVALUATION: 5}
                ),
                created_at=NOW,
                created_by=uuid4(),
            )
        )
        tuned_compute, _, _, _ = build((signal,), models=models)
        tuned = await run(tuned_compute)

        assert tuned.score is not None and default.score is not None
        assert tuned.score.value < default.score.value
        assert tuned.score.scoring_model_version == 1

    async def test_an_unconfigured_workspace_falls_back_to_the_shipped_artifact(self) -> None:
        signal = make_signal(signal_type=SignalType.ACTIVE_EVALUATION, events=(uuid4(),))
        compute, _, _, _ = build((signal,))

        result = await run(compute)

        assert result.score is not None
        assert result.score.scoring_model_version == 0
        assert result.score.model_artifact_version == ARTIFACT.version

    def test_a_workspace_cannot_invert_what_a_signal_type_means(self) -> None:
        """Posture is Signora's. Overriding weights is a commercial choice;
        redefining `CONTRACTION_RISK` as expansionary is not one on offer."""
        stored = WorkspaceScoringModel(
            id=uuid4(),
            workspace_id=WORKSPACE,
            version=1,
            overrides=ScoringOverrides(base_weights={SignalType.CONTRACTION_RISK: 99}),
            created_at=NOW,
            created_by=uuid4(),
        )

        resolved = resolve_model(ARTIFACT, stored)

        weight = resolved.weight_for(SignalType.CONTRACTION_RISK)
        assert weight.base_weight == 99
        assert weight.posture is Posture.CONTRACTIONARY


class TestSweep:
    async def test_only_scores_past_their_stated_validity_are_reconsidered(self) -> None:
        signal = make_signal(
            signal_type=SignalType.ACTIVE_EVALUATION,
            events=(uuid4(),),
            occurred_at=NOW,
            window_days=90,
        )
        compute, repository, _, _ = build((signal,), moment=NOW + timedelta(days=1))
        first = await run(compute)
        assert first.score is not None
        boundary = first.score.valid_until
        assert boundary is not None

        before = SweepStaleScores(
            repository=repository,
            compute=compute,
            clock=lambda: boundary - timedelta(seconds=1),
        )

        outcome = await before.execute(WORKSPACE)

        assert (outcome.examined, outcome.rescored) == (0, 0)

    async def test_an_aged_score_is_recomputed_and_explains_why(self) -> None:
        signal = make_signal(
            signal_type=SignalType.ACTIVE_EVALUATION,
            events=(uuid4(),),
            occurred_at=NOW,
            window_days=90,
        )
        compute, repository, _, _ = build((signal,), moment=NOW + timedelta(days=1))
        first = await run(compute)
        assert first.score is not None
        boundary = first.score.valid_until
        assert boundary is not None
        after = boundary + timedelta(seconds=1)

        aged_compute, repository, _, publisher = build(
            (signal,), moment=after, repository=repository
        )
        sweep = SweepStaleScores(
            repository=repository,
            compute=aged_compute,
            clock=lambda: after,
        )

        result = await sweep.execute(WORKSPACE)

        assert result.rescored == 1
        latest = await repository.current(WORKSPACE, ENTITY)
        assert latest is not None
        assert latest.trigger is ScoreTrigger.EVIDENCE_AGED
        assert latest.trend is Trend.FALLING
        assert latest.value < first.score.value


class TestReadSurface:
    async def test_an_explanation_carries_the_ledger_and_the_signals_behind_it(self) -> None:
        signal = make_signal(signal_type=SignalType.ACTIVE_EVALUATION, events=(uuid4(),))
        compute, repository, models, _ = build((signal,))
        result = await run(compute)
        assert result.score is not None

        queries = BuyingScoreQueries(
            repository=repository,
            models=models,
            signals=FakeSignalQueries((signal,), CATALOG),
            artifact=ARTIFACT,
        )
        explanation = await queries.explanation(WORKSPACE, result.score.id)

        assert explanation is not None
        assert explanation.score.id == result.score.id
        assert [e.signal.id for e in explanation.signals] == [signal.id]
        assert explanation.score.ledger.entries[0].reason

    async def test_history_keeps_every_reading_a_customer_was_shown(self) -> None:
        first_signal = make_signal(signal_type=SignalType.ACTIVE_EVALUATION, events=(uuid4(),))
        compute, repository, models, _ = build((first_signal,))
        await run(compute)
        compute2, repository, models, _ = build(
            (first_signal, make_signal(signal_type=SignalType.BUDGET_UNLOCKED, events=(uuid4(),))),
            repository=repository,
        )
        await run(compute2)

        queries = BuyingScoreQueries(
            repository=repository,
            models=models,
            signals=FakeSignalQueries((first_signal,), CATALOG),
            artifact=ARTIFACT,
        )

        assert len(await queries.history(WORKSPACE, ENTITY)) == 2

    async def test_the_read_surface_exposes_no_account_representation(self) -> None:
        """A score is a projection over signals. A port that also served
        account state would become where consumers get accounts from."""
        surface = {name for name in dir(BuyingScoreQueries) if not name.startswith("_")}

        assert not {
            name for name in surface if any(word in name for word in ("entity", "account", "top"))
        }
