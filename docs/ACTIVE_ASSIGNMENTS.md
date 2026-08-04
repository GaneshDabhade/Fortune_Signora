# Active assignments — the execution board

> **The repository's current execution state, and the only authoritative record of it.** Established 2026-08-01; became **the execution board** on 2026-08-02; became **claim-based** the same day, when scheduling moved from QE to a pull model.
>
> **A lane writes its own row when it claims work.** QE reconciles the board at Repository Closeout and removes what has been promoted, but **QE does not decide who does what** (`CLAUDE.md` §20e). If this file and any other document disagree about who is implementing what, **this file is right and the other is a defect.**
>
> **This file holds active execution only: who is working, on which task, on which branch, at what status.** What is *available* is [`BACKLOG.md`](BACKLOG.md), and **the queue's order is the priority — this board defines none of it.** The two are deliberately separate, because a board that also holds the queue becomes a place to negotiate priority.
>
> **Rows reference a `TASK-nnn` and not a description.** An id is immutable and a title drifts, and *"are these two lanes on the same task?"* has to be a fact rather than a reading.

## What a row records

**Four facts about execution, and nothing about priority.**

| | |
|---|---|
| **Who is working** | The `Lane` column |
| **On which task** | The `Task` column — **a `TASK-nnn` from [`BACKLOG.md`](BACKLOG.md)**, never free text |
| **On which branch** | The `Branch` column — where the work physically is, so QE knows what to take |
| **At what execution status** | The `Status` column, from the table below |

**And four that make a cold session useful rather than merely informed:** the `Module` it is inside (the permanent boundary, never a lane's property), the `Slice`, what it is `Blocked by` — named, never implied — and the `Next action`.

> **Priority is not among them.** If this board and [`BACKLOG.md`](BACKLOG.md) ever disagree about what matters most, **the backlog is right**: it is the queue, and this is a record of who is busy.

## What it is, and what it is not

**A lane is a temporary execution resource; a module is a permanent architectural boundary** (`CLAUDE.md` §20e). This file records the *temporary* half — who is executing what, right now — and nothing about architecture.

| | |
|---|---|
| **This file** | *Which lane is doing what today.* Lane-centric. Cleared as work promotes |
| [`README.md`](../README.md) module registry | *What modules exist*, their status, what is frozen. Module-centric. Permanent |
| [`PROJECT_STATUS.md`](../PROJECT_STATUS.md) | *Where the project is.* Measured, historical |
| [`LANE_COORDINATION.md`](LANE_COORDINATION.md) | *What one lane needs from another* |
| [`BUGS.md`](BUGS.md) | *What is wrong* |

**An idle lane has a row here. A module with no assignee does not.** That asymmetry is the point: this file answers *"who is free?"*, which a module-centric table structurally cannot.

## The rules

- **A lane records; nobody self-selects** *(amended 2026-08-03)*. The task arrives **recommended by [Lane C](PRODUCT_OFFICE.md) and approved by the product owner**; the lane then follows the **Task Claim Protocol** (`CLAUDE.md` §20e) to record it — a pushed standalone commit. **No production code before the claim is recorded and synchronized.**
- **Priority is read, never exercised.** [`BACKLOG.md`](BACKLOG.md)'s order is the priority and it is the product owner's. **A lane that believes a different task is the right next one says so in its `Recommended Next Action`** — which is input, exactly like Lane C's.
- **A row names a `TASK-nnn`.** If the work has no task id, it is not claimable work — it is a conversation with the product owner.
- **A lane edits only its own row.** Writing another lane's row, or clearing one, is the confusion this file exists to prevent.
- **One slice under construction per lane. One assignee per module.** Both directions, at all times. **A lane may also hold earlier rows at `IN VALIDATION`** — those are finished work waiting on QE, not a second thing being built.
- **When a lane finishes a slice: set its row `IN VALIDATION`, then immediately report `AVAILABLE`.** A lane never idles waiting for QE (`CLAUDE.md` §20e, *Continuous execution*) — *"my last slice has not been certified"* has never been a reason to stop, and **a recommendation that has not arrived is a finding rather than a reason to sit still.**
- **QE removes the row once the work reaches `main`.** A row describing work already on `main` is the defect this file exists to prevent — **no lane may remain recorded against shipped work, and no stale row is left behind.**
- **A row is a slice, not a milestone.** *Commercial Profile — slice 2* is an assignment; *Commercial Profile* is not.
- **`Started` is when the assignment was made**, not when the branch was created.
- **A lane whose module is blocked stays assigned** and the blocker is named — that is a fact about execution state, and hiding it makes the lane look idle when it is stuck.
- **Every row states its expected next action.** A board that says what is happening but not what happens next leaves a cold session to infer it, and an inferred next action is how two lanes do the same thing.

| Status | Meaning |
| `CLAIMED` | The claim commit is **pushed and confirmed first**. Implementation may begin |
| `ACTIVE` | Being implemented |
| `BLOCKED` | Waiting on a `C-` item or a dependency. **Name it** |
| `IN VALIDATION` | Handed to QE — **committed and pushed**, in the lifecycle, not yet promoted |
| `CHANGES REQUESTED` | **QE, during validation.** Something did not hold, and the corrections are named. Returned to the implementing lane, which fixes them in place and returns the task to `IN VALIDATION` |
| `COMPLETE` | Promoted to `main`. **Marked by QE at Closeout, then removed, and the lane returns to `AVAILABLE`** |
| `AVAILABLE` | No current slice. **Amended 2026-08-03: this now means *awaiting Lane C's analysis and recommendation*, not *free to choose*.** A lane reports `AVAILABLE`; [Lane C](PRODUCT_OFFICE.md) prepares the next recommendation; the product owner approves; the lane records the claim and builds |

> **`IN VALIDATION` means the work exists as commits QE can take.** Uncommitted work in a session's working tree is `ACTIVE`, whatever stage it feels like it has reached — **the board describes the repository, not an intention.** This distinction was added on 2026-08-02 after this file recorded QE's own governance slice as `IN VALIDATION` while it was still entirely uncommitted.

---

## Current — as of 2026-08-03, `bdc159f`

| Lane | Task | Branch | Module | Slice | Status | Blocked by | Next action | Started |
|---|---|---|---|---|---|---|---|---|
| **Lane A** | — | `lane-a-product-surface` | **Product Surface** — **assigned, and not released** | PS-01…08 · TS-02 · **CX-01…03** | **`ACTIVE`** — Implementation Waiting **ended 2026-08-02, the day it was declared** | **[C-203](LANE_COORDINATION.md) · [C-025](LANE_COORDINATION.md) · [C-026](LANE_COORDINATION.md) · [C-008](LANE_COORDINATION.md)** — for *those* slices only | **The module was declared waiting because nine review lenses stopped finding work, and that was the wrong test.** Every lens looked at screens that exist; none could see a capability with no screen at all. A capability audit — 31 endpoints against 5 screens — produced three slices the same afternoon, and every one was invisible to every test in the repository. **Driver is now [43-customer-experience.md](architecture/43-customer-experience.md)**; the correction is recorded in [37-product-surface.md](architecture/37-product-surface.md) | 2026-08-02 |
| **Lane A** | — | `lane-a-product-surface` | **`provider_platform`** — **assigned, and not released** | PP-01 · 02 · 04 · 05 · 06 built · PP-03 suspended | `BLOCKED` — module in **Implementation Waiting** | **[C-021](LANE_COORDINATION.md)** · owner **product owner** · entered waiting **2026-08-02** | **Every executable capability inside the accepted architecture is built.** What remains needs a dispatch direction; recorded in [41-provider-platform.md](architecture/41-provider-platform.md). **PP-03 stays suspended** — the module was not out of work, only its next *planned* slice was | 2026-08-02 |
| **Lane A** | **Team Management** *(customer capability, assigned by the product owner 2026-08-02)* | `lane-a-product-surface` | `workspace_tenancy` — **the capability, not the module** | Phases 1–3 complete · **TM-03 unblocked by evidence** | **`ACTIVE`** | **[C-207](LANE_COORDINATION.md)** for leaving only · **[C-206](LANE_COORDINATION.md)** narrowed to one email-delivery decision | **Self-challenge overturned this lane's own recommendation.** The plugin was unnecessary: every access token already carries `email` and `email_verified`, both **required claims** the Python verifier type-checks, and Better Auth already enforces verification — so accepting an invitation is matching a pending row against a claim that already arrives. **No plugin, no dependency, no frozen-file change.** The invitation table and acceptance are buildable now; the members list follows them. Analysis in [46-team-management.md](architecture/46-team-management.md) §11 | 2026-08-02 |
| **Lane A** | **M14b — Billing, Analytics & Feature Flags** *(implementation initiative, assigned by the product owner)* | `lane-a-product-surface` | **undecided — see [42-billing-and-entitlements.md](architecture/42-billing-and-entitlements.md)** | domain discovery | `BLOCKED` | **[C-200](LANE_COORDINATION.md)** — the bounded context is 🔴 | **Discovery complete, no code.** M14b has two roadmap table rows and no scope section, no module and no bounded context — the same shape as [C-020](LANE_COORDINATION.md) and [C-023](LANE_COORDINATION.md). **It is one module and two integrations, not one and not three**; every route into implementation decides the boundary by implementing it | 2026-08-02 |
| **Lane B** | **[TASK-300](BACKLOG.md) — Epic A, surface what already exists** *(assigned by the product owner 2026-08-03)* | `lane-b-commercial-profile` | `knowledge_graph` **(claimed — unassigned)** · `opportunity_engine` · `timeline` · `integrations` | A4 · A1 · A2 · A5 · A6 | **`ACTIVE`** | **[C-323](LANE_COORDINATION.md)** for A4, A1 and A5's render — **Lane A holds Product Surface and `provider_platform`, and is 128 files into `SW-01…04` in the same surface** | **Verified against Lane A's branch before starting: A2 is being built there now and B2 is done.** Proceeding on [B-200](BUGS.md) and the two `knowledge_graph` backends, which collide with nobody; **not entering Lane A's modules** pending the ruling | 2026-08-03 |
| **QE** | — | `lane-qe` | — (the repository) | permanent | `ACTIVE` | — | **Cycle 35 promoted (`bdc159f`). 35 pinned, 28 certified.** `make unsaved` (RS-1) · performance sequencing guideline · D-1 and D-2 ruled. **Next: PR-1, the demonstration beat runner — blocked on [C-100](LANE_COORDINATION.md)** | 2026-08-01 |

**Which lanes are available is the `Status` column above, and is not restated here** — a sentence beside a table is a second copy of one fact, and it drifted within an hour of being written (§2). **Unclaimed capacity:** lanes C, D and E ([`RUNNING.md`](RUNNING.md#running-a-lane) holds their reserved environments).

**QE's row is permanent** and is never removed — it is the one row that outlives its own completion, because the responsibility is the repository rather than a slice inside it. **QE claims nothing and is claimed by nothing.**

### Lane C — referenced, not rowed

**Lane C — Product Office, Architecture Governance & Cross-Lane Coordination** holds `lane-c-product-office` and is **deliberately absent from the table above** (product owner, 2026-08-03). **This board measures implementation; Lane C produces none.** It holds no `TASK-nnn` and claims nothing from [`BACKLOG.md`](BACKLOG.md). Its remit and boundaries are [`CLAUDE.md` §20e *Lane C*](../CLAUDE.md).

> **Lane C owns the coordination of implementation, not the implementation itself.**

**This board is an input to Lane C, not only a record.** When a lane's row reaches `AVAILABLE`, `BLOCKED` or `WAITING`, **Lane C reads it and recommends to the product owner** — the lane does not select for itself, and **Lane C does not assign.**

| | |
|---|---|
| **Current** | Continuous planning — queue depth, dependency horizon, blocking items |
| **Delivered** | [C-400](LANE_COORDINATION.md) doc-number collisions · [C-401](LANE_COORDINATION.md) merge-risk measurement · [C-403](LANE_COORDINATION.md) QE's action list · [C-404](LANE_COORDINATION.md) backlog reality · [C-406](LANE_COORDINATION.md) branch-visibility cause · [B-400](BUGS.md) 🔴 migration collision · [B-401](BUGS.md) the blocking check |
| **Next** | Recommend on `AVAILABLE`; **the product owner allocates** |

### Prepared portfolio — initiatives, not tasks

**Ratified 2026-08-04, product owner: the unit of allocation is an epic or milestone, never a `TASK-nnn`** ([`PRODUCT_OFFICE.md`](PRODUCT_OFFICE.md) §5). **Nothing here is an assignment.** It is what each lane could own **end to end**, so an allocation is one sentence and then days of unattended work. **Verified against branches rather than against the queue.**

#### Current — a lane could start today

| | Initiative | Lane | Modules | Duration | Deps | Conflict | Independent |
|---|---|---|---|---|---|---|---|
| **A1** | **Responsive Product Surface** — [CX-07](architecture/43-customer-experience.md) | **A** | Product Surface · shell · navigation · layout | **XL** · 2–3 wks | **none** | 🟢 | ✅ |
| **A2** | **Business Workspace** — [TASK-903](BACKLOG.md) stage 2 | **A** | Product Surface + `commercial_profile` **(Lane B's)** | **M** | none | 🟠 | ⚠️ read-only crossing |
| **B1** | **Timeline Intelligence** — [TASK-902](BACKLOG.md), M7 S05+ | **B** | `timeline` alone | **L** · ~2 wks | none | 🟢 | ✅ |
| **B2** | **CRM Integration** — [Epic E1](architecture/401-epic-e1-crm-read.md) ✅ **prepared** | **B** | `integrations` · `provider_platform` | **XL** · 2–3 wks | **credentials — yours** | 🟢 | ✅ |
| **B3** | **Observation Intelligence** — [A5](architecture/51-implementation-specifications.md) render + [B-319](BUGS.md) | **B** | `observation_engine` · Product Surface | **M** | **[C-324](LANE_COORDINATION.md)** | 🟢 | ✅ *if C-324 says yes* |

> **A1 is the recommendation, and it is the correction this pass produced.** Lane C reported CX-07 as *"no agreed scope, escalated to Pack I"* twice. **It was ruled on 2026-08-03**: [C-026](LANE_COORDINATION.md) put **phone in scope**, and [43-customer-experience.md](architecture/43-customer-experience.md) records it as *"the largest executable slice on this page — executable, unbuilt."* **Lane C escalated a decision that had already been made**, and in doing so reported Lane A's queue as three deep when a two-to-three week initiative was sitting in it.

> **B3 is the interesting one, because allocation is itself the answer.** [C-324](LANE_COORDINATION.md) asks *where Epic A's rendering stops being Lane B's.* **Giving Lane B the whole Observation Intelligence initiative — endpoint, [B-319](BUGS.md) and screen — answers it by removing the boundary**, and it is the only option that leaves no handover. The alternative splits one capability across two lanes for no gain.

#### Upcoming — blocker has a named owner and a visible end

| Initiative | Lane | Waiting on | Owner |
|---|---|---|---|
| **Epic A completion** — A6 | **A** | **[C-321](LANE_COORDINATION.md)** — what to do with a company it cannot name | **You** |
| **Risk Intelligence** — [Epic D](architecture/51-implementation-specifications.md) D2 | **B** | Nothing hard; **D1 depends on Epic C**, D2 does not | Sequencing only |
| **Event-driven Timeline** — [TASK-901](BACKLOG.md) | **B** | **[TASK-900](BACKLOG.md)** platform composition RFC | **You** |

> **The Timeline feed is mounted and nearly empty, and the cause is not the Timeline.** `make runtime-composition` reports **2 of 9 declared consumers wired** — `_project_to_timeline` and `_run_requested_research`. **Seven event families never reach a projection**, which is [TASK-901](BACKLOG.md), which is blocked on the [TASK-900](BACKLOG.md) RFC. **B1 above ships real slices regardless**; this is what makes the *experience* complete.

#### Blocked — waiting on a decision or a dependency

| Initiative | Blocked by | Owner |
|---|---|---|
| **M14b — Billing, Analytics & Feature Flags** ([TASK-906](BACKLOG.md)) | **[C-200](LANE_COORDINATION.md)** 🔴 — no bounded context. **It is one module and two integrations, not one and not three** | **You** |
| **Knowledge Graph vocabulary** ([TASK-003](BACKLOG.md)) | **[C-018](LANE_COORDINATION.md)** — nobody owns an attribute's customer-facing name | **You** ([Pack C](DECISION_PACKS.md)) |
| **Epic D3** — which accounts are already customers | **E1** — one boolean from the CRM, **and it unblocks the whole expansion/renewal half of the vision** | Sequencing |

#### Preparation portfolio — researched ahead of implementation

**Ratified 2026-08-04, product owner: preparation is continuous and does not wait for a decision.** *"Implementation lanes should never wait for discovery."* **Lane C prepares the next initiative the moment one becomes ready, without approval and without allocation.**

| Initiative | Maturity | Blocking questions **and** decisions | **Technically best suited** |
|---|---|---|---|
| **CX-07 · Responsive Surface** | ✅ **COMPLETED** | — *(Lane A, TASK-200, slice 4 closed the milestone)* | — |
| **E1 · CRM read** | 🔨 **ACTIVE IMPLEMENTATION** | **Credentials** — acquisition only. **[ADR-0401](architecture/adr/0401-a-customers-crm-is-not-a-provider.md) amended**; the firmographic mapper has landed | **Lane B** (TASK-402) |
| **G · Copilot** | 🔨 **ACTIVE IMPLEMENTATION** | **[C-222](LANE_COORDINATION.md)** — `reasoning@1` **earns a protocol-2 release on `llama3.1:8b`** and the repository cannot record it under its own 60 s timeout. **Blocks only a live G1 inference** | **Lane A** (TASK-202) |
| **F · Workflow** | 🟩 **READY** | **[ADR-0402](architecture/adr/0402-a-rule-is-data.md)** ratification — and nothing else | **Lane B** backend · **Lane A** builder |
| **D · Risk** | 🔨 **ACTIVE IMPLEMENTATION** | **Nothing** — claimed as **TASK-203** | **Lane A** ph. 1 · **Lane B** ph. 2–3 |
| **C · People** | ⏸️ **WAITING ON PRODUCT DECISIONS** | **❓1 answered — the provider returns no name.** ADR-0400 ratification · contact ruling · **E1's progression** — §7 route B is now the only path to a named person | **Lane B** *(one remnant: the committee role id)* |
| **M14a · Notifications** | 🔷 **ARCHITECTURE** *(not Lane C's)* | **[ADR-0040](architecture/adr/0040-notifications.md) `Proposed`.** Designed by Lane B; **F's phase 5 consumes it** | **Lane B** |
| **M14b · Billing** | 🔎 **DISCOVERY — cannot proceed** | **[C-200](LANE_COORDINATION.md) 🔴** — no bounded context. **Preparation cannot invent scope** | **Lane A** |
| **RIP · Revenue Intelligence** | ⛔ **RECOMMEND RETIRING** — [408](architecture/408-revenue-intelligence-platform.md) | **[C-411](LANE_COORDINATION.md)** — its job is `apps/api/composition/`, already built. **Nothing to implement** | — |
| **M14.5 · Cloud Infrastructure** | 🔎 **DISCOVERY** | **Scope, technology and topology already ratified** in [ADR-0022](architecture/adr/0022-devops-infrastructure-and-deployment-topology.md) — *"nothing removed or redesigned, only its position in the order."* **Preparation would restate a ratified ADR** | **QE / platform** |
| **M15 · GA readiness** | 🔎 **DISCOVERY** | **Depends on a deployed environment** (M14.5) for load testing at volume. **Three of its four workstreams already have live findings feeding them** — see below | **QE / platform** |
| **E2 · CRM write-back** | 🟩 **READY** — [406](architecture/406-epic-e2-crm-write-back.md) | **[E1](architecture/401-epic-e1-crm-read.md) acquisition** must land first. **Zero cross-lane crossings** | **Lane B** |
| **M11 · Recommendation** | 🔷 **ARCHITECTURE** — [407](architecture/407-m11-recommendation.md) | **Its input has never fired.** `reasoning@1` unreleased ([404](architecture/404-epic-g-copilot.md) §1) · **[C-410](LANE_COORDINATION.md)** | **Lane B** |

**Maturity states:** 🔎 Discovery → Research → 🔷 Architecture → Repository Validation → Reuse Analysis → Technical Design → 🟩 **READY** → 🔨 Active Implementation → ✅ Completed · ⏸️ Waiting on Product Decisions · ⛔ Recommend retiring *(any state may enter the last two)*.

> **Every roadmap initiative is now at the highest maturity repository evidence honestly allows.** Four sit below READY and **none of them is under-prepared** — [M11](architecture/407-m11-recommendation.md)'s input has never fired, [M14b](LANE_COORDINATION.md)'s scope does not exist, **M14.5's design is already a ratified ADR**, and **M15 needs a deployed environment that M14.5 has not built.** *Forcing any of them to READY would produce a package a lane discovers is hollow.*

**M15 is not prepared, and three of its four workstreams already have findings waiting for it** — recorded here rather than in a package nobody can act on yet:

| M15 workstream | What already feeds it |
|---|---|
| **PII** | **[405](architecture/405-cross-cutting-concerns.md) §2** — log redaction is credential-shaped and matches no name, email or phone. **[Epic C](architecture/400-epic-c-people.md) changes that on its first commit** |
| **Spend governance** | **[404](architecture/404-epic-g-copilot.md) §7** — **cost per inference is unmodelled anywhere**, and Epic G is active |
| **SOC 2** | **[406](architecture/406-epic-e2-crm-write-back.md) §9** — the write log, *"a feature, not a metric"*; and **[C-410](LANE_COORDINATION.md)**'s release-evidence trail |
| **Load testing** | **Nothing yet** — it needs M14.5's environment, and that is the whole dependency |

> **M15 becomes preparable the day M14.5 lands.** Until then, **the useful Product Office work is making sure each finding above is still true when it gets there** — which is cross-validation, not a new document.

> ⚠️ **Percentages were dropped, and the reason is a miss worth recording.** [Epic C](architecture/400-epic-c-people.md) was reported **READY, 100%**, with blockers given as *"ADR-0400 ratification · contact ruling."* **Its own ❓1 — *does the provider return a person's name?* — was documented in the package and omitted from the portfolio row.** Lane A checked it first, as the ADR instructed, and **the answer blocked the epic.** A percentage said *ready*; an unanswered question said *maybe not*, and only one of them reached the summary a reader allocates from. **The column now carries blocking *questions* alongside blocking *decisions*.**

### Roadmap evolution — 2026-08-04

**Standing section.** What changed about *what should be built*, as distinct from what is ready to build.

| | Initiative | Evidence |
|---|---|---|
| ⛔ **Recommend retiring** | **RIP** | Its job is `apps/api/composition/`, built. **The shape it would take was tried and import-linter refused it.** Fails every part of the aggregate test — [C-411](LANE_COORDINATION.md) |
| 🏷️ **Recommend renaming** | **Epic D phase 1 = the *Deprioritization Intelligence* differentiator** | A **governing differentiator in zero milestones**, and **already `READY` as [TASK-905](BACKLOG.md)**. The differentiator doc's own estimate — *"a policy decision more than a new module"* — matches what the code says |
| 📉 **Became smaller** | **E1** | Lane B's firmographic mapper: **six attributes, no RFC, no table, no event, no migration.** The interpretation half was free |
| 📉 **Became smaller** | **Epic C** | **The buying score needs no change at all** — it weights signals generically, so a person-subjected signal costs zero scoring work |
| 📈 **Became larger** | **Epic C** | **Its own ❓1 blocks it.** Not larger in code — **larger in what must be decided before any is written** |
| 🔗 **Newly independent** | **Epic F** | [ADR-0402](architecture/adr/0402-a-rule-is-data.md) — publishing an event instead of invoking actions **removes its dependency on Notifications, Slack, email and E2**, none of which exist |
| ♻️ **Newly discovered reuse** | **M11 · E2** | Both inherit **`MACHINE_AUTHORED`** — the enforced *"intelligence suggests, humans commit"* boundary — rather than inventing a guard |
| ⚠️ **Newly exposed gap** | **Data export · account deletion** | **No owner anywhere in the repository.** Epic C raises the stakes; M15 nominally covers it and sits behind an unbuilt environment — [C-412](LANE_COORDINATION.md) |
| ⚠️ **Newly exposed gap** | **PII in logs** | Redaction is credential-shaped — [405](architecture/405-cross-cutting-concerns.md) §2 |
| 🏷️ **Naming collision** | **Epic F** | `apps/api/composition/workflow.py` already means *the Opportunity Engine's write surface* |
| 🔁 **Recurring pattern** | **Three epics** | **Capability with no way in** — A5's observations · E1's firmographic read · E1's connect route. **All three found by implementation lanes after Lane C reported the gap as unbuilt** |
| 🔀 **Blocker changed shape** | **Epic G** | [TASK-013](BACKLOG.md) is no longer *"no released model"*. **A release is `EARNED` and cannot be recorded under a 60 s timeout** — [C-222](LANE_COORDINATION.md) |
| 🐛 **Hidden defect surfaced** | **E1 / E2** | Disconnect was irreversible. **[406](architecture/406-epic-e2-crm-write-back.md) §6 listed reconnection as an edge case to decide; it was already broken** |

> **The two recommendations that change future engineering effort are the retirement and the rename**, and they pull in opposite directions: **one removes a module nobody should build; the other reveals a differentiator that is already built and unlabelled.** Both cost a decision and no engineering.

### Section coverage — against the 2026-08-04 template

| Package | Product · Reuse · Architecture · Domain · Phases · Risks · Edge cases | Security | Perf | **Observability** | Testing | API · Data | UI/UX |
|---|---|---|---|---|---|---|---|
| **[C · People](architecture/400-epic-c-people.md)** | ✅ | ✅ | ✅ | ✅ **[405](architecture/405-cross-cutting-concerns.md)** | ✅ | ✅ | ⚠️ |
| **[E1 · CRM](architecture/401-epic-e1-crm-read.md)** | ✅ | ✅ | ✅ | ✅ **405** | ✅ | ✅ | ⚠️ |
| **[F · Workflow](architecture/402-epic-f-workflow.md)** | ✅ | ✅ | ✅ | ✅ **405** | ✅ | ✅ | ⚠️ |
| **[D · Risk](architecture/403-epic-d-risk.md)** | ✅ | n/a | ⚠️ | ✅ **405** | ✅ | ✅ | ⚠️ |
| **[G · Copilot](architecture/404-epic-g-copilot.md)** | ✅ | ✅ | ⚠️ *(cost)* | ✅ **405** | ✅ | ✅ | ⚠️ |
| **[E2 · write-back](architecture/406-epic-e2-crm-write-back.md)** | ✅ | ✅ | ✅ | ✅ **405** | ✅ | ✅ | ⚠️ |
| **[M11 · Recommendation](architecture/407-m11-recommendation.md)** | ✅ | n/a | ⚠️ | ✅ **405** | ✅ | ✅ | ⚠️ |

**Observability, testing, operations and deployment are backfilled** — as **[405-cross-cutting-concerns.md](architecture/405-cross-cutting-concerns.md)**, written **once** with a per-epic delta table, rather than five near-identical sections that would drift apart within a week (§2, *truth has exactly one authoritative representation*). **Each package links to it and states only its own deltas.**

> **The backfill found something the five packages had all missed.** Log redaction is **credential-shaped** — `password|secret|token|authorization|api_key|private_key|credential|cookie`, plus JWT and `Bearer` patterns in free text. **Nothing in it matches a name, an email or a phone number.** The guarantee *"no line ever carries a secret"* is intact and **does not extend to personal data**, because personal data has never been in the repository. **[Epic C](architecture/400-epic-c-people.md) changes that on its first commit**, in the module carrying the heaviest compliance obligation. **A phase-1 obligation, not a hardening task.**

**UI/UX stays ⚠️ deliberately.** Each package covers information architecture, states and the customer journey; **none specifies screens, loading, empty or error states.** That is where implementation genuinely owns the decomposition — **and for [D](architecture/403-epic-d-risk.md) and [G](architecture/404-epic-g-copilot.md) it is the larger share of what remains.**

> **The office names a technically suitable owner and stops there** *(product owner, 2026-08-04)*. **It does not sequence lanes, does not assign, and does not wait for one to be free.** The column above is guidance about *modules*, not a plan for *people*.

**Every prepared epic turned out smaller than its specification, and always for the same reason:** the expensive half was already built. **C** — six modules run people-shaped intelligence with no person in it. **E1** — the connection model is complete and nothing consumes it. **F** — the whole event substrate exists; only rule expression is missing. **D** — `Posture` and the Contribution Ledger already implement D2. **G** — the module, grammar, validator, harness and prompt all exist; one evaluation does not.

**What preparation now owes:** **re-validating prepared epics against repository changes**, so a package does not quietly go stale between preparation and allocation — the failure that produced [TASK-401](BACKLOG.md), where a task was built before its row was written.

#### Ownership boundaries — who owns what, end to end

| Initiative | Primary | Secondary | Conflict |
|---|---|---|---|
| **Responsive UX · Product Surface · Provider Platform · Team Management** | **Lane A** | none | 🟢 |
| **Timeline · CRM Integration · Observation · Commercial Profile · Knowledge Graph** | **Lane B** | none | 🟢 |
| **Business Workspace** | **Lane A** | **Lane B** *(reads `commercial_profile`)* | 🟠 |
| **Repository health · certification · promotion** | **QE** | none | 🟢 |
| **Architecture · coordination · decision preparation** | **Lane C** | none | 🟢 |

> **Nineteen of twenty-one module-initiative pairs have exactly one owner.** The one 🟠 is **Business Workspace**, and it crosses only to *read*. **That is why the measured conflict count is five and three of them are registers.**

**Measured conflict risk — dry-run merge of both lane branches, 2026-08-04:**

| | |
|---|---|
| **Files changed** | Lane A **140** · Lane B **114** · **14 paths overlap** |
| **Real conflicts** | **5** — `Makefile` · `backend/tests/integration/test_api_accounts.py` · and **three registers** |
| **Clean** | **Every shared frontend path auto-merges** — `lib/api/types.ts`, `lib/query/keys.ts`, `accounts/[accountId]/page.tsx`, `timeline/feed.tsx` |

> **The taxonomy holds, measured rather than asserted** ([`PRODUCT_OFFICE.md`](PRODUCT_OFFICE.md) §3). **Three of five conflicts are structural** — registers every lane must write. **One is [C-006](LANE_COORDINATION.md)**, the test file no lane owns. **And [B-400](BUGS.md), the only 🔴, produces no textual conflict at all**: two files named `0031_*.py` merge cleanly and break Alembic on the next migration run. **Semantic risk is invisible to git, and this is the cleanest example the repository has produced.**

**[TASK-401](BACKLOG.md) left this portfolio by being built before it was written** — Lane B shipped A5's backend in `145345f` on 2026-08-03. **Lane C had named the wrong module**: the row said `knowledge_graph`, the specification says **Observation Engine**, and Lane B built it there. **The second time in two days that the module owner's reading beat the office's inference, and the second time the module owner was right.**

**Predicted blockers, and what is being done now rather than when they land:**

| Horizon | Risk | Action |
|---|---|---|
| **Immediate** | **[B-400](BUGS.md) blocks promotion for both lanes.** Nothing certifies until it clears | **Recommended first, ahead of all feature work** |
| **Immediate** | **A6 is blocked by its own specification**, twice in its own words — [C-321](LANE_COORDINATION.md) | **Withdrawn from TASK-400**; the ruling is the product owner's |
| **Now** | **Twenty bug rows exist only on `lane-b-commercial-profile`** ([B-302](BUGS.md)–[B-321](BUGS.md)), and **[B-204](BUGS.md) only on Lane A's.** `integration` sees none of them | **Reported.** Three are 🟠 and open in Lane B's own modules |
| **Withdrawn** | ~~*Lane A runs out of approved scope in ~4 slices; CX-07 is its only candidate and has none*~~ | **Wrong, twice.** [C-026](LANE_COORDINATION.md) ruled CX-07's scope on **2026-08-03** — phone is in scope, and the slice is *"executable, unbuilt."* **Lane C escalated a decision that had already been made**, and reported a queue as thin while a 2–3 week initiative sat in it |
| **Standing** | **[TASK-003](BACKLOG.md) reads `READY` and is not claimable** — [C-018](LANE_COORDINATION.md) is open and Lane A skipped it with its reason recorded | **Flagged as stale.** A `READY` row nobody can take is the queue lying about its own depth |

> **Portfolio health is the measure, not task count.** **Every lane should have at least one *current* initiative it could own end to end**, and a named *upcoming* one behind it. **A lane with five small tasks and no initiative is not healthy** — it is five context switches and five chances to stop. [TASK-003](BACKLOG.md) is excluded from every depth reported: a `READY` row nobody can take is the queue lying about its own size.

> **One reference, not an assignment.** If this section ever needs a `Status`, a `Slice` and a `Next action`, Lane C has drifted into implementation and the drift should be corrected rather than accommodated by widening the table.

> **This file has changed hands twice in one day, and has ended up where it started.** Lane A created it as a **claim board** — a lane writes its own row before starting, so two lanes cannot take the same slice. It then became QE's, written at Closeout, with eight questions per row. It is now **claim-based again**, with QE reconciling rather than deciding: the eight questions were the improvement worth keeping, and **QE scheduling was the part that would not scale.** The claim it prevents has been the same one throughout.

## What is available to claim

**[`BACKLOG.md`](BACKLOG.md)** — `READY` first, in priority order. **It is not repeated here**: a queue in two places is a queue that will disagree with itself about what is next, and the copy nobody maintains is the one a lane will read (§2).

## Blocked, and on what

**Only lanes appear here — a *lane* that is stuck, not an *item* that is unstartable.** Blocked items live in [`BACKLOG.md`](BACKLOG.md) under `WAITING` and `BLOCKED`.

**Both lanes are producing design documents because neither can produce code.** That is not idling and it is not a process failure — it is what a lane correctly does when its next step needs a ruling nobody has made. It is recorded here because the board otherwise reads as two `ACTIVE` lanes, and a reader would not see that **eight commits across two branches contain no executable change.**

| Lane | Blocked on | Owner | Cycles waiting |
|---|---|---|---|
| **Lane A** — Product Surface | [C-025](LANE_COORDINATION.md) · [C-008](LANE_COORDINATION.md) | Product owner | **4** |
| **Lane A** — `provider_platform` | [C-021](LANE_COORDINATION.md) — dispatch direction | Product owner | 1 |
| **Lane A** — M14b | [C-200](LANE_COORDINATION.md) — the bounded context is 🔴 | Product owner | 1 |
| **Lane A** — Team Management | [C-206](LANE_COORDINATION.md) email delivery · [C-207](LANE_COORDINATION.md) leaving | Product owner | 1 |
| **Lane B** — `commercial_profile` | [ADR-0041](architecture/adr/0041-icp-aggregate.md) ratification | Product owner | 1 |

**Lane A's Team Management row is the exception worth reading**: the lane challenged its own recommendation and removed the blocker itself, discovering that the token already carries `email` and `email_verified`. **That slice is buildable now** — it needs no ruling.

## Recently completed

**Removed once the next assignment is made**, so this section stays short by construction. History belongs to [`PROJECT_STATUS.md`](../PROJECT_STATUS.md) and `git log`, not here.

| Lane | Assignment | Promoted | Commit |
|---|---|---|---|
| QE | **[`ENGINEERING_LAWS.md`](../ENGINEERING_LAWS.md)** — the Repository Engineering Standard · [B-101](BUGS.md) | 2026-08-03 | `d39b136` |
| A | **Team Management discovery · the customer-capability census** — documentation only | 2026-08-02 | `cb5cd33` |
| QE | **[B-100](BUGS.md)** — the board regression, and `state-check` rule 5g | 2026-08-02 | `1e269f5` |
| B | **B-301** — Timeline consumes what it projects · Timeline design doc | 2026-08-02 | `2262bb5` |
| A | **PS-01…PS-08 · PP-01…PP-06 · CX-01 · CX-02** — the product surface and provider platform batch | 2026-08-02 | `e5a266d` |
| B | **M13-S02** — the connections a customer can see, including the broken ones | 2026-08-02 | `3ef367d` |
| B | **M13-S01** — a customer's connection to their own systems | 2026-08-02 | `e08c7cb` |
| B | **M7 Timeline S01–S04a** — a seller can see what has happened to an account | 2026-08-02 | `048aeed` · `96bb5c0` · `7cb7fed` · `056a53a` |
| B | B-023 — a guard that narrows, and the gate that caught it | 2026-08-02 | `2e70b0e` |
| B | **TASK-005** — `state-check` learns the claims; the two registers must name the same holder | 2026-08-02 | `8da47b5` |
| B | ADR-0038 proposed — Timeline gets a design before it gets code | 2026-08-02 | `ffaeccb` · `e86b129` |
| QE | **ADR-0039** — the release engineering review, Parts I and II. *Accepted as direction, stays `Proposed`* | 2026-08-02 | `b1fd829` · `121cc76` · `c3435a0` |
| QE | The repository operating model, certification `f6691728aaf9`, and B-013 | 2026-08-02 | `f669172` · `6aadea9` |
| A | R2-01 — the guidance says what it is pointing at, and ADR-0037 | 2026-08-02 | `efaa987` |
| QE | Certification binds to an immutable commit, enforced by `certification-guard.py` | 2026-08-02 | `1bbee30` · `624f770` |
| QE | Pull-based work allocation — the backlog, and QE out of scheduling | 2026-08-02 | `3e36da9` |
| QE | The Task Claim Protocol, and permanent task ids | 2026-08-02 | `7b91948` |
| QE | Claim visibility, KPI tooling, and two dead checks made live | 2026-08-02 | `e1d2fa6` |
| B | TASK-001 — three QE fixes verified, two new defects found | 2026-08-02 | `a062adf` |
| B | M12.5 slice 5 — target accounts. **M12.5 complete** | 2026-08-02 | `3f4e988` |
| A | M12.4 — research on demand | 2026-08-02 | `c1f5985` |
| A | R4-02 · R4-03 — the words the product uses when it refuses you | 2026-08-02 | `bdb014f` |
| A | R2-02 · R3-01 — saying what the evidence cannot support | 2026-08-02 | `64d9f2e` |
| A | R4-04 — a decision you can undo | 2026-08-02 | `fba0647` |
| A | B-001 — `supersedes IS NULL` was never currency | 2026-08-02 | `c0bef97` |
| B | M12.5 slices 2–4 — ICP, buying committee, business priorities | 2026-08-02 | `30e66d0` · `960b604` · `3931b3c` |
| B | B-005 · B-006 — the two defects a customer would have hit | 2026-08-02 | `a440fad` |
