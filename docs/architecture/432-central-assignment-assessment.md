# 432 — Central task assignment: impact assessment and stress test

> **Lane C — Product Office, 2026-08-05.** **PREPARED — READY FOR PRODUCT OWNER. Nothing is modified.**
>
> Prepared on the directive: *"Do not assume it is correct because it came from the Product Owner. Challenge it… Do not simply accept the proposal. Stress-test it."*
>
> **This assessment recommends against the proposal as stated, and proposes a mechanism that meets every one of its success criteria without the cost.**

## 1 · What is actually being proposed, separated from what it is for

**The directive lists ten success criteria. Nine describe outcomes; one describes a mechanism.**

| Criterion | Kind |
|---|---|
| No implementation lane races · no lane starvation · no duplicate ownership · continuous execution · clear accountability · Product Office stays governance · lanes keep technical preparation · QE unchanged · reuse and governance intact | **Outcomes** |
| **"No autonomous task claiming"** | ⚠️ **A mechanism** |

> **That one line is not a success criterion. It is the proposal, written into the list of things the proposal must achieve.**
>
> **Stated as an outcome it would read: *no lane works on something other than the highest-value work available to it*.** That is a real and worthwhile goal — **and it does not require a human in the assignment path.**

**The distinction matters because the other nine can be checked against the repository today.**

## 2 · The repository has run this experiment twice, and reversed it twice

**This is the decisive evidence, and both reversals are the product owner's own.**

### 2a · 2026-08-02 — scheduling was moved *out* of QE

> **`CLAUDE.md` §20e, ratified by the product owner:**
>
> *"**The bottleneck is arithmetic, not authority.** With QE scheduling, an idle lane waits for the one session that is busy certifying — so **every additional lane increases the wait rather than the throughput**, which is the opposite of what lanes exist to do."*

**The argument does not depend on which lane holds scheduling.** Substitute *Lane C* for *QE* and *busy reviewing a package* for *busy certifying*, and every word still holds.

### 2b · 2026-08-04 — preparation was moved *out* of Lane C

**Two days ago, D-060:**

> *"The issue is not planning quality. **The issue is centralized preparation.**"*

**Measured then:** 12 of 32 task rows carried Lane C's `TASK-4xx` block — **37.5% of the queue authored by the one lane that may not implement any of it** — while `integration` stood still for eleven polls.

> **Centralizing assignment two days after decentralizing preparation puts the same bottleneck back into the same lane, in a different dimension.** **A queue with one assigner has one assigner's throughput, however many lanes consume it** — which is D-060's own sentence with one word changed.

## 3 · The latency, measured rather than argued

**This is the number the proposal turns on.**

| Path | Latency | Evidence |
|---|---|---|
| **Today — a lane claims** | **Seconds.** Commit, push, pull, confirm | The Task Claim Protocol is atomic because a push is. **Lane A claimed TASK-405 within minutes of cycle 53 promoting** |
| **Proposed — Lane C assigns** | ⚠️ **Hours at best. Days observed** | **Lane A idled several reporting cycles** waiting on Lane C artifacts (D-060's premise). **Lane C's own work sat 8 commits unpromoted** across this week |

> **Lane C is a session, not a service.** It is not resident, it is not polled, and it has no queue that fires on an event. **Every assignment would wait for Lane C to next be running and next be looking** — and the repository has already measured what that costs, because it is the exact failure D-060 was written to end.

## 4 · Impact assessment — the nine categories

### 4.1 Workflows that would change

| Workflow | Change |
|---|---|
| **The Task Claim Protocol** — all ten steps | **Steps 3, 4, 8 and 9 become meaningless.** Selecting, confirming you were first, and abandoning a lost race all presuppose the lane chooses |
| **Continuous execution** | **A lane setting `IN VALIDATION` currently claims the next task immediately.** It would instead wait for Lane C — **the idle state the rule exists to forbid** |
| **Startup** (step 7) | *"If you are `AVAILABLE`, run the Task Claim Protocol"* becomes *wait* |
| **Skip-with-a-reason** | Disappears. A lane cannot skip what it was handed |
| **Lane C's day** | Gains a **continuous, unbounded, interrupt-driven** responsibility |

### 4.2 Documents affected — **12 measured**

`CLAUDE.md` **[M]** · `README.md` · `docs/ACTIVE_ASSIGNMENTS.md` · `docs/BACKLOG.md` · `docs/BUGS.md` · `docs/LANE_COORDINATION.md` · `docs/PRODUCT_OFFICE.md` · `docs/QUALITY_ENGINEERING.md` · `docs/DECISION_REGISTER.md` · `419` · `423` · `428`

**Inside `CLAUDE.md` §20e alone**: *Nobody assigns; lanes pull* · *The Task Claim Protocol* · *Continuous execution* · *Execution ownership ends at `IN VALIDATION`* · *Shared files have one owner* · *Distributed Product Development*.

### 4.3 Automations affected

| Automation | Effect |
|---|---|
| **`certification-guard.py --audit-claims`** | **`CLAIM_PATHS` and the whole claim-commit exception exist to make a lane's push safe.** If lanes stop pushing claims, this guard protects nothing |
| **`state-check.py`** | Board-vs-backlog reconciliation assumes a lane wrote its own row |
| **`repository-dashboard.py`** | `_owners()` cross-checks declared owner against **rowed** lane. **The collision check works because a lane rows itself** |
| **`kpi.py`** | Reads claim throughput |
| **`backend/tests/test_claim_agreement.py`** | **Asserts the two registers name the same holder.** Its premise changes |

### 4.4 Polling mechanisms affected

**Every implementation lane polls `origin/integration` for `READY` work.** Under central assignment they would poll **for an assignment that only appears when Lane C is running** — **a poll against a non-resident producer**, which is precisely the shape that idled Lane A for days.

### 4.5 Dashboards affected

`repository-dashboard.py` §2 (execution) · §4 (lane) · §5 (task assignment) · §9 (review queue) · §11 (bottleneck) · the Portfolio and UI dashboards · `PROJECT_STATUS.md` · `IMPLEMENTATION_STATUS.md`.

> **§11 would need a new row: *assignment bottleneck*.** **A dashboard that has to measure the coordinator is evidence about the coordinator.**

### 4.6 Lifecycle states affected

| State | Effect |
|---|---|
| `READY` | Means *"claimable"*. Would mean *"assignable"* — **and a lane could no longer act on it** |
| `CLAIMED` | **Set by the lane today. Would be set by Lane C** — and the word becomes wrong |
| `AVAILABLE` | Becomes **"waiting for Lane C"**, which is `WAITING`, a state that already exists |
| `PREPARING` · `UNDER REVIEW` · `REVISION REQUESTED` | **Unaffected** — D-060's states are about packages, not allocation |

### 4.7 Rules that become obsolete

**`Nobody assigns; lanes pull`** · **the Task Claim Protocol's race arbitration** · **`Claim from the top… say why in its backlog note`** · **`A lane claims; nobody assigns`** · **the claim-commit exception to `integration`**.

### 4.8 Rules that *conflict* — and these are the finding

| Rule | Conflict |
|---|---|
| **§20e — *the bottleneck is arithmetic, not authority*** | ⛔ **Direct contradiction.** The proposal reinstates central scheduling in a different lane |
| **§20e — *Continuous execution*** | ⛔ *"A lane never idles waiting"* — it would now wait for Lane C |
| **§20e — *Lane C must never become the owner of roadmap priority*** | ⚠️ **Assignment is priority applied.** A lane choosing between two `READY` tasks is executing the queue; **a coordinator choosing is setting it** |
| **D-060 — *do not centrally prepare*** | ⚠️ Same lane, same argument, two days later |
| **§20e — *governance is stable; it evolves reactively*** | ⚠️ **Requires a real defect, or two lanes hitting the same friction.** **§5 tests whether one exists** |

### 4.9 What continues unchanged

**QE's seven lifecycle stages · certification binding to an immutable commit · the Security Invariants · promotion equality · the Change Budget · identifier blocks · module ownership and `modules.toml` · one assignee per module · the Slice Handoff · Repository Closeout · §20c-2 · D-060's preparation model · every architecture principle.**

## 5 · Is there a defect to fix? — four of six criteria are already met

**Governance changes on evidence (§20e). So each criterion is checked against the repository rather than assumed.**

| Criterion | Status | Evidence |
|---|---|---|
| **No races** | ✅ **MET** | The Task Claim Protocol is atomic. **Zero duplicate implementations recorded** |
| **No duplicate ownership** | ✅ **MET, and proven this cycle** | `modules.toml` + the collision check. **Lane A claimed TASK-405 in a module it owns: 0 collisions [M]** |
| **Clear accountability** | ✅ **MET** | One registry, one assignee, `_owners()` cross-checks declared against rowed |
| **Continuous execution** | ✅ **MET** | Lane A claimed **within minutes** of cycle 53 promoting |
| **No lane starvation** | ⚠️ **UNMEASURED** | Real risk; no metric exists. **See §7 phase 3** |
| **No autonomous claiming** | ❌ **Not met — and it is the proposal, not a criterion** | §1 |

### The one real defect, and it is small

> **Lane A held TASK-400 at `CHANGES REQUESTED`, claimed TASK-405, and recorded no reason.** §20e requires *"say why in its backlog note and take the next."*

**That is a genuine gap and it is worth closing.** **It is one guard rule, not a delivery-model change.** **Nothing about it is fixed by adding a human to the path** — a coordinator who forgets to record a reason produces the same silent skip, one round-trip later.

## 6 · Stress test — the fourteen dimensions

| | Central assignment |
|---|---|
| **Scalability** | ❌ **Worst dimension.** Assignment load is **O(lanes × slices)** and the coordinator is **one non-resident session.** **Every lane added makes every lane wait longer** — §20e's arithmetic |
| **Long-term maintainability** | ⚠️ Fewer moving parts in the protocol, **more in the coordinator's head.** The protocol is written down; a coordinator's judgement is not |
| **Governance complexity** | ❌ **Increases.** Obsoletes 5 rules, conflicts with 5, rewrites 12 documents — **to replace a mechanism that is 10 steps and already enforced by a machine** |
| **Implementation complexity** | ⚠️ Low to build, **high to operate** |
| **Workload balancing** | ✅ **Genuinely better.** A coordinator sees all lanes; a lane sees itself |
| **Module ownership** | ➖ Unchanged — `modules.toml` already decides this |
| **Dependency handling** | ✅ **Better.** Cross-module sequencing is visible centrally |
| **Review process** | ⚠️ **Compounds.** Lane C would hold **both** the review queue and the assignment queue — **two queues, one session** |
| **Synchronization** | ❌ **Worse, and this is measured.** An assignment is only real when it reaches `integration`. **Lane A idled for days on exactly that** |
| **Backlog health** | ✅ Better — one hand keeps status honest |
| **Bottleneck risk** | 🔴 **High. The central finding** |
| **Starvation risk** | ⚠️ **Shifts, does not vanish.** Today a lane starves when the queue is empty; then it starves **when Lane C is busy** — and the second is invisible |
| **Hidden queues** | 🔴 **Creates one.** *"Lane C intends to assign X next"* exists nowhere in the repository. **A queue in one session's head is the one no dashboard can measure** |
| **Central coordination** | 🔴 **This is the risk the directive asked about, and the answer is yes** |

## 7 · Recommendation — **Constrained Pull**

> **Keep the pull. Constrain what may be pulled, and enforce it with a machine rather than a session.**

**A lane still claims atomically and waits for nobody. What changes is that eligibility becomes *computed* rather than *chosen*.**

**A claim is valid only if all four hold, and `certification-guard.py` refuses it otherwise:**

| | Rule | Already exists? |
|---|---|---|
| **1** | The task's **module is the claiming lane's** in `modules.toml` | **Data exists; not enforced at claim time** |
| **2** | It is the **highest-priority eligible task** for that lane | Backlog order exists |
| **3** | **Any skipped higher task carries a recorded reason** in the same commit | Required in prose; **not enforced** |
| **4** | The lane holds **no returned slice**, or records why it cannot be progressed | Required in prose; **not enforced** |

**This delivers "no autonomous claiming" in the sense that matters — no lane picks freely — with zero coordinator latency.**

| Success criterion | Constrained Pull |
|---|---|
| No races | ✅ Atomic push, unchanged |
| No starvation | ✅ Rule 1 makes an empty eligible set **visible and measurable** |
| No duplicate ownership | ✅ Rule 1 enforces it **at claim time**, earlier than today |
| **No autonomous claiming** | ✅ **A lane cannot choose. It takes what the rules compute** |
| Continuous execution | ✅ **Preserved — the property central assignment loses** |
| Clear accountability | ✅ Strengthened: a refused claim names the rule |
| Product Office stays governance | ✅ **Lane C owns order and ownership; it does not sit in the path** |
| Lanes keep technical preparation | ✅ Unchanged |
| QE unchanged | ✅ Unchanged |
| Reuse and principles intact | ✅ **Extends `--audit-claims`; writes no new mechanism** |

**On the directive's suggested mechanisms:** **automatic assignment rules** — ✅ this is that · **module-local scheduling** — ✅ already exists via `modules.toml` · **priority queues** — ✅ the backlog order already is one · **queue ownership** — ✅ already the product owner's · **assignment windows** — ⛔ **rejected: latency is the defect, and a window institutionalises it.**

## 8 · Migration — four phases, each independently valuable

**None requires the next. Any phase can be the last.**

| | Phase | Delivers | Size |
|---|---|---|---|
| **0** | **Enforce the skip note.** `--audit-claims` refuses a claim that skips a higher eligible task with no recorded reason | **Closes the one real observed defect** | **One guard rule** |
| **1** | **Make eligibility computable.** `make next` prints what this lane may claim, and why each other task is ineligible | **Removes lane judgement without removing lane speed** | Small |
| **2** | **Enforce eligibility.** The guard refuses out-of-module and out-of-order claims | **"No autonomous claiming", achieved** | Small |
| **3** | **Measure starvation.** Eligible-queue depth per lane, in the dashboard | **The unmeasured criterion becomes measured** | Small |
| **4** | ⏸️ **Revisit central assignment — only if phases 0–3 leave a criterion unmet** | **Decided on evidence, not on prediction** | — |

> **Phase 0 is the whole of the observed problem.** If phases 0–3 satisfy every criterion — and §7 argues they do — **phase 4 never runs, and the repository keeps the property that a lane never waits for a person.**

## 9 · If the product owner still prefers central assignment

**It should be adopted with these three mitigations, because they address the measured failure modes rather than the theoretical ones:**

**① Lane C publishes the assignment queue as a file** — a coordinator's intention that exists only in a session is the hidden queue §6 names. **② A lane with no assignment for one full reporting cycle claims autonomously and records that it did** — a starvation escape hatch, because the alternative is silent idling. **③ Assignment is recorded on `integration` directly**, under the existing claim exception, or **the assignment does not exist** (§20e).

**Without all three, the model reproduces the two failures this repository has already paid for.**

## 10 · Recommendation

| | |
|---|---|
| **The proposal as stated** | ⛔ **Do not adopt.** It reinstates a bottleneck the product owner removed on 2026-08-02 and again on 2026-08-04 |
| **The concern behind it** | ✅ **Valid and worth acting on.** Lane A skipped a returned slice without recording why |
| **Recommended model** | ✅ **Constrained Pull** — meets **all ten** criteria, obsoletes no rule, conflicts with none |
| **Start with** | **Phase 0. One guard rule, and it closes the observed defect this week** |
| **Treat as a controlled migration** | ✅ **Agreed, and that is why the phases are independent** |

> **The honest summary: the repository already has the mechanism the directive wants, and it is nearly enforced.** **What it lacks is not a coordinator — it is four checks a machine can run in the time a push takes.** **The proposal would add a person where a rule is missing**, and this repository has twice measured what that costs.
