"""HTTP response schemas for the AI Research Engine.

Deliberately separate from the domain objects, even where field-identical:
coupling the wire contract to the domain model makes a domain refactor a
client-breaking change (19-api-conventions.md).

**Everything a client needs to tell computed from written arrives here.** The
whole argument of this surface is that a customer can see which part of a
research brief a model authored and which part deterministic code did, so the
response keeps them structurally apart rather than interleaved:

    statements   INFERRED — a model wrote these sentences
    findings     DERIVED  — code computed these, and cites the rows it used

**A finding carries its question**, taken from the derivation catalog. A client
mapping `corroboration` to *"which conclusions rest on a single provider?"*
would be a second copy of a reviewed vocabulary — wrong the moment the catalog
gains an entry, and invisible when it does. The same rule that put the signal
catalog on the wire at M12.3.

**`prompt_name`, `prompt_version`, `model` and `evidence_digest` are on the
response**, exactly as narration's are. An AI artifact whose provenance a
customer cannot see is one they can only believe.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.ai_research_engine.application.queries import (
    AccountResearch,
    ReadableFinding,
    ResearchArtifact,
    ResearchRun,
)
from modules.ai_research_engine.domain.request import ResearchRequestState, ResearchStatus


class ResearchStatementResponse(BaseModel):
    """One sentence a model wrote, and the findings it rests on."""

    model_config = ConfigDict(frozen=True)

    text: str = Field(description="The sentence, as the model produced it.")
    cites: list[str] = Field(
        description=(
            "Citation tokens (`research_finding:<uuid>`) naming the findings this rests on. "
            "**Every one of them resolves inside `findings` on this same response** — following "
            "a claim to its evidence is reading the payload you already have, never a second "
            "request. Grounding refuses a statement citing anything else, so an unresolvable "
            "token here is a defect rather than an ordinary absence."
        )
    )


class ResearchFindingResponse(BaseModel):
    """One deterministic comparison, and the rows it compared."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(
        description=(
            "The finding's identity — **derived from its content**, so re-running research over "
            "unchanged evidence produces this same id rather than a duplicate."
        )
    )
    ref: str = Field(
        description=(
            "How a statement addresses this finding. Matched against `cites` to resolve a "
            "citation client-side."
        )
    )
    derivation: str = Field(
        description="Which comparison was performed — the name of the code that computed it."
    )
    question: str = Field(
        description=(
            "What this comparison was performed to answer, in the catalog's own reviewed words. "
            "Sent so a client never maps a derivation key to a sentence of its own."
        )
    )
    attributes: dict[str, str] = Field(
        description=(
            "What the comparison produced, rendered for display. **Values are rendered here and "
            "typed in storage** — a client shows them, and a customer who wants to recompute one "
            "opens the cited rows rather than parsing this."
        )
    )
    cites: list[str] = Field(
        description=(
            "The pipeline rows this rests on, in the same citation form the evidence drawer "
            "already resolves — so a finding leads to the business event beneath it and from "
            "there to which providers reported it."
        )
    )

    @classmethod
    def from_domain(cls, readable: ReadableFinding) -> "ResearchFindingResponse":
        finding = readable.finding
        return cls(
            id=finding.id,
            ref=finding.ref.token,
            derivation=finding.derivation,
            question=readable.question,
            attributes={name: str(value) for name, value in finding.attributes},
            cites=[ref.token for ref in finding.cited],
        )


class ResearchArtifactResponse(BaseModel):
    """One completed run: what was compared, and what was made of it."""

    model_config = ConfigDict(frozen=True)

    task_id: UUID = Field(description="The run that produced this.")
    produced_at: datetime = Field(description="When the run happened.")
    statements: list[ResearchStatementResponse] = Field(
        description="What the model wrote. **INFERRED** — every sentence cites findings."
    )
    findings: list[ResearchFindingResponse] = Field(
        description=(
            "What deterministic code computed. **DERIVED** — recomputable by a customer from "
            "the rows each one cites, which is the only class of claim in Signora that needs no "
            "trust at all."
        )
    )
    prompt_name: str = Field(description="Which prompt wrote the statements.")
    prompt_version: int = Field(description="Which version of it.")
    model: str = Field(description="Which model served the call.")
    evidence_digest: str = Field(
        description=(
            "A fingerprint of the exact findings the model was shown. Two syntheses with the "
            "same digest saw the same evidence."
        )
    )

    @classmethod
    def from_domain(cls, artifact: ResearchArtifact) -> "ResearchArtifactResponse":
        return cls(
            task_id=artifact.task.id,
            produced_at=artifact.task.requested_at,
            statements=[
                ResearchStatementResponse(text=statement.text, cites=list(statement.evidence))
                for statement in artifact.synthesis.statements
            ],
            findings=[
                ResearchFindingResponse.from_domain(finding) for finding in artifact.findings
            ],
            prompt_name=artifact.synthesis.prompt_name,
            prompt_version=artifact.synthesis.prompt_version,
            model=artifact.synthesis.model,
            evidence_digest=artifact.synthesis.evidence_digest,
        )


class ResearchStateResponse(BaseModel):
    """Where research on this account stands.

    **Returned by both the request and the read**, so a client renders one
    shape whether it has just asked or is checking back. A response whose shape
    depended on which verb produced it would need two renderers for one thing.
    """

    model_config = ConfigDict(frozen=True)

    request_id: UUID = Field(description="The ask this describes.")
    status: ResearchStatus = Field(
        description=(
            "Where the ask has got to. `nothing_to_research` is **not a failure** — it means the "
            "run finished and found nothing worth comparing, which is a real answer on an "
            "account with little evidence and must never be shown as an error."
        )
    )
    requested_at: datetime = Field(description="When somebody asked.")
    updated_at: datetime = Field(description="When it last changed.")
    detail: str | None = Field(
        description=(
            "Why it failed, verbatim. **Null unless `status` is `failed`** — a reason attached "
            "to any other status would either be inventing one or hiding one."
        )
    )
    artifact: ResearchArtifactResponse | None = Field(
        description=(
            "The brief. **Null unless `status` is `completed`**, and never null when it is: a "
            "completed run with nothing to read is a storage fault the server raises on rather "
            "than rendering as absence."
        )
    )

    @classmethod
    def from_domain(cls, research: AccountResearch) -> "ResearchStateResponse":
        return cls(
            request_id=research.request.id,
            status=research.state.status,
            requested_at=research.request.requested_at,
            updated_at=research.state.occurred_at,
            detail=research.state.detail,
            artifact=(
                ResearchArtifactResponse.from_domain(research.artifact)
                if research.artifact is not None
                else None
            ),
        )

    @classmethod
    def from_request(
        cls, *, request_id: UUID, requested_at: datetime, state: ResearchRequestState
    ) -> "ResearchStateResponse":
        """The shape a fresh request answers with. No artifact can exist yet."""
        return cls(
            request_id=request_id,
            status=state.status,
            requested_at=requested_at,
            updated_at=state.occurred_at,
            detail=state.detail,
            artifact=None,
        )


class ResearchRunResponse(BaseModel):
    """One run of the research agent, as a list of them reads.

    ⛔ **No artifact, deliberately.** 📁 A list answers *"what has Signora been
    doing?"*; `ResearchStateResponse` answers *"what did it find?"*, and a list
    that carried every brief would ship a page of model output for rows nobody
    has opened.

    ⚡ **`account_id` is on the wire and the account's NAME is not.** Naming it
    here would make this module read `commercial_profile`'s records to render
    somebody else's; the identity read every other list on this surface already
    uses resolves it in one batch.
    """

    model_config = ConfigDict(frozen=True)

    request_id: UUID = Field(description="The ask this describes.")
    account_id: UUID = Field(description="The account that was researched.")
    requested_by: UUID = Field(
        description=(
            "Who asked. **The verified principal at the time of asking** — a surface saying "
            "*you requested it* needs to be right about that."
        )
    )
    requested_at: datetime = Field(description="When somebody asked.")
    status: ResearchStatus = Field(
        description=(
            "Where this run got to. `nothing_to_research` is **not a failure** — it finished "
            "and found nothing worth comparing."
        )
    )
    updated_at: datetime = Field(description="When it last changed.")
    detail: str | None = Field(
        description=(
            "Why it failed, verbatim. **Null unless `status` is `failed`.**"
        )
    )
    sources: int | None = Field(
        description=(
            "How many distinct sources the run read. **Null unless it completed** — a run still "
            "running has read nothing anybody may cite yet. **`0` is a different fact**: it "
            "completed and cited nothing."
        )
    )

    @classmethod
    def from_domain(cls, run: ResearchRun) -> "ResearchRunResponse":
        return cls(
            request_id=run.request.id,
            account_id=run.request.entity_id,
            requested_by=run.request.requested_by,
            requested_at=run.request.requested_at,
            status=run.state.status,
            updated_at=run.state.occurred_at,
            detail=run.state.detail,
            sources=run.sources,
        )
