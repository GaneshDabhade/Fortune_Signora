"""Produce the golden dataset from the real pipeline. Run rarely, by hand.

    cd backend && SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 \
        uv run python -m tests.ai_platform.seed_golden_dataset

**Not a test**, and named so pytest will not collect it — it needs a database
and it writes a repository artifact. It lives under `tests/` because that is
where the pipeline's composition root is (`tests/pipeline.py`), and putting a
pipeline composition inside `modules/ai_platform/` to satisfy a tool would be
the boundary violation this milestone exists to avoid.

**Why generate rather than write by hand.** A golden dataset asserts what a
narrative must say about a real account. Hand-authoring one would mean
inventing business data and then measuring a model's fidelity to an invention
— the evidence would be shaped by what is convenient to narrate rather than
by what the pipeline actually produces, and every number in it would be one
nobody could trace back to a provider payload.

**Why check it in rather than regenerate it.** Once written it is an
expectation, and expectations do not move because an upstream default
changed. Regenerating on every run would mean a prompt's score could shift
without the prompt, the model, or the criteria changing — which is exactly
the confound the version and fingerprint exist to prevent.

Re-running this **overwrites** the file. That is the deliberate act: review
the diff, and bump `version` if any case changed, because a result recorded
against version 1 must always be re-measurable against version 1.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from modules.ai_platform.evaluation.dataset import DATASET_DIR, fingerprint_of
from modules.ai_platform.infrastructure.explanation import BUYING_SCORE, CONTRIBUTION, assemble
from modules.opportunity_engine.public import OpportunityQueries
from signora_platform.db import tenant_scoped_session
from tests.conftest import DEFAULT_ADMIN_DATABASE_URL, DEFAULT_APP_DATABASE_URL

DATASET_NAME = "explanation_narration"
DATASET_VERSION = 1
SEEDED_FROM = "signora_platform/simulation/scenarios/baseline@1.json (M2.0)"

NOTE = (
    "Golden dataset for prompt evaluation (28-ai-platform.md, T120). Each case is a closed "
    "evidence set recorded from a real pipeline run over the M2.0 baseline scenario — not "
    "hand-written, so every fact traces back to a simulated provider payload and the id the "
    "pipeline minted for it. `load_bearing` names the facts a narrative must cite to be useful; "
    "coverage is measured against them. `fingerprint` is the SHA-256 of `cases`: editing an "
    "expectation without bumping `version` fails to load, because a result recorded against "
    "version 1 must remain re-measurable against version 1. Regenerate with "
    "`python -m tests.ai_platform.seed_golden_dataset`, review the diff, and bump the version "
    "if any case changed."
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

            evidence = assemble(explanation, assembled_at=tracked.opportunity.created_at)
            cases.append(_case(name, evidence))
        return cases
    finally:
        await app.dispose()
        await admin.dispose()


def _queries(session: AsyncSession, workspace_id: object) -> OpportunityQueries:
    from tests.pipeline import opportunities

    return opportunities(session, workspace_id)  # type: ignore[arg-type]


def _case(name: str, evidence: Any) -> dict[str, Any]:
    facts = [
        {
            "kind": fact.ref.kind,
            "id": str(fact.ref.id),
            "summary": fact.summary,
            "attributes": {key: str(value) for key, value in fact.attributes},
        }
        for fact in evidence
    ]
    # The score is what the opportunity rests on, and the counted signals are
    # why it reads as it does. The opportunity fact itself is deliberately not
    # load-bearing: "an opportunity was opened" is the frame, not the content,
    # and requiring it would let a narrative pass by restating the obvious.
    load_bearing = [
        f["kind"] + ":" + f["id"] for f in facts if f["kind"] in (BUYING_SCORE, CONTRIBUTION)
    ]
    return {
        "name": name,
        "workspace_id": str(evidence.workspace_id),
        "facts": facts,
        "load_bearing": load_bearing,
    }


def _write(cases: list[dict[str, Any]]) -> Path:
    document = {
        "_comment": NOTE,
        "name": DATASET_NAME,
        "version": DATASET_VERSION,
        "fingerprint": fingerprint_of(cases),
        "seeded_from": SEEDED_FROM,
        "cases": cases,
    }
    path: Path = DATASET_DIR / f"{DATASET_NAME}@{DATASET_VERSION}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n")
    return path


if __name__ == "__main__":
    written = _write(asyncio.run(_build()))
    print(f"wrote {written}")
