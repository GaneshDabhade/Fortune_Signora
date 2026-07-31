"""Produce M10's golden dataset from the real pipeline. Run rarely, by hand.

    cd backend && SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 \
        uv run python -m tests.ai_research_engine.seed_planning_dataset

**Not a test**, and named so pytest will not collect it — it needs a database
and it writes a repository artifact. It lives under `tests/` for the same
reason M8's seeder does: that is where the pipeline's composition root is, and
putting one inside `modules/ai_research_engine/` to satisfy a tool would be the
boundary violation this milestone exists to avoid.

**M10 owns its own dataset rather than reusing M8's**, and the reason is
mechanical rather than aesthetic. M8's dataset holds `opportunity`,
`buying_score` and `signal_contribution` facts; the derivation catalog consumes
`business_event` and `dissenting_signal` and nothing else. A planner evaluated
against M8's dataset could only produce steps aimed at facts its derivations
cannot read — every one of which `PlannedStep` refuses at construction. The
evaluation would measure the dataset's shape, not the prompt.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from modules.ai_platform.evaluation.dataset import fingerprint_of
from modules.ai_research_engine.domain.retrieval import BUSINESS_EVENT
from modules.ai_research_engine.infrastructure.retrieval import assemble
from modules.opportunity_engine.public import OpportunityQueries
from signora_platform.db import tenant_scoped_session
from tests.conftest import DEFAULT_ADMIN_DATABASE_URL, DEFAULT_APP_DATABASE_URL

DATASET_DIR = (
    Path(__file__).resolve().parents[2]
    / "modules"
    / "ai_research_engine"
    / "evaluation"
    / "datasets"
)
DATASET_NAME = "research_planning"
DATASET_VERSION = 1
SYNTHESIS_DATASET = "research_synthesis"
SEEDED_FROM = "signora_platform/simulation/scenarios/baseline@1.json (M2.0)"

NOTE = (
    "Golden dataset for M10 planning evaluation. Each case is the closed set of *research* "
    "facts recorded from a real pipeline run over the M2.0 baseline scenario — business events "
    "and preserved dissent, the two kinds the derivation catalog consumes. Not hand-written: "
    "every fact traces back to a simulated provider payload and the id the pipeline minted for "
    "it. `load_bearing` names the facts a useful plan must target; coverage is measured against "
    "them. `fingerprint` is the SHA-256 of `cases`: editing an expectation without bumping "
    "`version` fails to load, because a result recorded against version 1 must remain "
    "re-measurable against version 1. Regenerate with "
    "`python -m tests.ai_research_engine.seed_planning_dataset`, review the diff, and bump the "
    "version if any case changed."
)


async def _build() -> list[tuple[str, Any, Any]]:
    from tests.opportunity_engine.test_opportunity_pipeline import _tracked

    app = create_async_engine(DEFAULT_APP_DATABASE_URL)
    admin = create_async_engine(DEFAULT_ADMIN_DATABASE_URL)
    factory = async_sessionmaker(app, expire_on_commit=False)
    admin_factory = async_sessionmaker(admin, expire_on_commit=False)

    try:
        cases: list[tuple[str, Any, Any]] = []
        for name in ("northwind", "contoso"):
            workspace_id, user_id, entity_id, _ = await _tracked(factory, admin_factory, name)
            async with tenant_scoped_session(
                factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                queries = _queries(session, workspace_id)
                tracked = await queries.tracked(workspace_id, entity_id)
                if tracked is None:
                    raise RuntimeError(f"scenario '{name}' produced no tracked opportunity.")
                explanation = await queries.explanation(workspace_id, tracked.opportunity.id)
                if explanation is None:
                    raise RuntimeError(f"scenario '{name}' produced no explanation.")

            facts = assemble(explanation)
            if not facts:
                raise RuntimeError(f"scenario '{name}' produced no research facts.")
            cases.append((name, workspace_id, facts))
        return cases
    finally:
        await app.dispose()
        await admin.dispose()


def _queries(session: AsyncSession, workspace_id: object) -> OpportunityQueries:
    from tests.pipeline import opportunities

    return opportunities(session, workspace_id)  # type: ignore[arg-type]


def _case(name: str, workspace_id: str, evidence: Any) -> dict[str, Any]:
    facts = [
        {
            "kind": fact.ref.kind,
            "id": str(fact.ref.id),
            "summary": fact.summary,
            "attributes": {key: str(value) for key, value in fact.attributes},
        }
        for fact in evidence
    ]
    # Business events are what a plan must engage with: two of the three
    # derivations read them, and they carry the provider agreement that
    # nothing else in the product surfaces. Dissent is deliberately *not*
    # load-bearing — the baseline scenario may produce none, and a coverage
    # target that depends on whether a fixture happens to contain dissent
    # would measure the scenario rather than the prompt.
    load_bearing = [f["kind"] + ":" + f["id"] for f in facts if f["kind"] == BUSINESS_EVENT]
    return {
        "name": name,
        "workspace_id": workspace_id,
        "facts": facts,
        "load_bearing": load_bearing,
    }


SYNTHESIS_NOTE = (
    "Golden dataset for M10 synthesis evaluation. Each case is the set of *findings* a research "
    "run produces over the M2.0 baseline scenario — the deterministic results a brief is written "
    "about, addressed by the ids the derivations minted and summarised by the catalog's reviewed "
    "questions. **Generated without a model**: the planner chooses which comparisons to run, but "
    "which comparisons *can* run over a given fact set is a derivation question, so every "
    "derivation whose facts are present is executed. That keeps the dataset reproducible and "
    "keeps a prompt's score from moving because a planner happened to choose differently. "
    "`load_bearing` names every finding, since a brief must relate them rather than pick one. "
    "Regenerate with `python -m tests.ai_research_engine.seed_planning_dataset`."
)


def _synthesis_cases(built: list[tuple[str, Any, Any]]) -> list[dict[str, Any]]:
    """Findings, derived from the **typed** facts the pipeline produced.

    Deliberately not derived from the planning dataset on disk: that format
    renders every attribute as a string for the prompt, so a date read back
    from it is text — and `Recency` refuses text, correctly. Deriving from the
    live facts keeps a comparison operating on the types it was written for.
    """
    from datetime import UTC, datetime
    from uuid import UUID, uuid4

    from modules.ai_platform.public import EvidenceRef, EvidenceSet, GroundedStatement
    from modules.ai_research_engine.application.orchestrate import execute
    from modules.ai_research_engine.domain.derivations import as_evidence
    from modules.ai_research_engine.domain.plan import CATALOG, PlannedStep, ResearchPlan
    from modules.ai_research_engine.domain.research import ResearchTask

    now = datetime(2026, 7, 31, tzinfo=UTC)
    cases: list[dict[str, Any]] = []

    for name, workspace_id, facts in built:
        evidence = EvidenceSet(workspace_id=workspace_id, facts=facts, assembled_at=now)
        kinds = {fact.ref.kind for fact in facts}
        # Every derivation whose facts are present. The planner chooses which
        # comparisons to run, but which *can* run is a derivation question —
        # so the dataset stays reproducible and a prompt's score cannot move
        # because a planner happened to choose differently.
        steps = tuple(
            PlannedStep(
                derivation=derivation,
                reason=GroundedStatement(
                    text="Every comparison whose facts are present.",
                    evidence=tuple(
                        fact.ref.token for fact in facts if fact.ref.kind in definition.consumes
                    ),
                ),
            )
            for derivation, definition in CATALOG.items()
            if definition.consumes & kinds
        )
        task = ResearchTask(
            id=uuid4(),
            workspace_id=workspace_id,
            correlation_id=uuid4(),
            subject=EvidenceRef(kind="entity", id=UUID(int=0)),
            opportunity_id=uuid4(),
            requested_at=now,
        )
        findings = execute(task, ResearchPlan(steps=steps), evidence, now=now)
        rendered: list[dict[str, Any]] = [
            {
                "kind": fact.ref.kind,
                "id": str(fact.ref.id),
                "summary": fact.summary,
                "attributes": {key: str(value) for key, value in fact.attributes},
            }
            for fact in (as_evidence(finding) for finding in findings)
        ]
        cases.append(
            {
                "name": name,
                "workspace_id": str(workspace_id),
                "facts": rendered,
                "load_bearing": [f"{f['kind']}:{f['id']}" for f in rendered],
            }
        )
    return cases


def _write(name: str, version: int, note: str, cases: list[dict[str, Any]]) -> None:
    document = {
        "_comment": note,
        "name": name,
        "version": version,
        "fingerprint": fingerprint_of(cases),
        "seeded_from": SEEDED_FROM,
        "cases": cases,
    }
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    path = DATASET_DIR / f"{name}@{version}.json"
    path.write_text(json.dumps(document, indent=2) + "\n")
    print(f"wrote {path} — {len(cases)} cases")


def main() -> None:
    built = asyncio.run(_build())
    _write(
        DATASET_NAME,
        DATASET_VERSION,
        NOTE,
        [_case(name, str(workspace_id), facts) for name, workspace_id, facts in built],
    )
    _write(SYNTHESIS_DATASET, 1, SYNTHESIS_NOTE, _synthesis_cases(built))


if __name__ == "__main__":
    main()
