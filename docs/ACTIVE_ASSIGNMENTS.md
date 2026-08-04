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

- **A lane claims; nobody assigns.** Follow the **Task Claim Protocol** (`CLAUDE.md` §20e) — all ten steps, ending with a pushed standalone commit and a pull that confirms you were first. **No production code before step 10.**
- **Claim from the top of the queue.** If the highest `READY` task cannot be taken, **say why in its backlog note** and take the next. Skipping silently is re-prioritizing, and priority is the product owner's.
- **A row names a `TASK-nnn`.** If the work has no task id, it is not claimable work — it is a conversation with the product owner.
- **A lane edits only its own row.** Writing another lane's row, or clearing one, is the confusion this file exists to prevent.
- **One slice under construction per lane. One assignee per module.** Both directions, at all times. **A lane may also hold earlier rows at `IN VALIDATION`** — those are finished work waiting on QE, not a second thing being built.
- **When a lane finishes a slice: set its row `IN VALIDATION`, then immediately claim the next `READY` task.** A lane never idles waiting for QE (`CLAUDE.md` §20e, *Continuous execution*) — only four things stop it claiming again, and *"my last slice has not been certified"* is not among them.
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
| `AVAILABLE` | No current slice. **Free to claim from [`BACKLOG.md`](BACKLOG.md)** — not waiting for anyone |

> **`IN VALIDATION` means the work exists as commits QE can take.** Uncommitted work in a session's working tree is `ACTIVE`, whatever stage it feels like it has reached — **the board describes the repository, not an intention.** This distinction was added on 2026-08-02 after this file recorded QE's own governance slice as `IN VALIDATION` while it was still entirely uncommitted.

---

> **Lane C's creation moved no module.** Lane A owns exactly what it owned before; so do Lane B and QE. Lane C owns **no production module and no bounded context**, and descriptions of a lane's strategic direction are direction rather than reassignment. **Any future ownership transfer requires its own explicit decision** — a coordination item, ruled by the product owner, never arriving inside a governance edit (`CLAUDE.md` §2, *governance describes reality*).

## Current — as of 2026-08-03, `ba46132`

| Lane | Task | Branch | Module | Slice | Status | Blocked by | Next action | Started |
|---|---|---|---|---|---|---|---|---|
| **Lane A** | **[TASK-200](BACKLOG.md) — CX-07, the Responsive Product Surface** *(assigned directly by the product owner 2026-08-03)* | `lane-a-product-surface` | **Product Surface** — every screen and the shell | epic, assigned whole | **`CLAIMED`** | — | **Unblocked by [C-205](LANE_COORDINATION.md), ruled the same day: a phone is in scope.** That item's own analysis then binds — **a milestone rather than a slice**: the shell has no navigation below `768px` ([B-203](BUGS.md)), no screen has had a responsive pass, and the brief's eleven sections need an order that survives one column. **The frontend foundation is frozen (§20c) and this touches it deliberately**, under the clause that names an unreachable control a defect rather than an enhancement | 2026-08-03 |
| **Lane A** | **[TASK-400](BACKLOG.md) — Epic A completion** *(assigned by Lane C 2026-08-03, answering [C-217](LANE_COORDINATION.md))* | `lane-a-product-surface` | `provider_platform` (A7) · **Product Surface** (A6 render) — **both Lane A's** | **A6** *needs identity* render · **A7** *last looked* | **`CLAIMED`** | — | **Claimed on Lane C's assignment rather than on the row reaching `integration`**, per the product owner's direction of 2026-08-03: **Lane C is the source of truth for assignment, `integration` for claims and history.** **A6** renders `AccountIdentityResponse.agreement` so unnamed records leave the working list. **A7** adds `attempted_at` to `provider_watermark` so an account can say when a provider last *attempted* to read it — **and the hard part is the join, not the column**: `subject` is the customer's typed company name and the brief holds an entity id, which Lane A will resolve with Lane C rather than assume. **The word *checked* ships only once it is true** — A4 refuses it and `freshness.test.tsx` asserts the refusal; that test is the contract. **A5 is not in scope**: its backend is routed to Lane B, and the render returns here once the endpoint exists. **[B-400](BUGS.md) is 🔴 and blocks promotion for every lane, not implementation** — A7 adds a migration, so this lane expects to renumber on rebase | 2026-08-03 |
| **Lane A** | — | `lane-a-product-surface` | **Product Surface** — **assigned, and not released** | PS-01…08 · TS-02 · **CX-01…03** | **`ACTIVE`** — Implementation Waiting **ended 2026-08-02, the day it was declared** | **[C-203](LANE_COORDINATION.md) · [C-025](LANE_COORDINATION.md) · [C-026](LANE_COORDINATION.md) · [C-008](LANE_COORDINATION.md)** — for *those* slices only | **The module was declared waiting because nine review lenses stopped finding work, and that was the wrong test.** Every lens looked at screens that exist; none could see a capability with no screen at all. A capability audit — 31 endpoints against 5 screens — produced three slices the same afternoon, and every one was invisible to every test in the repository. **Driver is now [43-customer-experience.md](architecture/43-customer-experience.md)**; the correction is recorded in [37-product-surface.md](architecture/37-product-surface.md) | 2026-08-02 |
| **Lane A** | — | `lane-a-product-surface` | **`provider_platform`** — **assigned, and not released** | PP-01 · 02 · 04 · 05 · 06 built · PP-03 suspended | `BLOCKED` — module in **Implementation Waiting** | **[C-021](LANE_COORDINATION.md)** · owner **product owner** · entered waiting **2026-08-02** | **Every executable capability inside the accepted architecture is built.** What remains needs a dispatch direction; recorded in [41-provider-platform.md](architecture/41-provider-platform.md). **PP-03 stays suspended** — the module was not out of work, only its next *planned* slice was | 2026-08-02 |
| **Lane A** | **Team Management** *(customer capability, assigned by the product owner 2026-08-02)* | `lane-a-product-surface` | `workspace_tenancy` — **the capability, not the module** | Phases 1–3 complete · **TM-03 unblocked by evidence** | **`ACTIVE`** | **[C-207](LANE_COORDINATION.md)** for leaving only · **[C-206](LANE_COORDINATION.md)** narrowed to one email-delivery decision | **Self-challenge overturned this lane's own recommendation.** The plugin was unnecessary: every access token already carries `email` and `email_verified`, both **required claims** the Python verifier type-checks, and Better Auth already enforces verification — so accepting an invitation is matching a pending row against a claim that already arrives. **No plugin, no dependency, no frozen-file change.** The invitation table and acceptance are buildable now; the members list follows them. Analysis in [46-team-management.md](architecture/46-team-management.md) §11 | 2026-08-02 |
| **Lane A** | **M14b — Billing, Analytics & Feature Flags** *(implementation initiative, assigned by the product owner)* | `lane-a-product-surface` | **undecided — see [42-billing-and-entitlements.md](architecture/42-billing-and-entitlements.md)** | domain discovery | `BLOCKED` | **[C-200](LANE_COORDINATION.md)** — the bounded context is 🔴 | **Discovery complete, no code.** M14b has two roadmap table rows and no scope section, no module and no bounded context — the same shape as [C-020](LANE_COORDINATION.md) and [C-023](LANE_COORDINATION.md). **It is one module and two integrations, not one and not three**; every route into implementation decides the boundary by implementing it | 2026-08-02 |
| **Lane B** | **[TASK-300](BACKLOG.md) — Epic A, surface what already exists** *(assigned by the product owner 2026-08-03)* | `lane-b-commercial-profile` | `knowledge_graph` **(claimed — unassigned)** · `opportunity_engine` · `timeline` · `integrations` | A4 · A1 · A2 · A5 · A6 | **`ACTIVE`** | **[C-323](LANE_COORDINATION.md)** for A4, A1 and A5's render — **Lane A holds Product Surface and `provider_platform`, and is 128 files into `SW-01…04` in the same surface** | **Verified against Lane A's branch before starting: A2 is being built there now and B2 is done.** Proceeding on [B-200](BUGS.md) and the two `knowledge_graph` backends, which collide with nobody; **not entering Lane A's modules** pending the ruling | 2026-08-03 |
| **QE** | — | `lane-qe` | — (the repository) | permanent | `ACTIVE` | — | **Cycle 40 promoted (`ba46132`). 40 pinned, 33 certified.** **RS-2 shipped** — `make workstation`. RE-07 closed on measurement rather than built. **The Release Engineering backlog is nearly exhausted; what remains is not QE's, blocked, or without evidence.** Production stack off the review ports — a review and a certification now run together. Lane C introduced to governance. **Attempt 1 of this cycle aborted and was recorded rather than lost — RE-01's first real catch.** **Next: PR-1, blocked on [C-100](LANE_COORDINATION.md)** | 2026-08-01 |
| **Lane C** | **Product Office & Architecture Office** *(created 2026-08-03 by the product owner)* | `lane-c` | **none — owns no production module** | — | **`ACTIVE`** — operational 2026-08-03 | — | **Prepares; never decides.** Architectural options · implementation plans · ADR drafts · investigations · dependency analysis · migration strategies · decomposition · sequencing · consistency reviews · capability audits · roadmap refinement. **Needs no ports, database, Redis index or compose project.** **First assignment: [C-101](LANE_COORDINATION.md)** — the permanent workflow for keeping a 🔴 document synchronized when the lane that must change it may not write it. Assigned by the product owner 2026-08-03 | 2026-08-03 |

**Which lanes are available is the `Status` column above, and is not restated here** — a sentence beside a table is a second copy of one fact, and it drifted within an hour of being written (§2). **Unclaimed capacity:** the implementation environments `lane-c`, `lane-d` and `lane-e` ([`RUNNING.md`](RUNNING.md#running-a-lane)). **Lane C the *lane* is the Product Office and holds none of them** — it owns no module and needs no runtime.

**QE's row is permanent** and is never removed — it is the one row that outlives its own completion, because the responsibility is the repository rather than a slice inside it. **QE claims nothing and is claimed by nothing.**

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
