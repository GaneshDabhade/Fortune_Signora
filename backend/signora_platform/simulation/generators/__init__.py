"""Payload generators.

**All current generators emit DEVELOPMENT FIXTURE payloads** — representative
structures, not authentic vendor schemas. See
docs/architecture/provider-qualification.md for the replacement procedure.
"""

from signora_platform.simulation.generators.base import (
    GENERATOR_VERSION,
    GeneratedPayload,
    PayloadGenerator,
    PayloadProvenance,
)
from signora_platform.simulation.generators.enrichment import (
    ApolloFixtureGenerator,
    BuiltWithFixtureGenerator,
    CoreSignalFixtureGenerator,
    CrunchbaseFixtureGenerator,
)
from signora_platform.simulation.generators.intent import (
    NOISE_FLOOR,
    BomboraFixtureGenerator,
    TopicTrajectory,
    TrendDirection,
    build_trajectory,
)

__all__ = [
    "GENERATOR_VERSION",
    "NOISE_FLOOR",
    "ApolloFixtureGenerator",
    "BomboraFixtureGenerator",
    "BuiltWithFixtureGenerator",
    "CoreSignalFixtureGenerator",
    "CrunchbaseFixtureGenerator",
    "GeneratedPayload",
    "PayloadGenerator",
    "PayloadProvenance",
    "TopicTrajectory",
    "TrendDirection",
    "build_trajectory",
]
