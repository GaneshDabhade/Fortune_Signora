# ENGINEERING_LAWS.md — the Repository Engineering Standard

> **`CLAUDE.md` governs how work *moves*. This document governs how work is *built*.**
>
> Ratified 2026-08-02 by the product owner. **Binding on every lane, every slice, every milestone.** These are laws, not recommendations: a slice that violates one is incomplete, and QE returns it.
>
> **Every law here exists because violating it already cost this repository something.** Each one names the incident. Where a law is anticipatory rather than evidenced, it says so out loud and is deliberately thin — **a rule with no incident behind it is a rule nobody will remember under pressure**, and inventing them is how a standard becomes something lanes skim rather than obey.

---

## 0 · Why this document exists, and what it is not

**Seven milestones in, the lanes had begun rediscovering the same conclusions independently.** Lane A's capability census and Lane B's ICP reuse audit reached compatible principles a day apart, from different modules, with no shared instruction. That is the signal that a principle has stopped being a judgement and become a law: **when two engineers derive the same rule separately, the derivation is waste.**

**It is not a second constitution.** `CLAUDE.md` remains the repository's operating system and is authoritative on governance, module boundaries, tenancy, security, testing and the release lifecycle. **Where a law here would restate one of those, it references instead** — a rule written in two places is a rule that will eventually contradict itself, and the copy nobody maintains is the one somebody will read.

**Three documents, three questions:**

| | |
|---|---|
| **`CLAUDE.md`** | *How does work move, and who may do what?* |
| **`ENGINEERING_LAWS.md`** | *How must an implementation be built?* |
| **[`QUALITY_ENGINEERING.md`](docs/QUALITY_ENGINEERING.md)** | *How does QE verify that it was?* |

### How to read a law

Each carries the same seven fields. **`Verified by` is the field that decides whether a law is real** — a law nothing checks is documentation pretending to be code (`CLAUDE.md` §2), and three laws below are honest about being unenforced today.

---

# Part I — The Laws

---

## L-1 · Reuse is exhausted before anything is created

> **Nothing new is built until the repository has been searched for what already does it.**

**Why it exists.** Discovering existing behaviour costs more effort than writing new behaviour, so the incentive always points at duplication. Left alone, a modular monolith grows two of everything and neither is authoritative.

**What it prevents.** A second definition of a concept a module already owns (`CLAUDE.md` §4) — and the subtler failure underneath it: **capability that exists, is correct, and is invisible.**

**The evidence, and it is the strongest in this repository.** Lane A's Team Management discovery found `p, owner, *, member, remove` granted in `policy.csv:5` — **a reviewed authorization grant for an operation with no endpoint, no use case and no domain method.** Somebody decided owners may remove members; the product cannot. In the same week Lane B's M13 review found `EncryptedSecretStore.purge_for` never called, `SecretUndecryptable` raised and never caught, and `ConnectionState.DISCONNECTED` reachable by no transition ([B-027](docs/BUGS.md)) — **three declared contracts, none honoured, found only by reading for them.** Lane B's ICP reuse audit then found the model has no place to put an ICP, which is why [ADR-0041](docs/architecture/adr/0041-icp-aggregate.md) proposes an aggregate rather than a column.

### The Repository Reuse Audit — mandatory before implementation

**Seven questions, in this order.** The order matters: each is cheaper than the one after it.

| | Question | If yes |
|---|---|---|
| 1 | **Does this already exist?** | Use it. Stop |
| 2 | **Can it be reused unchanged?** | Use it. Stop |
| 3 | **Can it be extended?** | Extend it — additively |
| 4 | **Can it be generalized?** | Generalize, **only if a second caller exists today** (`CLAUDE.md` §6 forbids speculative generalization) |
| 5 | **Can it be refactored in place?** | Refactor, inside your assigned module only |
| 6 | **Can it be extracted and shared?** | Extract — **and this is 🟠 or 🔴; announce or raise it** |
| 7 | **Must it be new?** | **Justify why 1–6 fail.** The justification is part of the slice |

**Where to search, at minimum:** the module's `public/` contracts · `04-modules.md`'s glossary · `policy.csv` · `06-events.md` · the module design docs `22`–`29`, `33`, `41`–`46` · `components/ui` · `lib/api/types.ts` · existing migrations.

**Every implementation report classifies its work into exactly these five buckets:**

```
Reused unchanged   ·  Extended  ·  Generalized  ·  Refactored  ·  New
```

**Exceptions.** None to performing the audit. The audit may *conclude* that new implementation is correct — that is a legitimate and common outcome, and it is not a failure. **What is forbidden is reaching that conclusion without looking.**

**Verified by.** The `Reuse` field of the Slice Handoff (L-15). QE checks the claim against the diff during validation and rejects a slice whose `New` bucket contains something the audit would have found.

**Good.** Lane A discovering that Better Auth's access token already carries `email` and `email_verified` as required claims, and **withdrawing its own recommendation to add a plugin.** No dependency, no frozen-file change, and the blocker removed by reading rather than building.

**Violation.** Adding a second way to resolve a user, a second connection-state enum, or a second `Settings` object for a module that has one — because finding the first would have taken twenty minutes.

---

## L-2 · Evidence before assumption

> **A claim about the repository is measured, not remembered.**

**Why it exists.** This repository's records are load-bearing under rotating assignment, and the cheapest way to corrupt them is to state something plausible.

**What it prevents.** Confident wrong answers that survive review because they sound like the answer.

**The evidence, and some of it is mine.** Lane A's nine review lenses stopped finding work and the module was declared *Implementation Waiting* — **the wrong conclusion from a real observation**, because every lens looked at screens that exist and none could see a capability with no screen at all. A capability audit measuring 31 endpoints against 5 screens produced three slices the same afternoon. Separately, and worse because it is the lane that publishes measurements: **QE reported a capability table showing Timeline Backend ✅ when `project_to_timeline` was referenced zero times in `apps/`**; and on 2026-08-02 QE reported eleven `VERIFIED` bug rows when the true figure was five, **using the same broken precedence as the tool it was accusing of being broken** ([B-101](docs/BUGS.md)).

**The rule.** Any statement about *what the repository is* — counts, coverage, wiring, reachability, status — is produced by running something. **A figure that was true last cycle is not evidence; it is a memory.**

**Exceptions.** Judgement calls are exempt, and must be labelled as judgement. *"~81% complete by engineering effort"* is an estimate and says so. *"15 modules"* is not an estimate and must be counted.

**Verified by.** `infra/state-check.py` for document/repository agreement · `make kpi` for register figures · `make runtime-composition` for wiring · `pytest --cov` for coverage. **QE re-measures everything at Closeout and never transcribes a lane's report** (`CLAUDE.md` §20e).

**Violation.** Carrying a metric forward into a new cycle's dashboard. Asserting a module is wired because its package is imported.

---

## L-3 · Document before complexity

> **When a change is architecturally significant, the design is written and agreed before the code is written.**

**Why it exists.** `CLAUDE.md` §12 already requires documentation to *ship with* implementation. This law is about **sequence**, not existence: for a specific class of change, documentation-after is too late, because the code will have decided the question.

**What it prevents.** An architectural decision taken silently inside a feature slice — *"I could just add it"*, which `CLAUDE.md` §20e already names as how an architectural blocker becomes a design decision nobody ruled on.

**The change classes this law binds** — write the design first:

**a new aggregate · a new bounded context · a customer-data migration · a new workflow or state machine · an identity change · a tenancy change · a security boundary · a new cross-module contract.**

**The evidence.** M14b has two roadmap rows, no scope section, no module and no bounded context — and Lane A correctly stopped rather than choosing one, because **every route into implementation decides the boundary by implementing it** ([C-200](docs/LANE_COORDINATION.md)). Lane B did the same for the ICP: rather than adding a column, it wrote [ADR-0041](docs/architecture/adr/0041-icp-aggregate.md) and stopped. **Both are this law working before it was written down.**

**Exceptions.** A change inside an existing agreed design is not architecturally significant however large. The test is *has anybody decided this?*, never *how many lines is it?*

**Verified by.** QE checks that a slice touching a listed class cites a design doc or ADR predating its implementation commits. **This is checkable by date and is not checked automatically today** — recorded as a gap, not claimed as a gate.

**Violation.** Introducing an aggregate in the same commit that first uses it.

---

## L-4 · A slice stands alone

> **Every slice is independently testable, deployable, demonstrable and reviewable.**

**Why it exists.** `CLAUDE.md` §2 requires a slice to be demoable by a non-engineer. This law states the three other independences that make that possible, because a slice failing any of them cannot be validated on its own — and the lifecycle validates slices on their own.

**What it prevents.** Work that only becomes meaningful after several more slices, which forces batching, which delays defect discovery to the point where the code that caused it is no longer fresh.

**The evidence.** The pipeline ran nine stages ahead of any user-visible surface — recorded in `31-m10-design-review-evidence.md` *before* it was felt, and measured a year of milestones later as 31 endpoints against 5 screens. **Every one of those stages was correct work and none of them was independently demonstrable.**

**The four tests, and all four must pass:**

| | |
|---|---|
| **Independently testable** | Its tests pass without another unshipped slice |
| **Independently deployable** | It can be promoted alone and the product still works |
| **Independently demonstrable** | Showable **without naming a module, table, port or event** (`CLAUDE.md` §2) |
| **Independently reviewable** | Its diff can be judged without reading the next slice's |

**Exceptions.** A slice may be *invisible* to a customer if it is honestly reported as infrastructure — that is permitted work and forbidden reporting. **What is never permitted is calling it a completed product slice.**

**Verified by.** The `Demo` field of the Slice Handoff, in customer vocabulary. QE performs the demo during validation; a demo requiring a paragraph of architecture fails.

**Violation.** *"This will be demonstrable once slice 4 lands."*

---

## L-5 · Every slice increases customer capability, or says plainly that it does not

> **Replacing behaviour without increasing capability requires a stated reason.**

**Why it exists.** A repository can be extremely busy and deliver nothing, and the busyness is indistinguishable from progress in a commit log.

**What it prevents.** Reporting motion as value.

**The evidence.** Cycle 23 promoted nine commits — eight documentation, one governance fix — and the dashboard now records **`Customer value this cycle: No`**. Cycle 22 fixed [B-301](docs/BUGS.md) and the record distinguishes *reliability* from *capability*, because **a cycle that fixes something already claimed as shipped is easy to report as progress twice.**

**Every slice answers three questions in its handoff:**

1. **What new customer capability exists that did not before?**
2. **How is it demonstrated?**
3. **How does QE validate it?**

**`None` is a valid answer to (1)** — for a refactor, a fix, a governance change or a documentation slice. **Silence is not.**

**Exceptions.** Reliability, security and correctness work is exempt from *increasing* capability and must still answer all three.

**Verified by.** `Delivered` and `Demo` in the Slice Handoff; QE publishes the honest answer in `PROJECT_STATUS.md` §1.

**Violation.** A release summary describing what was built rather than what a customer can now do.

---

## L-6 · Customer Journey Integrity — a capability a customer cannot reach is not delivered

> **A backend capability is complete only when a customer can discover it, reach it, and use it.**

**Why it exists.** Every module was built to its own milestone's Definition of Done, and each is correct. **The gap is between them**, and no module's suite can see it.

**What it prevents.** The single largest category of finished-but-inert work in this repository.

**The evidence, measured.** 31 backend endpoints across 11 modules · **5 navigable screens** · **2 reachable by a `member`**. And `/settings/connections` was **linked from nowhere in the product** — the only links to it were the two OAuth redirect helpers *inside the connection flow itself*, so a customer could reach the Connection Center only by already being in it. **A closed loop with no door** ([43-customer-experience.md](docs/architecture/43-customer-experience.md)).

**The three tests:**

| | |
|---|---|
| **Discoverable** | A route exists **and something links to it** from a place a customer will be |
| **Reachable** | The customer's *role* can reach it — not just an owner |
| **Usable** | It does what the surface says it does |

**Exceptions.** A deliberately deferred surface is permitted when the deferral is stated in `Limitations`, and it must not be reported as a completed customer capability.

**Verified by.** QE's exploratory use of the product during validation, and the census method in `43-customer-experience.md`. **Not automated today** — recorded as the gap that let a doorless route ship.

**Good.** CX-01 adding a Connections card to Settings — ten lines that turned an unreachable module into a reachable one.

**Violation.** *"The endpoint works"* offered as evidence a customer can use it.

---

## L-7 · Production Path First — validate the composition, not only the components

> **A capability is not working until the deployed runtime is proven to exercise it.**

**Why it exists.** Five layers get validated and every module's suite covers four of them. **The composition root is the one file no module's own suite covers**: each module tests its half and assumes the wiring.

**What it prevents.** A handler that nothing calls passing every gate in the repository.

**The evidence, and it is exact.** Timeline was built, tested and promoted across **four certified slices** — and the deployed worker never subscribed to its projection, so an account timeline would have stayed empty forever ([B-301](docs/BUGS.md)). **2568 tests, 360 Security Invariants, `make smoke` and four certifications did not see it.**

```
  module implementation      ✅ unit tests
  module tests               ✅ its own suite
  cross-module composition   ✅ integration tests
  runtime composition        ✅ make smoke
  deployed composition       ← the gap
```

**The rule.** Any slice that registers a subscription, a route, a worker, a scheduled job or a composition-root entry must **demonstrate the deployed path exercising it**, not only its own unit.

**Exceptions.** Pure domain logic with no runtime registration is exempt.

**Verified by.** **`make runtime-composition`** — the permanent fix for this class. It reports *what is deployed today*, never *what should eventually exist*, and it deliberately separates the seven modules blocked by [C-012](docs/LANE_COORDINATION.md) from genuine gaps. **`Unexpected missing wiring` is the line that matters; it was 1 when B-301 was found and is 0 now.** Measurement first; gating later, and only on evidence it is needed.

**Violation.** Registering a handler and testing only the handler.

---

## L-8 · Behaviour is preserved

> **A capability that worked before a slice works after it.**

**Why it exists.** New functionality should expand behaviour, not silently replace it — and replacement is rarely deliberate. It is usually a side effect nobody modelled.

**What it prevents.** Regression, which this repository classifies as **repository debt owed by the lane that introduced it**, not as a discovery.

**The evidence.** [B-023](docs/BUGS.md): `tsc --noEmit` failed on the Timeline feed tests while the suite that ran them passed — **a gate and a suite disagreeing about the same code**, so a green lane report was not a green repository. [B-025](docs/BUGS.md): a coverage failure reported as a test failure, naming the wrong gate and sending the lane to the wrong place.

**Every slice performs a behaviour-preservation analysis** proportional to its blast radius, and states the result:

- What existing behaviour does this touch?
- What proves it still holds — **a test that existed before, or a test written now?**
- What is *deliberately* changed, and who is affected?

**Exceptions.** Deliberate behaviour change is legitimate and must be named as such in `Delivered`, with the old behaviour's retirement stated. **An undeclared change is the violation, not a declared one.**

**Verified by.** The repository-wide suite at QE validation — the only place merged code is exercised together. A regression found there is `CHANGES REQUESTED`, returned to the implementing lane.

**Violation.** Changing a shared component to suit one page (`CLAUDE.md` §20c), which is behaviour replacement wearing a styling coat.

---

## L-9 · Customer data is never disposable

> **Schema evolution preserves existing customer data whenever technically possible.**

**Why it exists.** Customer configuration is *irreplaceable* — it is one of the data categories `CLAUDE.md` §2 distinguishes precisely because it cannot be rebuilt from anything.

**What it prevents.** A migration that is convenient for the engineer and catastrophic for the tenant.

**Always prefer, in this order:**

```
  migrate  →  transform  →  normalize  →  backfill  →  version
```

**over**

```
  delete  ·  replace  ·  ask the customer to re-enter it
```

**The evidence.** [B-004](docs/BUGS.md): `provider_watermark` could not tell two targets apart, and the fix was migration `0029` **adding a subject rather than replacing the table** — renumbered twice on rebase and shipped without data loss. `CLAUDE.md` §8 already requires explicit confirmation for destructive migrations; this law states the ordering that usually makes the question unnecessary.

**Exceptions.** A destructive migration is permitted with **explicit product-owner confirmation**, a stated data-loss scope, and a rollback note saying what cannot be recovered. **"No customer has this data yet" is a valid reason and must be verified, not assumed** (L-2).

**Verified by.** Migration reversibility to base and back, run every certification cycle. **Reversibility proves the schema returns; it does not prove the data survived** — that is the reviewer's job, and it is stated here because the gate's limit is easy to over-read.

**Violation.** `DROP COLUMN` where an additive column plus a backfill would have worked.

---

## L-10 · Evolution over replacement

> **The repository grows. It is not periodically rewritten.**

**Why it exists.** Architectural resets discard working, tested, certified behaviour in exchange for a cleaner starting point that will itself need evolving within a quarter.

**What it prevents.** Big-bang rewrites, and the long uncertifiable period in the middle of one.

**The lifecycle every replacement follows:**

```
  old implementation
        ↓
  new implementation, alongside
        ↓
  migration
        ↓
  parallel validation
        ↓
  customer rollout
        ↓
  old implementation retired
```

**Each arrow is a slice boundary**, which is what makes a replacement compatible with L-4.

**The evidence.** [ADR-0039](docs/architecture/adr/0039-release-engineering-model.md) is the worked example — a full release-engineering review that **root-caused seven recurring failures and was accepted as long-term direction while remaining `Proposed`**, with nothing implemented from it. The repository chose to keep a model with known defects over a migration it did not yet need. **Two of its predicted failure classes have since occurred exactly as described** ([B-018](docs/BUGS.md), [B-100](docs/BUGS.md)), and the answer is still not to rewrite: it is to fix the class when the cost is felt.

**Backward compatibility — when it is required:**

| Situation | Compatibility required? |
|---|---|
| A published event payload changes | **Yes** — version bump and stated deprecation window (`CLAUDE.md` §9) |
| A cross-module `public/` contract changes | **Yes** — until every consumer is migrated |
| An API a customer's browser calls changes | **Yes** — until the frontend ships |
| Module-internal structure changes | **No** — that is what the boundary is for |
| A capability nothing consumes changes | **No.** Verify *nothing consumes it* by measurement (L-2, L-7) |

**Temporary duplication is acceptable only inside a stated migration window**, with the retirement slice identified when the duplication is introduced. **Duplication with no retirement date is not a migration; it is L-1 violated slowly.**

**Exceptions.** A stable implementation is not refactored for tidiness. *"It would be cleaner"* is not a reason; a demonstrated defect or a blocked requirement is.

**Verified by.** QE's review of the migration plan against this lifecycle at validation.

---

## L-11 · Every migration carries a contract

> **A migration states what it does to customer data and what happens if it is reversed.**

**Why it exists.** A migration is the only routine change that can destroy something irreplaceable, and it is reviewed in a diff that shows schema rather than consequence.

**What it prevents.** Discovering the data implication after the migration has run.

**The contract — ten fields, in the migration's docstring:**

| | |
|---|---|
| **Purpose** | What requirement it serves |
| **Customer impact** | What a tenant sees, including *nothing* |
| **Preserved data** | What survives untouched |
| **Transformed data** | What changes shape, and the transformation |
| **New data** | What is created, and its default |
| **Rollback behaviour** | What `downgrade` restores |
| **Rollback limitations** | **What `downgrade` cannot restore.** The most important field |
| **Migration ordering** | Its `down_revision`, and why it sits there |
| **Dependency ordering** | What must ship before or after it |
| **Compatibility period · cleanup** | How long duplication lives, and which slice ends it |

**The evidence.** Alembic's `down_revision` is a **linear chain**, so a migration identifier is not cosmetic — which is why migrations are the one identifier class deliberately exempt from block allocation (`CLAUDE.md` §20e) and why Lane A renumbered `0026` twice on rebase and said so. **A gap here is a broken migration graph, not an oddity.**

**Exceptions.** None. A migration with no customer-data implication states that in one line and satisfies the law.

**Verified by.** `alembic downgrade base && alembic upgrade head`, every certification cycle. **QE verifies rollback before promotion** — and the gate proves the *schema* returns, never that the *data* did (L-9).

**Violation.** A migration whose `downgrade` silently drops a column the upgrade backfilled, with no `Rollback limitations` line.

---

## L-12 · Technical debt is classified, not lumped

> **"Technical debt" is seven different things, and they have different owners.**

**Why it exists.** A single label makes everything equally urgent and therefore nothing urgent, and it hides the two categories that are somebody's *decision* rather than somebody's *shortcut*.

**What it prevents.** A backlog where a product-owner ruling and a missing test look identical.

**The seven classes:**

| Class | What it is | Owner | Where it lives |
|---|---|---|---|
| **Intentional debt** | A shortcut taken knowingly, with a stated repayment | The lane that took it | Slice Handoff `Limitations` |
| **Temporary compatibility** | Duplication inside a migration window (L-10) | The migrating lane | The migration contract |
| **Future roadmap** | Not built because it is not next | Product owner | [`BACKLOG.md`](docs/BACKLOG.md) |
| **Missing implementation** | Declared and never built | The module's assignee | [`BUGS.md`](docs/BUGS.md) — it is a defect |
| **Architectural limitation** | The design cannot do this yet | Product owner | [`LANE_COORDINATION.md`](docs/LANE_COORDINATION.md) |
| **Repository bug** | It is simply wrong | The module's assignee | [`BUGS.md`](docs/BUGS.md) |
| **Process gap** | The way we work allowed it | QE | [`BUGS.md`](docs/BUGS.md) + a check |

**The evidence.** The distinction is load-bearing, not academic. [C-012](docs/LANE_COORDINATION.md) — *`EventHandler` receives no session, so the pipeline runs in-process* — has been open since M3A and is an **architectural limitation with an RFC attached**, which is why `make runtime-composition` counts its seven modules separately and would be **useless if it called them defects**. Meanwhile [B-027](docs/BUGS.md)'s absent disconnect was **missing implementation**, filed as a defect and fixed. Same shape, different class, different owner.

**Exceptions.** None. An item that resists classification is usually two items.

**Verified by.** QE at Closeout, reconciling the registers. An item in the wrong register is moved and the move is recorded.

**Violation.** Filing a product-owner decision as technical debt, where it will wait for an engineer who cannot make it.

---

## L-13 · Operational readiness is part of completion

> **A feature ships with the means to understand it in production.**

**Why it exists.** `CLAUDE.md` §17 states it as a principle — *a system cannot be improved using information it never recorded, and the record cannot be added retroactively.* This law makes it a completion condition rather than an aspiration.

**What it prevents.** A failure whose explaining runs are already gone.

**Every significant slice accounts for:** structured logging with `workspace_id` and `correlation_id` · error handling with transient/permanent distinguished · OpenTelemetry traceability for any new async flow · auditability where the record is a customer-facing claim · recovery behaviour on restart.

**The evidence.** `make dr` restarts PostgreSQL, Redis, API, workers and relay and re-runs 360 invariants against the restarted stack — **a gate that exists because recovery was treated as a property to prove rather than assume.** [B-013](docs/BUGS.md) is the counter-example: the worker and relay could not start from a production image, and **2325 passing tests did not see it, because only `make smoke` builds production images.**

**Exceptions.** A slice adding no new runtime behaviour is exempt and says so.

**Verified by.** `make smoke` · `make dr` · the Security Invariants suite.

---

## L-14 · Three laws that live in `CLAUDE.md`, referenced and not restated

**These are laws of equal force. They are not repeated here because they already have an authoritative home**, and `CLAUDE.md` §2's *truth has exactly one authoritative representation* binds this document as much as any other.

| Law | Authoritative in | One-line statement |
|---|---|---|
| **Architecture Preservation** | `CLAUDE.md` §5 · §20e Change Budget | **A module boundary is never crossed for convenience.** A change outside your budget is a finding to raise, not a change to make |
| **Single Source of Truth** | `CLAUDE.md` §2 | **One fact, one owner.** When implementation reveals two representations of one fact, remove one rather than synchronising both |
| **Security & Least Privilege** | `CLAUDE.md` §8 · §13 | **Authorization, tenancy, RLS, secrets and audit are reviewed before implementation**, never after. Runtime credentials are never migration credentials |

> **A fourth candidate was considered and rejected: *Performance & Scalability by Design*.** **No performance defect has occurred in this repository**, `CLAUDE.md` §14 already forbids both obvious waste and speculative optimization, and `12-scalability.md` already defines evidence-based scaling triggers. **Adding a law here would have been inventing one** — which is precisely what the standard's own mandate forbids. It is recorded as considered so the omission reads as a decision rather than an oversight, and it becomes a law the first time a performance defect is filed.

---

# Part II — How compliance is established

## L-15 · The gates before handover

**These become part of the Definition of Done (`CLAUDE.md` §19) and are the lane's, before they are QE's.** The lane establishes them; **QE validates that it happened and does not make it happen.**

| # | Gate | Satisfied when |
|---|---|---|
| 1 | **Repository Reuse Audit** (L-1) | The five buckets are stated, and `New` is justified |
| 2 | **Behaviour Preservation Review** (L-8) | What was touched, and what proves it still holds |
| 3 | **Data Preservation Review** (L-9) | Stated, including *no customer data involved* |
| 4 | **Migration Review** (L-11) | The ten-field contract, if the slice has a migration |
| 5 | **Backward Compatibility Review** (L-10) | Required or not, decided against the table |
| 6 | **Architecture Consistency Review** (L-14) | Budget respected; no boundary crossed |
| 7 | **Runtime Composition Check** (L-7) | `make runtime-composition` shows no new unexpected gap |
| 8 | **Customer Journey Check** (L-6) | ⚡ **For a customer-visible slice: a Playwright scenario that completes the journey.** Discoverable, reachable by role, usable — **demonstrated, not asserted** ([D-113](docs/DECISION_REGISTER.md)) |
| 9 | **Documentation Updated** (L-3) | The module's design doc is true of the code |
| 10 | **QE Impact Statement** | What QE must do to validate this — named, not implied |
| 11 | **No lane-owned Blocking Quality Defect** | Coverage, tests, types, migrations, import contracts, invariants |

### ⚡ Gate 8 becomes executable — [D-113](docs/DECISION_REGISTER.md), 2026-08-06

> ## **Every customer-visible feature has a corresponding customer-visible Playwright journey.**

**This adds no twelfth gate.** **Gate 8 has always asked *"can a customer complete this journey?"* and has always accepted a sentence as the answer.** ⚡ **A Playwright scenario is the same question with an executable answer**, and the repository already has the whole apparatus — 15 spec files, `make e2e`, a narrated `demo` project, `HEADED=1`, traces and video on failure. **What was missing was never the capability. It was the requirement.**

| | |
|---|---|
| ✅ **What a scenario must be** | **A complete user journey** — sign in · create an ICP · triage a signal · create a saved view · open Account 360 · perform a bulk action. **It proves a customer can accomplish meaningful work** |
| ⛔ **What it must not be** | ***button exists · modal opens · icon renders · CSS verification.*** **Those are component tests and `frontend/tests/components/` already holds them** |
| **Coverage a journey earns** | **authentication · navigation · API interaction · persistence · UI refresh · permissions · audit behaviour where applicable** |
| ⚡ **Growth is progressive** | ⛔ **Do not wait for a module to finish.** **When a screen becomes usable, its scenario exists; it expands as functionality arrives** |
| **Headed by default in development** | **`HEADED=1`** — already wired: `headless: process.env.HEADED !== '1'`, with `slowMo` and video. ***"I want implementation to be visible."*** **QE keeps whatever mode is right for certification reliability** |

⚠️ **The suite is therefore also the product demonstration.** **`make product-demo` already runs it narrated, headed and recorded** — **so a stakeholder review, a regression check and an onboarding walkthrough are the same artifact, and it stays true because it runs.**

**All eleven precede the handover, not the rejection.** A gap found at certification is the same gap that was visible to the lane in seconds.

## L-16 · The Slice Handoff gains four fields

**The Slice Handoff (`CLAUDE.md` §20e) is where these laws become checkable**, because it travels with the change forever and is greppable. Four fields are added; every one is required, and `none` is a valid value where silence is not.

```
  Reuse:          reused unchanged — WorkspaceMemberRepository, useWorkspaceMembers
                  extended        — Membership gains a lifecycle transition
                  new             — InvitationRepository; no equivalent exists (audit L-1)
  Preserved:      behaviour — existing member list unchanged, covered by its own suite
                  data      — additive table; no existing row touched
  Reachable:      Settings → Team → Invite. Reachable by owner; member sees the list
  Rollback:       0031 down-migration drops invitation rows.
                  LIMITATION: pending invitations are not recoverable
```

---

# Part III — Governance integration

**Where each rule lives, and why there.** The organising question is the one `CLAUDE.md` §20e already uses: **`CLAUDE.md` answers *"what are the rules?"*; every other document answers *"how do I perform this responsibility?"***

| Rule | Lives in | Reason |
|---|---|---|
| L-1 Reuse · L-2 Evidence · L-3 Document-first · L-4 Independent slice · L-5 Capability · L-6 Journey · L-7 Production path · L-8 Behaviour · L-9 Data · L-10 Evolution · L-11 Migration · L-12 Debt · L-13 Operational | **`ENGINEERING_LAWS.md`** *(this file)* | They govern **how an implementation is built** — a class of rule `CLAUDE.md` deliberately did not carry |
| Architecture Preservation · Single Source of Truth · Security & Least Privilege | **`CLAUDE.md`** §2 · §5 · §8 · §13 · §20e | Already authoritative there. **Referenced here, never restated** |
| The eleven handover gates (L-15) | **`CLAUDE.md` §19**, Definition of Done | Completion is a governance question, and §19 is where a slice is declared done |
| The four Slice Handoff fields (L-16) | **`CLAUDE.md` §20e**, Slice Handoff | The handoff's shape is governance; the fields' meaning is here |
| **How QE verifies each law** | **[`QUALITY_ENGINEERING.md`](docs/QUALITY_ENGINEERING.md)** | QE's operating procedure. **The verification steps are not duplicated here** |
| **The commands** | **[`REPOSITORY_RELEASE_CHECKLIST.md`](docs/REPOSITORY_RELEASE_CHECKLIST.md)** | The runbook carries every command and tick-box |

**What was deliberately *not* created:** a per-law checklist file, a compliance tracker, and a review template. **Every one would be a second place for a rule to live**, and the repository already has the mechanism — the Slice Handoff, which QE reads on every slice.

---

## Honesty about enforcement

**Six of these thirteen laws are checked by a command today. Three are checked by a human. Four are checked by nothing.** Stated plainly, because a standard that implies uniform enforcement is a standard that will be trusted unevenly.

| Enforcement | Laws |
|---|---|
| **Automated** | L-7 `make runtime-composition` · L-9/L-11 migration reversibility · L-13 `make smoke`, `make dr` · L-2 `state-check`, `kpi` · L-15 gate 11 `make coverage-debt` |
| **Human — QE validation** | L-4 the demo · L-6 exploratory use · L-8 the repository-wide suite |
| **Unenforced — declared and not checked** | **L-1 reuse · L-3 document-first · L-5 capability · L-12 classification** |

> **The four unenforced laws are the ones most likely to erode**, and naming them is the first defence. **The right response is a check, not a stronger sentence** — the lesson of [B-022](docs/BUGS.md), where a bolded warning in the runbook was violated within hours by the person who wrote it, and only a preflight fixed it. **Automating them is not scheduled here**, because `CLAUDE.md` §20e binds this document too: governance evolves on observed repeated friction, never on the fact that an improvement is possible.

---

## Amendment

**These laws are amended by the product owner, through the same route as `CLAUDE.md`.** A lane that finds a law wrong raises it in [`LANE_COORDINATION.md`](docs/LANE_COORDINATION.md); it does not route around it. **A law that is inconvenient is not thereby wrong** — and a law that has never been inconvenient has probably never bound anything.
