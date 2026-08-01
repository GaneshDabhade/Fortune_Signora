"""What a customer can read about research on one account.

**One question, one answer.** *"What is the state of research here?"* — which
is a request, sometimes an artifact, and never one without the other. A caller
that had to ask two endpoints and stitch them would be reconstructing a story
the module already knows.

---

**The findings travel with the synthesis, and that is the design.** A research
statement cites `research_finding:<id>` tokens, and every finding it can cite
is in the same response — so following a claim to what it rests on is reading
the payload you already have, not another request. That is the same shape M12.3
gave the ledger, one level up.

**And it goes one level further on its own.** Each finding cites the
`business_event` and `dissenting_signal` rows it compared, in the tokens the
evidence drawer already resolves. The chain is therefore complete from the
sentence a model wrote to the provider that reported the fact, with a
deterministic step at every joint:

    statement  →  finding  →  business event  →  provider readings
    (INFERRED)    (DERIVED)   (DERIVED)          (recorded)

**The question comes from the catalog, not from the model.** A finding's
`derivation` is a key; what it *asks* is a reviewed sentence a domain expert
wrote. Asking a model to paraphrase it would be inventing something the system
already knows — the top rung of the least-powerful-author rule, climbed by
accident.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from modules.ai_platform.public import EvidenceValue
from modules.ai_research_engine.application.ports import (
    ResearchArtifactReader,
    ResearchRequestRepository,
)
from modules.ai_research_engine.domain.plan import CATALOG, DerivationType
from modules.ai_research_engine.domain.request import ResearchRequest, ResearchRequestState
from modules.ai_research_engine.domain.research import (
    ResearchFinding,
    ResearchSynthesis,
    ResearchTask,
)


@dataclass(frozen=True, slots=True)
class ReadableFinding:
    """One comparison, with the question it was performed to answer."""

    finding: ResearchFinding
    #: The catalog's reviewed question. Carried rather than looked up by the
    #: caller, because a client mapping a derivation key to a sentence would
    #: be a second copy of the vocabulary — wrong the moment the catalog gains
    #: an entry, and invisible when it does.
    question: str

    @property
    def attributes(self) -> tuple[tuple[str, EvidenceValue], ...]:
        return self.finding.attributes


@dataclass(frozen=True, slots=True)
class ResearchArtifact:
    task: ResearchTask
    synthesis: ResearchSynthesis
    findings: tuple[ReadableFinding, ...]


@dataclass(frozen=True, slots=True)
class AccountResearch:
    """Everything the product knows about research on one account."""

    request: ResearchRequest
    state: ResearchRequestState
    #: Present exactly when the state is `COMPLETED`. The state's own
    #: invariant already guarantees a completed request names a task, so a
    #: completed request with nothing here is a storage fault rather than an
    #: ordinary absence, and it raises rather than rendering as *"no research
    #: yet"*.
    artifact: ResearchArtifact | None


class ResearchQueries:
    """Read-only. Every method is scoped to one workspace, explicitly."""

    def __init__(
        self, *, requests: ResearchRequestRepository, artifacts: ResearchArtifactReader
    ) -> None:
        self._requests = requests
        self._artifacts = artifacts

    async def for_account(self, workspace_id: UUID, entity_id: UUID) -> AccountResearch | None:
        """The latest request for this account, with its artifact if it has one.

        `None` when nobody has ever asked. That is a different thing from a
        request that found nothing, and the surface says so differently.
        """
        found = await self._requests.latest_for(workspace_id, entity_id)
        if found is None:
            return None
        request, state = found

        artifact = None
        if state.task_id is not None:
            artifact = await self._artifact(workspace_id, state.task_id)
        return AccountResearch(request=request, state=state, artifact=artifact)

    async def _artifact(self, workspace_id: UUID, task_id: UUID) -> ResearchArtifact:
        stored = await self._artifacts.by_task(workspace_id, task_id)
        if stored is None:
            raise ResearchArtifactMissing(
                "This research request settled as completed and its artifact is not "
                "stored. A completed run with nothing to read is a storage fault; "
                "rendering it as 'no research yet' would hide the loss of an AI artifact."
            )
        task, findings, synthesis = stored
        return ResearchArtifact(
            task=task,
            synthesis=synthesis,
            findings=tuple(
                ReadableFinding(
                    finding=finding,
                    question=CATALOG[DerivationType(finding.derivation)].question,
                )
                for finding in findings
            ),
        )


class ResearchArtifactMissing(RuntimeError):
    """A completed request names an artifact that is not stored."""
