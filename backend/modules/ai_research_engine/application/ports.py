"""What this module needs from the outside, in its own vocabulary.

One port. Retrieval already has its own in `domain/retrieval.py`, where it
belongs — it represents this module's language. This one is storage, which is
machinery rather than vocabulary, so it lives here.
"""

from __future__ import annotations

from typing import Protocol

from modules.ai_research_engine.domain.research import (
    ResearchFinding,
    ResearchSynthesis,
    ResearchTask,
)


class ResearchRepository(Protocol):
    """Stores one completed run. **There is no update, and no partial save.**

    A task, its findings and its synthesis describe one run and are written
    together: a task whose findings are missing looks like a run that found
    nothing, and a synthesis whose findings are missing cites rows that do not
    exist.
    """

    async def save(
        self,
        task: ResearchTask,
        findings: tuple[ResearchFinding, ...],
        synthesis: ResearchSynthesis,
    ) -> None: ...
