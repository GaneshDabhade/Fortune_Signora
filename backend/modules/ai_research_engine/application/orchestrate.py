"""Executing a plan. **Nothing here decides anything.**

The orchestrator turns selected work into findings and does no comparing of its
own: it resolves each step's targets, hands them to the one rule that computes
that derivation, and assembles the result. Move a single arithmetic operation
into this file and the boundary is gone — the layer that chooses what to run
would also be deciding what it means.

    Planner chooses · orchestrator executes · derivation computes

---

**An ungrounded plan is refused before anything runs.** `verify()` is M8's, and
it already answers the only question that matters here: does every target
resolve inside the evidence the planner was actually shown? A step aimed at an
invented fact never reaches a derivation, so no finding can cite one.

**Re-running is safe, and that is what resumability rests on.** A finding's
identity is derived from its content — workspace, subject, derivation and
version, and the sorted refs it cites — so executing the same plan over the same
facts produces the *same* findings, with the same ids. A partially completed run
resumes by simply running again: what already exists collides on its primary key
and inserts nothing, and what did not is computed. **There is no progress
checkpoint to keep consistent**, which is the failure mode a checkpoint would
introduce.

---

**On the step budget, and why there is no counter here.**

The bound is structural and was installed one task earlier: a plan may not name
one derivation twice, so its length can never exceed the catalog. Counting steps
against a limit would add a guard that cannot fail — the plan reaching this
function is already too short to exceed any limit worth setting.

**On the timeout, and why R-09 is not resolved here.** R-09 asks how long a
research task may run. Everything this function executes is a pure comparison
over facts already in memory, measured in microseconds (see
`test_orchestrate.py`). The term that actually dominates a research task is the
model call — planning and synthesis — and **no prompt exists yet**, so the
number cannot be measured, only guessed. Wrapping microseconds in a timeout
would make the risk *look* addressed while the part that takes minutes stayed
unmeasured, which is worse than leaving it open.
"""

from __future__ import annotations

from datetime import datetime

from modules.ai_platform.public import EvidenceFact, EvidenceRef, EvidenceSet, verify
from modules.ai_research_engine.domain.derivations import for_type
from modules.ai_research_engine.domain.plan import PlannedStep, ResearchPlan
from modules.ai_research_engine.domain.research import (
    ResearchError,
    ResearchFinding,
    ResearchTask,
    research_finding_id,
)


def execute(
    task: ResearchTask,
    plan: ResearchPlan,
    evidence: EvidenceSet,
    *,
    now: datetime,
) -> tuple[ResearchFinding, ...]:
    """Every finding the plan asks for, in the order the plan asks for it.

    `now` is a parameter rather than a clock read: an assembly timestamp that
    varied with when the code ran would be a hidden input, and this module's
    output has to be reproducible from its declared arguments alone.
    """
    if task.workspace_id != evidence.workspace_id:
        raise ResearchError(
            f"task {task.id} belongs to workspace {task.workspace_id} but was given evidence "
            f"assembled for {evidence.workspace_id}. Nothing may cross a workspace boundary, "
            "and a derivation over two workspaces' facts would be the worst way to find out."
        )
    verify(plan, evidence)
    return tuple(_finding(task, step, evidence, now=now) for step in plan.steps)


def _finding(
    task: ResearchTask, step: PlannedStep, evidence: EvidenceSet, *, now: datetime
) -> ResearchFinding:
    targets = step.targets
    facts = tuple(_resolve(evidence, ref) for ref in targets)
    rule = for_type(step.derivation)

    return ResearchFinding(
        id=research_finding_id(
            workspace_id=task.workspace_id,
            subject=task.subject,
            derivation=step.derivation.value,
            derivation_version=rule.version,
            cited=targets,
        ),
        workspace_id=task.workspace_id,
        task_id=task.id,
        subject=task.subject,
        derivation=step.derivation.value,
        derivation_version=rule.version,
        attributes=rule.run(facts),
        cited=targets,
        created_at=now,
    )


def _resolve(evidence: EvidenceSet, ref: EvidenceRef) -> EvidenceFact:
    """`verify` has already established that every target resolves, so this
    cannot return `None` — and asserting that rather than defaulting is the
    difference between a bug that raises and a derivation over silently fewer
    facts than the planner asked for."""
    fact = evidence.resolve(ref)
    if fact is None:  # pragma: no cover - verify() refuses this first
        raise ResearchError(f"{ref.token} passed grounding but resolves to nothing.")
    return fact
