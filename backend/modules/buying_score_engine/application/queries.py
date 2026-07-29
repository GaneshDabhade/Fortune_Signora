"""The Buying Score Engine's read surface.

Built around the questions a number has to answer before anyone should act
on it:

1. **What is it, and which way is it moving?** — the value, trend, delta
2. **Why is it that?** — the ledger, entry by entry, with the arithmetic
3. **Is anything in tension?** — contested, with the dissent named
4. **How long is it correct for?** — a stated validity, not "recently"
5. **What did we say before?** — the immutable history

**Deliberately absent: any account representation.** No name, no domain, no
industry, no entity lookup, no "top accounts with details". A score is a
projection over signals, and a read port that also served account state
would become the place consumers get accounts from — at which point the
score has quietly replaced the intelligence it summarizes.

**Also absent: any recommendation, action, or opportunity.** Those are
later modules' questions, and a convenience method here would answer them
where nobody could review the answer.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from modules.buying_score_engine.application.ports import (
    BuyingScoreRepository,
    ScoringModelRepository,
    SignalReader,
)
from modules.buying_score_engine.domain.score import BuyingScore
from modules.buying_score_engine.domain.scoring_model import ScoringModel
from modules.buying_score_engine.domain.workspace_model import resolve_model
from modules.signal_engine.public import SignalExplanation


@dataclass(frozen=True, slots=True)
class BuyingScoreExplanation:
    """Everything needed to understand — or challenge — one number.

    The ledger explains the arithmetic; the signal explanations continue the
    chain outward to business events, observations, claims and the raw
    provider payloads underneath. **A caller can walk from a score to a
    vendor record without writing a join**, which is the property that keeps
    a score a projection rather than a replacement.
    """

    score: BuyingScore
    #: One per contributing signal, each carrying its own evidence and the
    #: profile entry that made it relevant.
    signals: tuple[SignalExplanation, ...]
    #: The signals whose reading is outweighed but not dismissed. Present
    #: only when the score is contested, and never netted away.
    dissent: tuple[SignalExplanation, ...]


class BuyingScoreQueries:
    """Read-only. Every method is scoped to one workspace, explicitly."""

    def __init__(
        self,
        *,
        repository: BuyingScoreRepository,
        models: ScoringModelRepository,
        signals: SignalReader,
        artifact: ScoringModel,
    ) -> None:
        self._repository = repository
        self._models = models
        self._signals = signals
        self._artifact = artifact

    async def current(self, workspace_id: UUID, entity_id: UUID) -> BuyingScore | None:
        """The reading no later score replaces.

        It may be past its `valid_until` — that is a fact the caller can
        read off the score itself, and hiding a stale reading would be worse
        than showing one that admits it is stale.
        """
        return await self._repository.current(workspace_id, entity_id)

    async def explanation(
        self, workspace_id: UUID, score_id: UUID
    ) -> BuyingScoreExplanation | None:
        score = await self._repository.by_id(workspace_id, score_id)
        if score is None:
            return None

        explanations: list[SignalExplanation] = []
        for signal_id in score.ledger.contributing_signals():
            explanation = await self._signals.explanation(workspace_id, signal_id)
            if explanation is not None:
                explanations.append(explanation)

        dissenting = set(score.dissenting_signal_ids)
        return BuyingScoreExplanation(
            score=score,
            signals=tuple(explanations),
            dissent=tuple(e for e in explanations if e.signal.id in dissenting),
        )

    async def history(self, workspace_id: UUID, entity_id: UUID) -> tuple[BuyingScore, ...]:
        """Every reading for this entity, newest first.

        The audit trail of what a customer was shown, and what `trend` is a
        fact about. Immutability is what makes it exist at all.
        """
        return await self._repository.for_entity(workspace_id, entity_id)

    async def scoring_model(self, workspace_id: UUID) -> ScoringModel:
        """The weighting actually in force: Signora's model with this
        workspace's values, and posture always Signora's."""
        return resolve_model(self._artifact, await self._models.current(workspace_id))

    def artifact(self) -> ScoringModel:
        """Signora's shipped defaults. Exposed so the product, analytics,
        documentation and support read the same weights rather than
        re-describing them."""
        return self._artifact
