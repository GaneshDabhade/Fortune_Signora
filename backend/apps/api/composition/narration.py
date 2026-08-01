"""Composing the AI Platform's narration read surface.

**One level deep, and that is the point.** Reading a stored narration needs the
repository and nothing else — no evidence assembly, no prompt registry, no
provider. Those are what *producing* one needs, and production happens in a
background worker where a twenty-second model call belongs (§7).

The AI Platform is the only module the pipeline may not depend on
(import-linter, "no business module depends on the AI Platform"), which is why
this file exists at the composition root and holds nothing else.
"""

from typing import Annotated

from fastapi import Depends

from modules.ai_platform.application.ports import NarrationRepository
from modules.ai_platform.infrastructure.repository import SqlNarrationRepository
from signora_platform.api import CurrentWorkspace


def narrations(context: CurrentWorkspace) -> NarrationRepository:
    """The narration store, scoped to one request.

    Typed as the **port**, not the SQL implementation: the router programs
    against the contract, so the one method it needs stays the one method it
    can reach.
    """
    return SqlNarrationRepository(context.session)


NarrationRead = Annotated[NarrationRepository, Depends(narrations)]

__all__ = ["NarrationRead", "narrations"]
