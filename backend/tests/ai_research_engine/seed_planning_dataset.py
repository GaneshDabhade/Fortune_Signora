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


async def _build() -> list[dict[str, Any]]:
    from tests.opportunity_engine.test_opportunity_pipeline import _tracked

    app = create_async_engine(DEFAULT_APP_DATABASE_URL)
    admin = create_async_engine(DEFAULT_ADMIN_DATABASE_URL)
    factory = async_sessionmaker(app, expire_on_commit=False)
    admin_factory = async_sessionmaker(admin, expire_on_commit=False)

    try:
        cases: list[dict[str, Any]] = []
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
            cases.append(_case(name, str(workspace_id), facts))
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


def main() -> None:
    cases = asyncio.run(_build())
    document = {
        "_comment": NOTE,
        "name": DATASET_NAME,
        "version": DATASET_VERSION,
        "fingerprint": fingerprint_of(cases),
        "seeded_from": SEEDED_FROM,
        "cases": cases,
    }
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    path = DATASET_DIR / f"{DATASET_NAME}@{DATASET_VERSION}.json"
    path.write_text(json.dumps(document, indent=2) + "\n")
    print(f"wrote {path} — {len(cases)} cases")


if __name__ == "__main__":
    main()
