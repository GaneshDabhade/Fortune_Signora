"""The one file in the AI Reasoning Engine that speaks the pipeline's language.

It satisfies `ReasoningContextSource`, and it sits in `infrastructure/` for
exactly that reason: `reason.py` orchestrates and decides nothing, so the
translation from *opportunities, scores, signals and events* into *support,
temporal and limitations* happens here, behind a Protocol the application
declares.

**It composes; it derives nothing.** Every field below already exists,
computed by the module that owns it:

| Part | Read from | Owner |
|---|---|---|
| evidence | `ExplanationSource` | AI Platform |
| support | `corroborating_providers`, `EvidenceState`, `contested` | Business Event · Opportunity |
| temporal | `trigger`, `basis_at`, `delta`, `trend`, `valid_until` | Buying Score Engine |
| alternatives | `SignalQueries.unsupported_types()` | Signal Engine |
| limitations | `SignalCatalog` | domain experts, reviewed |

Nothing here totals, ranks, infers or summarises. If this file ever needs to
*decide* something, the capability has moved and the correct response is to
halt — the same boundary M8's `explanation.py` names for itself.

**Evidence is obtained rather than assembled.** `ExplanationSource` is already
published through `ai_platform.public`, and reusing it means the model sees the
byte-identical closed universe M8 shows it, under the same digest. A second
evidence translation in M9 would be a second thing to keep in step, and the two
would disagree about a digest that customers cite.
"""

from __future__ import annotations

from uuid import UUID

from modules.ai_platform.public import ExplanationSource
from modules.ai_reasoning_engine.domain.context import ReasoningContext
from modules.ai_reasoning_engine.domain.package import AlternativeReading
from modules.ai_reasoning_engine.domain.support import SupportBasis
from modules.ai_reasoning_engine.domain.temporal import TemporalExplanation
from modules.buying_score_engine.public import BuyingScoreExplanation
from modules.opportunity_engine.public import EvidenceState, OpportunityQueries
from modules.signal_engine.public import SignalCatalog, SignalQueries, SignalType


class PipelineReasoningContext:
    """Assembles the deterministic twelve-fifteenths of a Decision Package."""

    def __init__(
        self,
        *,
        opportunities: OpportunityQueries,
        signals: SignalQueries,
        evidence: ExplanationSource,
    ) -> None:
        self._opportunities = opportunities
        self._signals = signals
        self._evidence = evidence

    @property
    def _catalog(self) -> SignalCatalog:
        """**Read from `SignalQueries`, never injected separately.**

        Taking a catalog as its own constructor argument would allow a
        composition to hand this file one revision while the signals it is
        describing were produced under another — two authorities for one
        reviewed artifact, and a package stating limitations from a version
        that never applied to it. There is one catalog in force, and the
        module that owns signals is the one that knows which.
        """
        return self._signals.catalog()

    async def context_for(self, workspace_id: UUID, entity_id: UUID) -> ReasoningContext | None:
        """`None` when there is nothing to reason about.

        **Never an empty context.** An empty evidence set would reach a model
        and come back as a fluent paragraph about nothing, perfectly grounded
        in no facts at all — which is the failure a closed evidence set exists
        to make impossible.

        Four `None` returns, each a different absence and none of them an
        error: no opportunity, no explanation, no originating score, no
        evidence. A conclusion about an account the pipeline has said nothing
        about is not a degraded conclusion; it is an invented one.
        """
        tracked = await self._opportunities.tracked(workspace_id, entity_id)
        if tracked is None:
            return None
        explanation = await self._opportunities.explanation(workspace_id, tracked.opportunity.id)
        if explanation is None or explanation.originating_score is None:
            return None

        evidence = await self._evidence.evidence_for(workspace_id, entity_id)
        if evidence is None:
            return None

        score = explanation.originating_score
        # Sorted, **not** de-duplicated. A set here survived mutation testing:
        # its removal changed nothing, because `_catalog_text` already collapses
        # repeats and is the single authority for that. Two deduplications where
        # one suffices is the same defect as two representations of one truth,
        # so the redundant one was removed rather than left to look load-bearing.
        types = sorted((s.signal.signal_type for s in score.signals), key=lambda t: t.value)
        limitations, validation = self._catalog_text(types)

        return ReasoningContext(
            evidence=evidence,
            subject_id=entity_id,
            originating_buying_score_id=score.score.id,
            support=_support(score, explanation.evidence_state),
            temporal=_temporal(score, explanation.evidence_state),
            alternative_readings=tuple(
                AlternativeReading(signal_type=reading.signal_type.value, reason=reading.reason)
                for reading in await self._signals.unsupported_types(workspace_id, entity_id)
            ),
            limitations=limitations,
            suggested_validation=validation,
            catalog_version=self._catalog.version,
        )

    def _catalog_text(
        self, signal_types: list[SignalType]
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        """What the contributing signal types do **not** imply, and how to
        check them.

        Composed only for the types actually present: a package listing the
        limitations of a signal that contributed nothing would be describing
        someone else's account.

        **The one deduplication.** A caveat shared by two signal types is
        stated once, and a type appearing twice contributes once — the caller
        deliberately does not pre-deduplicate, because a second collapse would
        be redundant protection that reads as though it were the real one.
        Order is the reviewed artifact's declared order, never a set's
        iteration order, which is a hidden input.
        """
        limitations: list[str] = []
        validation: list[str] = []
        for signal_type in signal_types:
            definition = self._catalog.definition(signal_type)
            limitations.extend(t for t in definition.limitations if t not in limitations)
            validation.extend(t for t in definition.suggested_validation if t not in validation)
        return tuple(limitations), tuple(validation)


def _support(score: BuyingScoreExplanation, evidence_state: EvidenceState) -> SupportBasis:
    """Corroboration counted across **distinct providers**, never events.

    One provider repeating itself across ten events is one source, however
    many rows it produced — the same distinction `ReasonedOutput.premises`
    draws for citations. The events themselves are counted and shown, and
    deliberately do not enter the level.
    """
    events = {event.id: event for signal in score.signals for event in signal.business_events}
    providers = {
        provider for event in events.values() for provider in event.corroborating_providers
    }
    return SupportBasis(
        corroborating_providers=frozenset(providers),
        contributing_events=len(events),
        evidence_state=evidence_state,
        contested=score.score.contested,
        dissenting_signals=len(score.score.dissenting_signal_ids),
    )


def _temporal(score: BuyingScoreExplanation, evidence_state: EvidenceState) -> TemporalExplanation:
    """Copied from one immutable reading. **Nothing is recomputed.**

    `ScoreTrigger` exists precisely because *"a number that moved for an
    unexplainable reason is a number nobody trusts"*; re-deriving why this
    reading exists would be a second answer to a question already answered.
    """
    reading = score.score
    return TemporalExplanation(
        trigger=reading.trigger,
        basis_at=reading.basis_at,
        computed_at=reading.computed_at,
        delta=reading.delta,
        trend=reading.trend,
        evidence_state=evidence_state,
        valid_until=reading.valid_until,
        supersedes=reading.supersedes,
    )


# **Nothing here reads a clock.** Every timestamp flows through from an
# immutable buying score, so a context assembled twice from the same rows is
# byte-identical — which is what keeps a package's digest reproducible and an
# assembly timestamp out of the hidden-inputs list.

__all__ = ["PipelineReasoningContext"]
