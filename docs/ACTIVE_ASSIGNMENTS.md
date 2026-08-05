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
| `PAUSED` | **Set by the product owner, and by nobody else.** The lane holds no module and claims nothing. **Deliberately not `AVAILABLE`**, which reads *free to claim*, and deliberately not `BLOCKED`, which reads *something is in the way* — **neither is true of a lane that has been stood down.** Only the product owner resumes it |

> **`PAUSED` is an eighth state and it was added rather than approximated** (2026-08-04). §20e says *"do not invent statuses — a lane that needs an eighth has a state the model does not describe, and that is a finding to raise."* **This is that finding, raised**: the product owner created the state by standing Lane A down, and the seven existing values could only have described it by lying. **Recording a new state honestly is cheaper than filing a true condition under a false label**, which is how a board starts being read as advisory.

> **`IN VALIDATION` means the work exists as commits QE can take.** Uncommitted work in a session's working tree is `ACTIVE`, whatever stage it feels like it has reached — **the board describes the repository, not an intention.** This distinction was added on 2026-08-02 after this file recorded QE's own governance slice as `IN VALIDATION` while it was still entirely uncommitted.

---

> **Recorded 2026-08-03, and true of that day.** **Lane C's creation moved no module.** Lane A owned exactly what it owned before; so did Lane B and QE. Lane C owns **no production module and no bounded context**, and descriptions of a lane's strategic direction are direction rather than reassignment. **Any future ownership transfer requires its own explicit decision** — a coordination item, ruled by the product owner, never arriving inside a governance edit (`CLAUDE.md` §2, *governance describes reality*).
>
> **Two such decisions have since been taken, both on 2026-08-04, both by the product owner, neither inside a governance edit** — the morning's C-415 ruling and the afternoon's consolidation onto Lane B. **The paragraph above is left standing as the dated record it is**, because the rule it states is precisely the rule those two transfers followed (§2 — *correct a claim about the present; date a record of the past*).

## Current — as of 2026-08-05, `1e55191`

## Module assignment — the product owner's ruling, 2026-08-04 (second ruling, same day)

> **One implementation module → one implementation lane → one current assignee → one source of truth.** **Dual ownership of an implementation module is not permitted** (`CLAUDE.md` §20e, *module assignment is authoritative*).
>
> **Responsibility follows the module.** A coordination item, a backlog row or a defect against a module belongs to **its current assignee**, whoever opened it.

**Ruled 2026-08-04 by the product owner, superseding the morning's split ruling:** *"we'll continue with Lane B only for some time and will start Lane A later once this conflict issue gets resolved."* **Lane A is paused; every implementation module consolidates on Lane B.**

| Module | Current assignee | Note |
|---|---|---|
| `commercial_profile` | **Lane B** | held by Lane A for seven hours on [C-415](LANE_COORDINATION.md) |
| `knowledge_graph` | **Lane B** | held by Lane A for seven hours, resolving [C-413](LANE_COORDINATION.md) |
| `signal_engine` | **Lane B** | from Lane A |
| `opportunity_engine` | **Lane B** | from Lane A |
| `ai_reasoning_engine` | **Lane B** | from Lane A |
| `sales_engagement` | **Lane B** | carries TASK-205, now unblocked |
| `ai_platform` | **Lane B** | from Lane A |
| `provider_platform` | **Lane B** | carries [C-021](LANE_COORDINATION.md), the product owner's |
| `integrations` | **Lane B** | unchanged — Lane B's throughout |
| `provider_normalization` | **Lane B** | unchanged — Lane B's throughout |
| `timeline` | **Lane B** | **was unassigned** — carries [C-215](LANE_COORDINATION.md) |
| `workspace_tenancy` | **Lane B** | **was unassigned** |
| `observation_engine` | **Lane B** | **was unassigned** |
| `business_event_engine` | **Lane B** | **was unassigned** |
| `buying_score_engine` | **Lane B** | **was unassigned** |
| `ai_research_engine` | **Lane B** | **was unassigned** |
| **Product Surface** | **Lane B** | carries [C-025](LANE_COORDINATION.md) · [C-008](LANE_COORDINATION.md) |
| `infra/` · `Makefile` · repository process · `signora_platform/simulation` | **Lane C** | unchanged — Platform Foundation, [D-022](DECISION_REGISTER.md) |
| — | **Lane A holds no module** | **`PAUSED`**, not idle and not available |

> **Nothing is unassigned any more, and that is the change worth noticing.** The previous table left six modules **Unassigned — claimable by either implementation lane**, which was a correct answer while there were two lanes. **With one implementation lane there is no allocation left to get wrong**, and the entire class of defect this consolidation is a response to — a row naming a lane that has moved on — has no way to occur.

**In-flight work inside a reassigned module** either **transfers**, **completes before transfer if already in progress**, or is **explicitly re-planned.** **The transfer was clean**: `lane-a-product-surface` was at `2591951`, **identical to `origin/integration`**, so Lane A held **zero unpromoted commits** and nothing was in flight to lose.

| Lane | Task | Branch | Module | Slice | Status | Blocked by | Next action | Started |
|---|---|---|---|---|---|---|---|---|
| **Lane A** | — | `lane-a-product-surface` | **none — every module transferred to Lane B** | — | **`PAUSED`** *(product owner, 2026-08-04)* | — | **Paused by the product owner, not blocked and not available.** *"We'll continue with Lane B only for some time and will start Lane A later once this conflict issue gets resolved."* **The transfer cost nothing**: this branch was at `2591951`, identical to `origin/integration`, so **no unpromoted commit and no half-built slice existed to hand over.** **Twelve rows stood here and eleven were claims, not code.** **Four returned to [`BACKLOG.md`](BACKLOG.md) as `READY`** for Lane B to claim in priority order — TASK-202, TASK-203, TASK-405, TASK-406 — **because a claim released is a queue entry, not a board row.** **TASK-201 returns `BLOCKED`** on [C-221](LANE_COORDINATION.md), which is the product owner's and which the transfer did not touch. **TASK-205 returns `READY` and unblocked** — it waited on [C-213](LANE_COORDINATION.md), and the module holding the export and the module consuming it are now one lane's. Three were already `IN VALIDATION` and are QE's to reconcile at Closeout: TASK-200, TASK-204 and Lead lifecycle. **TASK-400 carries `CHANGES REQUESTED` and transfers as inherited work** — the row below. **The two milestone rows carried no task and transferred with their modules**, both still held by the product owner's own undecided items, [C-021](LANE_COORDINATION.md) and [C-200](LANE_COORDINATION.md). ⚠️ **This row corrects a disagreement it found**: the board recorded TASK-200 as `CLAIMED` while [`BACKLOG.md`](BACKLOG.md) recorded it `IN VALIDATION — all four slices shipped`. **The backlog was right**, and two files stating one task's state is exactly the defect [428](architecture/428-lane-coordination-model.md) proposes to make unrepresentable. **Resumption is the product owner's alone** — no gate, no cycle count, and no lane may restart it | **Paused 2026-08-04** |
| **Lane B** | **[TASK-400](BACKLOG.md) — Epic A completion** *(inherited from Lane A 2026-08-04 on the consolidation, [D-058](DECISION_REGISTER.md))* | `lane-b-commercial-profile` | `provider_platform` (A7) · **Product Surface** (A6 render) — **both Lane B's now** | **A6** *needs identity* render · **A7** *last looked* | **`CHANGES REQUESTED`** — QE, 2026-08-04 | — | **The one Lane A row carrying work rather than a claim, and §20e sends returned work to the implementing lane** — which is now this one. **[B-107](BUGS.md) is the substance**: ten tests in the A7 slice have never passed and stall the suite at 68%, while the rest of the candidate is green — 2922 pass with that one file deselected. **B-109 was fixed by Lane A and its validation deferred** on a rebase conflict in `backend/tests/integration/test_api_accounts.py` against Lane B's own promoted work — **and that conflict is now internal to one lane**, which is the first dividend of the consolidation. **Take this before claiming from the queue** (§20e — a returned slice is addressed first). ✅ **Taken first, 2026-08-05, and both named corrections are already closed.** [B-107](BUGS.md) is `VERIFIED` and [B-109](BUGS.md) is `VERIFIED` and promoted at `a955016` — **verified by running them rather than by reading the register**: `tests/provider_platform/test_last_looked.py` plus the convention test Lane A added give **12 passed** at `61d4361`. **Nothing of the return remains.** What is left of the task is **A7's render, blocked on [C-219](LANE_COORDINATION.md), and A6, blocked on [C-321](LANE_COORDINATION.md)** — neither moved with the transfer, and neither is this lane's to answer. **The status is left as QE set it**: only QE clears its own return | **Inherited 2026-08-04** |
| **Lane B** | **[TASK-402](BACKLOG.md) — Epic E1, a customer's CRM becomes a source Signora can read** *(assigned directly by the product owner 2026-08-04)* | `lane-b-commercial-profile` | **`integrations`** — Lane B's, which built S01, S02 and S09 · **`provider_normalization`** for the canonical shape | epic, assigned whole and owned end to end | **`VERIFIED`** — QE, 2026-08-04 | **[C-300](LANE_COORDINATION.md)** · owner **product owner** — steps 3–5 are `provider_platform`'s, and step 4 is 🔴 | **Validated with no corrections.** 3374 backend, 95.23%, 383 Security Invariants, `mypy` clean over 722 files, 35 import contracts kept. **Built to a ratified decision, not an assumption** — [C-326](LANE_COORDINATION.md) was ruled by the product owner (ADR-0300, Option A) before this slice, steps 1/2/6 of 409 are built, and **steps 3–5 were left alone because they are `provider_platform`'s**. ⚠️ **Not a completed product slice, and the lane said so first**: *"Nothing a customer can see yet, and that is stated rather than dressed up."* Under §2 this is correct work that has not reached a customer, and it is **recorded as infrastructure rather than reported as a delivered capability.** **Everything the epic could execute is pushed and promoted**: interpretation (`HubSpotCompanyMapper`, canonical claims with **no vocabulary extension**), acquisition (the code exchange, `POST /connections`, and the disconnect that was irreversible until this epic found it), the grant lifecycle (revocation, refresh-on-use, `EXPIRED → CONNECTED` revival) and the vendor read (`HubSpotCompanies`, typed failures). **What remains is one signature, not engineering** — nothing can put a record in front of the mapper until the inbound source port exists. **The inventory was closed once, deliberately, and is not re-swept** | 2026-08-04 |
| **Lane B** | **[TASK-203](BACKLOG.md) — Epic D, Risk Intelligence** *(claimed 2026-08-05 by the Task Claim Protocol)* | `lane-b-commercial-profile` | `commercial_profile` (a fifth declaration) · `signal_engine` (a catalog row) · Product Surface | **phase 1 — competitor entry** | **`CLAIMED`** | — | **Claimed after [TASK-202](BACKLOG.md) proved blocked**, which is the loop §20e requires rather than a lane idling on a decision. **Its row states no dependency and the detection half already exists.** On claiming, validate before building, in the order the row sets: that `competitor` genuinely appears nowhere · that the four existing declarations share one shape a fifth can follow · that `TECHNOLOGY_ADOPTED` carries a resolvable technology identity rather than a free string · and that **no threshold enters code** — `signal_engine` keeps them in a reviewed catalog | 2026-08-05 |
| **Lane B** | **[TASK-202](BACKLOG.md) — Epic G, Copilot** *(claimed 2026-08-05 by the Task Claim Protocol)* | `lane-b-commercial-profile` | `ai_reasoning_engine` · `ai_platform` (evaluation) · Product Surface | epic, assigned whole | **`BLOCKED`** | **[C-222](LANE_COORDINATION.md)** · owner **product owner** (recording the measurement) · **QE** (whether the manifest may hold it) | **Blocked by measurement, not by reading.** `make eval-reasoning --model llama3.1:8b` at the committed policy returns `UNMEASURABLE — 2 of 2 cases never reached a verdict`; [404 §0](architecture/404-epic-g-copilot.md) records the same pairing passing at 172.8 s for two cases against a 60.0 s `InferencePolicy`. **Every later phase of the epic depends on this release, so it is blocked whole.** The one change that would make it pass is the one [TASK-013](BACKLOG.md) forbids in writing, and this lane did not make it. **Two corrections to 404 were found by claiming it and are recorded in the backlog row.** ⏭️ **[TASK-408](BACKLOG.md) stood higher when this was claimed and was skipped with its reason recorded.** [TASK-408](BACKLOG.md) stands higher and carries an acceptance criterion that contradicts a decision already shipped in [TASK-301](BACKLOG.md) — *"a zero-match group is returned rather than omitted"* against *"an absent type is absent, never an empty group"* — **which its own row says is a product ruling, not a lane's.** First slice: **author a `reasoning` dataset and evaluate `reasoning@1` under protocol 2.** ⚠️ **[C-222](LANE_COORDINATION.md) is open and does not block the epic** — it blocks only a live G1 inference — but it names the same workstation limit this slice will meet: `llama3.1:8b` was measured *unmeasurable* here. **The pinned model is part of the benchmark and is not a lane's to change** ([ADR-0028](architecture/adr/0028-model-runtime-by-environment.md)); if the measurement cannot complete, that is reported as an observation about the machine and never worked around | 2026-08-05 |
| **Lane C** | **[TASK-409](BACKLOG.md) — Platform Foundation: a `demo` profile in the allocation table** *(claimed 2026-08-04, the first slice under [D-022](DECISION_REGISTER.md))* | `lane-c-sync` | `infra/` | one slice | **`CLAIMED`** | — | Add the profile. **No launcher in this slice** | 2026-08-04 |
| **QE** | — | `lane-qe` | — (the repository) | permanent | `ACTIVE` | — | **Cycle 52 promoted (`1e55191`) — the lane consolidation. 52 pinned, 46 certified. Eight promotions.** **Module assignment is now authoritative** and the dashboard renders from it; an audit found two rows that disagreed. **Until this promoted, Lane B read a board showing Lane A holding every module and had nothing to claim** — the invisibility failure [428](architecture/428-lane-coordination-model.md) diagnoses, observed while the document describing it waited in the same queue. **[427](architecture/427-impact-based-validation.md) and 428 await the product owner's ruling; neither is implemented.** **QE added a seven-minute standing-state sweep** in its session runtime, not the repository — the watcher fires on movement, and a branch sitting still while ahead raised no event | 2026-08-01 |
| **Lane C** | **Product Office & Architecture Office** *(created 2026-08-03 by the product owner)* | `lane-c` | **none — owns no production module** | — | **`ACTIVE`** — operational 2026-08-03 | — | **Prepares; never decides.** Architectural options · implementation plans · ADR drafts · investigations · dependency analysis · migration strategies · decomposition · sequencing · consistency reviews · capability audits · roadmap refinement. **Needs no ports, database, Redis index or compose project.** **First assignment: [C-101](LANE_COORDINATION.md)** — the permanent workflow for keeping a 🔴 document synchronized when the lane that must change it may not write it. Assigned by the product owner 2026-08-03 | 2026-08-03 |

**Which lanes are available is the `Status` column above, and is not restated here** — a sentence beside a table is a second copy of one fact, and it drifted within an hour of being written (§2). **Unclaimed capacity:** the implementation environments `lane-c`, `lane-d` and `lane-e` ([`RUNNING.md`](RUNNING.md#running-a-lane)). **Lane C the *lane* is the Product Office and holds none of them** — it owns no module and needs no runtime.

**QE's row is permanent** and is never removed — it is the one row that outlives its own completion, because the responsibility is the repository rather than a slice inside it. **QE claims nothing and is claimed by nothing.**

> **This file has changed hands twice in one day, and has ended up where it started.** Lane A created it as a **claim board** — a lane writes its own row before starting, so two lanes cannot take the same slice. It then became QE's, written at Closeout, with eight questions per row. It is now **claim-based again**, with QE reconciling rather than deciding: the eight questions were the improvement worth keeping, and **QE scheduling was the part that would not scale.** The claim it prevents has been the same one throughout.

## What is available to claim

**[`BACKLOG.md`](BACKLOG.md)** — `READY` first, in priority order. **It is not repeated here**: a queue in two places is a queue that will disagree with itself about what is next, and the copy nobody maintains is the one a lane will read (§2).

## Blocked, and on what

**Only lanes appear here — a *lane* that is stuck, not an *item* that is unstartable.** Blocked items live in [`BACKLOG.md`](BACKLOG.md) under `WAITING` and `BLOCKED`.

**Rewritten 2026-08-04 on the consolidation.** The rows below were Lane A's; **a paused lane cannot be blocked**, so each one moved to the lane that now holds the module. **Nothing was closed by the transfer** — a decision nobody has made is still unmade, whoever is waiting for it.

| Lane | Blocked on | Owner | Cycles waiting |
|---|---|---|---|
| **Lane B** — Product Surface | [C-025](LANE_COORDINATION.md) · [C-008](LANE_COORDINATION.md) | Product owner | **4** |
| **Lane B** — `provider_platform` | [C-021](LANE_COORDINATION.md) — dispatch direction | Product owner | 1 |
| **Lane B** — M14b | [C-200](LANE_COORDINATION.md) — the bounded context is 🔴 | Product owner | 1 |
| **Lane B** — `commercial_profile` | [ADR-0041](architecture/adr/0041-icp-aggregate.md) ratification | Product owner | 1 |

**Team Management left this table rather than moving**: the lane that raised it challenged its own recommendation and removed the blocker itself, discovering the token already carries `email` and `email_verified`. **[C-206](LANE_COORDINATION.md) and [C-207](LANE_COORDINATION.md) do not gate it** — that slice is buildable now, by Lane B, and needs no ruling.

> ⚠️ **Consolidation did not create capacity; it concentrated it.** **Four of these five rows were the product owner's before the transfer and all four still are** — the queue Lane B can now reach is longer, and **the decisions in front of it are the same decisions.** Reporting the merge as an unblocking would be the [§11c](PRODUCT_OFFICE.md) error again.

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
