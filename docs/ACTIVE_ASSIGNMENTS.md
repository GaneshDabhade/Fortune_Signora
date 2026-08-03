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

**This board is now an input to Lane C, not only a record.** When a lane's row reaches `AVAILABLE`, `BLOCKED` or `WAITING`, **Lane C reads it and prepares the next recommendation for the product owner to approve** — the lane no longer selects for itself.

| | |
|---|---|
| **Current** | **Assignment preparation and B-400 coordination** |
| **Delivered** | [C-400](LANE_COORDINATION.md) doc-number collisions · [C-401](LANE_COORDINATION.md) merge-risk measurement · [C-403](LANE_COORDINATION.md) QE's action list · [C-404](LANE_COORDINATION.md) backlog reality · [B-400](BUGS.md) 🔴 migration collision · [B-401](BUGS.md) the blocking check |
| **Next** | Assign on `AVAILABLE`, after [B-400](BUGS.md) clears |

### Prepared queues — planning artifacts; only the first item is assigned

**Maintained continuously by Lane C, not when a lane finishes.** **Verified against branches, never against the queue.**

| | **Lane A** | **Lane B** |
|---|---|---|
| **Current** | **[TASK-400](BACKLOG.md)** — Epic A completion (A6 + A7) · *assigned* | **[B-400](BUGS.md)** — renumber to `0035` · *assigned* |
| **Next** | [TASK-903](BACKLOG.md) stage 2 | **[TASK-401](BACKLOG.md)** — A5 backend · **S** |
| **Then** | [TASK-905](BACKLOG.md) — posture on the attention row | [TASK-902](BACKLOG.md) — M7 Timeline S05+ |
| **Then** | **A5 render** — needs [TASK-401](BACKLOG.md) | [TASK-402](BACKLOG.md) — Epic E1, the CRM read |
| **Future** | **CX-07 responsive** — no task id, **needs scope** ([Pack I](DECISION_PACKS.md)) | Epic D, **after E1** |
| **Depth** | **4 executable + 1 pending scope** | **4 executable** |

**Two sequencing decisions, both made to prevent a stall rather than to react to one:**

- **[TASK-401](BACKLOG.md) moved ahead of [TASK-402](BACKLOG.md) in Lane B's queue.** A5's *render* is Lane A's fourth item and needs A5's *backend*, which sat behind **Epic E1 — an L**. **Lane A would have reached A5 while Lane B was mid-epic and stalled.** TASK-401 is **S**; moving it costs Lane B days and saves Lane A a stop. **Sequencing within a prepared queue is the office's; [`BACKLOG.md`](BACKLOG.md)'s priority order is untouched.**
- **[TASK-905](BACKLOG.md) inserted as Lane A's third**, which is where Lane A itself ranked it in [C-217](LANE_COORDINATION.md). It is Product Surface's, self-contained, and needs nothing from anyone.

**Predicted blockers, and what is being done now rather than when they land:**

| Horizon | Risk | Action taken |
|---|---|---|
| **Immediate** | **[B-400](BUGS.md) blocks promotion for both lanes.** Nothing certifies until it clears | Assigned first, ahead of all feature work |
| **~2 slices** | Lane A reaches **A5's render** before Lane B ships the backend | **Resequenced above** |
| **~4 slices** | **Lane A runs out of approved scope.** CX-07 is its only remaining candidate and has none | **Escalated** ([Pack I](DECISION_PACKS.md)) — the one item genuinely needing the product owner |
| **Standing** | **[TASK-003](BACKLOG.md) reads `READY` and is not claimable** — [C-018](LANE_COORDINATION.md) is still `OPEN` and Lane A skipped it with its reason recorded | **Flagged as stale.** A `READY` row nobody can take is the queue lying about its own depth |

> **Queue health is the measure, not assignment count.** **Fewer than three prepared executable tasks for any lane starts preparation immediately** — and the number that matters is *executable*, which is why [TASK-003](BACKLOG.md) is excluded from both depths above.

### Lane C — referenced, not rowed

**Lane C — Product Office, Architecture Governance & Cross-Lane Coordination** holds `lane-c-product-office` and is **deliberately absent from the table above** (product owner, 2026-08-03). **This board measures implementation; Lane C produces none.** It holds no `TASK-nnn` and claims nothing from [`BACKLOG.md`](BACKLOG.md). Its remit and boundaries are [`CLAUDE.md` §20e *Lane C*](../CLAUDE.md).

> **Lane C owns the coordination of implementation, not the implementation itself.**

**This board is now an input to Lane C, not only a record.** When a lane's row reaches `AVAILABLE`, `BLOCKED` or `WAITING`, **Lane C reads it and prepares the next recommendation for the product owner to approve** — the lane no longer selects for itself.

| | |
|---|---|
| **Current** | **Assignment preparation and B-400 coordination** |
| **Delivered** | [C-400](LANE_COORDINATION.md) doc-number collisions · [C-401](LANE_COORDINATION.md) merge-risk measurement · [C-403](LANE_COORDINATION.md) QE's action list · [C-404](LANE_COORDINATION.md) backlog reality · [B-400](BUGS.md) 🔴 migration collision · [B-401](BUGS.md) the blocking check |
| **Next** | Assign on `AVAILABLE`, after [B-400](BUGS.md) clears |

### Next assignments — prepared, and what each is waiting on

**Verified against branches, not against the queue** ([`PRODUCT_OFFICE.md`](PRODUCT_OFFICE.md) §10). **Neither lane is `AVAILABLE` today; both are carrying large unmerged branches.**

| | **Lane B** | **Lane A** |
|---|---|---|
| **ASSIGNED NOW** | **[B-400](BUGS.md) — renumber `0031_commercial_profile_segment.py` to `0035`** | **[TASK-400](BACKLOG.md) — Epic A completion (**A6** + **A7**), assigned whole |
| **Why** | 🔴 **Blocking Quality Defect.** Alembic cannot build the revision map with two `0031`s, so **neither lane can be certified** until it clears. One file, one line | **`provider_platform` is Lane A's**, the slice is **S**, it is **verified unbuilt** on every branch, and it sits inside **Epic A, which the product owner already approved** — so it needs no new ruling |
| **Prepared next** | **[TASK-902](BACKLOG.md) — M7 Timeline S05+**, an epic rather than a slice: `timeline` is Lane B's, [ADR-0038](architecture/adr/0038-timeline.md) is ratified, the surface is mounted, nothing open blocks it | **[TASK-903](BACKLOG.md) stage 2.** Lane A shipped **CX-05**, so the first half is done; the remainder is the brief-side surface, scoped by Lane A in [C-217](LANE_COORDINATION.md) |
| **Then** | **[TASK-402](BACKLOG.md) — Epic E1, the CRM read.** Assigned fresh by Lane C; **most of the connection half is already built**, and it unblocks Epic D, E2 and the expansion/renewal half of the vision · then **[TASK-401](BACKLOG.md) — A5 backend.** `knowledge_graph` was unassigned and A5 was stalled behind it; **routed to Lane B**, which already built A1 and A4 there. **A5's render returns to Lane A** | **A5 render**, once TASK-401 lands |
| **Escalated, not assigned** | [TASK-900](BACKLOG.md) platform RFC — **a different discipline**, and Lane B declined it on 2026-08-02 | **CX-07 responsive** — Lane A's own first choice, and **it has no task id and no agreed scope.** [Pack I](DECISION_PACKS.md) carries it; **new scope is the product owner's, not the office's** |

> **[C-217](LANE_COORDINATION.md) is answered by this row.** Lane A asked the office for its next epic and is assigned **[TASK-400](BACKLOG.md)**, with **[TASK-903](BACKLOG.md) stage 2 prepared behind it** so the lane does not wait twice. **Lane A records the assignment on its own row, sets it `ACTIVE`, and closes C-217 in the slice that begins the work.**

> **The honest finding: with three rows corrected, the `READY` queue has little Lane A can take.** [TASK-900](BACKLOG.md) is the only substantial unclaimed item and it is a platform RFC. **That is a queue-depth observation for the product owner, not a request** — and it is what *"lanes rarely wait for work"* looks like when it stops being true.

> **One reference, not an assignment.** If this ever needs a `Status`, a `Slice` and a `Next action`, Lane C has drifted into implementation and the drift should be corrected rather than accommodated by widening the table.

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
