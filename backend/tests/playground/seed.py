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
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
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
    roles = _demo_roles()

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
            await session.execute(text(f'SELECT id, email FROM {schema}."user"'))
        ).all()
        for user_id, email in users:
            await session.execute(
                text(
                    "INSERT INTO membership (id, workspace_id, user_id, role, created_at,"
                    " updated_at, created_by, updated_by)"
                    " VALUES (gen_random_uuid(), :w, :u, :r, now(), now(), :u, :u)"
                    " ON CONFLICT DO NOTHING"
                ),
                # A demo persona keeps the role its entry declares; anybody
                # else who has signed in is the developer, and owning the
                # workspace is what lets them look at everything.
                {"w": workspace_id, "u": user_id, "r": roles.get(email, "owner")},
            )
        await session.commit()
        return len(users)


def _app_url() -> str:
    """Where to open the product that was just seeded.

    **It used to say `http://localhost:3000` unconditionally**, which is Human
    Review's port and belongs to no lane (`docs/RUNNING.md` § Running a lane).
    A lane seeding its own database was told, in the same breath, to go and look
    at somebody else's environment — where it would have found different data
    and might well have acted on it.

    Harmless-looking, and the same shape as the default this suite already
    removed once (`frontend/tests/e2e/fixtures/environment.ts`): **an
    instruction that is wrong for everybody except the one person who wrote
    it.** `SIGNORA_APP_URL` is the variable every lane already sets; 3000 is
    correct only when nothing else is.
    """
    return os.environ.get("SIGNORA_APP_URL", "http://localhost:3000")


def _demo_roles() -> dict[str, str]:
    """Which workspace role each seeded persona holds.

    **Read from `infra/demo-users.json`, which the Next tier's `demo:users`
    script also reads.** Two lists would disagree about who exists the first
    time either changed, and the disagreement would look like a permissions
    bug.

    Absent or unreadable is not an error: the file is development tooling, and
    a developer who has only signed in themselves has no personas to place.
    """
    path = Path(__file__).resolve().parents[3] / "infra" / "demo-users.json"
    if not path.exists():
        return {}
    declared = json.loads(path.read_text())["users"]
    return {user["email"]: user["role"] for user in declared}


async def _retire_previous(admin_factory: async_sessionmaker[AsyncSession]) -> int:
    """Remove Playgrounds seeded by an earlier run, so *re*-seeding replaces.

    **Every run used to add one.** `_tracked` creates a workspace and nothing
    removed the last, so a database seeded twelve times held **twelve
    organizations all named `Playground`** — and the product then had to choose
    between them. The selector offered *Playground* twelve times, the active one
    was whichever the browser had stored, and if that was an early one its
    accounts had long since been superseded: **a reviewer opened the product and
    found an empty list, in a database with twelve full ones.**

    Harmless while nobody re-seeded, which is why it went unseen. It stopped
    being harmless when `make e2e` began re-seeding before every run, and the
    same trap was always waiting for anyone who ran `make demo-seed` twice.

    ### One workspace per transaction, and that is not fussiness

    The first version deleted them in a single statement. A seeded workspace is
    the whole pipeline — provider records, observations, business events,
    signals, scores, opportunities, timeline entries, outbox rows — and twelve
    of them cascading at once **took the development PostgreSQL down**, into
    crash recovery, on a machine three lanes share. It recovered with nothing
    lost, and the lesson stands: *the normal case is one, so make the
    pathological case twelve bounded steps rather than one unbounded one.*

    Scoped to this seeder's own name, deliberately: a workspace somebody created
    by hand is not this function's to delete. `CASCADE` is the schema's own
    foreign keys doing the work; nothing here knows the table list, which would
    be a second copy of the schema that drifts.
    """
    async with admin_factory() as session:
        stale = [
            row[0]
            for row in (
                await session.execute(
                    text("SELECT id FROM workspace WHERE name = :name"),
                    {"name": WORKSPACE_NAME},
                )
            ).all()
        ]

    for workspace_id in stale:
        async with admin_factory() as session:
            await session.execute(
                text("DELETE FROM workspace WHERE id = :id"), {"id": workspace_id}
            )
            await session.commit()

    return len(stale)


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
        retired = await _retire_previous(admin_factory)
        if retired:
            print(f"replacing {retired} previous Playground(s)")
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
        app_url = _app_url()
        if enrolled:
            print(f"members     {enrolled} signed-in user(s) enrolled")
            print(f"\nOpen {app_url}")
        else:
            print("members     none — no accounts exist yet")
            print(
                "\nCreate the demo accounts with `make demo-users`, or register at "
                f"{app_url}/sign-up, then re-run this command."
            )
        return 0
    finally:
        await app.dispose()
        await admin.dispose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
