# 433 — Assigned Execution Queues: the hybrid model

> **Lane C — Product Office, 2026-08-05.** **PREPARED — READY FOR PRODUCT OWNER. Nothing is implemented.** Supersedes [432](432-central-assignment-assessment.md)'s recommendation, which the product owner accepted and then improved.

## 1 · The two models converged, and the difference is worth naming

**[432](432-central-assignment-assessment.md) recommended *Constrained Pull*: lanes claim atomically, and eligibility is computed rather than chosen. The product owner proposed *assigned execution queues*: Lane C maintains Current/Next/Future per lane, and lanes execute without a round-trip.**

> **These are the same mechanism from two ends.** **The queue *is* the eligibility set — precomputed, ordered, and written down instead of derived at claim time.**

**The product owner's version is better, for two reasons this document keeps:**

| | |
|---|---|
| **Ordering becomes explicit** | Constrained Pull computed *eligibility* and left *order within it* to the backlog. **A queue states the intended sequence**, which is where dependency knowledge actually lives |
| **The plan becomes reviewable** | An eligibility rule is checkable only when a claim happens. **A queue can be read, questioned and resequenced before anybody builds anything** |

**And the product owner's framing is the sentence to keep:**

> ***The problem is not autonomous execution. The problem is uncontrolled task selection.*** **Those are different problems, and only the second one needed solving.**

## 2 · The measurement that matters — the model's first finding already exists

**Queue depth, measured against `origin/integration` today [M]:**

| Lane | `READY` in its modules | In flight | Target | |
|---|---|---|---|---|
| **Lane A** | **2** — TASK-904, TASK-905 | TASK-405 `CLAIMED` · TASK-400 returned | **5** | 🔴 **Below depth** |
| **Lane B** | 4 — TASK-003, TASK-408, TASK-902, TASK-903 | 6 `IN VALIDATION` · 3 `BLOCKED` | 5 | 🟠 **At risk** |
| **Lane C** | — | 3 `IN VALIDATION` | 5 | ⚠️ **Unattributable — see §7** |

> **Lane A would run dry after two more slices, and under this model that is a Product Office finding rather than an implementation problem.** **The model's first job exists before the model does**, which is the strongest argument for adopting it.

## 3 · Queue structure

**One file per lane. Lane C writes it. No lane ever writes another's, and no lane writes its own.**

```
docs/coordination/queues/
  lane-a.toml
  lane-b.toml
  lane-c.toml
```

```toml
# docs/coordination/queues/lane-a.toml
lane      = "Lane A"
updated   = 2026-08-05
depth_target = 5

current = "TASK-405"          # being built now
next    = "TASK-904"          # starts the moment current reaches IN VALIDATION
future  = ["TASK-905", "TASK-400", "TASK-003"]

# **Why this order**, and it is recorded because a sequence without a reason
# gets re-argued every time somebody reads it.
[rationale]
"TASK-400" = "returned slice, but blocked on C-219 and C-321 — both rulings, so it sits behind buildable work rather than ahead of it"
"TASK-904" = "Team Management is buildable now; its blockers were withdrawn by the lane that raised them"
```

### Three rules that keep it from becoming a second priority source

> **① The queue is a *projection*, never an origin.** **`BACKLOG.md` remains the product owner's priority order.** Lane C derives each queue from **priority × module ownership × dependency**, and **may not promote a task above one the product owner ranked higher without recording why.**
>
> **② The queue holds order. It never holds state.** `current`/`next`/`future` are **task ids only**. Execution state stays in `BACKLOG.md` and the board, written by the lane. **One fact, one writer** — the rule that made `modules.toml` work.
>
> **③ A task appears in exactly one lane's queue.** Enforced mechanically; it is *one assignee per module* expressed at task level.

## 4 · Assignment lifecycle

```
  PO orders BACKLOG.md
          │
          ▼
  Lane C sequences ──▶  queues/lane-*.toml  ──▶  lane executes current
          ▲                                              │
          │                                              ▼
          └────── resequences ◀── blocked ──┬──▶  IN VALIDATION
                                            │            │
                                            └────────────┴──▶ next becomes current
```

**No approval round-trip anywhere in that loop.** **A lane finishing `current` promotes `next` itself** — the queue is already on `integration`, so nothing waits for Lane C to be running.

### When a task becomes blocked

**The product owner's four steps, adopted as written, with the mechanism named for each:**

| | Step | How |
|---|---|---|
| **1** | **Document the dependency** | A `C-` item, naming the **module** — the assignee is joined from `modules.toml` ([D-062](../DECISION_REGISTER.md)) |
| **2** | **Update the task state** | `BLOCKED` in `BACKLOG.md` and on the board — **the lane's own rows** |
| **3** | **Notify Product Office** | **The `C-` item is the notification.** No second channel — a notification that is not a repository record does not exist (§20e) |
| **4** | **Continue with the next assigned task immediately** | Promote `next`. **Continuous execution, preserved exactly** |

> **Lane C resequences afterwards, and the blocked task keeps its place in `future` until it does.** **A lane never waits for a resequence** — that is the round-trip this model exists to avoid.

## 5 · Lifecycle changes

| State | Change |
|---|---|
| `READY` | ⚠️ **Meaning narrows.** Today: *claimable by whoever owns the module.* Under this model: *eligible to be **queued***. **A lane may not act on `READY` alone** |
| **`ASSIGNED`** | 🆕 **The new state.** In a lane's queue and not yet started. **Set by Lane C** |
| `CLAIMED` | ⚠️ **Becomes bookkeeping, not arbitration.** There is no race left to win. **Recommend retaining the name and dropping steps 3, 4, 8 and 9 of the Task Claim Protocol** |
| `IN PROGRESS` · `IN VALIDATION` · `CHANGES REQUESTED` | **Unchanged** |
| `PREPARING` · `UNDER REVIEW` · `REVISION REQUESTED` | **Unchanged** — [D-060](../DECISION_REGISTER.md)'s states are about packages, not allocation |
| `BLOCKED` | **Unchanged in meaning**, gains the four-step flow above |
| `AVAILABLE` | ⚠️ **Becomes a Product Office finding.** A lane reaching it means the queue ran dry |

## 6 · Responsibilities

| | Owns | Never |
|---|---|---|
| **Product Owner** | Priority, scope, the order of `BACKLOG.md` | — |
| **Lane C** | **Sequencing · dependency management · workload balancing · queue depth · assignment planning** · governance · architecture · review | ⛔ **Runtime scheduling.** It writes queues in batches, **never one task at a time**, and **is never in the execution path** |
| **Lane A / Lane B** | **Execute `current`, promote `next`, prepare packages for their own modules**, report blockers | ⛔ **Browse the global backlog. Reorder their own queue. Take work from another lane's queue** |
| **QE** | **Unchanged in every respect** | — |

## 7 · Automation — what can actually be enforced

**The product owner asked how much is mechanical rather than procedural. Evaluated honestly: five of seven are fully mechanical, one is partial, and one needs a gap closed first.**

| | Check | Feasible? | How |
|---|---|---|---|
| **Highest eligible assigned task** | ✅ **Fully** | A claim naming anything but `current` is refused by `certification-guard.py` — **a string comparison** |
| **Skip-note enforcement** | ✅ **Fully** | If `current` changes without the skipped task gaining a `BLOCKED` state or a rationale line, refuse. **Closes the defect Lane A hit this week** |
| **Out-of-order execution** | ✅ **Fully** | Same comparison as row 1 |
| **Queue depth monitoring** | ✅ **Fully** | `repository-dashboard.py` §4 — **`len(future) + 2 < depth_target` is a finding** |
| **Assignment consistency** | ✅ **Fully** | A task in two queues, or in a queue whose lane does not own its module, is refused |
| **Module ownership validation** | ✅ **Already built** | `_owners()`'s collision check, live since 2026-08-04 |
| **Dependency tracking** | ⚠️ **Partial** | ⛔ **Dependencies are prose today.** `BACKLOG.md` says *"blocked on C-213"* in a sentence. **Mechanical resequencing needs structured `blocked_by` fields**, which is a real change to how tasks are written — **and it should not be smuggled in here** |

> ⚠️ **One gap must be closed before any of this runs: `modules.toml` has no row for `infra/`, the `Makefile` or `signora_platform/simulation`.** **Lane C's own tasks are therefore unattributable to a lane by machine — measured in §2, where Lane C's queue could not be computed.** **A registry that cannot describe the lane maintaining it is the first thing to fix.**

## 8 · The new risk this model creates, and it is the important part

> 🔴 **Starvation stops being visible to the lane that suffers it.**

**Today a lane with nothing to do can see `READY` work and say so.** **Under assigned queues, a lane with an empty queue simply stops** — and the only party who can notice is the one who failed to fill it.

**Three mitigations, and the model should not ship without them:**

| | Mitigation |
|---|---|
| **①** | **Queue depth is reported every cycle, computed, in the dashboard.** Not a Lane C claim about itself |
| **②** | **A lane whose queue empties reports `AVAILABLE — QUEUE EMPTY` and names Lane C as the owner.** Loud, and attributed |
| **③** | **The escape hatch: a lane idle for one full reporting cycle with an empty queue may execute the highest-priority `READY` task in a module it owns, and must record that it did.** **This is deliberately not "browsing"** — it is bounded to its own modules, requires an empty queue, and leaves a record |

> **Mitigation ③ is the one to argue about, and it is worth keeping.** Without it, **a Lane C that is slow, busy or absent silently halts every implementation lane** — which is exactly the centralized bottleneck [432](432-central-assignment-assessment.md) was written to avoid, arriving through the back door. **With it, the worst case is a lane doing its own second-best work and saying so.**

## 9 · Governance changes required

**When implemented, not now.**

**`CLAUDE.md` §20e** — *Nobody assigns; lanes pull* is **replaced** by *Lane C sequences; lanes execute* · the **Task Claim Protocol loses steps 3, 4, 8 and 9** and gains *"execute `current`"* · **Continuous execution** is **preserved and re-stated** against the queue · **Shared files** gains `docs/coordination/queues/**` — **Lane C writes, no lane writes** · **the claim-commit exception to `integration` narrows**, because a claim no longer arbitrates.

**`BACKLOG.md`** gains **`ASSIGNED`** and keeps its order as the product owner's. **`ACTIVE_ASSIGNMENTS.md`** stops recording arbitration and records execution only. **No ADR is required** — no architecture, boundary or contract moves. **[D-060](../DECISION_REGISTER.md) is unaffected**: preparation stays with the owning lane.

## 10 · Migration — five phases, each independently valuable

| | Phase | Delivers standing alone | Size |
|---|---|---|---|
| **0** | **Close the registry gap** — `infra/` and `simulation/` get rows in `modules.toml` | **Lane C's own work becomes attributable by machine.** Blocks nothing else, but everything else assumes it | **Very small** |
| **1** | **Enforce the skip note** — `--audit-claims` refuses an unexplained skip | **Closes the one defect actually observed this week.** Independent of queues entirely | One guard rule |
| **2** | **Publish queues, advisory.** Lane C writes them; **lanes still claim as they do today** | **Weeks of evidence that the sequencing is right, at zero risk** — if a lane would have chosen differently, that disagreement is free to discover | Small |
| **3** | **Queue depth in the dashboard**, plus the `AVAILABLE — QUEUE EMPTY` state | **Makes §2's finding permanent and computed** | Small |
| **4** | **Enforce.** Lanes execute `current`; the guard refuses out-of-queue claims; the escape hatch is written into §20e | **The model, live** | Medium |

> **Phase 2 is the whole design decision, and it costs nothing to abandon.** **If Lane C's sequencing disagrees with what a free lane would have chosen even twice, the queues are wrong and no lane was ever blocked by them** — the same staged shape [427](427-impact-based-validation.md) uses, for the same reason.

## 11 · Objectives, checked

| Objective | Met by |
|---|---|
| **No lane races** | ✅ **Structurally** — a task is in one queue |
| **No idle lanes** | ✅ Queue depth monitoring + **escape hatch §8③** |
| **No centralized execution bottleneck** | ✅ **Batched queues, not per-task assignment.** Lane C is never in the execution path |
| **No autonomous backlog browsing** | ✅ Lanes read one file — their own queue |
| **Continuous execution** | ✅ `next` promotes without approval |
| **Clear ownership** | ✅ Queue + `modules.toml`, both mechanically checked |
| **Automation before manual process** | ✅ **6 of 7 checks mechanical; the 7th named honestly as partial** |

## 12 · Recommendation

| | |
|---|---|
| **The hybrid model** | ✅ **Adopt.** It is Constrained Pull with the eligibility set made explicit and reviewable, and it is the better of the two |
| **Start at** | **Phase 0 and 1 together — a registry row and a guard rule.** Both are worth doing whatever happens to the rest |
| **Phase 2 before phase 4** | ✅ **Advisory queues first.** The sequencing must be shown right before a lane is forbidden to disagree with it |
| **The escape hatch** | ⚠️ **Not optional.** Without it the model has a single point of failure whose failure mode is silent |
| **Dependency automation** | ⏸️ **Defer.** It needs structured `blocked_by` fields, which is its own change |

> **The honest summary: the product owner's model is better than the one I recommended, and it is better for a reason worth stating — it makes the *plan* reviewable rather than only the *claim*.** **What it adds is a dependency on Lane C being current, and §8 is the price of that.**
