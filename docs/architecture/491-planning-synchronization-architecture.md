# 491 · Planning synchronization — why it is coupled, and the architecture that uncouples it

**Lane C · Product Office · 2026-08-08.** **[D-173](../DECISION_REGISTER.md), which rejected [C-435](../LANE_COORDINATION.md)'s option C and asked for the class of problem to be eliminated rather than the occurrence.**

> ⛔ **The rejection was right and the reason is worth stating first.** **Option C bought Lane A a cycle by weakening *"a cycle is warranted by executable change"* — a rule that exists because certifying documentation alone is *"how a team learns to skip cycles."*** ⚡ **A workaround that costs a guarantee is a bad trade even when it works.**

---

## 0 · The finding, before the analysis

> ## ⚡ **This exact problem was ruled on already. [D-142](../DECISION_REGISTER.md) ⑨ says *"Planning and release are separate pipelines"*, and its opening sentence is the diagnosis in the product owner's own words:**
>
> ## ⛔ ***"The problem is not whether Lane C may push a claim commit. The problem is that our coordination model currently depends on QE integration for information flow. That is the wrong dependency."***
>
> ## ⚠️ **[D-144](../DECISION_REGISTER.md) then built `origin/coordination` to implement it — and implemented half.** **Planning *information* was separated. Planning *authority* was not.**

**So the recommendation below is not a new architecture. It is the completion of one the product owner already ruled and this office delivered incompletely.**

---

## 1 · Why planning depends on QE integration — the mechanism, not the symptom

**The chain is four links and each is individually correct:**

| | |
|---|---|
| **①** | **A lane may claim only a `READY` row** (§20e) |
| **②** | ⚡ **`READY` is read from `BACKLOG.md`, and [C-425](../LANE_COORDINATION.md) settles which copy: *"the backlog wins on state"*, meaning the copy on `origin/integration`** |
| **③** | **`BACKLOG.md` is a file in the versioned tree, so it moves by branch, merge and fast-forward** |
| **④** | ⛔ **`integration` is fast-forwarded by QE alone**, and QE runs when executable change warrants a cycle |

> ## ⛔ **Therefore: planning state inherits the release lifecycle of executable code, because it is stored in the same tree and transported by the same mechanism.**

⚡ **That is the root cause in one sentence, and every symptom follows from it** — the 136 idle cycles, the `claimable_now = 0`, the three stranded commits, and [C-422](../LANE_COORDINATION.md) before them.

### ⚠️ Three consumers, three cadences, one transport

| The question | Who answers | How fast it must travel | Where it lives today |
|---|---|---|---|
| ⚡ **"Is this row claimable?"** | **Product Office** | **Poll cadence — minutes** | ⛔ **`integration`, so QE cadence — hours** |
| ⚡ **"Did I claim it before anyone else?"** | **The lane, atomically** | **Must be a single contended write** | ✅ **`integration`, correctly** |
| **"Is this commit fit to promote?"** | **QE** | **Cycle cadence** | ✅ **`integration`, correctly** |

⛔ **Two of the three are right. The first is wrong, and it is wrong because it was never separated from the second.**

---

## 2 · ✅ The measurement that makes this safe to change

**`BACKLOG.md` is already classified as non-executable by certification itself, and a test enforces it:**

> **`certification-guard.py` — `test_the_two_classifiers_in_this_file_agree` asserts `docs/BACKLOG.md` satisfies `CLOSEOUT_PATHS` and `CLOSEOUT_SUFFIXES`.** ⚡ **A Closeout commit may touch it precisely because it *"provably changes nothing executable."***

**And the fast path already exists — for lanes:**

> **`CLAIM_PATHS = ("docs/ACTIVE_ASSIGNMENTS.md", "docs/BACKLOG.md")`.** ⛔ **A feature lane *may* fast-forward `integration` with a commit touching only those two**, guarded by `--audit-claims`.

> ## ⚡ **So the same file is on the fast path for a lane and the slow path for Product Office. The asymmetry is by role, not by risk — and no gate reads `BACKLOG.md` to decide whether anything is fit to promote.**

⚠️ **No backend code reads it. `smoke.sh`, `disaster-recovery.sh`, `release-preflight.py` and `validate.py` do not mention it.** ✅ **Only the three planning instruments do, and all three are advisory.**

---

## 3 · Four architectures, compared

### ⛔ Option 1 — Keep files, change cadence *(rejected by [D-173](../DECISION_REGISTER.md), correctly)*

**Let `Planning-Sync` warrant an integration.** ⛔ **Introduces a second class of integration and weakens the cycle rule.** **Solves the occurrence, not the class.**

### ⚡ Option 2 — Extend `CLAIM_PATHS` to Product Office

**Product Office fast-forwards `integration` with a commit touching `BACKLOG.md` alone**, refused by a `--audit-planning` guard if it touches anything else.

| ✅ | ⛔ |
|---|---|
| **The mechanism, the guard and the path classification all exist** | **A second lane may write to `integration`** |
| **Zero new concepts. Reversible in one commit** | ⚠️ **[D-136](../DECISION_REGISTER.md) declined this twice — *"Product Office gains no write authority"*** |
| **Unblocks Lane A today** | **It relieves the symptom without moving the boundary** |

### ✅ Option 3 — Complete [D-142](../DECISION_REGISTER.md) ⑨: separate *eligibility* from *arbitration*

> ## **`BACKLOG.md` moves to `origin/coordination`. `ACTIVE_ASSIGNMENTS.md` stays on `integration`.**

**The insight: *"is this claimable"* and *"did I claim it first"* are different facts with different consumers and different atomicity requirements, and they have been stored together only by accident of both being markdown.**

| | Fact | Ref | Cadence | Why |
|---|---|---|---|---|
| **Eligibility** | **`READY` · `SEQUENCED` · `BLOCKED`** | ⚡ **`origin/coordination`** | **Product Office's poll** | **Nobody contends it — one author** |
| **Arbitration** | **`CLAIMED` and who holds it** | ✅ **`integration`** | **Atomic push** | ⛔ **Two lanes race for it; a push is the only atomic primitive here** |
| **Certification** | **executable trees** | ✅ **`integration` → `main`** | **QE cycle** | **Unchanged in every respect** |

⛔ **This is a *relocation*, not a duplication** — **[D-173](../DECISION_REGISTER.md) asks for *"a single source of truth without creating duplicate authorities"*, and moving a file creates no second copy.** ⚡ **The backlog remains the one authority for scope and state; only its *transport* changes.**

| ✅ **What it fixes permanently** | ⚠️ **What it costs** |
|---|---|
| **A planning correction reaches a lane at poll cadence, always** | **The claim protocol reads two refs — one fetch each, both already in Startup** |
| **Starvation caused by transport becomes structurally impossible** | **`state-check` and `coordination.py` change where they read** |
| ⚡ **[D-142](../DECISION_REGISTER.md) ⑨ becomes true rather than half-true** | ⚠️ **A lane on a stale `coordination` fetch reads stale eligibility** — **the same failure mode as a stale `integration` fetch, and Startup already fetches both** |
| **QE's authority is untouched — it never wanted this file** | ⛔ **One migration, and every historical reference to `docs/BACKLOG.md` must resolve** |

### ⚠️ Option 4 — Planning as an append-only event log, backlog as a projection

**Product Office appends facts (`released`, `sequenced`, `claimed`); every view derives.** ⚡ **Architecturally the cleanest — it is what `coordination.toml` half is already.** ⛔ **It is a build, not a change, and [§20c-2](../../CLAUDE.md)'s ordering is explicit: *architecture first · implementation second · automation third*.** **Recommended as the destination, not the next step.**

---

## 4 · ✅ Recommendation — Option 3, reached through Option 2

> ## **Adopt Option 3 as the target architecture. Take Option 2 first, as a bounded, reversible step that unblocks Lane A this cycle and *measures* whether the boundary move is warranted.**

**Why staged rather than direct:**

⚡ **Option 2 is Option 3's authority question in miniature, at one-tenth the cost.** **If Product Office writing `BACKLOG.md` to `integration` proves uneventful for a week, Option 3 is the same trust with a better boundary.** ⛔ **If it produces a conflict, a race or a stale read, that is evidence *against* Option 3 obtained for the price of one guard.**

⚠️ **And it inverts the failure this office keeps having.** **[C-435](../LANE_COORDINATION.md), [C-422](../LANE_COORDINATION.md) and B-409 were all discovered by a lane rather than by measurement.** ✅ **Option 2 makes the coupling *measurable* — every planning push becomes a timestamped event, and the interval between "Product Office published" and "a lane could claim" stops being invisible.**

### The guard that makes Option 2 safe, stated precisely

| | |
|---|---|
| **`certification-guard.py --audit-planning`** | **Refuses any commit on `integration` from Product Office that touches a path outside `docs/BACKLOG.md`** — **the same shape as `--audit-claims`, which already refuses a claim commit carrying code** |
| ⛔ **What it must never permit** | **`ACTIVE_ASSIGNMENTS.md`** — ⚡ **that is the arbitration point and a Product Office write there could overwrite a lane's claim**, which is [D-123](../DECISION_REGISTER.md)'s prohibition and a mistake this office has already made once |
| ✅ **Certification is untouched** | **`BACKLOG.md` is already a Closeout path with a test asserting it, so `--audit-main` continues to pass by paths rather than by trust** |

---

## 5 · ⚠️ Challenging my own analysis, as [D-173](../DECISION_REGISTER.md) requires

**Three ways this recommendation could be wrong:**

| | |
|---|---|
| ⚠️ **The real constraint may be QE's cadence, not the transport** | **If QE ran a cycle every fifteen minutes, none of this would matter.** ⛔ **Measured against that: QE ran 23 Closeout cycles in a day — roughly one an hour — and Lane A still idled 136 times.** ✅ **So cadence is not the binding constraint; the *dependency* is** |
| ⚠️ **Option 3 may be solving a problem that shrinks on its own** | **With one implementation lane, contention is lower than the model was designed for.** ⛔ **But the coupling is not about contention — a single lane starved by a single transport is exactly today's failure** |
| 🔴 **The strongest objection, and it is against this whole document** | ⚡ **Every architecture here moves *when* information travels. None makes Product Office notice that a lane is starved.** **B-409 fixed the metric; nothing yet acts on it.** ⛔ **An architecture that delivers a correction instantly still requires somebody to have written the correction** — **and this office has twice been told by Lane A rather than seeing it first** |

> ## ✅ **So the honest recommendation is two changes, not one.** **Option 2 now and Option 3 next fix the *transport*.** ⛔ **Neither fixes *detection*, and detection is where this office has actually failed.**

**The detection half costs almost nothing and is proposed here rather than deferred: `state-check.py` already computes the starvation condition, and Product Office runs it every cycle.** ⚡ **What is missing is that a starved lane does not make it into this office's own report as the first line.** **From this cycle it does** — **before the workflow status, before the pipeline, before anything else.**

---

## 6 · What this does not change

⛔ **Certification, promotion, `--audit-main`, the promotion-equality rule and QE's exclusive authority over `integration` for *executable* change are all untouched by every option above.** ✅ **[D-173](../DECISION_REGISTER.md)'s constraint is met: no partially-integrated class of change, and no weakening of the certification model.**

⚡ **And the planning-depth work continues in parallel, as [D-173](../DECISION_REGISTER.md) requires** — **the two are independent, and treating them as a trade-off would be the error.**
