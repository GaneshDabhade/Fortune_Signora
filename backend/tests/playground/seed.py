"""Seed the Product Playground — twelve accounts, through the real pipeline.

    cd backend && SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 uv run python -m tests.playground.seed

**There is one product.** This runs `_tracked` — the same function the pipeline
suite runs — over `playground@2` instead of `baseline@1`. Provider simulation →
ingestion → normalization → knowledge graph → observations → business events →
signals → buying scores → opportunities, every stage the real path takes, in the
real order, with no branch anywhere that knows this is a playground.

The only things that differ are **which scenario file is named** and **when the
story is anchored**. That is the whole point: a playground that simulated the
product would validate a thing that does not ship.

### Why this file owns the epoch

A scenario declares offsets. *Where* those offsets sit is the decision of
whoever tells the story — the same narrative is today's book or a historical
replay depending only on the anchor, which is why `playground@2.json` does not
carry a date and this module does.

`playground@1` had no anchor at all, so it inherited the simulator's fixed epoch
and the demonstration showed evidence seven months old. Every account read
*"evidence expired"*, and the account whose whole story was *stale evidence*
showed a ledger of fresh evidence (D17).

### Why the score is computed twice

Because that is what actually happens, and because **no state here is set.**

Opportunities are qualified against the scores as they stood at `OPENED`, some
weeks ago — which is when a seller would have committed to them. The sweep then
re-reads whatever has passed the moment its own arithmetic changes, as of
`LAST_SWEEP`. Accounts whose evidence held keep their score; accounts whose
evidence aged fall; accounts whose evidence expired between the last sweep and
now read *stale*.

Current, ageing, cooling, stale, contested — every one of them is produced by
the band arithmetic from the dates in the scenario. **Not one is declared**,
which is the only way a demo environment is worth reviewing a product against.

**Not a test**, and named so pytest will not collect it — it needs a database and
it writes durable rows. It lives under `tests/` for the reason M8's dataset
seeder does: that is where the pipeline's composition root already is, and moving
one into `modules/` to satisfy a directory convention would be the boundary
violation the architecture exists to prevent.
"""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from signora_platform.simulation import dataset as dataset_module
from tests.conftest import DEFAULT_ADMIN_DATABASE_URL, DEFAULT_APP_DATABASE_URL
from tests.opportunity_engine.test_opportunity_pipeline import _tracked
from tests.pipeline import sweep_stale

SCENARIO = ("playground", 2)
WORKSPACE_NAME = "Playground"

HORIZON = timedelta(days=150)
"""How far back the narrative begins.

The scenario's offsets run 0–150, so anchoring here places its last step at
today and its first five months ago. Long enough that a 90-day relevance window
can expire inside it, which is what produces a stale account without one being
asked for."""

OPENED = timedelta(days=35)
"""When the seller committed to these accounts.

Opportunities are qualified against the scores as they stood then, so
`score_at_creation` is a fact about a real earlier moment. Without this every
opportunity would open at the same instant it is read, and *cooling* — a score
that has fallen since somebody decided to work it — could not occur at all."""

LAST_SWEEP = timedelta(days=3)
"""When the scheduled re-scoring last ran.

Shelf-life expiry publishes no event, so scores are refreshed by a sweep rather
than by a trigger. In production that sweep is a scheduled job and there is
always a gap behind it; representing the gap is what lets an account whose
evidence expired *within* it read as stale. Setting it to zero would mean the
demo is only ever seen the instant after a sweep, which no customer ever is."""


def _midnight_today() -> datetime:
    """Today at 00:00 UTC.

    Truncated to the day so two runs on the same day produce byte-identical
    timelines, entity ids and score ids. The epoch is an explicit input to the
    simulation clock, and determinism means *same inputs, same outputs* — not
    that the inputs may never include today's date.
    """
    now = datetime.now(UTC)
    return datetime(now.year, now.month, now.day, tzinfo=UTC)


async def _enrol_everyone(
    admin_factory: async_sessionmaker[AsyncSession], workspace_id: UUID
) -> int:
    """Add every signed-in user to the seeded workspace.

    **No credential ships in this repository.** Better Auth owns users and
    hashes its own passwords, so a seeder that invented one would either commit
    a password or reach into another system's schema. Both are worse than
    asking someone to sign in once.

    Everyone rather than a named account, because on a local machine the set of
    users *is* the developer, and asking for an email address to type is a step
    that exists only to be typed.

    **Better Auth's tables live in the `auth` schema, not `public`.** This
    looked in `public` and therefore always found nobody — and then printed
    *"no signed-in users exist yet"*, which was a false statement about a
    database that had one. It went unnoticed because until M12.3 nothing in the
    repository created those tables at all, so the sentence was accidentally
    true (**R6-01**). Corrected once signing in became possible.
    """
    schema = os.environ.get("SIGNORA_AUTH_SCHEMA", "auth")

    async with admin_factory() as session:
        exists = (
            await session.execute(
                text("SELECT to_regclass(:table) IS NOT NULL"),
                {"table": f'{schema}."user"'},
            )
        ).scalar()
        if not exists:
            return 0

        users = (
            await session.execute(text(f'SELECT id FROM {schema}."user"'))
        ).scalars().all()
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

    today = _midnight_today()
    app = create_async_engine(DEFAULT_APP_DATABASE_URL)
    admin = create_async_engine(DEFAULT_ADMIN_DATABASE_URL)
    factory = async_sessionmaker(app, expire_on_commit=False)
    admin_factory = async_sessionmaker(admin, expire_on_commit=False)

    try:
        print(f"seeding {len(subjects)} accounts through the real pipeline…")
        workspace_id, user_id, _, _ = await _tracked(
            factory,
            admin_factory,
            WORKSPACE_NAME,
            scenario=SCENARIO,
            subjects=subjects,
            epoch=today - HORIZON,
            moment=today - OPENED,
            # Only used to pick the entity returned for the caller's
            # convenience; the scoring moment above is what decides *when* the
            # question is asked, and it is the same for every account.
            anchor="snowflake",
        )

        examined, rescored = await sweep_stale(
            factory, workspace_id, user_id, moment=today - LAST_SWEEP
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
        print(f"re-scored   {rescored} of {examined} readings had aged since they were opened")
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
