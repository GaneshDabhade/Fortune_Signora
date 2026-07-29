"""A workspace's own weighting — the second customer-authored artifact.

The signal profile said *which hypotheses we care about*. This says *how
much attention caring earns*. They are deliberately separate rows: every
signal records the profile version that produced it, so folding weights
into the profile would mean tuning a score mints a new profile version and
churns the explanation of every historical signal.

**Immutable and versioned**, superseded rather than edited, for the reason
that governs every configuration artifact in this platform: every score
records the model version that produced it, and if a model could be edited
in place, every historical score would become unexplainable — *"why was I
shown 68?"* would have no answer, because the reason changed underneath it.

**A workspace overrides values, never meaning.** Weights, multipliers,
bands, ceiling and the steady band are all commercial judgements and all
theirs. `Posture` is not: whether `CONTRACTION_RISK` reads as
contractionary is a fact about the language, and a workspace inverting it
would make `contested` incomparable across the platform — which would
quietly break benchmarking, AI reasoning and support for everyone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Final
from uuid import UUID

from modules.buying_score_engine.domain.scoring_model import (
    AgeBand,
    ScoringModel,
    TypeWeight,
)
from modules.signal_engine.public import Relevance, SignalType

DEFAULT_MODEL_VERSION: Final = 0
"""The version recorded when a workspace has configured no weighting.

An absent model falls back to the shipped artifact rather than scoring
nothing, so out-of-box behaviour is reviewable in a pull request instead of
emerging from an empty table — and no seeding write is needed, which keeps
the module free of any dependency on workspace creation.
"""


@dataclass(frozen=True, slots=True)
class ScoringOverrides:
    """What a workspace has chosen to change. Absent means "use Signora's"."""

    base_weights: dict[SignalType, int] = field(default_factory=dict)
    relevance_multipliers: dict[Relevance, int] = field(default_factory=dict)
    age_bands: tuple[AgeBand, ...] | None = None
    ceiling: int | None = None
    steady_delta: int | None = None

    @property
    def is_empty(self) -> bool:
        return (
            not self.base_weights
            and not self.relevance_multipliers
            and self.age_bands is None
            and self.ceiling is None
            and self.steady_delta is None
        )


@dataclass(frozen=True, slots=True)
class WorkspaceScoringModel:
    id: UUID
    workspace_id: UUID
    version: int
    overrides: ScoringOverrides
    created_at: datetime
    #: Auditability. A weighting change is a commercial decision, and a
    #: customer should be able to see who made it and when.
    created_by: UUID
    supersedes: UUID | None = None


def resolve_model(artifact: ScoringModel, stored: WorkspaceScoringModel | None) -> ScoringModel:
    """The model actually in force: Signora's, with the workspace's values.

    Posture is taken from the artifact for every type regardless of what the
    override says, so there is no code path — including a hand-edited
    database row — by which a workspace can change what a signal type means.
    """
    if stored is None or stored.overrides.is_empty:
        return artifact

    overrides = stored.overrides
    types = tuple(
        TypeWeight(
            key=weight.key,
            posture=weight.posture,
            base_weight=overrides.base_weights.get(weight.key, weight.base_weight),
        )
        for weight in artifact.types
    )
    return ScoringModel(
        version=artifact.version,
        ceiling=overrides.ceiling if overrides.ceiling is not None else artifact.ceiling,
        steady_delta=(
            overrides.steady_delta
            if overrides.steady_delta is not None
            else artifact.steady_delta
        ),
        age_bands=overrides.age_bands if overrides.age_bands is not None else artifact.age_bands,
        relevance_multipliers={
            **artifact.relevance_multipliers,
            **overrides.relevance_multipliers,
        },
        types=types,
    )
