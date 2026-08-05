# 434 — Assigned Execution Queues: the final governance package

> **Lane C — Product Office, 2026-08-05.** **PREPARED — READY FOR PRODUCT OWNER REVIEW. Nothing is implemented.**
>
> The reviewable package for [433](433-assigned-execution-queues.md), with the product owner's two refinements incorporated: **Product Office service level objectives** and a **bounded escape hatch**. **This document is what §20e would become**, presented for review before adoption.

## 1 · The final principle, and the quantity that resolves it

> **"The implementation lanes should never have to decide what to build next. The Product Office should never become a runtime bottleneck. The governance must achieve both simultaneously."**

**These pull against each other, and exactly one quantity reconciles them: queue depth.**

| Depth | Lane decides? | Lane C in the path? |
|---|---|---|
| **0** | ⛔ **Yes — it must, or stop** | — |
| **1** | ✅ No | ⛔ **Yes.** Lane C must act between every slice |
| **5** | ✅ **No** | ✅ **No** — Lane C acts once per ~5 slices |
| **∞** | ✅ No | ✅ No — but **Lane C is planning blind**, and stale sequencing is worse than none |

> **So the final principle is not a philosophy to be balanced; it is a number to be held.** **Depth is what makes both halves true at once**, and that is why §2 makes it measurable rather than aspirational.

## 2 · Product Office Service Level Objectives

**Governance metrics, each with the source it is computed from.** ⚙️ **computable today** · 🕐 **computable once queues exist (phase 2)** · 📊 **needs history (phase 3+)**

| # | Metric | Target | Finding threshold | Source |
|---|---|---|---|---|
| **1** | **Assigned queue depth** per implementation lane | **≥ 5** — `current` + `next` + ≥3 `future` | **< 3 amber · 0 red** | 🕐 `queues/lane-*.toml` |
| **2** | **Time with an empty assigned queue** | **0 cycles** | **≥ 1 cycle → escape hatch arms.** **≥ 2 → P0 governance finding against Lane C** | 🕐 |
| **3** | **Replenishment latency** | **Refilled to ≥5 within 1 reporting cycle** of dropping below 3 | **> 1 cycle** | 📊 |
| **4** | **Starvation detection** | Depth ≥ 3 at every report | **Any lane below 3** | 🕐 |
| **5** | **Average queue depth**, rolling 5 cycles | **≥ 5** | **< 4** | 📊 |
| **6** | **Queue ageing** — cycles a task sits in `future` without advancing | **≤ 5** | **> 5 → the task is mis-sequenced, or belongs in `SEQUENCED`/deferred, and the queue is hiding it** | 📊 |
| **7** | **% of reporting cycles every lane was at or above target** | **≥ 90%** | **< 90%** | 📊 |
| **8** | **Escape-hatch invocations**, rolling 3 cycles | **0** | **≥ 1 → Product Office planning finding** · **≥ 2 → P0** | 🕐 |

> **Running below target is a Product Office finding, recorded against Lane C by name.** **Not against the lane that starved** — that lane did nothing wrong, and attributing it to them is how a metric stops being honest.

**Measured today, before the model exists [M]:** **Lane A holds 2 `READY` tasks in its own modules against a target of 5.** **SLO 1 would already be amber and SLO 4 already breached** — the model's first finding predates the model.

> ⚠️ **SLOs 3, 5, 6 and 7 need history and cannot be reported at phase 2.** **They are listed with the phase that makes them real rather than presented as available now** — a metric quoted before it can be computed is the defect §2 exists to prevent.

## 3 · The escape hatch — an emergency mechanism, bounded five ways

> **It exists to prevent a repository-wide stall, and for nothing else.** **It is not a route back to autonomous execution**, and every bound below is there to keep it from becoming one.

| | Bound | Enforcement |
|---|---|---|
| **1** | **Only after one complete reporting cycle with an empty assigned queue.** Not "no suitable work" — **empty** | ⚙️ Queue file + cycle count |
| **2** | **Only `READY` work inside the lane's own modules**, per `modules.toml`. **Never another lane's, never a non-`READY` task** | ⚙️ **The check `_owners()` already performs** |
| **3** | **It must create a governance event** | **The claim commit carries an `Escape-Hatch:` trailer** naming the empty-queue cycle and the task taken. **Greppable, permanent, and it travels with the change** — the mechanism `Slice-Handoff` already proves |
| **4** | **It must appear in the next executive summary** | **Counted by the dashboard from the trailer**, not reported by the lane that used it |
| **5** | **Repeated use is a Product Office planning failure** | **≥1 in 3 cycles is a finding against Lane C; ≥2 is P0** — SLO 8 |

**The trailer, so it is checkable rather than described:**

```
Escape-Hatch:
  Empty since:   cycle 57
  Cycles idle:   1
  Task taken:    TASK-904
  Module:        workspace_tenancy  (this lane's, per modules.toml)
  Queue state:   current=— next=— future=[]
```

> **Why a commit trailer rather than a register row.** **A register row is written by whoever remembers to write it.** A trailer is part of the change, cannot be separated from it, and `--audit-claims` already reads commits by path and content. **The event should be a by-product of doing the thing, never a second action that can be skipped.**

**And the framing that keeps it honest:** **an invocation is evidence about Lane C, not about the lane that invoked it.** A lane using the hatch has followed governance exactly.

## 4 · The executive dashboard — thirteen items, and what each costs

**⚙️ exists today · 🆕 new, computable · ⚖️ judgement, marked as such**

| Item | | Source |
|---|---|---|
| **Overall repository health** | ⚖️ | Lane C judgement over gates, defects, sync |
| **Overall project completion** | ⚖️ | **Estimate. A module has no denominator in the repository** — stated every time |
| **Epic completion** | ⚙️ | §3 Epic Dashboard |
| **Module completion** | ⚙️/⚖️ | §2, `implementation` from `modules.toml` — **an estimate, banded to 5** |
| **Assigned queues per lane** | 🆕 | `queues/lane-*.toml` |
| **Queue depth** | 🆕 | `len(future) + 2` |
| **Queue health against target** | 🆕 | SLO 1 · 4 |
| **Starvation warnings** | 🆕 | SLO 2 · 4 · 8 |
| **Blocked tasks** | ⚙️ | §5 Task Assignment |
| **Current bottleneck** | ⚙️ | §11 Bottleneck Dashboard — **gains a *queue* row** |
| **Risks** | ⚖️ | Lane C |
| **Governance findings** | 🆕 | **SLO breaches, computed** — not a lane's claim about itself |
| **Upcoming transitions** | ⚙️ | `modules.toml` `transition` + `gate` |

> **Nine of thirteen are computed. Four are judgement and are marked `«judgement»` in the output**, so a missing one is visible rather than silently absent — the rule the generator already follows.

**The dashboard becomes the single place the project is understood from** — and **`PROJECT_STATUS.md` remains QE's measured record of the promoted commit.** **They answer different questions and neither restates the other** (§2).

## 5 · The governance package — what §20e becomes

**Presented for review. Not applied.**

### 5a · Replaces *Nobody assigns; lanes pull*

> ### Lane C sequences; lanes execute
>
> **The product owner owns priority. Lane C owns sequence. A lane owns execution.** **No lane decides what to build next, and no lane waits for a person to tell it.**
>
> **Each implementation lane has one queue — [`docs/coordination/queues/`](../coordination/queues/) — holding `current`, `next` and `future`.** **A lane executes `current`, and promotes `next` itself the moment `current` reaches `IN VALIDATION`.** **There is no approval step, and none may be introduced.**
>
> **A lane does not browse [`BACKLOG.md`](../BACKLOG.md), does not reorder its own queue, and does not take work from another's.**
>
> **The queue is a projection, never an origin.** `BACKLOG.md` remains the product owner's order; **Lane C derives each queue from priority × module ownership × dependency and records why whenever it deviates from priority.** **The queue holds task ids and never state.**

### 5b · The Task Claim Protocol becomes the Execution Protocol

**Steps 3, 4, 8 and 9 are removed** — selecting, confirming you were first, and abandoning a lost race all presuppose a race. **A task is in exactly one queue, so there is none.**

**What remains:** synchronize · rebase · **read your queue** · record `current` on the board · commit alone · push to `integration` · **implement immediately**.

> **The claim commit survives and its bound narrows**: it records execution, not arbitration. **`--audit-claims` keeps `CLAIM_PATHS` and gains the queue directory.**

### 5c · Continuous execution — preserved, restated

**Only four things stop a lane, and *"my queue is empty"* is the new fourth:** no `next` · a returned slice to address · an architectural blocker · **an empty queue, which arms the escape hatch after one cycle.**

### 5d · Shared files

**`docs/coordination/queues/**` — Lane C writes. No implementation lane writes, including its own.**

### 5e · Lifecycle

**`ASSIGNED` is added** — in a queue, not started, set by Lane C. **`CLAIMED` becomes bookkeeping rather than arbitration. `AVAILABLE` becomes a Product Office finding.** **Everything from `IN PROGRESS` onward is unchanged, and QE's seven stages are untouched.**

## 6 · Migration — approved phases, with the evidence gate

| | Phase | Exit criterion |
|---|---|---|
| **0** | **Registry completeness** — `infra/`, `Makefile`, `simulation/` gain rows in `modules.toml` | **Every task attributable to a lane by machine.** Today Lane C's own are not |
| **1** | **Skip-note enforcement** — `--audit-claims` refuses an unexplained skip | **The observed defect closed.** Independent of queues entirely |
| **2** | **Advisory queues.** Lane C publishes; **lanes claim exactly as they do today** | **Held in observation.** See below |
| **3** | **Depth, SLOs and starvation in the dashboard** | SLOs 1, 2, 4, 8 computed; 3, 5, 6, 7 begin accumulating |
| **4** | ⏸️ **Enforcement — considered only on evidence** | **Five conditions, below** |

### The evidence gate on phase 4 — stated so it is checkable

**Phase 2 stays in observation until all five hold, measured over at least five reporting cycles:**

| | Evidence | Measured by |
|---|---|---|
| **1** | **Queues remain healthy** | SLO 7 ≥ 90% |
| **2** | **Throughput improves** | Promoted executable slices per cycle, against the pre-queue baseline |
| **3** | **Races disappear** | **Zero, and it is already zero** — so this is *maintained*, not achieved |
| **4** | **Starvation decreases** | SLO 4 breaches trending down; escape-hatch invocations at 0 |
| **5** | **No new governance bottleneck** | **Replenishment latency (SLO 3) ≤ 1 cycle**, and the review queue not growing |

> ⚠️ **Condition 5 is the one that would fail, and it is the one to watch.** **A queue that is always full proves nothing if Lane C is the reason a lane's next task is wrong.** **Advisory mode is what makes that free to discover**: a lane still claims, so a disagreement between the queue and what the lane would have chosen costs a note rather than a stall.

**Do not rush to phase 4** — recorded here as governance rather than as advice.

## 7 · Risks this package carries

| | Risk | Mitigation |
|---|---|---|
| **1** | 🔴 **Lane C becomes the single point of failure for all execution** | **Depth ≥5 keeps it out of the path** · **the escape hatch bounds the failure** · **SLO 2 makes it loud within one cycle** |
| **2** | **The escape hatch normalises** | **Five bounds; a permanent commit trailer; and use is a finding against Lane C, not the lane** |
| **3** | **Queues go stale and lanes build the wrong thing correctly** | **Queue ageing, SLO 6** · advisory phase 2 |
| **4** | **SLOs become a target rather than a measure** | **They are computed from repository state, not reported by Lane C.** A lane cannot pad them and neither can the office |
| **5** | **Dependency resequencing stays manual** | **Deferred honestly** — dependencies are prose today, and structuring them is its own change |

## 8 · Recommendation

| | |
|---|---|
| **The package** | ✅ **Ready for review.** Two refinements incorporated; nothing implemented |
| **Start** | **Phases 0 and 1 — a registry row and a guard rule.** Worth doing whatever is decided about the rest |
| **Phase 2** | ✅ **Advisory, and held there.** Five conditions, five cycles |
| **Phase 4** | ⏸️ **Not scheduled, deliberately** |
| **The number to watch** | **Queue depth.** It is the one quantity that makes both halves of the final principle true at once |

> **The honest summary: this package is mostly measurement.** **The model was agreed in [433](433-assigned-execution-queues.md); what was missing was any way to tell whether it was working** — and a governance model without a metric is a preference with a process attached.
