# Active assignments — the execution board

> **The repository's current execution state, and the only authoritative record of it.** Established 2026-08-01; became **the execution board** on 2026-08-02; became **claim-based** the same day, when scheduling moved from QE to a pull model.
>
> **A lane writes its own row when it claims work.** QE reconciles the board at Repository Closeout and removes what has been promoted, but **QE does not decide who does what** (`CLAUDE.md` §20e). If this file and any other document disagree about who is implementing what, **this file is right and the other is a defect.**
>
> **This file holds active execution only.** What is *available* to work on is [`BACKLOG.md`](BACKLOG.md), which the product owner prioritizes — the two are deliberately separate, because a board that also holds the queue becomes a place to negotiate priority.

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

- **A lane claims; nobody assigns.** Take the highest [`READY`](BACKLOG.md) item you can, and **write the row here before the first line of implementation.** A claim that is not written down is two lanes about to build the same thing.
- **Claim from the top of the queue.** If the top item cannot be taken, say why in its backlog note and take the next — skipping silently is re-prioritizing, and priority is the product owner's.
- **One active assignment per lane. One assignee per module.** Both directions, at all times.
- **When a lane finishes a slice: mark it `COMPLETE`, return the lane to `AVAILABLE`, and remove the completed row.** A row describing work already on `main` is the defect this file exists to prevent — **no lane may remain assigned to work that has shipped, and no stale assignment is left behind.**
- **A row is a slice, not a milestone.** *Commercial Profile — slice 2* is an assignment; *Commercial Profile* is not.
- **`Started` is when the assignment was made**, not when the branch was created.
- **A lane whose module is blocked stays assigned** and the blocker is named — that is a fact about execution state, and hiding it makes the lane look idle when it is stuck.
- **Every row states its expected next action.** A board that says what is happening but not what happens next leaves a cold session to infer it, and an inferred next action is how two lanes do the same thing.

| Status | Meaning |
|---|---|
| `CLAIMED` | Taken from the backlog, not yet started |
| `ACTIVE` | Being implemented |
| `BLOCKED` | Waiting on a `C-` item or a dependency. **Name it** |
| `IN VALIDATION` | Handed to QE — **committed and pushed**, in the lifecycle, not yet promoted |
| `COMPLETE` | Promoted to `main`. **Marked by QE at Closeout, then removed, and the lane returns to `AVAILABLE`** |
| `AVAILABLE` | No current slice. **Free to claim from [`BACKLOG.md`](BACKLOG.md)** — not waiting for anyone |

> **`IN VALIDATION` means the work exists as commits QE can take.** Uncommitted work in a session's working tree is `ACTIVE`, whatever stage it feels like it has reached — **the board describes the repository, not an intention.** This distinction was added on 2026-08-02 after this file recorded QE's own governance slice as `IN VALIDATION` while it was still entirely uncommitted.

---

## Current — as of 2026-08-02, `624f770`

| Lane | Assignment | Module | Milestone | Slice | Status | Blocked by | Depends on | Next action | Started |
|---|---|---|---|---|---|---|---|---|---|
| **Lane A** | — | — | — | — | `AVAILABLE` | — | — | **Claim from [`BACKLOG.md`](BACKLOG.md).** Last slice: R2-01, promoted in `1bbee30` | — |
| **Lane B** | — | — | — | — | `AVAILABLE` | — | — | **Claim from [`BACKLOG.md`](BACKLOG.md).** Last slice: M12.5 slice 5, promoted at `3f4e988` | — |
| **QE** | Repository lifecycle and governance | — (the repository) | — | permanent | `ACTIVE` | — | — | Next cycle: validate whatever a lane hands over | 2026-08-01 |

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
| B | M12.5 slice 5 — target accounts. **M12.5 complete** | 2026-08-02 | `3f4e988` |
| A | M12.4 — research on demand | 2026-08-02 | `c1f5985` |
| A | R4-02 · R4-03 — the words the product uses when it refuses you | 2026-08-02 | `bdb014f` |
| A | R2-02 · R3-01 — saying what the evidence cannot support | 2026-08-02 | `64d9f2e` |
| A | R4-04 — a decision you can undo | 2026-08-02 | `fba0647` |
| A | B-001 — `supersedes IS NULL` was never currency | 2026-08-02 | `c0bef97` |
| B | M12.5 slices 2–4 — ICP, buying committee, business priorities | 2026-08-02 | `30e66d0` · `960b604` · `3931b3c` |
| B | B-005 · B-006 — the two defects a customer would have hit | 2026-08-02 | `a440fad` |
