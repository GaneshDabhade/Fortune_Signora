"""Seed the Product Playground — twelve accounts, through the real pipeline.

    cd backend && SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 uv run python -m tests.playground.seed

**There is one product.** This runs `_tracked` — the same function the pipeline
suite runs — over `playground@1` instead of `baseline@1`. Provider simulation →
ingestion → normalization → knowledge graph → observations → business events →
signals → buying scores → opportunities, every stage the real path takes, in the
real order, with no branch anywhere that knows this is a playground.

The only thing that differs is **which scenario file is named**. That is the
whole point: a playground that simulated the product would validate a thing that
does not ship.

**Not a test**, and named so pytest will not collect it — it needs a database and
it writes durable rows. It lives under `tests/` for the reason M8's dataset
seeder does: that is where the pipeline's composition root already is, and moving
one into `modules/` to satisfy a directory convention would be the boundary
violation the architecture exists to prevent.
"""

from __future__ import annotations

import asyncio
import os
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from signora_platform.simulation import dataset as dataset_module
from tests.conftest import DEFAULT_ADMIN_DATABASE_URL, DEFAULT_APP_DATABASE_URL
from tests.opportunity_engine.test_opportunity_pipeline import _tracked

SCENARIO = ("playground", 1)
WORKSPACE_NAME = "Playground"


async def _enrol_everyone(
    admin_factory: async_sessionmaker[AsyncSession], workspace_id: UUID
) -> int:
    """Add every signed-in user to the seeded workspace.

    **No credential ships in this repository.** Better Auth owns users, creates
    its tables on first run in the Next tier, and hashes its own passwords — so
    a seeder that invented a user would either commit a password or reach into
    another system's schema. Both are worse than asking someone to sign in once.

    Everyone rather than a named account, because on a local machine the set of
    users *is* the developer, and asking for an email address to type is a step
    that exists only to be typed.
    """
    async with admin_factory() as session:
        exists = (
            await session.execute(
                text("SELECT to_regclass('public.\"user\"') IS NOT NULL")
            )
        ).scalar()
        if not exists:
            return 0

        users = (await session.execute(text('SELECT id FROM "user"'))).scalars().all()
        for user_id in users:
            await session.execute(
                text(
                    "INSERT INTO membership (id, workspace_id, user_id, role, created_at,"
                    " updated_at, created_by, updated_by)"
                    " VALUES (gen_random_uuid(), :w, :u, 'owner', now(), now(), :u, :u)"
                    " ON CONFLICT DO NOTHING"
                ),
                {"w": workspace_id, "u": user_id},
            )
        await session.commit()
        return len(users)


async def main() -> int:
    if os.environ.get("SIGNORA_ALLOW_DESTRUCTIVE_TESTS") != "1":
        print(
            "Refusing to seed. This writes to the target database and reuses the "
            "pipeline suite's helpers.\n"
            "Set SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 to confirm the database is disposable."
        )
        return 2

    cast = dataset_module.load(*SCENARIO)
    subjects = tuple(sorted(cast.entities))

    app = create_async_engine(DEFAULT_APP_DATABASE_URL)
    admin = create_async_engine(DEFAULT_ADMIN_DATABASE_URL)
    factory = async_sessionmaker(app, expire_on_commit=False)
    admin_factory = async_sessionmaker(admin, expire_on_commit=False)

    try:
        print(f"seeding {len(subjects)} accounts through the real pipeline…")
        workspace_id, _, _, _ = await _tracked(
            factory,
            admin_factory,
            WORKSPACE_NAME,
            scenario=SCENARIO,
            subjects=subjects,
            # The moment the scenario is scored *at* is derived from one
            # account's evidence. Any of the twelve would do; naming the
            # displacement story makes the choice legible rather than
            # incidental.
            anchor="northwind-logistics",
        )

        # Counted on the admin connection: `SET LOCAL` cannot take a bind
        # parameter, and the alternative — interpolating a workspace id into
        # SQL — is the habit that becomes an injection the first time the
        # value comes from somewhere else.
        async with admin_factory() as session:
            opportunities = (
                await session.execute(
                    text("SELECT count(*) FROM opportunity WHERE workspace_id = :w"),
                    {"w": workspace_id},
                )
            ).scalar()

        enrolled = await _enrol_everyone(admin_factory, workspace_id)

        print(f"\nworkspace   {workspace_id}")
        print(f"accounts    {opportunities} qualified opportunities")
        if enrolled:
            print(f"members     {enrolled} signed-in user(s) enrolled as owner")
            print("\nOpen http://localhost:3000/opportunities")
        else:
            print("members     none — no signed-in users exist yet")
            print(
                "\nSign in once at http://localhost:3000/sign-in, then re-run this "
                "command to be enrolled."
            )
        return 0
    finally:
        await app.dispose()
        await admin.dispose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
