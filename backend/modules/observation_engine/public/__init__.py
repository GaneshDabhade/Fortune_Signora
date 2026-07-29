"""The Observation Engine's public contract.

Downstream modules import from here and nowhere deeper. What they get is
**structural change, never business significance**: what moved, according
to whom, by how much, between when and when.

Whether a move *matters* is the Business Event Engine's question. There is
deliberately no importance, score, or threshold anywhere in this surface.
"""

from modules.observation_engine.application.queries import ObservationEvidence, ObservationQueries
from modules.observation_engine.domain.observation import (
    Observation,
    ObservationDirection,
    ObservationKind,
)
from modules.observation_engine.domain.semantics import AttributeKind, attribute_kind

__all__ = [
    "AttributeKind",
    "Observation",
    "ObservationDirection",
    "ObservationEvidence",
    "ObservationKind",
    "ObservationQueries",
    "attribute_kind",
]
