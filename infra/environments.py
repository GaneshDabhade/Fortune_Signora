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
    def database(self) -> str:
        """The application database. `signora` for slot 0 by history."""
        return "signora" if self.slot == 0 else f"signora_{self.name.replace('-', '_')}"

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
        "Human review": "review",
        "QE": "lane-qe",
        "Lane A — Product Surface": "lane-a",
        "Lane B — Commercial Profile": "lane-b",
        "Lane C": "lane-c",
        "Lane D": "lane-d",
        "Lane E": "lane-e",
    }
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
    args = parser.parse_args()

    if args.check:
        return _check()

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
