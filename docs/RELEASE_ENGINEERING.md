# Release Engineering — the pipeline review, and the backlog it produced

> **Owned by QE.** `CLAUDE.md` governs how work moves; [`ENGINEERING_LAWS.md`](../ENGINEERING_LAWS.md) governs how it is built; **this governs how it is released.**
>
> **Two parts.** §1–§4 are a **study** of the certification pipeline — where it assumes nothing else is running, and what the evidence actually says. §5 is the **backlog**, ordered by value over cost.
>
> **Nothing here is implemented on the strength of this document.** QE picks the highest-value item when it is genuinely idle, never while a candidate is waiting. **Measure first, optimise second, never optimise blindly.**

**Reviewed against `main` at `34d8acb`, 2026-08-03.**

---

## 1 · RE-01 — challenged, corrected, and shipped

**The original finding was right about the symptom and wrong about the cause**, and the [L-1](../ENGINEERING_LAWS.md) reuse audit is what found the difference.

**What I first wrote:** *"the manifest does not preserve failed runs."*

**What the code actually does:** `store.append()` writes **every** run, pass or fail. `CertificationRun.failures` already enumerates every reason a run did not certify. **The model was never the problem** — and had I implemented before auditing, I would have built a parallel failure log beside a store that already recorded failures.

### The real cause is a circular dependency, and it is structural

```
  certification requires a clean tree   (tree_is_clean → git status --porcelain)
            ↓
  every run dirties it                  (manifest.json modified, report untracked)
            ↓
  re-running requires cleaning it       (git checkout -- certification/)
            ↓
  which deletes the failure record
```

**A passing run survives only because Closeout commits it.** A failing run has no commit to carry it, so the operator's *correct* next move erases the only evidence it happened. **The tree-clean condition and the failure record are in direct conflict by construction.**

### A second gap, entirely separate

**`append()` is called once, after every gate.** A run that hangs, is killed or crashes never reaches it. This cycle's 22-minute hang against an exited database **wrote nothing to any file** — an abort is invisible not by accident but by design.

**So "preserve failed runs" was two problems wearing one name:** completed-but-failed runs are *erased*; aborted runs are *never written*.

### The design questions, answered

| Question | Answer, and why |
|---|---|
| Preserve every failed run, or only meaningful ones? | **Every one.** "Meaningful" is a judgement made after the fact, and filtering at write time is how a dataset acquires the bias it was built to remove |
| Should attempts be first-class? | **Yes — that is the fix.** A *run* is a completed measurement; an *attempt* may never finish. Writing a `started` event before the first gate is the only way an abort can be counted at all |
| Classify environment vs repository vs operator failures? | **No.** A column of guesses is worse than none. It records **what a human needs to make that call** — which gate failed, what containers were up, which ports were held, which database was configured — and infers nothing |
| Where does it live? | **A separate, git-ignored `certification/attempts.jsonl`.** Two reasons, and the first is decisive: **git-ignored files do not appear in `--porcelain`, so the log survives the reset that erases the manifest entry.** The second is architectural — `CLAUDE.md` §2 already separates *repository truth* (which commits are certified; a customer could audit it) from *operational history* (the pipeline's account of its own behaviour). They are different data categories and should not share a file |
| Reuse or new? | **Extended.** It lives in `backend/tests/certification/` beside `store.py`, `record.py` and `conditions.py`, and reuses their shape. **No parallel tooling, no second manifest** |

### What it now answers, that nothing could before

```
  Attempts            3
    ↳ certified       1
    ↳ failed          1
    ↳ aborted         1     started, never reached a verdict
  First-pass rate     33.3%
  Completion rate     66.7%
  Failures by gate    smoke 1
```

**Against the manifest's `100% (21 of 21)` for the same cycle.** The KPI block now carries both, with the success rate explicitly pointing at the stability panel — because deleting the old metric would lose a true statement about certification, and leaving it alone was leaving a false impression of release health.

> **`make kpi` prints `no attempts recorded yet` until the next `make certify`.** The log starts empty and says so, rather than printing a confident zero. **RE-01 buys the ability to measure; it does not retroactively measure.**

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
| ~~**RE-01**~~ | ~~Preserve failed certification runs~~ | **✅ Shipped 2026-08-03.** Challenged first, and the challenge changed the design — see §1. `certification/attempts.jsonl`, git-ignored so it survives the reset; `started` written before the first gate so aborts are countable | **S** | Survivorship bias in every stability figure |
| ~~**RE-02**~~ | ~~A lock around `make certify`~~ → **an environment lease** | **✅ Shipped 2026-08-03, and the challenge changed it — see §7.** A certify-lock would have permitted every command that actually caused the incident | **S** | A-2 · A-4 · A-6 · A-7 |
| **RE-03** | **`certify` creates and drops its own database** | A-3 · [B-022](BUGS.md). Removes the last hand-typed correctness requirement in the pipeline | **M** | A-3, permanently |
| ~~**RE-04**~~ | ~~A connection preflight before `pytest`~~ | **✅ Shipped 2026-08-03**, by extending `release-preflight.py` rather than adding a checker — an **integration** gap, not a missing capability | **S** | A-5 |
| **RE-05** | **Per-run compose project name** | **Deprioritised 2026-08-03.** The lease *serialises* what this would *parallelise*, and A-2 is prevented today. **Its remaining value is parallel certification** — a Stage 4 concern, not a now one | **S** | A-2, in parallel |
| ~~**RE-06**~~ | ~~Certification stability metrics in `make kpi`~~ | **✅ Shipped with RE-01**, because a measurement nobody reads is not a measurement | **S** | — |
| **RE-07** | **Resolve the duplicated suite run** | ~250s per cycle — **but it may be load-bearing for ADR-0032** | **S**, after a ruling | — |
| **RE-08** | **Flaky-test detection** — record per-test durations, flag non-determinism | No evidence of flakiness yet. **Listed so it is not forgotten, not because it is due** | **M** | — |
| **RE-09** | **Ephemeral certification environments** | The shape a multi-lane, multi-branch future needs | **L** | A-1, A-2, A-4 together |

**RE-01 and RE-06 shipped 2026-08-03. RE-02 through RE-05 are all small, and each has an incident behind it from this week.** That is deliberate: **the cheap preventions come first, and the large redesign waits for evidence it is needed.**

> **What is not on this backlog, and why.** No item optimises certification *time*: §3 shows time is not the problem. No item weakens a gate, shortens the sequence, or reduces coverage — **the pipeline must become faster because it is engineered better, never because it checks less.**

---

## 6 · How this document is maintained

**Reviewed by QE at Closeout when the cycle produced a pipeline incident**, and otherwise when an item is picked up. **An item is deleted when it ships**, and the evidence for it moves to the commit that closed it — this is a backlog, not a record.

**New items require the same standard as [`ENGINEERING_LAWS.md`](../ENGINEERING_LAWS.md):** an incident that already happened, or a specific assumption in current code with a named failure mode. **A speculative improvement is not a backlog item.**

---

## 7 · RE-02, RE-04, RE-05 — challenged before building

**The same process RE-01 proved.** All three were re-derived from the incidents rather than implemented as written, and **two of the three changed.**

### RE-02 was wrong as written, and the test that proves it now exists

**Written as:** *"a lock around `make certify` — refuse a second run."*

**Challenged by replaying the incident.** Cycle 25's contamination came from `make smoke` and `make down` running **beside** a certification. **No second `certify` was ever started.** A certify-lock would have permitted every command that actually did the damage.

**So the lease belongs to the environment, not to a command.** One production stack, one pair of review ports, one test database — and until now **nothing knew who was using them.** In the taxonomy: not *missing capability* but **missing ownership**.

**It is prevention rather than detection.** The preflight *reports* a held port and asks the operator to look; the lease *refuses to start*.

**Two properties that keep it from becoming a new failure mode:**

| | |
|---|---|
| **A dead holder is reclaimed silently** | `pkill` on a hung run is legitimate recovery — it happened **twice** in cycle 25. A lease surviving it would turn one stuck run into a permanently stuck repository |
| **It is re-entrant** | `certify` shells out to `smoke.sh` inside its own lease. Without inheritance the nested acquisition would block on its own parent forever |

### RE-04 was an integration gap, not a missing capability

`release-preflight.py` **already existed** and already checked prerequisites. Nothing had taught it about the one service the suite cannot run without. **Extended, not replaced** — and `make dr` and `make certify` now depend on it, which they did not: only `make smoke` was preflighted, which is why `make dr` once failed with *"API did not become ready"* against a stack that was never up.

### RE-05 was deprioritised on the evidence

A per-run compose project name would let two smoke runs coexist. **The lease makes them not need to** — it serialises where RE-05 parallelises, and A-2 is prevented today. **Its remaining value is parallel certification**, which belongs to Stage 4 below, not to now.

---

## 8 · Where this is going — visibility, not a plan

**Seven stages. Nothing here is scheduled**; its purpose is to tell whether today's improvements build toward it or away from it.

| Stage | | Today |
|---|---|---|
| **1** | **Reliable certification** | **Substantially here.** Gates deterministic, promotion commit-bound, environment leased |
| **2** | **Reliable measurement** | **Started.** RE-01 made attempts countable; the stability panel has one data point |
| **3** | **Reliable environments** | **Not started.** The stack is shared and long-lived; RE-03 (disposable database) is the first step |
| **4** | **Parallel certification** | Needs Stage 3 and RE-05. **The lease is deliberately the opposite of this** — serialising was the correct answer for one machine and is the wrong one for several |
| **5** | **Distributed certification** | Far. Would need the attempt log to be shared rather than git-ignored — **the one design decision here that a future stage reverses** |
| **6** | **Predictive certification** | Needs a year of stability data |
| **7** | **Self-healing certification** | Needs 3–6 |

> **The honest read: RE-01 and RE-02 build toward Stages 1 and 2 and are neutral on 3–7, except that the git-ignored attempt log is a decision Stage 5 would revisit.** That is recorded rather than avoided — a local log answers today's question, and a distributed one is not justified by a repository with one machine.

### Stability has dimensions, and today they are reported as one

**Identified, not yet implemented.** The single *"pipeline stability"* figure currently mixes at least six things:

| Dimension | Would answer | Today |
|---|---|---|
| **Repository stability** | Does the code pass its own gates? | The only one measured cleanly |
| **Environment stability** | Was the stack there and healthy? | The attempt log's `containers` and `ports_held` are the raw signal |
| **Infrastructure stability** | Docker, disk, the machine | Not captured |
| **Operator stability** | Did a human contaminate the run? | **Cycle 25 was entirely this**, and nothing distinguishes it |
| **Tool stability** | Did a gate misreport? | [B-101](BUGS.md) was this — a KPI counting nine rows twice |
| **Certification stability** | Did the process complete? | RE-01's `completion_rate` |

**Separating them is the natural next measurement step**, and it is deliberately not attempted yet: the attempt log has one entry, and classifying a dimension from a single data point is exactly the anecdote-driven work §1 exists to prevent.

## 9 · Configuration loading — investigated 2026-08-03, and the finding is narrower than the brief

**Assignment:** *"one canonical environment loading mechanism across the repository — nobody reads `.env`, nobody calls dotenv, nobody assembles configuration."*

**The investigation says most of that already exists**, and naming what does not is worth more than a redesign that would rewrite the half that is correct.

### Three questions were being asked as one

| | | Today |
|---|---|---|
| **Who *reads* a variable?** | Which code touches `os.environ` / `process.env` | **Backend: solved.** Frontend: not |
| **Who *populates* the process?** | What puts values into the environment before an entrypoint starts | **Four mechanisms, and one entrypoint has none** |
| **Who *validates* it?** | Where a missing or wrong value is refused | Backend at construction · frontend at use |

**These have different answers and different fixes.** Treating them as one problem is how a redesign starts.

### The backend already has the loader

Every `os.environ` in `backend/` outside tests:

| Where | What | Verdict |
|---|---|---|
| `signora_platform/settings.py` · `modules/ai_platform/infrastructure/settings.py` | *Docstrings saying never to do it* | The rule, not a violation |
| `apps/worker/pools.py` | A pool **name** | Legitimate — process identity, not configuration |
| `apps/migrate/main.py` | **Sets** `SIGNORA_LOGGING_CONFIGURED` | A flag to a child, not a read |
| `migrations/env.py` | `SIGNORA_DATABASE_URL` | **Alembic's own contract**, outside the application. It is why [B-106](BUGS.md) happened |

**There is no scattered reading to consolidate.** Typed `Settings`, `env_prefix="SIGNORA_"`, `env_file=".env"`, constructed at the composition root, injected inward — `CLAUDE.md` §6 as written. **The pipeline the assignment describes is the one the backend runs.**

### The frontend is where the divergence is

`process.env` outside tests, by file:

```
lib/auth/config.ts          11 reads — centralised, typed, validated at use (post-B-104)
lib/api/client.ts            1 read  — SIGNORA_API_URL, deliberately decoupled
lib/auth/server.ts           1 read  — NODE_ENV
app/api/integrations/*       4 reads — SIGNORA_INTEGRATIONS_STATE_SECRET, provider credentials
playwright.config.ts         2 reads — a config file, correctly
```

**Sixteen reads across five files, and no typed object.** `loadAuthConfig()` is close to one for the auth surface and covers none of the rest. **This is the real gap**, and it is a frontend-foundation change (🔒 §20c) rather than QE's.

### The populating gap is B-105, and it is separate

| Entrypoint | What populates its environment |
|---|---|
| `uvicorn` / worker / `pytest` | `pydantic-settings` reads `backend/.env` |
| `next dev` · `next build` | Next's own loader reads `frontend/.env.local` |
| `alembic` | **Whatever the shell holds** — the B-106 mechanism |
| **`tsx` scripts** (`auth:migrate`, `demo:users`) | **Nothing.** This is [B-105](BUGS.md) |
| `make` targets | Nothing, except values a recipe passes explicitly |

**Four mechanisms and one hole.** The hole is not that there are four — a Python tier and a Node tier having their own loaders is correct, and unifying them would mean one tier reading the other's file. **The hole is that `tsx` has none**, so a script run from `make` sees a different environment from the application it configures.

### Recommendation — three items, none of them a redesign

| | | Owner | Size |
|---|---|---|---|
| **RE-10** | **`tsx` scripts load `frontend/.env.local`** — Node's `--env-file`, or the loader Next already uses. Closes B-105, and deletes `infra/review.py`'s `_dotenv` in the same change | Frontend foundation (🔒) | **S** |
| **RE-11** | **A typed frontend configuration object**, the shape `loadAuthConfig()` already has, covering the sixteen reads. Nothing outside it touches `process.env` | Frontend foundation (🔒) | **M** |
| **RE-12** | **Alembic receives its URL rather than reading it** — the last entrypoint whose configuration is ambient. B-106 fixed the *test*; the *contract* is unchanged | `apps/migrate` | **S** |

> **What is deliberately not recommended: one loader for both tiers.** They are separate runtimes with separate secrets — the private signing key belongs to Next and must never reach Python ([ADR-0026](architecture/adr/0026-jwt-boundary-architecture.md)). A shared loader would be a shared reachability surface for exactly the values the boundary exists to separate. **Two loaders, each canonical within its tier**, is the correct target, and the backend is already there.

---

## 10 · Performance work — what belongs now, and what belongs to Production Readiness

**Ratified 2026-08-03 by the product owner, and binding on every lane.** Recorded here rather than in `CLAUDE.md` because it is a *guideline about sequencing*, not a rule about behaviour — but it is the answer any lane should get when it wonders whether to benchmark something.

> **Performance is not deferred. Performance *engineering* is.** The distinction is which numbers are meaningful today.

### The two categories

| **Development-time performance — fix now, always** | **Production performance — Production Readiness milestone** |
|---|---|
| N+1 queries | Load testing · concurrency testing |
| Unbounded fetches | Autoscaling validation · ECS/EKS sizing |
| Accidental quadratic algorithms | Redis and PostgreSQL tuning |
| Infinite loops · memory leaks | ALB/NLB tuning · CDN behaviour |
| Browser freezes | Cache tuning · distributed load generation |
| Extremely slow queries | Response-time SLAs |
| **Catastrophic regressions** | Endurance testing · chaos testing |

**The left column is already `CLAUDE.md` §14**, and nothing about it relaxes: *"obvious inefficiency is a defect at write time, not a future task."* A lane that ships an N+1 has shipped a defect, today, whatever milestone it is.

### Why the right column would produce meaningless numbers today

**Not because performance does not matter. Because the measurement would not describe anything that will exist:**

| | |
|---|---|
| **The infrastructure is temporary** | Everything runs on one laptop. [ADR-0022](architecture/adr/0022-devops-infrastructure-and-deployment-topology.md)'s topology is not provisioned until M14.5, so a latency figure measured now is a figure about a workstation |
| **The architecture is incomplete** | Modules are still being built. A benchmark of a pipeline missing stages measures a different pipeline |
| **The features are still changing** | A tuned query in a module whose schema changes next month is tuning that must be redone |
| **The data volumes are artificial** | Twelve seeded accounts. Nothing about their behaviour predicts ten thousand |
| **The deployment is local** | No load balancer, no CDN, no autoscaler, no network between tiers |

**`12-scalability.md` already says this**, and this section is its operational reading: scaling work is justified by *evidence-based triggers*, and **a trigger requires production**. Benchmarking before there is a production to trigger on inverts the rule — it produces a number in search of a decision.

### What QE keeps doing meanwhile

**Regression prevention is not performance engineering**, and QE continues it:

- **Certification records `make smoke`'s duration and slowest stage** every cycle. That is how the 104s–4830s variance was root-caused to memory pressure rather than to the repository.
- **`release-preflight` reports machine pressure** before a gate runs, so a slow run is diagnosable instead of mysterious.
- **A catastrophic regression is a Blocking Quality Defect** whenever it appears, at any milestone. *"Performance is deferred"* is never a defence for a change that made something ten times slower.

### What this means for a lane

**Write efficient code. Do not benchmark it.**

If a lane believes it has found a genuine performance problem, the test is the one `CLAUDE.md` §14 already sets: **is it obviously wrong, or is it unmeasured?** Obviously wrong is a defect to fix now. Unmeasured is a Production Readiness concern, and the correct action is a [`BACKLOG.md`](BACKLOG.md) note — not a benchmark, not a tuning slice, and not an optimisation nobody can show is needed.

> **Endurance and load suites written today are the clearest case.** They are real engineering effort, they will run against infrastructure that does not exist yet, and their numbers will be replaced entirely by the first run in AWS. **The work is not wrong; the timing is** — and the same suite written after M14.5 measures the system customers will actually use.

### When this is revisited

**At M14.5**, when the target AWS environment exists. At that point the right column becomes a milestone with its own acceptance criteria, and this section is replaced by it rather than amended.

---
