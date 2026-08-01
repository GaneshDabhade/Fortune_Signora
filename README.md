# Signora

**The AI reasoning layer that tells revenue teams which companies to pursue, why now, and what to do next — with evidence, not guesses.**

A modular monolith: Python 3.13 · FastAPI · PostgreSQL 17 · SQLAlchemy 2.x async · Next.js 15. Fourteen modules turn a provider payload into a commercial conclusion a seller can act on **and defend** — every claim followed to the record that produced it.

> **This file is the entry point.** Humans, Claude sessions and other AI agents start here. It routes; it does not duplicate. Anything volatile — test counts, coverage, milestone status — lives in [`PROJECT_STATUS.md`](PROJECT_STATUS.md) and is deliberately not repeated below.

---

## Read these first, in this order

| # | Document | Why |
|---|---|---|
| 1 | **[`CLAUDE.md`](CLAUDE.md)** | The engineering constitution. **Binding, not advisory.** Read §20e before touching anything if you are a second session |
| 2 | **[`docs/architecture/21-intelligence-pipeline.md`](docs/architecture/21-intelligence-pipeline.md)** | How a fact travels from raw payload to conclusion, and what each stage may *not* do |
| 3 | **[`PROJECT_STATUS.md`](PROJECT_STATUS.md)** | Where the project actually is, and **what is currently broken** |
| 4 | Your module's design doc | `docs/architecture/22`–`29`, or the manifest in [`04-modules.md`](docs/architecture/04-modules.md) |

**Then**: [`docs/RUNNING.md`](docs/RUNNING.md) to run it.

## Run it

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
cd frontend && npm install && npm run keys:generate
make demo          # database, migrations, auth tables, 4 sign-in accounts, 12 seeded accounts
```

Then start the API and the web app ([`docs/RUNNING.md`](docs/RUNNING.md) has the exact commands) and sign in as `dana.reyes@northwind.example`.

> **`make test` truncates its target database.** Never run it while reviewing the Playground — or point it elsewhere, as a lane does.

## How the repository is organised

```
backend/modules/<module>/     domain · application · infrastructure · interface · public
backend/signora_platform/     the substrate — FROZEN (CLAUDE.md §20a)
backend/apps/api/composition/ one file per read surface
frontend/components/ui/       the design system — FROZEN (§20c)
frontend/components/<area>/   business components, composed from ui/
docs/architecture/            01–21 architecture · 22–29 module designs · 30+ records
docs/architecture/adr/        36 decisions. Never edited; a reversal is a new ADR
```

## Module registry

**The control tower for parallel development.** One row per module, edited only by the lane that owns it.

| Module | Lane | Status | Frozen |
|---|---|---|---|
| `workspace_tenancy` | A | ✅ Built | — |
| `commercial_profile` | **B** | 🔵 Slice 1 of 5 | — |
| `provider_platform` · `provider_normalization` | A | ✅ Built | — |
| `knowledge_graph` · `observation_engine` | A | ✅ Built | — |
| `business_event_engine` · `signal_engine` · `buying_score_engine` | A | ✅ Built | — |
| `opportunity_engine` | A | ✅ Built | — |
| `ai_platform` | A | ✅ Built | 🔒 since M10 |
| `ai_reasoning_engine` | A | 🔴 **`reasoning@1` unreleased** — would refuse at runtime | — |
| `ai_research_engine` | A | ✅ Built · no HTTP entry point yet | — |
| `signora_platform` | Integrator | ✅ Built | 🔒 §20a |
| Frontend foundation | Integrator | ✅ Built | 🔒 §20c |
| Recommendation Engine · Timeline · Revenue Intelligence Platform | — | ⏳ Not started | — |

**Unowned capabilities**, recorded so they stop disappearing: attribute resolution projection *(Knowledge Graph, needs a slice)* · company discovery *(future context — trigger: a provider adapter with company search)* · deprioritization intelligence *(owner exists, no milestone)* · the RevOps surface *(RIP owns it, no journey defined)* · data export and account deletion *(no owner)*.

## Parallel development

Two lanes, governed by **[`CLAUDE.md` §20e](CLAUDE.md)** — read it before starting a second session.

| Lane | Owns | Branch |
|---|---|---|
| **A — Product Surface** | The pipeline's interface layers, the attention list, the account brief | `lane/surface` |
| **B — Commercial Profile** | `modules/commercial_profile/**`, `/settings/products` | `lane/commercial` |

**The rules in one paragraph.** One session per lane, one lane per module. Branch per *slice*, two days maximum, rebase then fast-forward into `main`. Every slice declares its **Change Budget** (🟢 your module · 🟠 announce it · 🔴 product owner + ADR · ⚫ never). **Shared documents have one owner** — a lane does not edit `PROJECT_STATUS.md`, `SESSION_HANDOFF.md`, `RUNNING.md`, the roadmaps, or `38`/`39`; it reports findings in its commit message and its module doc, and the integrator folds them in at merge. **Touching a file outside your budget is a finding to raise, not a change to make.**

**Each lane needs its own database and ports.** See [`docs/RUNNING.md`](docs/RUNNING.md#running-a-second-lane).

## How we work

**Correctness and clarity outrank cleverness.** Boring, explicit solutions win; novelty needs a real constraint. Consistency across the codebase is worth more than local optimisation.

**No change ships without tests.** Domain logic is unit-tested against fakes; integration tests use a real database and the least-privileged role. Failure paths are not optional. **Run only the impacted suites during a slice**; repository-wide gates are milestone gates.

**Every guarantee is enforced, not documented.** 327 Security Invariants · 31 import-linter contracts · `mypy --strict` · a design-token test · a no-mock-data test · a vocabulary test. *A guard that cannot fail is documentation pretending to be code.*

**All verification is local** ([ADR-0027](docs/architecture/adr/0027-local-first-development.md)). **A `git push` stores the repository and triggers nothing.** Do not create CI/CD.

**The repository must always tell the truth.** A dashboard describing the previous milestone is a defect. Correct a claim about the present; **date a record of the past, never rewrite it.**

**Two vocabularies** ([ADR-0034](docs/architecture/adr/0034-ubiquitous-language.md)). A customer says *organization, account, opportunity, evidence*. The platform says *workspace, tenant, provider, entity, business event*. Both are correct; only the first reaches a screen.

## Current state

See [`PROJECT_STATUS.md`](PROJECT_STATUS.md) — the executive dashboard, and the only place milestone status, test counts and coverage are stated.
