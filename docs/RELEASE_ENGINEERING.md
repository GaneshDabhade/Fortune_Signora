# Release Engineering — the pipeline review, and the backlog it produced

> **Owned by QE.** `CLAUDE.md` governs how work moves; [`ENGINEERING_LAWS.md`](../ENGINEERING_LAWS.md) governs how it is built; **this governs how it is released.**
>
> **Two parts.** §1–§4 are a **study** of the certification pipeline — where it assumes nothing else is running, and what the evidence actually says. §5 is the **backlog**, ordered by value over cost.
>
> **Nothing here is implemented on the strength of this document.** QE picks the highest-value item when it is genuinely idle, never while a candidate is waiting. **Measure first, optimise second, never optimise blindly.**

**Reviewed against `main` at `34d8acb`, 2026-08-03.**

---

## 1 · The finding that changes how everything below is measured

> **The certification manifest cannot measure certification stability, because failed runs do not survive.**

`make certify` writes a record for every run, pass or fail. **But a failed run leaves the working tree dirty**, and the operator's next move is `git checkout -- certification/manifest.json` — which is the *correct* move, because a contaminated measurement must not become repository truth.

**The consequence is structural:**

```
  runs recorded          21
  gate failures recorded  0
  reruns recorded         0
```

**That 100% is not a measurement. It is an artefact of the discard.** This cycle alone produced **two** failed runs and **three** attempts at one commit; the manifest retains none of it. The KPI block already carries a caveat that the success rate *"excludes candidates rejected at validation"* — this is a second, larger exclusion nobody had named.

**Every stability question the review was asked — rerun frequency, environment failures, false failures, recovery time — is unanswerable from the current data.** That makes **RE-01** the first item in the backlog: not because it is the biggest problem, but because **without it every other item below is prioritised on anecdote.**

---

## 2 · Where the pipeline assumes nothing else is running

**Seven places. Each is a real assumption in current code, with the incident it has already caused or would cause.**

| # | Assumption | Where | Evidence |
|---|---|---|---|
| **A-1** | **Ports 3000/8000 are mine** | `smoke.sh:29-30` binds them absolutely | Caused the review-mode collision that produced `release-preflight.py`. **Now detected, still not prevented** |
| **A-2** | **The compose project is mine** | `smoke.sh:97,601` — `down -v --remove-orphans` on a fixed project name | A second smoke run **destroys the first's stack mid-test**. This is what produced *"7 stages in 38s"* this cycle |
| **A-3** | **The test database is whatever the operator exported** | `conftest.py:53-58` defaults to the shared `signora` | **[B-022](BUGS.md).** Certification measured 2238/94.34% against the wrong database and recorded it as fact. **Still unfixed structurally** — it works because QE types three variables correctly every time |
| **A-4** | **Only one certification runs at a time** | Nothing anywhere enforces it | **This cycle.** Two runs wrote two records for one commit; the second reported `pytest 134 passed` because the first truncated its database |
| **A-5** | **The dev stack is up** | `pytest` connects to `localhost:5432` and blocks | **This cycle.** `pytest` hung **22 minutes** against an exited container, with no timeout and no diagnostic |
| **A-6** | **A failed run cleans up after itself** | `smoke.sh` tears down on failure, but a *killed* run does not | A `pkill`'d certify leaves the prod stack holding 3000/8000 — which the preflight then reports, correctly, as a block |
| **A-7** | **Nobody edits the tree mid-run** | Nothing enforces it | **158 phantom test failures**, and `QUALITY_ENGINEERING.md` §10a written in response. **The rule was too narrow** — it says *edit the tree*; this cycle's damage came from running competing *gates* |

> **A-2, A-4 and A-5 are one root cause wearing three coats: the pipeline has exactly one of everything, and no way to notice a second actor.** Every workaround so far has been a *detector* — the preflight, §10a, the KPI caveat. **Detection is where this repository has been living, and the backlog below is about moving to prevention.**

---

## 3 · What the timing data actually says

**Measured across 21 recorded runs.**

| | |
|---|---|
| **smoke duration** | **min 104s · median 122s · max 4830s** |
| **The 4830s outlier** | One run, `2e70b0e`. **Forty times the median** — and it is a single point, so it is an *observation*, not a trend |
| **Full certification** | ~6–10 min typical; this cycle's clean run was **145s of smoke** inside it |

**The suite runs twice per cycle** — once in QE validation, once inside `make certify` — costing roughly **250 duplicated seconds**. I have held this observation for three cycles without proposing it, and the reason is unchanged: **the duplication may be load-bearing.** ADR-0032 requires a certification record to be self-contained, and a `certify` that trusted an earlier external run would record a result it did not produce. **Removing it needs a ruling, not a refactor** — it is RE-07, and it is deliberately low in the order.

> **The honest summary of the timing data: certification is not slow.** 6–10 minutes for 2589 tests, 360 invariants, a full production stack build and a scenario run is respectable. **Time is not where the pain is — reliability is.** Three attempts were needed for this cycle, and none of the failures were the software's.

---

## 4 · Environment isolation — the questions, and what the evidence supports

**Asked, not answered. Implementing any of these without the RE-01 data would be optimising blind.**

| Question | What the evidence currently says |
|---|---|
| Should smoke and certification share containers? | **They already do, and A-2 is the cost.** A dynamic compose project name is a small change with a clear incident behind it |
| Should every certification get its own namespace? | **Probably, eventually.** It subsumes A-1, A-2 and A-4 at once. It is also the largest change here |
| Should ports be allocated dynamically? | **Not yet.** `RUNNING.md`'s fixed allocation is what makes a lane's environment predictable, and the preflight already names collisions |
| Should temporary databases be disposable? | **This is A-3, and it is the highest-value isolation item.** A certification that creates and drops its own database cannot measure the wrong one |
| Should locks exist around shared resources? | **Yes, narrowly.** A lock file around `certify` prevents A-4 for a few lines. **A lock is a detector with teeth, not true isolation** — worth doing because it is cheap, not because it is the answer |
| Should certification run in ephemeral environments? | **The right long-term shape**, and it is what a future with parallel lanes, nightly runs and hotfix branches needs. **Not justified by today's evidence** |

---

## 5 · The Release Engineering Backlog

**Ordered by value over cost.** QE picks the top item **only when genuinely idle** — never while a candidate waits, and never mid-cycle.

| Id | Item | Why | Cost | Prevents |
|---|---|---|---|---|
| **RE-01** | **Preserve failed certification runs** — a `failures` list the reset does not touch, or a separate append-only log | **Every other item here is currently prioritised on anecdote.** The manifest's 100% is an artefact of the discard | **S** | Nothing directly. **Enables everything** |
| **RE-02** | **A lock around `make certify`** — refuse a second run, naming the first's PID and start time | A-4, which cost three attempts this cycle | **S** | A-4 |
| **RE-03** | **`certify` creates and drops its own database** | A-3 · [B-022](BUGS.md). Removes the last hand-typed correctness requirement in the pipeline | **M** | A-3, permanently |
| **RE-04** | **A connection preflight before `pytest`** — fail in 2s with *"postgres is not running"* | A-5. A 22-minute hang that should have been a two-second message | **S** | A-5 |
| **RE-05** | **Per-run compose project name** | A-2. Two smoke runs stop destroying each other | **S** | A-2 |
| **RE-06** | **Certification stability metrics in `make kpi`**, once RE-01 exists | Answers the questions this review could not | **S** | — |
| **RE-07** | **Resolve the duplicated suite run** | ~250s per cycle — **but it may be load-bearing for ADR-0032** | **S**, after a ruling | — |
| **RE-08** | **Flaky-test detection** — record per-test durations, flag non-determinism | No evidence of flakiness yet. **Listed so it is not forgotten, not because it is due** | **M** | — |
| **RE-09** | **Ephemeral certification environments** | The shape a multi-lane, multi-branch future needs | **L** | A-1, A-2, A-4 together |

**RE-01 through RE-05 are all small, and four of the five have an incident behind them from this week.** That is deliberate: **the cheap preventions come first, and the large redesign waits for evidence it is needed.**

> **What is not on this backlog, and why.** No item optimises certification *time*: §3 shows time is not the problem. No item weakens a gate, shortens the sequence, or reduces coverage — **the pipeline must become faster because it is engineered better, never because it checks less.**

---

## 6 · How this document is maintained

**Reviewed by QE at Closeout when the cycle produced a pipeline incident**, and otherwise when an item is picked up. **An item is deleted when it ships**, and the evidence for it moves to the commit that closed it — this is a backlog, not a record.

**New items require the same standard as [`ENGINEERING_LAWS.md`](../ENGINEERING_LAWS.md):** an incident that already happened, or a specific assumption in current code with a named failure mode. **A speculative improvement is not a backlog item.**
