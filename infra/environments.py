#!/usr/bin/env python3
"""**One identity. Everything else derived.**

Phase 1 of the Environment Framework: the *model*, and nothing else. **No
behaviour changes here** — no launcher, no compose, no seeding. This makes the
allocation rule executable, so that everything built on top has exactly one
place to ask *"what is this environment's database?"*

**The rule already existed, written in prose.** [`RUNNING.md`](../docs/RUNNING.md)
says it plainly: *"web `3000 + 100n`, API `8000 + 100n`, database
`signora_lane_<letter>`, Redis logical index `n`."* Beneath that sentence sits a
seven-row table somebody maintains by hand — **a rendering of a derivation**,
which is the duplicated truth `CLAUDE.md` §2 forbids. This is the derivation.

**Two columns the hand-maintained table never had, and their absence caused
defects:**

* **The authentication database.** Every lane's app database was allocated; the
  auth database was not, so all of them shared one — which is how the product
  owner's review session wrote users into another environment
  ([B-104](../docs/BUGS.md)).
* **The compose project.** Two projects exist, both fixed and singleton, so a
  review stack and a certification run are structurally the same project and
  cannot coexist regardless of ports.

**And one column the table had but the code ignored.** Redis is allocated per
environment here and `signora_platform/settings.py` defaults it to index 0
anyway. **A queue is worse to share than a database**: a shared database
corrupts data, a shared queue *executes* it — one environment's workers consume
another's jobs.

    python3 infra/environments.py            # the matrix
    python3 infra/environments.py --check    # agrees with RUNNING.md?
"""

from __future__ import annotations

import argparse
import os
import subprocess
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

REPO_ROOT: Final = Path(__file__).resolve().parent.parent

#: Where a slot's ports start. One block of 100 per environment, so nothing
#: collides and the arithmetic is obvious from any single row.
WEB_BASE: Final = 3000
API_BASE: Final = 8000
SLOT_STRIDE: Final = 100

#: **Backing-service host ports, from the same arithmetic as web and API.**
#:
#: Approved 2026-08-05 by the product owner — *"create separate environment for
#: each lane so that nothing could be shared"* — and it is [436](../docs/architecture/436-execution-isolation.md)
#: change ②. Docker already scopes container names and volumes by project, so
#: **the host port is the only thing four projects genuinely collide on.**
#:
#: Slot 0 keeps today's numbers exactly, so the environment that has always
#: answered on 5432 still does. **A migration nobody has to perform is the only
#: kind that gets performed.**
POSTGRES_BASE: Final = 5432
REDIS_BASE: Final = 6379
MINIO_BASE: Final = 9000
MINIO_CONSOLE_BASE: Final = 9001


@dataclass(frozen=True, slots=True)
class Environment:
    """**Everything an environment is, derived from what it is called.**

    Nothing here is configurable per environment. An environment that needed a
    special database name would be an environment nobody could reason about
    from its identity, which is the property this exists to provide.
    """

    #: The identity. Every other field is a function of this and `slot`.
    name: str
    #: Its block. Ports, Redis index and every other numbered resource come
    #: from it, so two environments cannot collide unless two share a slot —
    #: which `--check` refuses.
    slot: int
    purpose: str
    owner: str
    #: **Ports derive from a different number than Redis does, today.**
    #:
    #: `RUNNING.md` states one rule — *"web `3000 + 100n`, API `8000 + 100n`,
    #: Redis logical index `n`"* — and **its own table does not obey it**: QE
    #: sits on port block 2 and Redis index 1. Block `3100/8100` was allocated
    #: to nobody, which is exactly why the production stack could be moved into
    #: it without renumbering a live environment. The divergence itself remains
    #: a finding for the product owner (see `--check`).
    port_slot: int | None = None
    #: Whether it is expected to be running alongside everything else.
    coexists: bool = True

    @property
    def _ports_from(self) -> int:
        return self.slot if self.port_slot is None else self.port_slot

    @property
    def web_port(self) -> int:
        return WEB_BASE + SLOT_STRIDE * self._ports_from

    @property
    def api_port(self) -> int:
        return API_BASE + SLOT_STRIDE * self._ports_from

    @property
    def postgres_port(self) -> int:
        """**The host port, and therefore the whole of B-118.**

        A PostgreSQL *role* is cluster-wide: two suites reaching `ALTER ROLE`
        collide however many databases they own, which is what aborted cycle
        57. **Per-database separation cannot reach a shared cluster; a separate
        cluster has separate roles.** This is what makes that separation real.
        """
        return POSTGRES_BASE + SLOT_STRIDE * self._ports_from

    @property
    def redis_port(self) -> int:
        return REDIS_BASE + SLOT_STRIDE * self._ports_from

    @property
    def minio_port(self) -> int:
        return MINIO_BASE + SLOT_STRIDE * self._ports_from

    @property
    def minio_console_port(self) -> int:
        return MINIO_CONSOLE_BASE + SLOT_STRIDE * self._ports_from

    @property
    def database(self) -> str:
        """The application database. **`signora`, on every slot.**

        ⛔ **This returned `signora_{name}` for every non-zero slot until
        2026-08-15, and no such database has ever existed.**
        [B-271](../docs/BUGS.md): `infra/docker-compose.yml:31` hardcodes
        `POSTGRES_DB: signora`, so a lane's own stack creates `signora` and
        nothing creates the derived name. **The two together described no
        environment that exists**, and QE's own clone is the worked case — its
        `.env` names `5432/signora_lane_qe`, which is slot 0's *server* holding
        a database `RUNNING.md:324` told somebody to create there by hand.

        **The port is the discriminator and always was.** Every lane runs its
        own PostgreSQL on `5432 + 100n`, so one database name per server is
        correct — the isolation is the server, not the string.

        ⚠️ **The cost, stated rather than implied: the port becomes the SOLE
        discriminator, so a misconfigured port is a silent cross-lane write
        where a wrong name used to fail loudly.** `refuse-slot-0` in the
        `Makefile` covers the case that matters — slot 0 — and the remaining
        exposure is lane-to-lane, which requires overriding
        `SIGNORA_ENVIRONMENT` by hand.

        ⚡ **The alternative was to make compose create the derived name. It was
        rejected on measurement**: lane `.env` files are hand-written and would
        still point at the old database, so it changes what compose creates
        without changing what anything consults — the mismatch survives the fix.
        """
        return "signora"

    @property
    def auth_database(self) -> str:
        """**Better Auth's database — the column that did not exist.**

        Deliberately the *same* database as the application's, because Better
        Auth lives in its own `auth` schema (migration `0005`) and a schema is
        already the isolation boundary. **What matters is that it varies per
        environment**, which is precisely what it did not do.
        """
        return self.database

    @property
    def redis_index(self) -> int:
        """Redis logical index. **Never shared** — a shared queue executes."""
        return self.slot

    @property
    def compose_project(self) -> str:
        """The Docker Compose project. Two containers of the same name in two
        projects are two containers; in one project they are one."""
        return f"signora-{self.name}"

    @property
    def bucket(self) -> str:
        return f"signora-{self.name}"


#: Name → environment, for `SIGNORA_ENVIRONMENT` and for `--check`.
BY_NAME: Final[dict[str, "Environment"]] = {}

#: **The registry.** Adding an environment is a row here, not a table edit in a
#: document — and a row is three facts rather than eight columns somebody keeps
#: consistent by hand.
#:
#: **`lane-c`, `lane-d` and `lane-e` are *environments*, not lanes**, and the
#: distinction became load-bearing on 2026-08-03. **Lane C — the Product Office
#: & Architecture Office — holds none of them**: it owns no production module
#: and runs no production code, so it needs a clone and a branch and nothing
#: numbered. These three rows are free slots waiting for the next
#: *implementation* lane, whichever letter it is given.
ENVIRONMENTS: Final = (
    Environment("review", 0, "Human product review", "Product owner"),
    Environment("lane-qe", 1, "Certification and repository validation", "QE", port_slot=2),
    Environment("lane-a", 2, "Development — Product Surface", "Lane A", port_slot=3),
    Environment("lane-b", 3, "Development — Commercial Profile", "Lane B", port_slot=4),
    Environment("lane-c", 4, "Development — free implementation slot", "—", port_slot=5),
    Environment("lane-d", 5, "Development — free implementation slot", "—", port_slot=6),
    Environment("lane-e", 6, "Development — free implementation slot", "—", port_slot=7),
    #: **The demo environment — the model only** (TASK-409). It is slotted
    #: rather than unslotted because everything about it *does* derive from a
    #: slot: its own seeded database, its own Redis index, its own compose
    #: project. `prod-local` is unslotted because its database and Redis are
    #: private to its own project and a slot would make this model assert names
    #: that are not the ones it uses — **that exception is not this one.**
    #:
    #: **Slot 7 and port block 8, and the two differ deliberately.** Slot 7 is
    #: the first free Redis index; port block 8 is the first free port block,
    #: because block 1 belongs to `prod-local`, which holds no slot. **The
    #: divergence between slot and port block is pre-existing and documented
    #: above — this row inherits it rather than introducing it.**
    #:
    #: **It coexists.** A demonstration a product owner cannot start without
    #: stopping something else is the collision that took 3000/8000 out of
    #: service, and *every runnable environment must be independently startable,
    #: independently stoppable and independently disposable.*
    #:
    #: **No launcher, deliberately** — that is TASK-410's shape. A row here is a
    #: reservation of ports, a database and an index; nothing starts because of
    #: it, and nothing may until the launcher is designed.
    Environment("demo", 7, "Seeded demonstration of shipped capability", "Lane C", port_slot=8),
)

#: **Deliberately outside the slot table, and no longer colliding.**
#:
#: `prod-local` is a self-contained compose project: its PostgreSQL, its Redis
#: and its service names are **private to it** and reachable only from inside.
#: Nothing about it derives from a slot, and giving it one would make this model
#: assert a database name and a Redis index that are not the ones it uses —
#: a model that lies is worse than a model with a documented exception.
#:
#: **What it does share with everything else is host ports**, and that is what
#: went wrong. It bound **3000 and 8000** — `review`'s — which made a
#: certification run and a product review mutually exclusive *by construction*.
#: Phase 1 recorded the collision rather than fixing it. **It was fixed when the
#: product owner hit it**: they could not start a review because a leftover
#: `make dr` stack still held both ports.
#:
#: It now binds **3100/8100**, the block this model had recorded as allocated
#: to nobody, and the two environments no longer meet.
#:
#: **The rule this is an instance of:** *every runnable environment must be
#: independently startable, independently stoppable and independently
#: disposable.* An environment that requires another to be stopped first is not
#: isolated; it is merely documented.
UNSLOTTED: Final = {
    "prod-local": "binds 3100/8100 — its own compose project; nothing else is shared",
}

BY_NAME: Final = {environment.name: environment for environment in ENVIRONMENTS}


BY_NAME.update({e.name: e for e in ENVIRONMENTS})


def current() -> Environment | None:
    """**Which environment this clone is**, without anybody having to remember.

    The product owner approved one stack per lane. **A stack per lane is only
    real if a lane lands on its own one by default** — a mechanism that has to
    be typed correctly every time is the manual convention the directive ruled
    out, wearing a flag.

    Three sources, in order, and each is honest about what it knows:

    **① `SIGNORA_ENVIRONMENT`** — explicit, and it wins. A lane driving a stack
    that is not its own must be able to say so out loud.

    **② The checked-out branch.** `lane-a-product-surface` → `lane-a`,
    `lane-qe` → `lane-qe`, `lane-c-sync` → `lane-c`. **This is derivation, not
    configuration**: the branch already says which lane a clone is, and asking
    it removes the step somebody would forget.

    **③ Nothing.** On `integration`, `main`, or a detached head, **this returns
    `None` rather than guessing.** A wrong guess here points a suite at another
    lane's database, which is the class of defect the whole change exists to
    end — so the caller falls back to the historical shared stack and says so.
    """
    explicit = os.environ.get("SIGNORA_ENVIRONMENT")
    if explicit:
        return BY_NAME.get(explicit)
    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=Path(__file__).resolve().parent.parent,
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return None
    # **Longest first**, so `lane-qe` is not swallowed by a shorter prefix.
    for environment in sorted(ENVIRONMENTS, key=lambda e: -len(e.name)):
        if branch == environment.name or branch.startswith(f"{environment.name}-"):
            return environment
    return None


def _exports() -> int:
    """The shell environment for this clone's stack, or the historical default.

    Consumed by the Makefile, so **no target has to know the arithmetic** and
    no lane has to type a port. Prints to stdout for `eval`.
    """
    environment = current()
    if environment is None:
        # **Named, not silent.** Falling back is correct on `integration`; doing
        # it without saying so is how four clones came to share one server.
        print("# no environment derived (not on a lane branch) — historical shared stack")
        print("COMPOSE_PROJECT_NAME=signora-v2")
        print(f"SIGNORA_POSTGRES_PORT={POSTGRES_BASE}")
        print(f"SIGNORA_REDIS_PORT={REDIS_BASE}")
        print(f"SIGNORA_MINIO_PORT={MINIO_BASE}")
        print(f"SIGNORA_MINIO_CONSOLE_PORT={MINIO_CONSOLE_BASE}")
        # **`signora` by history**, and this branch is the only place that name
        # is correct: it is the shared stack a clone falls back to.
        print("SIGNORA_DATABASE=signora")
        return 0
    print(f"# {environment.name} — {environment.purpose}")
    print(f"COMPOSE_PROJECT_NAME={environment.compose_project}")
    print(f"SIGNORA_POSTGRES_PORT={environment.postgres_port}")
    print(f"SIGNORA_REDIS_PORT={environment.redis_port}")
    print(f"SIGNORA_MINIO_PORT={environment.minio_port}")
    print(f"SIGNORA_MINIO_CONSOLE_PORT={environment.minio_console_port}")
    print(f"SIGNORA_WEB_PORT={environment.web_port}")
    print(f"SIGNORA_API_PORT={environment.api_port}")
    # **The database name, published for the same reason as the ports —
    # TASK-455.** `Environment.database` has always known it; nothing emitted
    # it, so the Makefile hardcoded `/signora` and every slot but `review`
    # pointed at a database that is not its own. ⛔ **The `demo` environment is
    # slot 7 with `signora_demo`, and `make demo` was reaching `signora` on
    # slot 7's port** — a name that exists only because slot 0 is historical.
    print(f"SIGNORA_DATABASE={environment.database}")
    return 0


def _running_md_table() -> dict[str, tuple[int, int, str, int]]:
    """What `RUNNING.md` currently claims, parsed from its table.

    **Read rather than trusted.** The point of `--check` is to find the day the
    document and the derivation disagree, which is the day somebody edited one.
    """
    text = (REPO_ROOT / "docs" / "RUNNING.md").read_text()
    found: dict[str, tuple[int, int, str, int]] = {}
    for row in re.finditer(
        r"^\|\s*\*\*([^*]+)\*\*[^|]*\|[^|]*\|\s*\**(\d{4})\**\s*\|\s*\**(\d{4})\**\s*"
        r"\|\s*`?([a-z_]+)`?\s*\|\s*(\d+)\s*\|",
        text,
        re.M,
    ):
        label, web, api, database, redis = row.groups()
        found[label.strip()] = (int(web), int(api), database, int(redis))
    return found


def _check() -> int:
    """Every slot unique, and the document agreeing with the derivation."""
    problems: list[str] = []

    slots: dict[int, str] = {}
    for environment in ENVIRONMENTS:
        if environment.slot in slots:
            problems.append(
                f"slot {environment.slot} is claimed by both "
                f"'{slots[environment.slot]}' and '{environment.name}' — they would "
                f"share ports, a Redis index and a database."
            )
        slots[environment.slot] = environment.name

    documented = _running_md_table()
    aliases = {
        "Demo": "demo",
        "Human review": "review",
        "QE": "lane-qe",
        "Lane A — Product Surface": "lane-a",
        "Lane B — Commercial Profile": "lane-b",
        "Lane C": "lane-c",
        "Lane D": "lane-d",
        "Lane E": "lane-e",
    }
    # **An environment the document has never heard of.** The loop below walks
    # what `RUNNING.md` documents, so a row added here and nowhere else was
    # simply not checked — **absence read as agreement**, the defect
    # `missing_gates` exists to refuse (ADR-0032) and the one
    # `36-empty-array-checks.md` found nine times in shipped constraints.
    #
    # **It reports rather than repairs, because `RUNNING.md` is QE's file**
    # (`CLAUDE.md` §20e). Lane C may add the model row and may not write the
    # document that describes it, so the correct output is a finding addressed
    # to the lane that owns the document.
    for environment in ENVIRONMENTS:
        if environment.name not in {aliases.get(label) for label in documented}:
            problems.append(
                f"'{environment.name}' is in the derivation and not in RUNNING.md's "
                f"table — web {environment.web_port}, API {environment.api_port}, "
                f"database {environment.database}, Redis {environment.redis_index}. "
                f"RUNNING.md is QE's to write; this is a finding for QE, not a defect here."
            )

    for label, (web, api, database, redis) in documented.items():
        name = aliases.get(label)
        if name is None or name not in BY_NAME:
            continue
        derived = BY_NAME[name]
        for what, doc, code in (
            ("web port", web, derived.web_port),
            ("API port", api, derived.api_port),
            ("database", database, derived.database),
            ("Redis index", redis, derived.redis_index),
        ):
            if doc != code:
                problems.append(
                    f"RUNNING.md says {label}'s {what} is {doc}; the derivation "
                    f"gives {code}. One of them is wrong, and a reader cannot tell which."
                )

    if problems:
        print("\n  Environment model — DISAGREEMENT\n")
        for problem in problems:
            print(f"    ✗ {problem}")
        print(
            "\n  The table in RUNNING.md is a rendering of this derivation. When"
            "\n  they differ, somebody edited the rendering (§2)."
        )
        return 1

    print("\n  Environment model — every slot unique, RUNNING.md agrees.\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify the model")
    parser.add_argument("--exports", action="store_true",
                        help="shell exports for this clone's stack (for eval)")
    parser.add_argument("--which", action="store_true",
                        help="name the environment this clone resolves to")
    args = parser.parse_args()

    if args.check:
        return _check()
    if args.exports:
        return _exports()
    if args.which:
        environment = current()
        print(environment.name if environment else "none")
        return 0

    print("\n  Signora environments — one identity, everything derived\n")
    header = f"    {'ENVIRONMENT':<10} {'WEB':>5} {'API':>5} {'DATABASE':<18} {'REDIS':>5}  {'COMPOSE PROJECT':<18} OWNER"
    print(header)
    print("    " + "─" * (len(header) - 4))
    for environment in ENVIRONMENTS:
        print(
            f"    {environment.name:<10} {environment.web_port:>5} {environment.api_port:>5} "
            f"{environment.database:<18} {environment.redis_index:>5}  "
            f"{environment.compose_project:<18} {environment.owner}"
        )
    print("\n    unslotted, and deliberately:")
    for name, why in UNSLOTTED.items():
        print(f"      · {name:<10} {why}")
    print(
        "\n  **Phase 1: the model only.** Nothing launches from this yet — it exists"
        "\n  so that everything built on top asks one place what an environment is."
        "\n"
        "\n  The authentication database is the *same* database as the application's"
        "\n  (Better Auth lives in its `auth` schema). What matters is that it varies"
        "\n  per environment, which until B-104 it did not."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
