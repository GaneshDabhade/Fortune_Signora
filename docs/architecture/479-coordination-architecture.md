# 479 · The Coordination subsystem — planning flows without waiting for release

✅ **RATIFIED — product owner, 2026-08-07, [D-144](../DECISION_REGISTER.md).** *"It has the right foundation. Let Lane C implement and use the coordination subsystem, and refine it based on real repository behavior rather than continuing to redesign it theoretically."*

**Lane C · Product Office · 2026-08-07.** **[D-142](../DECISION_REGISTER.md) §10, strengthened by [D-143](../DECISION_REGISTER.md), ratified by [D-144](../DECISION_REGISTER.md).**

> ⚡ **v1 is live.** **`origin/coordination` carries `coordination.toml` and a README, on an orphan ref with no history — a lane fetches two files, not a repository.** ⛔ **§10's steps ③ to ⑤ are done: the ref exists, `CLAUDE.md` §20e is amended, and all three lanes are notified.**

> ## ⛔ **This is a subsystem, not a generated file.**
>
> **[D-143](../DECISION_REGISTER.md) §1: its responsibility is to be the single operational source every implementation lane consults for day-to-day execution.** ⛔ **No lane derives work from `BACKLOG.md`, the registers, commit history or QE state.** ⚡ **Coordination *projects the current executable view of the repository* — and it computes that view by walking a dependency graph, not by re-deriving relationships every cycle.**

> ⚠️ **The directive arrived labelled `D-137`, which is already allocated to Canonical Design Accessibility. Registered as `D-142`** — §20e forbids two rows under one id, and [C-423](../LANE_COORDINATION.md) is the open item about making that unrepresentable.

---

# 0 · The problem, as a number

> ## **A lane must read 14,392 lines across seven files to learn what to build next — and none of them reaches it until QE integrates.**

| What a lane reads today | Lines |
|---|---|
| `LANE_COORDINATION.md` · `BUGS.md` · `BACKLOG.md` · `ACTIVE_ASSIGNMENTS.md` · `modules.toml` · its queue · `DECISION_REGISTER.md` | **14,392** |

⛔ **And the deeper fault is not the volume.** **[§20e](../../CLAUDE.md) step 6 says *"Backup, not a trigger — QE does not poll"***, so planning information reaches a lane only when a release pipeline carries it. ⚡ **Planning waited on release, and that is the wrong dependency.**

**Measured three times in three days:** **[C-422](../LANE_COORDINATION.md)** — a correction stranded while a lane claimed the row it corrected · **[C-234](../LANE_COORDINATION.md)** — a lane blocked on a delivered slice it could not see · **Lane A's report of 2026-08-07** — *"two finished answers for this lane are still stranded."*

---

# 1 · The decision

> ## **Planning and release become two pipelines. They share a repository and nothing else.**

```
  PLANNING                                     RELEASE
  ────────                                     ───────
  Lane C                                       lane branch
     │ regenerates                                │ push
     ▼                                            ▼
  origin/coordination  ──── every lane reads   QE: validate · certify
     │                      it on every poll      │ integrate · promote
     └── no merge, no QE, no integration          ▼
                                               integration → main
```

**`origin/coordination` is a dedicated ref carrying one generated file.** ⛔ **Lane C is its only writer. QE never touches it. It is never merged into anything.**

### Why a ref rather than a file on `integration`

| | |
|---|---|
| ⛔ **A file on `integration`** | **Requires Product Office write authority there, which [D-136](../DECISION_REGISTER.md) declined** — *"I want to preserve a single integration authority"* |
| ⛔ **Lanes polling `lane-c-sync`** | **Forbidden by [D-142](../DECISION_REGISTER.md) §3** — *"Lane A and Lane B should never poll Product Office branches"* — **and rightly: a working branch carries half-finished governance** |
| ✅ **A dedicated ref** | **Neither.** ⚡ **`lane-c-sync` is where Product Office *works*; `coordination` is what it *publishes*.** **A lane reads the published state and never sees work in progress** |

⚠️ **This is not automation and §20c-2 is untouched.** **No workflow fires, no push triggers anything, nothing runs remotely.** **A lane fetches a ref and reads a file** — the same act as fetching `integration`, pointed at a different ref.

---

# 2 · The single source of truth

**One file: `coordination.toml`, on `origin/coordination`.** **It answers all seven questions [D-142](../DECISION_REGISTER.md) §2 names, for every task, in one read.**

```toml
[meta]
generated_at   = 2026-08-07
generated_from = "a5f2e91"          # the integration commit the projection was taken at
generator      = "infra/coordination.py"

[[task]]
id            = "TASK-419"
title         = "A handler can reach a provider adapter"
state         = "IN VALIDATION"      # exactly one of the eight in §4
lane          = "Lane C"             # joined from modules.toml, never stored twice
module        = "apps"
depends_on    = []
unblocks      = ["TASK-901"]
next_owner    = "Lane A"             # who receives what this releases
ready_when    = "—"                  # the condition, not a date
blocker_owner = "—"
```

### ⛔ It is a projection, not a second truth

⚡ **The file is *generated*, never hand-written.** **`BACKLOG.md` remains authoritative for scope, `modules.toml` for ownership, `LANE_COORDINATION.md` for dependencies** — and **`coordination.toml` is their published join.**

> **[§2](../../CLAUDE.md): *truth has exactly one authoritative representation; everything else derives from it*.** ⛔ **A hand-maintained coordination file would be an eighth place to disagree.** ✅ **A generated one cannot drift, because regenerating it is the only way to change it.**

---

# 3 · The polling flow

**A lane's poll becomes one command and one read.**

```
  git fetch origin coordination
  read coordination.toml → the rows where lane == mine
```

⛔ **No lane inspects another lane's branch, commit history, decision logs or registers to find work.** ✅ **The registers remain the record and the *reason*; the coordination source is the *instruction*.**

⚠️ **A lane still reads [`BUGS.md`](../BUGS.md) and [`LANE_COORDINATION.md`](../LANE_COORDINATION.md) at Startup** (§20e steps 3 and 5) — **that is unchanged and is about awareness, not assignment.** ⚡ **The change is that *what to build next* no longer requires them.**

---

# 4 · Every item is in exactly one state

**[D-142](../DECISION_REGISTER.md) §7, enumerated so nothing floats:**

| State | Means | Claimable |
|---|---|---|
| **`ASSIGNED`** | Executable now, owned | ✅ |
| **`BLOCKED`** | A named blocker, with an owner | ⛔ |
| **`SEQUENCED`** | Behind a predecessor in the same lane | ⛔ |
| **`WAITING_PRODUCT_OWNER`** | A ruling is owed | ⛔ |
| **`WAITING_EXTERNAL`** | A credential, a vendor, a dataset | ⛔ |
| **`WAITING_ARCHITECTURE`** | An ADR or a boundary decision | ⛔ |
| **`FUTURE_MILESTONE`** | Real, placed, and not this wave | ⛔ |
| **`IN FLIGHT`** | A lane or QE holds it — ⛔ **never written by Product Office** ([D-123](../DECISION_REGISTER.md)) | ⛔ |

⛔ **There is no eighth bucket and no absent value.** **The generator refuses to emit a task it cannot place**, which is how *floating backlog* becomes unrepresentable rather than discouraged.

---

# 5 · Dependencies are objects, not prose

**Each carries: `depends_on` · `unblocks` · `blocker_owner` · `next_owner` · `ready_when` · `auto_promote`.**

⚡ **The pair that matters is `unblocks` and `next_owner`.** **Today a dependency is discovered by reading a blocker's row and inferring who was waiting** — **which is how [TASK-419](../BACKLOG.md) sat `READY` for a day while Lane A was blocked on it.** ✅ **Stated forward, the generator can compute the successor rather than a human rediscovering it.**

---

# 6 · Automatic promotion

**When the generator observes all five, it promotes without being asked:**

**① every `depends_on` is complete · ② the owning lane is resolvable · ③ no `WAITING_PRODUCT_OWNER` remains · ④ no `WAITING_ARCHITECTURE` remains · ⑤ no external dependency remains** → **the task becomes `ASSIGNED`, the lane's queue updates, and the coordination source carries it on the next publish.**

⛔ **`auto_promote = false` is available and must state a reason.** ⚡ **The one legitimate use is a row whose readiness is a *judgement* rather than a computation** — **and [D-130](../DECISION_REGISTER.md) is why it exists: `READY` means *fit to implement*, and fitness is sometimes a behaviour nobody has read yet.**

---

# 7 · Starvation becomes measured, not reported

**[D-142](../DECISION_REGISTER.md) §8. The generator emits these on every run:**

| | |
|---|---|
| **`lane_utilization`** | Rows in flight ÷ capacity |
| **`queue_depth`** | Claimable rows per lane |
| **`days_until_starvation`** | Depth ÷ observed claim rate — ⚡ **Lane A claimed seven rows in one day; that rate is measurable** |
| **`dependency_wait`** | How long each blocked row has waited, and on whom |
| **`planning_latency`** | Blocker cleared → task promoted |
| **`assignment_latency`** | Task promoted → lane could see it |
| **`idle_attributed_to`** | `product_office` · `qe` · `external` — ⛔ **attributed, never aggregated, because the three have different fixes** |

> ⛔ **If a lane reaches zero claimable while assignable work exists elsewhere, that is a Product Office defect and the generator raises it.** ⚡ **[D-142](../DECISION_REGISTER.md) §1 says so outright, and it is the metric this whole document exists to drive to zero.**

---

# 8 · What QE keeps, unchanged

✅ **Validation · certification · integration · promotion · Closeout · synchronization · Repository Ready.** ⛔ **QE loses nothing.** ⚡ **It stops being asked to carry planning information, which was never its job** — **[§20e](../../CLAUDE.md) already says *"QE validates, certifies, integrates, promotes, closes out, synchronizes and declares. It does not decide who works on what."***

**The execution board, the backlog's lifecycle states and the claim protocol are all unchanged.** **A lane still claims from `BACKLOG.md`, still pushes its branch, still hands to QE.**

---

# 9 · What this does not solve

⛔ **A blocked row stays blocked.** **This propagates readiness; it does not create it.** **Lane A's fourteen rows are parked behind real blockers and would be parked behind them under any coordination model.**

⛔ **It does not reduce QE's queue.** **Thirty-five rows sit in validation and this changes none of them.**

⚠️ **And it adds a ref that can go stale.** ✅ **Mitigated by construction: `[meta] generated_from` names the commit the projection was taken at, so a lane can see how old its instruction is** — **and a stale coordination source is detectable, which the current model's silence was not.**

---

# 10 · Sequencing

| | |
|---|---|
| **① This document** | ✅ **Ratified 2026-08-07, [D-144](../DECISION_REGISTER.md)** |
| **② `infra/coordination.py`** | ✅ **Built and running** — the generator, and `state-check` gains a check that the published ref matches what the generator would emit today** |
| **③ The `coordination` ref** | ✅ **Created and published** — `origin/coordination`, orphan, two files |
| **④ `CLAUDE.md` §20e** | ✅ **Amended** — *A lane learns what to build from `origin/coordination`* |
| **⑤ The lanes** | ✅ **Told, in all three queue files** |

✅ **All five are done as of 2026-08-07. The subsystem is in use.**

> ## **v1 ships deliberately unfinished, and [D-144](../DECISION_REGISTER.md) is why.**
>
> ⛔ **`planning_latency` and `assignment_latency` are specified and not emitted** — both need the moment a blocker *cleared*, and the repository records when a state *string appeared*. **Computing them would mean inventing a number.**
>
> ⚡ **They are the first thing to learn from use rather than to perfect on paper**: *"this metric isn't useful · this dependency should be automatic · this queue should predict starvation · this assignment should happen earlier"* — **each of those is cheaper to find in a running system than to specify in advance.**
