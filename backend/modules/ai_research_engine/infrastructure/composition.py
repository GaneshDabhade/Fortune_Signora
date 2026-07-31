"""Composition root for the AI Research Engine.

Wires the adapters into the use case. Everything concrete is constructed here
and nowhere else, so `application/` and `domain/` see only ports.

**`Infer` is a parameter, not a construction**, for the reason M9 recorded: this
module owns its own prompts, `load_prompt_registry(directory)` is per-directory
precisely so each module can, but the loader lives in `ai_platform/
infrastructure/` and `public/` sits *below* `infrastructure/` in the layering
contract. Binding a module's prompt directory to an `Infer` is the application
composition root's job — the one place that may legitimately import both
modules' infrastructure.

**Both prompt names are this module's decision**, not a caller's. A caller free
to choose could name an unevaluated version and route around the release rule.

**`research_synthesis@1` is authored and unreleased.** `Infer.execute` will
refuse it until it earns a release against the model it is asked to serve, and
that refusal is the release rule working rather than a wiring defect.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from modules.ai_platform.public import Infer
from modules.ai_research_engine.application.plan import PROMPT_NAME, PROMPT_VERSION
from modules.ai_research_engine.application.research import (
    SYNTHESIS_PROMPT,
    SYNTHESIS_VERSION,
    Research,
)
from modules.ai_research_engine.infrastructure.repository import SqlResearchRepository
from modules.ai_research_engine.infrastructure.retrieval import OpportunityFactSource
from modules.opportunity_engine.public import OpportunityQueries
from signora_platform.event_bus import EventPublisher

#: Where M10's prompts live. Exported so the application composition root can
#: bind an `Infer` to them without knowing this module's internal layout.
PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"

#: The two prompts M10 ships, re-exported so a caller can name what it is
#: wiring without importing across layers.
PLANNING_PROMPT = PROMPT_NAME
PLANNING_PROMPT_VERSION = PROMPT_VERSION
SYNTHESIS_PROMPT_NAME = SYNTHESIS_PROMPT
SYNTHESIS_PROMPT_VERSION = SYNTHESIS_VERSION


def build_research(
    session: AsyncSession,
    *,
    infer: Infer,
    model: str,
    opportunities: OpportunityQueries,
    publisher: EventPublisher,
) -> Research:
    """The use case, with every concrete dependency supplied here.

    The artifact and its event share the caller's `session`: they are one unit
    of work, so a rolled-back transaction leaves neither behind — a brief
    nobody committed was never shown to anyone.

    `opportunities` is passed in rather than constructed: it is another
    module's published query surface, and building one would mean knowing how
    that module wires its own repository.
    """
    return Research(
        facts=OpportunityFactSource(opportunities),
        infer=infer,
        model=model,
        repository=SqlResearchRepository(session),
        publisher=publisher,
        session=session,
    )
