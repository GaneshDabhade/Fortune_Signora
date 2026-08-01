"""Narrate the Playground's accounts with the real released prompt and model.

    cd backend && SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 uv run python -m tests.playground.narrate

**Deliberately separate from `make demo`, and deliberately opt-in.** Seeding is
offline: it runs the deterministic pipeline and never touches a model, which is
what lets `make demo` work on a machine with no Ollama and finish in seconds.
Narration is a real inference per account — roughly twenty seconds each — so
folding it into the seed would turn a one-command demo into a four-minute one
that fails without a local runtime.

**There is one product.** This runs `Narrate`, the same use case the pipeline
invokes, against the real provider registry, the real prompt registry and the
real release rule. Nothing here is scripted and nothing is patched: if
`explanation_narration@1` were not released for the configured model, this
would refuse — which is the behaviour production has, and the reason it is
worth running here rather than faking.

Ollama is a **development** runtime (ADR-0028). This is a development tool; it
has no production counterpart, and production narration is produced by a
background worker against a hosted model.
"""

from __future__ import annotations

import asyncio
import os
import time
from uuid import UUID, uuid4

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from modules.ai_platform.application.infer import InferencePolicy
from modules.ai_platform.application.narrate import NarrateInput, NothingToNarrateError
from modules.ai_platform.infrastructure.composition import (
    build_narrate,
    build_provider_registry,
)
from modules.ai_platform.infrastructure.explanation import OpportunityExplanationSource
from modules.ai_platform.infrastructure.settings import AISettings
from signora_platform.db import tenant_scoped_session
from signora_platform.event_bus import PostgresOutboxEventPublisher
from tests.conftest import DEFAULT_ADMIN_DATABASE_URL, DEFAULT_APP_DATABASE_URL
from tests.pipeline import opportunities

WORKSPACE_NAME = "Playground"


async def _playground(
    admin_factory: async_sessionmaker[AsyncSession],
) -> tuple[UUID, tuple[UUID, ...]]:
    """The seeded workspace, and any member of it to attribute the run to."""
    async with admin_factory() as session:
        workspace_id = (
            await session.execute(
                text(
                    "SELECT id FROM workspace WHERE name = :n ORDER BY created_at DESC LIMIT 1"
                ),
                {"n": WORKSPACE_NAME},
            )
        ).scalar_one_or_none()
        if workspace_id is None:
            raise SystemExit(
                "No Playground workspace found. Run `make demo-seed` first — narration "
                "explains accounts the deterministic pipeline has already produced."
            )
        entities = (
            (
                await session.execute(
                    text(
                        "SELECT DISTINCT entity_id FROM opportunity WHERE workspace_id = :w"
                    ),
                    {"w": workspace_id},
                )
            )
            .scalars()
            .all()
        )
    return UUID(str(workspace_id)), tuple(UUID(str(e)) for e in entities)


async def _still_there(
    admin_factory: async_sessionmaker[AsyncSession], workspace_id: UUID
) -> bool:
    """Has the workspace survived since the last account?

    **A guard rather than a note, because the note failed three times.** The
    test suite truncates every table in this database, so a `pytest` run in
    another terminal deletes the Playground underneath a narration in
    progress. The run then continues writing into a workspace that no longer
    exists and reports nothing at the end — a silent failure whose symptom
    ("narration produced nothing") points nowhere near its cause.

    One cheap query per account turns several minutes of looking in the wrong
    place into one sentence.
    """
    async with admin_factory() as session:
        return bool(
            (
                await session.execute(
                    text("SELECT 1 FROM workspace WHERE id = :w"), {"w": workspace_id}
                )
            ).scalar()
        )


async def main() -> int:
    if os.environ.get("SIGNORA_ALLOW_DESTRUCTIVE_TESTS") != "1":
        print(
            "Refusing to run. This writes narrations to the target database.\n"
            "Set SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 to confirm it is disposable."
        )
        return 2

    settings = AISettings()
    app = create_async_engine(DEFAULT_APP_DATABASE_URL)
    admin = create_async_engine(DEFAULT_ADMIN_DATABASE_URL)
    factory = async_sessionmaker(app, expire_on_commit=False)
    admin_factory = async_sessionmaker(admin, expire_on_commit=False)

    try:
        workspace_id, entities = await _playground(admin_factory)
        user_id = uuid4()

        print(
            f"narrating {len(entities)} accounts with {settings.ollama_model} "
            f"— a real inference each, ~20s\n"
        )
        # One long-lived client: a connection per account would spend more time
        # in TLS setup than the model spends thinking.
        # Generous, because a local 8B model on modest hardware is slow and a
        # timeout here would look like a product failure rather than a laptop.
        async with httpx.AsyncClient(timeout=180.0) as client:
            providers = build_provider_registry(settings, client=client)
            written = 0

            for entity_id in entities:
                if not await _still_there(admin_factory, workspace_id):
                    print(
                        "\nThe Playground workspace disappeared mid-run. The test suite "
                        "truncates this database — something ran `pytest` against it.\n"
                        "Re-seed and re-run, with nothing else touching the database."
                    )
                    return 1

                started = time.monotonic()
                try:
                    async with tenant_scoped_session(
                        factory, workspace_id=workspace_id, user_id=user_id
                    ) as session:
                        narrate = build_narrate(
                            session,
                            recording_sessions=factory,
                            providers=providers,
                            source=OpportunityExplanationSource(
                                opportunities(session, workspace_id)
                            ),
                            publisher=PostgresOutboxEventPublisher(),
                            policy=InferencePolicy(max_attempts=2),
                        )
                        narration = await narrate.execute(
                            NarrateInput(
                                workspace_id=workspace_id,
                                entity_id=entity_id,
                                model=settings.ollama_model,
                                correlation_id=uuid4(),
                            )
                        )
                    written += 1
                    print(
                        f"  {str(entity_id)[:8]}  {len(narration.statements)} statements"
                        f"  {time.monotonic() - started:5.1f}s"
                    )
                except NothingToNarrateError:
                    # A real outcome, not a failure: an account whose evidence
                    # has expired has nothing to explain, and inventing prose
                    # about an empty evidence set is the exact failure grounding
                    # exists to prevent.
                    print(f"  {str(entity_id)[:8]}  no evidence to explain — skipped")
                except Exception as failure:  # noqa: BLE001 - a demo tool reports and continues
                    print(f"  {str(entity_id)[:8]}  FAILED: {type(failure).__name__}: {failure}")

        print(f"\n{written} of {len(entities)} accounts narrated")
        print("Open http://localhost:3000/opportunities and click any account.")
        return 0
    finally:
        await app.dispose()
        await admin.dispose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
