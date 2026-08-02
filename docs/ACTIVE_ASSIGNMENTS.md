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
- **One active assignment per lane. One assignee per module.** Both directions, at all times.
- **When a lane finishes a slice: mark it `COMPLETE`, return the lane to `AVAILABLE`, and remove the completed row.** A row describing work already on `main` is the defect this file exists to prevent — **no lane may remain assigned to work that has shipped, and no stale assignment is left behind.**
- **A row is a slice, not a milestone.** *Commercial Profile — slice 2* is an assignment; *Commercial Profile* is not.
- **`Started` is when the assignment was made**, not when the branch was created.
- **A lane whose module is blocked stays assigned** and the blocker is named — that is a fact about execution state, and hiding it makes the lane look idle when it is stuck.
- **Every row states its expected next action.** A board that says what is happening but not what happens next leaves a cold session to infer it, and an inferred next action is how two lanes do the same thing.

| Status | Meaning |
|---|---|
| `CLAIMED` | The claim commit is **pushed and confirmed first**. Implementation may begin |
| `ACTIVE` | Being implemented |
| `BLOCKED` | Waiting on a `C-` item or a dependency. **Name it** |
| `IN VALIDATION` | Handed to QE — **committed and pushed**, in the lifecycle, not yet promoted |
| `COMPLETE` | Promoted to `main`. **Marked by QE at Closeout, then removed, and the lane returns to `AVAILABLE`** |
| `AVAILABLE` | No current slice. **Free to claim from [`BACKLOG.md`](BACKLOG.md)** — not waiting for anyone |

> **`IN VALIDATION` means the work exists as commits QE can take.** Uncommitted work in a session's working tree is `ACTIVE`, whatever stage it feels like it has reached — **the board describes the repository, not an intention.** This distinction was added on 2026-08-02 after this file recorded QE's own governance slice as `IN VALIDATION` while it was still entirely uncommitted.

---

## Current — as of 2026-08-02, `7b91948`

| Lane | Task | Branch | Module | Slice | Status | Blocked by | Next action | Started |
|---|---|---|---|---|---|---|---|---|
| **Lane A** | — | `lane-a-product-surface` | — | — | `AVAILABLE` | — | **Run the Task Claim Protocol.** Nobody will assign it; the queue is open | — |
| **Lane B** | **[TASK-001](BACKLOG.md#task-001--verify-the-three-fixes-qe-may-not-close)** | `lane-b-commercial-profile` | Repository — documentation, `infra/`, production image | one slice | `CLAIMED` | — | Reproduce [B-009](BUGS.md), [B-013](BUGS.md) and [B-014](BUGS.md) from a clean shell, **from the original steps, never from the diff** | 2026-08-02 |
| **QE** | — | `lane-qe` | — (the repository) | permanent | `ACTIVE` | — | Idle until a lane pushes work to `integration`. **QE's turn begins there** | 2026-08-01 |

**Available lanes:** **Lane A and Lane B — both, and neither is waiting on anybody.** An `AVAILABLE` lane claims its next slice from [`BACKLOG.md`](BACKLOG.md) and starts. **Unclaimed capacity:** lanes C, D and E ([`RUNNING.md`](RUNNING.md#running-a-lane) holds their reserved environments).

**QE's row is permanent** and is never removed — it is the one row that outlives its own completion, because the responsibility is the repository rather than a slice inside it. **QE claims nothing and is claimed by nothing.**

> **This file has changed hands twice in one day, and has ended up where it started.** Lane A created it as a **claim board** — a lane writes its own row before starting, so two lanes cannot take the same slice. It then became QE's, written at Closeout, with eight questions per row. It is now **claim-based again**, with QE reconciling rather than deciding: the eight questions were the improvement worth keeping, and **QE scheduling was the part that would not scale.** The claim it prevents has been the same one throughout.

## What is available to claim

**[`BACKLOG.md`](BACKLOG.md)** — `READY` first, in priority order. **It is not repeated here**: a queue in two places is a queue that will disagree with itself about what is next, and the copy nobody maintains is the one a lane will read (§2).

## Blocked, and on what

**Only lanes appear here — a *lane* that is stuck, not an *item* that is unstartable.** Blocked items live in [`BACKLOG.md`](BACKLOG.md) under `WAITING` and `BLOCKED`.

*No lane is currently blocked.* Both are `AVAILABLE`, which is a different thing: nothing prevents either from claiming its next slice right now.

## Recently completed

**Removed once the next assignment is made**, so this section stays short by construction. History belongs to [`PROJECT_STATUS.md`](../PROJECT_STATUS.md) and `git log`, not here.

| Lane | Assignment | Promoted | Commit |
|---|---|---|---|
| QE | The repository operating model, certification `f6691728aaf9`, and B-013 | 2026-08-02 | `f669172` · `6aadea9` |
| A | R2-01 — the guidance says what it is pointing at, and ADR-0037 | 2026-08-02 | `efaa987` |
| QE | Certification binds to an immutable commit, enforced by `certification-guard.py` | 2026-08-02 | `1bbee30` · `624f770` |
| QE | Pull-based work allocation — the backlog, and QE out of scheduling | 2026-08-02 | `3e36da9` |
| QE | The Task Claim Protocol, and permanent task ids | 2026-08-02 | `7b91948` |
| B | M12.5 slice 5 — target accounts. **M12.5 complete** | 2026-08-02 | `3f4e988` |
| A | M12.4 — research on demand | 2026-08-02 | `c1f5985` |
| A | R4-02 · R4-03 — the words the product uses when it refuses you | 2026-08-02 | `bdb014f` |
| A | R2-02 · R3-01 — saying what the evidence cannot support | 2026-08-02 | `64d9f2e` |
| A | R4-04 — a decision you can undo | 2026-08-02 | `fba0647` |
| A | B-001 — `supersedes IS NULL` was never currency | 2026-08-02 | `c0bef97` |
| B | M12.5 slices 2–4 — ICP, buying committee, business priorities | 2026-08-02 | `30e66d0` · `960b604` · `3931b3c` |
| B | B-005 · B-006 — the two defects a customer would have hit | 2026-08-02 | `a440fad` |
