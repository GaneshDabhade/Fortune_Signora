# `backend/tests/` — what lives here, and who owns it

> **QE's** (`CLAUDE.md` §20e), except the per-module suites listed below, which belong to whichever lane is currently assigned that module.
>
> This file answers one question — *where does my test go, and may I edit the one that is failing?* It does not restate the testing rules; those are `CLAUDE.md` §11 and [ADR-0023](../../docs/architecture/adr/0023-testing-strategy.md).

## Two kinds of directory

**A module suite** is named after a module and tests that module alone. **It belongs to whichever lane is currently assigned that module** — 🟢 in that lane's Change Budget while the assignment lasts, and no other lane edits it. **The suite belongs to the module permanently; the lane only rents it.**

**A cross-cutting suite** tests something no single module owns: the boundary between modules, the platform, the deployed stack, or the architecture itself. **QE owns all of them.**

| Directory | Belongs to | What it holds |
|---|---|---|
| every directory named after a module | **that module's current assignee** — see the registry in [`README.md`](../../README.md) | module suites |
| `integration/` | **QE** | the API surface, event bus, relay, tenancy, migrations, cross-tier JWT — anything needing a real PostgreSQL |
| `security_invariants/` | **QE** | the architectural guarantees, each proven to fail when its guarantee is removed |
| `contract/` | **QE** | the shared Provider Port contract, run against the simulated *and* production adapters. The keystone test |
| `simulation/` | **QE** | the Provider Simulation Framework itself |
| `playground/` | **QE** | `seed` and `narrate` — not tests, the Playground's build scripts |
| `certification/` | **QE** | the ADR-0032 certification record. QE builds it and runs it before every promotion |
| `conftest.py` · `pipeline.py` | **QE** | shared fixtures and the pipeline driver every suite reuses |

A module's *unit* tests may also sit inside the module, at `modules/<module>/tests/`. Only `workspace_tenancy` does this today; both locations are collected (`pyproject.toml`, `testpaths`).

## Where a new test goes

Ask what would have to change for it to fail.

- **One module's own behaviour** → that module's suite. Domain and application layers use fakes; if a domain test needs a database, the Clean Architecture boundary has leaked (`CLAUDE.md` §6).
- **Two modules, or a module against real infrastructure** → `integration/`.
- **A guarantee the architecture depends on**, that should survive any rewrite of the feature that carries it → `security_invariants/`. Deliberate overlap with a feature test is the point: rewriting the feature must not be able to remove its guarantee.
- **A defect somebody hit** → the *affected module's* suite, written by the lane that fixes it. A bug fixed without a regression test is not fixed ([BUGS.md](../../docs/BUGS.md)).
- **A new table** → register it in `security_invariants/tenancy_policy.py` in the same change that creates it, as `TENANT_OWNED` or `PLATFORM_INFRASTRUCTURE`. An unregistered table fails the build, and classification is never inferred from the presence of a `workspace_id` column (`CLAUDE.md` §8).

## QE's standing permission, and its limit

QE **may add a test to any module's suite** — a failing test is a bug report in executable form, and the module's current assignee makes it pass. QE **may not change that module's production code** (`CLAUDE.md` §20e).

Nobody may delete, skip, or weaken a Security Invariant to make a change pass. A failure there means a guarantee has stopped holding (`CLAUDE.md` §11).

## Running it

**Three** environment variables, not two. The third is the one that is easy to miss and is currently a defect — see [B-007](../../docs/BUGS.md).

```bash
cd backend
export SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1
export SIGNORA_TEST_APP_DATABASE_URL=postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:5432/signora_lane_qe
export SIGNORA_TEST_ADMIN_DATABASE_URL=postgresql+asyncpg://signora:signora@localhost:5432/signora_lane_qe
export SIGNORA_DATABASE_URL=postgresql+asyncpg://signora:signora@localhost:5432/signora_lane_qe

uv run pytest                      # your slice: the impacted suites only
uv run pytest --cov                # the gate: everything, coverage ≥ 95%
uv run pytest -m security_invariant
```

Substitute your own lane's database ([`RUNNING.md` § Running a lane](../../docs/RUNNING.md#running-a-lane)). **`SIGNORA_DATABASE_URL` must be exported, not only written to `backend/.env`** — `migrations/env.py` reads `os.environ` directly and does not see the file.

> **The suite truncates `workspace` in whatever database it is pointed at.** Point it at `signora` and the Playground's screens go empty — which is why every lane has its own database. It does **not** truncate the other twenty-four tables, whatever the consent prompt says ([B-008](../../docs/BUGS.md)).
