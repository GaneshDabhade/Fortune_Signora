"""What comes back from a model, before it has earned the name *synthesis*.

**Two failures, and they are not the same failure.** A model can return
something that is not the declared shape at all, and a model can return the
declared shape carrying a claim the graph never made. Conflating them makes an
evaluation unreadable: a prompt a model cannot hold the schema for needs
different work from a prompt a model embellishes.

```
  raw text ──▶ DraftMalformedError      the shape was wrong
           └─▶ tuple[Passage, ...] ──▶ SynthesisRefusedError   the content was
                                                                 invented
```

So parsing lives here and says only *"is this the shape"*, and
`synthesis.validate` says *"is this supported"*. Neither one guesses at the
other's job.

**Untrusted until validated** (`CLAUDE.md` §10). Model output is external input
and is parsed against a declared Pydantic structure before any of it is read as
a value — including the fence's own input, which would otherwise be the one
place unvalidated text entered the module.
"""

from __future__ import annotations

import json
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from modules.sales_engagement.domain.reasoning import ReasoningError
from modules.sales_engagement.domain.synthesis import Passage


class DraftMalformedError(ReasoningError):
    """A model's reply was not the declared shape.

    **Distinct from a refusal**, and the operational record needs both: *"why
    did this brief render without prose?"* is answered by *the model cannot hold
    the schema* or by *the model invented a competitor*, and those have opposite
    remedies.
    """


class _Passage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)
    #: **Never empty, and refused here rather than downstream.** A passage with
    #: no citation is free-floating prose, which this module publishes none of;
    #: catching it at the shape boundary means the fence's message stays about
    #: *content* rather than about arity.
    cites: tuple[str, ...] = Field(min_length=1)


class _Draft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passages: tuple[_Passage, ...] = Field(min_length=1)


#: The schema a prompt shows the model, rendered once so the artifact and the
#: parser can never disagree about it. **Derived from the validating type**
#: rather than hand-written beside it — truth has one authoritative
#: representation (`CLAUDE.md` §2), and a hand-copied schema is the second one.
SCHEMA: Final[str] = json.dumps(_Draft.model_json_schema(), indent=2, sort_keys=True)


def parse(raw: str) -> tuple[Passage, ...]:
    """Read a model's reply as passages, or say precisely why it is not.

    **Tolerant of exactly one thing**: a fenced code block, which several
    models emit despite instruction and which is a presentation artifact rather
    than a failure to follow the schema. Tolerating more would be the platform
    quietly repairing output whose defects it is supposed to be measuring.
    """
    text = _unfence(raw.strip())
    if not text:
        raise DraftMalformedError(
            "the model returned nothing. An empty reply is not a refusal — a refusal is a "
            "draft that failed the fence, and this never reached it."
        )
    try:
        draft = _Draft.model_validate_json(text)
    except ValidationError as exc:
        raise DraftMalformedError(
            f"the reply is not the declared shape: {exc}. The brief renders without prose; "
            "nothing a seller reads depended on it."
        ) from exc
    return tuple(Passage(text=one.text, cites=tuple(one.cites)) for one in draft.passages)


def _unfence(text: str) -> str:
    if not text.startswith("```"):
        return text
    body = text.split("\n", 1)[1] if "\n" in text else ""
    return body.rsplit("```", 1)[0].strip()
