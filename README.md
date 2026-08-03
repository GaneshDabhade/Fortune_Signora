# Signora

**The AI reasoning layer that tells revenue teams which companies to pursue, why now, and what to do next — with evidence, not guesses.**

A modular monolith: Python 3.13 · FastAPI · PostgreSQL 17 · SQLAlchemy 2.x async · Next.js 15. Fifteen modules turn a provider payload into a commercial conclusion a seller can act on **and defend** — every claim followed to the record that produced it.

> **This file is the entry point.** Humans, Claude sessions and other AI agents start here. It routes; it does not duplicate. Anything volatile — test counts, coverage, milestone status — lives in [`PROJECT_STATUS.md`](PROJECT_STATUS.md) and is deliberately not repeated below.

---

## Read these first, in this order

| # | Document | Why |
|---|---|---|
| 1 | **[`CLAUDE.md`](CLAUDE.md)** | The engineering constitution. **Binding, not advisory.** Read §20e before touching anything if you are working in a lane |
| 2 | **[`ENGINEERING_LAWS.md`](ENGINEERING_LAWS.md)** | **The Repository Engineering Standard — how an implementation must be built.** Thirteen laws, each grounded in a defect this repository actually had. `CLAUDE.md` governs how work *moves*; this governs how it is *built* |
| 3 | **[`docs/architecture/21-intelligence-pipeline.md`](docs/architecture/21-intelligence-pipeline.md)** | How a fact travels from raw payload to conclusion, and what each stage may *not* do |
| 4 | **[`PROJECT_STATUS.md`](PROJECT_STATUS.md)** | Where the project actually is, and **what is currently broken** |
| — | [`docs/BUGS.md`](docs/BUGS.md) | Open defects, each against a module. **Any lane opens; the module's current assignee fixes; QE verifies.** Read it before every slice |
| — | [`docs/LANE_COORDINATION.md`](docs/LANE_COORDINATION.md) | **What one lane needs from another**, and what is waiting on a decision. Read it before every slice — this is where an assumption gets caught before it becomes architecture |
| — | [`docs/BACKLOG.md`](docs/BACKLOG.md) | **The READY queue**, in priority order, every task carrying a permanent `TASK-nnn`. If you are a lane with no current slice, **run the Task Claim Protocol** (`CLAUDE.md` §20e) — nobody will assign it to you |
| — | [`docs/ACTIVE_ASSIGNMENTS.md`](docs/ACTIVE_ASSIGNMENTS.md) | **The execution board** — who is doing what right now, on which module, at which slice, blocked by what, and what happens next. **Write your claim here before writing code** |
| — | [`docs/REPOSITORY_RELEASE_CHECKLIST.md`](docs/REPOSITORY_RELEASE_CHECKLIST.md) | **QE only.** The seven-stage repository cycle — validate · certify · integrate · promote · close out · synchronize · declare — with every command and tick-box |
| 5 | **Your assigned module's design doc** | `docs/architecture/22`–`29`, or the manifest in [`04-modules.md`](docs/architecture/04-modules.md). **Under rotating assignment this is your only inherited context** |

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
docs/architecture/adr/        40 decisions. Never edited; a reversal is a new ADR
```

## Module registry

**What exists, and what state it is in.** Modules are **permanent architectural boundaries**; this table describes them and nothing about who is working on them.

> **Who is assigned to what is in [`docs/ACTIVE_ASSIGNMENTS.md`](docs/ACTIVE_ASSIGNMENTS.md)** — the single authoritative record of execution state, written by QE after every promotion. It is deliberately **not** repeated here: a lane assignment changes weekly and a module does not, and two tables stating one fact eventually disagree.

| Module | Status | Frozen | Design doc |
|---|---|---|---|
| `workspace_tenancy` | ✅ Built | — | [`04-modules.md`](docs/architecture/04-modules.md) |
| `commercial_profile` | ✅ Built — all five slices promoted (M12.5) | — | [ADR-0035](docs/architecture/adr/0035-commercial-profile.md) · [ADR-0041](docs/architecture/adr/0041-icp-aggregate.md) *(proposed)* |
| `provider_platform` · `provider_normalization` | ✅ Built | — | [`20`](docs/architecture/20-provider-simulation.md) · [`34`](docs/architecture/34-knowledge-contract.md) |
| `knowledge_graph` · `observation_engine` | ✅ Built | — | [`22`](docs/architecture/22-knowledge-graph.md) · [`23`](docs/architecture/23-observation-engine.md) |
| `business_event_engine` · `signal_engine` · `buying_score_engine` | ✅ Built | — | [`24`](docs/architecture/24-business-event-engine.md) · [`25`](docs/architecture/25-signal-engine.md) · [`26`](docs/architecture/26-buying-score-engine.md) |
| `opportunity_engine` | ✅ Built | — | [`27`](docs/architecture/27-opportunity-engine.md) |
| `ai_platform` | ✅ Built | 🔒 since M10 | [`28`](docs/architecture/28-ai-platform.md) |
| `ai_reasoning_engine` | 🔴 **`reasoning@1` unreleased** — would refuse at runtime | — | [`29`](docs/architecture/29-ai-reasoning-engine.md) |
| `ai_research_engine` | ✅ Built · no HTTP entry point yet | — | [`33`](docs/architecture/33-ai-research-engine-scope.md) |
| The product surface — pipeline `interface/` layers, `frontend/app/(app)/` | 🔵 In progress | — | [`37`](docs/architecture/37-product-surface.md) · [`38`](docs/architecture/38-product-design-principles.md) |
| `signora_platform` | ✅ Built | 🔒 §20a | **Not assignable** — [C-010](docs/LANE_COORDINATION.md) |
| Frontend foundation | ✅ Built | 🔒 §20c | **Not assignable** — [C-010](docs/LANE_COORDINATION.md) |
| Test suites · Playground · reviews · integration · promotion | ✅ Built | — | [`QUALITY_ENGINEERING.md`](docs/QUALITY_ENGINEERING.md) — **QE, permanently** |
| `timeline` | ✅ Built — S01–S04a promoted; **the deployed worker consumes it** ([B-301](docs/BUGS.md)) | — | [`45`](docs/architecture/45-timeline.md) |
| `integrations` | 🔵 In progress — M13 S01, S02, S09 promoted | — | [`13`](docs/architecture/13-integrations.md) · [`44`](docs/architecture/44-integrations.md) |
| Recommendation Engine · Revenue Intelligence Platform | ⏳ Not started | — | — |

**The design doc column is load-bearing.** Under rotating assignment it is the next lane's only inherited context, and a slice is not complete until it is true (`CLAUDE.md` §12).

**Unowned capabilities**, recorded so they stop disappearing: attribute resolution projection *(Knowledge Graph, needs a slice)* · company discovery *(future context — trigger: a provider adapter with company search)* · deprioritization intelligence *(owner exists, no milestone)* · the RevOps surface *(RIP owns it, no journey defined)* · data export and account deletion *(no owner)*.

## Parallel development

Governed by **[`CLAUDE.md` §20e](CLAUDE.md)** — read it before starting a lane.

**A lane is a temporary execution resource, not an owner.** It is assigned one slice inside one module at a time, and the assignment rotates while the architecture does not. **Current assignments: [`docs/ACTIVE_ASSIGNMENTS.md`](docs/ACTIVE_ASSIGNMENTS.md).** Branch names are historical and do not imply a permanent module ([C-009](docs/LANE_COORDINATION.md)).

| Lane | Branch | Builds features? |
|---|---|---|
| **Lane A** | `lane-a-product-surface` | Yes — one assigned slice at a time |
| **Lane B** | `lane-b-commercial-profile` | Yes — one assigned slice at a time |
| **QE — Quality Engineering & Integration** | `lane-qe`, `integration`, `main` | **No.** Validation · certification · integration · promotion, and the repository-state records |
| **Lane C — Product Office, Architecture Governance & Cross-Lane Coordination** | `lane-c-product-office` | **No.** Planning · task decomposition · dependency and ownership analysis · decision preparation · roadmap stewardship. **Writes no production code, and recommends the next assignment rather than claiming one** |

```
Feature Lane ─▶ integration ─▶ QE validation ─▶ QE certification ─▶ QE promotion ─▶ main
                               └──────── QE is the only lane that does these ────────┘
```

**Feature lanes build. QE validates, certifies, integrates and promotes.** No feature lane pushes to `main`; no feature lane bypasses QE. QE builds no customer feature, which is what qualifies it to hold the merge — and **promotion is deterministic: if certification passes, it happens.**

**Lane C sits outside that flow entirely.** It prepares decisions rather than producing commits to promote: it investigates, verifies against the repository, proposes and recommends, and **the change is then made by whoever owns it.**

> **Lane C owns the coordination of implementation, not the implementation itself.**

**Since 2026-08-03 a lane does not select its own next task.** It reports `AVAILABLE`, Lane C analyses roadmap, dependencies, ownership and readiness and recommends, and **the product owner approves.** The boundary with QE is one question: **whether work should proceed is Lane C's; whether the work is correct is QE's.** See [`CLAUDE.md` §20e *Lane C*](CLAUDE.md).

**The workflow is defined in exactly one place: [`CLAUDE.md` §20e](CLAUDE.md).** Startup, slice, completion; who owns each stage; which gates run when; the **Slice Handoff** every lane writes so QE can publish an accurate project status. Nothing here restates it, deliberately: a workflow described in two places is a workflow that will disagree with itself.

**The startup sequence is mandatory and every lane runs it every session:** sync with `integration` · read [`BUGS.md`](docs/BUGS.md) and take the rows assigned to you · read [`LANE_COORDINATION.md`](docs/LANE_COORDINATION.md) · use only the environment [`RUNNING.md`](docs/RUNNING.md#running-a-lane) assigns you · confirm your assignment, its boundaries and its dependencies · `git log integration..HEAD`. **Then** write code.

**Each lane's ports, database and Redis index are allocated by the permanent convention in [`docs/RUNNING.md` § Running a lane](docs/RUNNING.md#running-a-lane).** No lane invents ports; no lane shares a database; **3000/8000 belong to human review on `main`.**

**How QE does its half** — the validation pass, the review method, the isolation audit — is [`docs/QUALITY_ENGINEERING.md`](docs/QUALITY_ENGINEERING.md).

## How we work

**Correctness and clarity outrank cleverness.** Boring, explicit solutions win; novelty needs a real constraint. Consistency across the codebase is worth more than local optimisation.

**No change ships without tests.** Domain logic is unit-tested against fakes; integration tests use a real database and the least-privileged role. Failure paths are not optional. **Run only the impacted suites during a slice**; repository-wide gates are milestone gates.

**Every guarantee is enforced, not documented.** 328 Security Invariants · 31 import-linter contracts · `mypy --strict` · a design-token test · a no-mock-data test · a vocabulary test. *A guard that cannot fail is documentation pretending to be code.*

**All verification is local** ([ADR-0027](docs/architecture/adr/0027-local-first-development.md)). **A `git push` stores the repository and triggers nothing.** Do not create CI/CD.

**The repository must always tell the truth.** A dashboard describing the previous milestone is a defect. Correct a claim about the present; **date a record of the past, never rewrite it.**

**Two vocabularies** ([ADR-0034](docs/architecture/adr/0034-ubiquitous-language.md)). A customer says *organization, account, opportunity, evidence*. The platform says *workspace, tenant, provider, entity, business event*. Both are correct; only the first reaches a screen.

## Current state

See [`PROJECT_STATUS.md`](PROJECT_STATUS.md) — the executive dashboard, and the only place milestone status, test counts and coverage are stated.
