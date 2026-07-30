"""The output contract of ``explanation_narration@1``.

A prompt's output shape belongs beside the prompt, because the two are one
artifact: changing either without the other produces a released version whose
recorded results describe something else.

**This is language, and nothing more.** `Narration` adds no field a model
could use to reach a conclusion — no priority, no recommendation, no verdict,
no confidence. There is deliberately no un-cited `summary`: the one sentence
a reader looks at first must not be the one statement exempt from grounding.

The M8 stop condition applies directly here. If narrating ever requires a
field holding a proposition the deterministic pipeline did not already
compute, that is not a schema change — it is M9's work arriving early, and
the correct response is to halt and say so.
"""

from __future__ import annotations

from modules.ai_platform.domain.grounding import GroundedOutput, GroundedStatement


class Narration(GroundedOutput):
    """Prose about one account, every sentence citing what it rests on."""

    points: tuple[GroundedStatement, ...]

    def statements(self) -> tuple[GroundedStatement, ...]:
        return self.points
