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


@dataclass(frozen=True, slots=True)
class ResearchRun:
    """One run of the research agent, as a list reads it.

    ⚡ **The same request and state `AccountResearch` carries, WITHOUT the
    artifact.** 📁 A list of runs answers *"what has Signora been doing?"*; the
    artifact answers *"what did it find?"*, and loading every finding and
    synthesis for a list nobody has opened yet is the cost `sources` exists to
    avoid.
    """

    request: ResearchRequest
    state: ResearchRequestState
    #: How many distinct sources this run read. **`None` unless it completed** —
    #: a run still running has read nothing yet that anybody may cite, and a
    #: failed one produced no artifact to count. ⛔ **`0` is a different fact**:
    #: a completed run that found nothing worth citing.
    sources: int | None


#: 📁 **How many runs a workspace read returns.**
#:
#: ⚡ **Four times what any one surface shows.** Home's two agent cards read
#: this ONE list and filter it differently — 📁 *"agent output awaiting a
#: person"* takes completed runs, *"scheduled and triggered runs, failures
#: first"* takes every run — so a list cut to five would leave the first card
#: empty on a morning when five runs failed.
#:
#: ⛔ **Not a page size and there is no cursor.** Nothing in the design pages
#: this: both cards show a handful and link onward, and a pagination contract
#: invented here would be a second one to keep in step with the real list
#: screen when one is designed.
RECENT_RUNS: int = 20


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

    async def recent_runs(
        self, workspace_id: UUID, *, limit: int = RECENT_RUNS
    ) -> tuple[ResearchRun, ...]:
        """What the research agent has been asked for lately, newest first.

        ⛔ **Ordering by status is NOT done here.** 📁 *"Failures first"* is one
        surface's ranking of the same list another surface ranks by recency,
        and a read model that baked in one of them would make the other
        re-sort what it was given. **The order this returns is the order the
        runs happened.**

        ⚡ **One extra query for the whole page, not one per run.** The source
        counts arrive as a single grouped read over the tasks that completed.
        """
        runs = await self._requests.recent(workspace_id, limit=limit)
        tasks = tuple(
            state.task_id for _, state in runs if state.task_id is not None
        )
        counts = await self._artifacts.source_counts(workspace_id, tasks)
        return tuple(
            ResearchRun(
                request=request,
                state=state,
                # ⚡ **`0` when the run completed and cited nothing**, `None`
                # when there is nothing to have cited. 📁 The two read
                # differently on a card and the distinction is made here rather
                # than by a renderer inferring it from the status.
                sources=None if state.task_id is None else counts.get(state.task_id, 0),
            )
            for request, state in runs
        )

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
