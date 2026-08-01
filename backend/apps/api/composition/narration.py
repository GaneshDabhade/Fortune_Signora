"""Composing the AI Platform's narration read surface.

Reading a stored narration needs the repository and nothing else — no prompt
registry, no provider, no model. Those are what *producing* one needs, and
production happens in a background worker where a twenty-second model call
belongs (§7).

**Since D42 it also needs the evidence, and that is a second dependency rather
than a deeper one.** Resolving a citation means re-deriving the set the model
was given, which is `OpportunityExplanationSource` — an adapter the AI Platform
already owns, reaching `opportunity_engine.public` and nothing deeper. The
opportunity chain it stands on is assembled by `opportunities.py` and reused
here rather than rebuilt: two constructions of one chain would be two things to
keep in step.

The AI Platform is the only module the pipeline may not depend on
(import-linter, "no business module depends on the AI Platform"), which is why
this file exists at the composition root.
"""

from typing import Annotated

from fastapi import Depends

from apps.api.composition.opportunities import opportunity_queries
from modules.ai_platform.application.ports import ExplanationSource, NarrationRepository
from modules.ai_platform.infrastructure.explanation import OpportunityExplanationSource
from modules.ai_platform.infrastructure.repository import SqlNarrationRepository
from modules.opportunity_engine.application.queries import OpportunityQueries
from signora_platform.api import CurrentWorkspace


def narrations(context: CurrentWorkspace) -> NarrationRepository:
    """The narration store, scoped to one request.

    Typed as the **port**, not the SQL implementation: the router programs
    against the contract, so the one method it needs stays the one method it
    can reach.
    """
    return SqlNarrationRepository(context.session)


def explanations(
    queries: Annotated[OpportunityQueries, Depends(opportunity_queries)],
) -> ExplanationSource:
    """Where a citation's fact is re-derived from, for one request.

    Typed as the **port** for the same reason as above: the router asks for
    evidence about an account and never learns that an opportunity is what
    supplies it.
    """
    return OpportunityExplanationSource(queries)


NarrationRead = Annotated[NarrationRepository, Depends(narrations)]
ExplanationRead = Annotated[ExplanationSource, Depends(explanations)]

__all__ = ["ExplanationRead", "NarrationRead", "explanations", "narrations"]
