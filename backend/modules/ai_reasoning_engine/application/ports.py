"""What the AI Reasoning Engine needs from the world outside it.

Two ports, both narrow. The first exists because **assembling reasoning
context is not this layer's decision to make** — which evidence matters, and
how a buying score becomes a `SupportBasis`, is translation between another
module's vocabulary and this one's, so it lives in `infrastructure/` behind a
Protocol the application declares.

The M5B finding, applied a third time: *if a fake cannot stand in for a
dependency, the dependency was never really a boundary.*
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from modules.ai_reasoning_engine.domain.context import ReasoningContext
from modules.ai_reasoning_engine.domain.package import DecisionPackage


class ReasoningContextSource(Protocol):
    """Everything deterministic a Decision Package needs, assembled.

    Returns `None` when there is nothing to reason about. **Never an empty
    context** — an empty evidence set would reach a model and come back as a
    fluent paragraph about nothing, perfectly grounded in no facts at all.
    """

    async def context_for(self, workspace_id: UUID, entity_id: UUID) -> ReasoningContext | None: ...


class DecisionPackageRepository(Protocol):
    """Stores a package. No update, no delete.

    A package is a materialized AI artifact and therefore a historical fact:
    a better conclusion is a new package naming a later score, never an edit
    to one a customer has already read.
    """

    async def save(self, package: DecisionPackage) -> None: ...

    async def latest_for(self, workspace_id: UUID, subject_id: UUID) -> DecisionPackage | None: ...
