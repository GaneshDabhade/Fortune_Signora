"""The Buying Score Engine's public contract.

**The pipeline's first intentional reduction.** Every module upstream adds
information and destroys none; this one summarizes many live hypotheses
into a single number so a seller can act across three hundred accounts
instead of reading forty signals about each.

*Permanent architectural principle, ratified 2026-07-29:*

> Buying scores **prioritize commercial attention**. They do not predict
> purchasing behaviour. They do not estimate probability. They do not
> resolve contradiction. They summarize *explainable* commercial attention.

What consumers get is a number **with its ledger**, never a number alone.
The ledger is the authoritative explanation: the score reproduces from it
exactly, and every entry walks outward to business events, observations,
claims and the raw provider payload underneath.

There is deliberately no account representation in this surface, no
recommendation, no opportunity, and no probability. A score is a
decision-support artifact, not a source of truth about an account — and the
moment a consumer reads it *instead of* the intelligence, the pipeline has
been replaced by its own summary.
"""

from modules.buying_score_engine.application.queries import (
    BuyingScoreExplanation,
    BuyingScoreQueries,
)
from modules.buying_score_engine.domain.ledger import Contribution, ContributionLedger
from modules.buying_score_engine.domain.score import BuyingScore, ScoreTrigger, Trend
from modules.buying_score_engine.domain.scoring_model import (
    AgeBand,
    Posture,
    ScoringModel,
    TypeWeight,
)
from modules.buying_score_engine.domain.workspace_model import (
    DEFAULT_MODEL_VERSION,
    ScoringOverrides,
    WorkspaceScoringModel,
)

__all__ = [
    "DEFAULT_MODEL_VERSION",
    "AgeBand",
    "BuyingScore",
    "BuyingScoreExplanation",
    "BuyingScoreQueries",
    "Contribution",
    "ContributionLedger",
    "Posture",
    "ScoreTrigger",
    "ScoringModel",
    "ScoringOverrides",
    "Trend",
    "TypeWeight",
    "WorkspaceScoringModel",
]
