# Active assignments — the execution board

> **The repository's current execution state, and the only authoritative record of it.** Established 2026-08-01; became **the execution board** on 2026-08-02, on the product owner's direction.
>
> **Written by QE at Repository Closeout, after every promotion** (`CLAUDE.md` §20e). A lane reads it; it does not write it. If this file and any other document disagree about who is implementing what, **this file is right and the other is a defect.**

## The eight questions it answers

**Every row answers all eight. A row that cannot is incomplete, not brief.**

| | |
|---|---|
| **Which lane is currently working?** | The `Lane` column |
| **Which module is currently assigned?** | The `Module` column — **the permanent boundary**, never a lane's property |
| **Which milestone?** | The `Milestone` column |
| **Which slice?** | The `Slice` column — *slice 2 of 5*, not *the module* |
| **Current status?** | The `Status` column, from the table below |
| **Blockers?** | The `Blocked by` column — **named, never implied**. `—` means genuinely none |
| **Dependencies?** | The `Depends on` column — the `C-` items and lane outputs this slice waits on |
| **Expected next action?** | The `Next action` column — **what happens next and who does it**, so a cold session knows where to pick up |

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

- **QE assigns.** A lane does not claim work, and does not carry work forward into a new slice without an assignment.
- **One active assignment per lane. One assignee per module.** Both directions, at all times.
- **When a lane finishes a slice: mark it `COMPLETE`, return the lane to `AVAILABLE`, and remove the completed row.** A row describing work already on `main` is the defect this file exists to prevent — **no lane may remain assigned to work that has shipped, and no stale assignment is left behind.**
- **A row is a slice, not a milestone.** *Commercial Profile — slice 2* is an assignment; *Commercial Profile* is not.
- **`Started` is when the assignment was made**, not when the branch was created.
- **A lane whose module is blocked stays assigned** and the blocker is named — that is a fact about execution state, and hiding it makes the lane look idle when it is stuck.
- **Every row states its expected next action.** A board that says what is happening but not what happens next leaves a cold session to infer it, and an inferred next action is how two lanes do the same thing.

| Status | Meaning |
|---|---|
| `ASSIGNED` | Allocated, not yet started |
| `ACTIVE` | Being implemented |
| `BLOCKED` | Waiting on a `C-` item or a dependency. **Name it** |
| `IN VALIDATION` | Handed to QE — **committed and pushed**, in the lifecycle, not yet promoted |
| `COMPLETE` | Promoted to `main`. **Marked, then removed, and the lane returned to `AVAILABLE`** |
| `AVAILABLE` | No assignment. **Free to be allocated** |

> **`IN VALIDATION` means the work exists as commits QE can take.** Uncommitted work in a session's working tree is `ACTIVE`, whatever stage it feels like it has reached — **the board describes the repository, not an intention.** This distinction was added on 2026-08-02 after this file recorded QE's own governance slice as `IN VALIDATION` while it was still entirely uncommitted.

---

## Current — as of 2026-08-02, `6aadea9`

| Lane | Assignment | Module | Milestone | Slice | Status | Blocked by | Depends on | Next action | Started |
|---|---|---|---|---|---|---|---|---|---|
| **Lane A** | — | — | — | — | `AVAILABLE` | — | — | **QE to assign.** R2-01 landed on `integration` at `f450a36`, **not yet validated or promoted** | — |
| **Lane B** | — | — | — | — | `AVAILABLE` | — | — | **QE to assign.** M12.5 completed and promoted at `3f4e988` | — |
| **QE** | Repository lifecycle and governance | — (the repository) | — | permanent | `ACTIVE` | — | — | Next cycle: validate whatever a lane hands over | 2026-08-01 |

**Available lanes:** **Lane A and Lane B — both.** **Unassigned capacity:** lanes C, D and E are unclaimed ([`RUNNING.md`](RUNNING.md#running-a-lane) holds their reserved environments).

**QE's assignment is permanent** and is never removed — it is the one row that outlives its own completion, because the responsibility is the repository rather than a slice inside it.

> **This file changed hands on 2026-08-02.** Lane A created it the same day as a **claim board** — a lane wrote its own row before starting, so two lanes could not take the same slice. The product owner has since made it **QE's, written at Repository Closeout**, and given it eight questions to answer per row. **The change is who writes it, not what it is for**, and the claim it prevents is the same one.

## Unassigned work, highest value first

**Available to allocate — but a lane does not claim; QE assigns** (`CLAUDE.md` §20e).

| Item | Where | Note |
|---|---|---|
| **[C-008](LANE_COORDINATION.md)** — sellers cannot see what their company sells | Product Surface | **Proposal accepted 2026-08-02**; awaiting the choice of option A/B/C/D from the product owner. *"A repository-level capability, not a module enhancement"* |
| **[C-007](LANE_COORDINATION.md)** — the guided first run | Product Surface | The sequencing condition has fired: all five declarations exist. **Blocked on a capability, not a decision** — the `target_accounts_changed` consumer |
| **R2-03** — an account with nothing live says nothing at all | Product Surface | 🟡, and overlaps R1-04 |
| **R11-06** — the attributes are engineering's words | Knowledge Graph | 🟡 |
| **R9-04 / D5** — what changed since you last looked | Product Surface | Needs per-user read state. **Trigger unfired** — a design partner saying they cannot tell what is new |
| **The brief's hierarchy pass** | Product Surface | **Not allocatable to a lane.** A collaborative product-design activity that needs a seller present |
| **Verification of [B-009](BUGS.md)** | Repository documentation | **Not QE's** — QE wrote the fix, so somebody else reproduces it from a clean shell |

## Blocked, and on what

| Item | Lane | Blocked on |
|---|---|---|
| [B-004](BUGS.md) — `provider_watermark` cannot tell two target accounts apart | A | Lane B's M12.5 slice 5. **Not to be fixed opportunistically** — the consumer is what makes it reachable |
| [C-005](LANE_COORDINATION.md) implementation — the signal-profile write path | A | The product owner's ruling on *whether* a customer should author relevance at all. Ownership is answered; sequencing is not |
| [C-007](LANE_COORDINATION.md) implementation — the guided first run | A | M12.5 slice 5 |
| [C-009](LANE_COORDINATION.md) — an internal fault reaches a customer as a `422` | A | The product owner. A `signora_platform/` change under §20a, with a full proposal recorded |
| [B-007](BUGS.md) · [B-012](BUGS.md) | **nobody** | [C-010](LANE_COORDINATION.md) — no lane is assignable to `apps/` or repository process |

## Recently completed

**Removed once the next assignment is made**, so this section stays short by construction. History belongs to [`PROJECT_STATUS.md`](../PROJECT_STATUS.md) and `git log`, not here.

| Lane | Assignment | Promoted | Commit |
|---|---|---|---|
| QE | The repository operating model, certification `f6691728aaf9`, and B-013 | 2026-08-02 | `f669172` · `6aadea9` |
| A | R2-01 — the guidance is generic; what it points at is not. **On `integration`, awaiting validation** | *not yet promoted* | `f450a36` |
| B | M12.5 slice 5 — target accounts. **M12.5 complete** | 2026-08-02 | `3f4e988` |
| A | M12.4 — research on demand | 2026-08-02 | `c1f5985` |
| A | R4-02 · R4-03 — the words the product uses when it refuses you | 2026-08-02 | `bdb014f` |
| A | R2-02 · R3-01 — saying what the evidence cannot support | 2026-08-02 | `64d9f2e` |
| A | R4-04 — a decision you can undo | 2026-08-02 | `fba0647` |
| A | B-001 — `supersedes IS NULL` was never currency | 2026-08-02 | `c0bef97` |
| B | M12.5 slices 2–4 — ICP, buying committee, business priorities | 2026-08-02 | `30e66d0` · `960b604` · `3931b3c` |
| B | B-005 · B-006 — the two defects a customer would have hit | 2026-08-02 | `a440fad` |
