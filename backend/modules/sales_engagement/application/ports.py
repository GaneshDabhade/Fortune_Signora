"""What the reasoning needs, expressed as this module's own contracts.

**A port belongs to the module that owns the language it represents**
(`CLAUDE.md` §6). These say what *commercial reasoning* needs, in its own
vocabulary — a Buying Committee Role, evidence that names a title — rather
than mirroring the shapes the modules upstream happen to store.

That is not ceremony. **The Buying Committee is not exported from
`commercial_profile.public` today** ([C-213](../../../../docs/LANE_COORDINATION.md)),
and Commercial Profile is another lane's module. Declaring the need here means
the reasoning core is built, tested and reviewable now, and the adapter that
satisfies it is a separate, small change once the export exists.

**It also keeps this module from importing another's vocabulary.** When
Commercial Profile extends its five committee parts to six, nothing here
breaks: `part` travels as the string it declared, and a part with no rule
ranks on title evidence alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from modules.sales_engagement.domain.fit import ProductRef
from modules.sales_engagement.domain.reasoning import CommitteeRoleRef, Evidence


class CommitteeReader(Protocol):
    """Who the Signora Customer says has to agree, for one of their products.

    **Roles, never people.** No person exists in the platform and none may be
    named here ([C-210](../../../../docs/LANE_COORDINATION.md)); a role is a
    slot a Stakeholder could later fill without changing anything derived from
    it.
    """

    async def committee(
        self, workspace_id: UUID, *, product_id: UUID
    ) -> tuple[CommitteeRoleRef, ...]: ...


class EvidenceReader(Protocol):
    """What has actually happened at a Target Account.

    Returns Business Events as **citations** — an identifier, a summary, when,
    and how many providers agreed. **Never copies of the underlying
    observations**: this module reproduces nothing and stores nothing, and a
    reader follows the identifier back to the evidence that produced it.
    """

    async def evidence(self, workspace_id: UUID, *, account_id: UUID) -> tuple[Evidence, ...]: ...


class PortfolioReader(Protocol):
    """What the Signora Customer sells.

    **Needed only to infer which product a Target Account is about.** When the
    seller has already said, the portfolio is not read at all — an override is
    an answer, not a hint to be re-checked.
    """

    async def portfolio(self, workspace_id: UUID) -> tuple[ProductRef, ...]: ...


@dataclass(frozen=True, slots=True)
class ModelReply:
    """What came back from one model call, in this module's words.

    **`inference_id` is carried rather than looked up**, so a `Synthesis` can
    name the record that produced it without this module knowing what a record
    is, which model answered, or which vendor served it.
    """

    text: str
    inference_id: UUID


class SynthesisModel(Protocol):
    """The one place AI enters commercial reasoning, and it enters last.

    **It names a model, never a vendor** (`CLAUDE.md` §10). Business intent is
    *execute against this model*; who serves it is configuration resolved inside
    the AI Platform, and a port that let this module ask for a vendor would make
    vendor neutrality a rule people remember rather than a shape they cannot
    violate.

    **Deliberately the narrowest possible surface.** Prompt in, text out. No
    conversation, no tools, no streaming, no options — every one of those would
    be a way for the synthesis layer to acquire state, and *statelessness is
    what makes grounding verifiable* (`28-ai-platform.md`). A synthesis that
    remembered the previous account could not be checked against the closed set
    the model was actually shown.
    """

    async def complete(
        self, *, prompt: str, model: str, workspace_id: UUID, correlation_id: UUID
    ) -> ModelReply: ...
