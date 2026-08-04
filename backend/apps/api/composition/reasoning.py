"""Composing the AI Reasoning Engine's read surface.

Reading a stored Decision Package needs the repository and nothing else — no
context source, no prompt registry, no provider, no model. **Those are what
*producing* one needs**, and production happens in a background worker where a
model call belongs (§7). The asymmetry is the clearest evidence that this is a
read path: the composition root for the write path assembles six dependencies
and this one assembles a session.
"""

from typing import Annotated

from fastapi import Depends

from modules.ai_reasoning_engine.application.ports import DecisionPackageRepository
from modules.ai_reasoning_engine.infrastructure.repository import SqlDecisionPackageRepository
from signora_platform.api import CurrentWorkspace


def decision_packages(context: CurrentWorkspace) -> DecisionPackageRepository:
    """The package store, scoped to one request.

    Typed as the **port**, not the SQL implementation: the router programs
    against the contract, so the one method it needs stays the one method it
    can reach — and `save` is not on the router's horizon at all.
    """
    return SqlDecisionPackageRepository(context.session)


DecisionPackageRead = Annotated[DecisionPackageRepository, Depends(decision_packages)]

__all__ = ["DecisionPackageRead", "decision_packages"]
