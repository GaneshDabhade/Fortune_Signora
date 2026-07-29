"""Compute an account's buying score from its live hypotheses.

**This use case answers "how much commercial attention should this account
receive?" and stops.** It does not decide which contradictory hypothesis is
true, why the account behaved this way, what Sales should do, or which
opportunity to create. Those belong to later modules, and a shortcut here
would put a judgement where nobody could review it.

Three properties shape the flow:

**The ledger is built first, and the score falls out of it.** Read the
dependency as ledger → score. There is no path that computes a number and
then assembles an explanation to match.

**An unchanged situation writes nothing.** Score identity is derived from
the configuration in force, the signals contributing, and the
evidence-derived moment their composition last changed — so recomputing
over an unchanged account produces the same id, inserts nothing, and
publishes nothing. Replay is therefore safe to run repeatedly.

**No signals, no score.** An account nothing has been observed about does
not get a zero; it gets no reading at all. A zero is a statement, and
Signora has not made one.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from modules.buying_score_engine.application.ports import (
    BuyingScoreRepository,
    ScoringModelRepository,
    SignalReader,
)
from modules.buying_score_engine.domain.events import BuyingScoreUpdated
from modules.buying_score_engine.domain.score import BuyingScore, ScoreTrigger, score_id
from modules.buying_score_engine.domain.scoring import build_ledger
from modules.buying_score_engine.domain.scoring_model import ScoringModel
from modules.buying_score_engine.domain.workspace_model import (
    DEFAULT_MODEL_VERSION,
    WorkspaceScoringModel,
    resolve_model,
)
from modules.signal_engine.public import DEFAULT_PROFILE_VERSION
from signora_platform.event_bus import EventPublisher
from signora_platform.observability import get_logger

logger = get_logger(__name__)

PRODUCER_MODULE = "buying_score_engine"


@dataclass(frozen=True, slots=True)
class ComputeBuyingScoreInput:
    workspace_id: UUID
    entity_id: UUID
    trigger: ScoreTrigger
    #: Which weighting to score through. `None` means the current one —
    #: **current replay**, answering *"what would we say now?"*. A specific
    #: version is **historical replay**, reproducing the number the customer
    #: was originally shown. The two answer different business questions and
    #: are never conflated.
    scoring_model_version: int | None = None


@dataclass(frozen=True, slots=True)
class ComputeBuyingScoreResult:
    score: BuyingScore | None
    #: False when nothing about the account's evidence or configuration had
    #: moved, so the stored reading still stands.
    changed: bool


class ComputeBuyingScore:
    def __init__(
        self,
        *,
        repository: BuyingScoreRepository,
        models: ScoringModelRepository,
        signals: SignalReader,
        artifact: ScoringModel,
        publisher: EventPublisher,
        session: AsyncSession,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._repository = repository
        self._models = models
        # Signals are read through the Signal Engine's published port, never
        # re-derived from business events: the Buying Score Engine weighs
        # hypotheses, it does not form them.
        self._signals = signals
        self._artifact = artifact
        self._publisher = publisher
        self._session = session
        self._clock = clock

    async def execute(
        self,
        request: ComputeBuyingScoreInput,
        *,
        correlation_id: UUID,
        causation_id: UUID | None = None,
    ) -> ComputeBuyingScoreResult:
        moment = self._clock()
        stored_model = await self._resolve_model(request)
        model = resolve_model(self._artifact, stored_model)
        model_version = (
            DEFAULT_MODEL_VERSION if stored_model is None else stored_model.version
        )

        signals = await self._signals.signals(
            request.workspace_id, request.entity_id, live_only=True, now=moment
        )
        profile = await self._signals.stored_profile(request.workspace_id)
        profile_version = DEFAULT_PROFILE_VERSION if profile is None else profile.version

        previous = await self._repository.current(request.workspace_id, request.entity_id)
        ledger = build_ledger(
            signals, model=model, catalog=self._signals.catalog(), moment=moment
        )

        basis_at = _basis_at(ledger.basis_at(), previous)
        if basis_at is None:
            # Nothing is contributing and nothing ever was. An account with
            # no evidence gets no reading — a zero would be a statement.
            return ComputeBuyingScoreResult(score=None, changed=False)

        prospective = score_id(
            workspace_id=request.workspace_id,
            entity_id=request.entity_id,
            scoring_model_version=model_version,
            model_artifact_version=self._artifact.version,
            profile_version=profile_version,
            contributing_signal_ids=ledger.contributing_signals(),
            basis_at=basis_at,
        )
        if previous is not None and prospective == previous.id:
            return ComputeBuyingScoreResult(score=previous, changed=False)

        score = BuyingScore.projected_from(
            ledger,
            workspace_id=request.workspace_id,
            entity_id=request.entity_id,
            computed_at=moment,
            basis_at=basis_at,
            trigger=request.trigger,
            scoring_model_version=model_version,
            model_artifact_version=self._artifact.version,
            profile_version=profile_version,
            steady_delta=model.steady_delta,
            previous=previous,
        )

        if not await self._repository.record(score):
            # A concurrent worker recorded the same reading. Identity is
            # derived, so "the same reading" means byte-identical — there is
            # nothing to reconcile and nothing new to announce.
            return ComputeBuyingScoreResult(score=score, changed=False)

        await self._publisher.publish(
            # See the note in provider_normalization's handler: the platform's
            # PublishableEvent Protocol declares settable members, which frozen
            # domain events cannot satisfy. Raised as a finding, not fixed here.
            [_updated_event(score, causation_id)],  # type: ignore[list-item]
            session=self._session,
            producer_module=PRODUCER_MODULE,
            correlation_id=correlation_id,
        )

        logger.info(
            "buying score computed",
            extra={
                "entity_id": str(request.entity_id),
                "score": score.value,
                "trend": score.trend.value,
                "contested": score.contested,
                "trigger": score.trigger.value,
                "contributions": len(score.ledger.entries),
                "scoring_model_version": model_version,
                "model_artifact_version": self._artifact.version,
            },
        )
        return ComputeBuyingScoreResult(score=score, changed=True)

    async def _resolve_model(
        self, request: ComputeBuyingScoreInput
    ) -> WorkspaceScoringModel | None:
        if request.scoring_model_version is None:
            return await self._models.current(request.workspace_id)
        if request.scoring_model_version == DEFAULT_MODEL_VERSION:
            return None
        return await self._models.by_version(
            request.workspace_id, request.scoring_model_version
        )


def _basis_at(from_ledger: datetime | None, previous: BuyingScore | None) -> datetime | None:
    """The evidence-derived moment the ledger's composition last changed.

    An empty ledger has none of its own. When the last contribution expires,
    the moment that happened is the previous reading's `valid_until` — still
    derived from evidence, just from the reading being replaced.
    """
    if from_ledger is not None:
        return from_ledger
    return None if previous is None else previous.valid_until


def _updated_event(score: BuyingScore, causation_id: UUID | None) -> BuyingScoreUpdated:
    return BuyingScoreUpdated(
        event_id=uuid4(),
        workspace_id=score.workspace_id,
        occurred_at=score.computed_at,
        score_id=score.id,
        entity_id=score.entity_id,
        score=score.value,
        trend=score.trend.value,
        delta=score.delta,
        contested=score.contested,
        source_signal_ids=score.ledger.contributing_signals(),
        dissenting_signal_ids=score.dissenting_signal_ids,
        trigger=score.trigger.value,
        valid_until=score.valid_until,
        model_version=score.scoring_model_version,
        payload_version=score.payload_version,
        causation_id=causation_id,
    )
