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

from dataclasses import dataclass
from datetime import datetime
from typing import Final
from uuid import UUID

from modules.ai_platform.domain.errors import AIPlatformError
from modules.ai_platform.domain.grounding import GroundedOutput, GroundedStatement
from modules.ai_platform.domain.provider import AIVendor

#: Bumped when the stored shape changes in a way a consumer would notice.
PAYLOAD_VERSION: Final = 1


class NarrationError(AIPlatformError):
    """A narration was constructed that could not describe a real one."""


class Narration(GroundedOutput):
    """Prose about one account, every sentence citing what it rests on."""

    points: tuple[GroundedStatement, ...]

    def statements(self) -> tuple[GroundedStatement, ...]:
        return self.points


@dataclass(frozen=True, slots=True)
class NarrationSubject:
    """What a narration is about, in this module's own vocabulary.

    The `EvidenceRef` shape — a kind and an id — rather than an `entity_id`.
    The substrate addresses things the way it addresses evidence; naming the
    pipeline's concepts here would put the pipeline's vocabulary into the
    schema of the module that must not know it exists.
    """

    kind: str
    id: UUID

    def __post_init__(self) -> None:
        if not self.kind.strip():
            raise NarrationError("a narration must say what it is about.")


@dataclass(frozen=True, slots=True)
class MaterializedNarration:
    """One narration, as it was produced, with everything needed to explain it.

    **A historical fact, not current truth** (ratified 2026-07-30). It records
    what the platform produced at one moment against one prompt, one model and
    one evidence set. A better explanation is a *new* narration; editing this
    one would destroy the only record of what a customer was actually shown.

    Provenance is carried on the object rather than reachable from it, so the
    questions *which evidence · which prompt · which model · which inference ·
    when* are answered without a join and without reconstruction.
    """

    id: UUID
    workspace_id: UUID
    correlation_id: UUID
    subject: NarrationSubject

    prompt_name: str
    prompt_version: int
    prompt_fingerprint: str
    model: str
    vendor: AIVendor
    evidence_digest: str
    evidence_refs: tuple[str, ...]
    #: The operational record of the call. A pointer, never the authority —
    #: everything above is stored here too, so this row stays explicable if
    #: operational history is ever pruned.
    inference_id: UUID

    statements: tuple[GroundedStatement, ...]
    created_at: datetime
    payload_version: int = PAYLOAD_VERSION

    def __post_init__(self) -> None:
        if not self.statements:
            raise NarrationError(
                f"narration {self.id} holds no statements. A row asserting the platform "
                "produced an explanation while holding none passes every grounding check "
                "vacuously."
            )
        if not self.evidence_refs:
            raise NarrationError(
                f"narration {self.id} cites nothing. Grounding refuses an uncited statement; "
                "an uncited narration is the same defect at rest."
            )
