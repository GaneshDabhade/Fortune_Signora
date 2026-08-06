# 465 · The long-term certification strategy — taxonomy, profiles and what the record cannot yet say

**Lane C · Product Office · 2026-08-06.** **[D-098](../DECISION_REGISTER.md). Extends [463](463-certification-architecture-assessment.md).**

> ***"The objective is not simply faster certification… the highest confidence for the lowest justified cost."*** ⛔ **Planning only. No QE workflow or certification behaviour is modified.**

---

# 0 · The finding that outranks everything else in both documents

**[463](463-certification-architecture-assessment.md) measured *how often* each gate fails. This one asked *what they caught*, and the answer is the exercise's most important result.**

| Run | Gate | Recorded detail |
|---|---|---|
| **26** | `smoke` | ***"2 stages in 38s"*** — of **24** |
| **38** | `smoke` | ***"2 stages in 53s, slowest 1. Build 53s"*** — of **24** |
| **54** | `mypy` | ***"no summary line"*** |

> ## ⚡ **Across 70 certifications, not one gate has caught a product defect.**
>
> **Two `smoke` runs stopped at stage 2 of 24 — the build.** **One `mypy` gate could not parse its own tool's output.** **All three are the gate failing to *run*, or the environment failing to come up. None is the repository being wrong.**

## And the repository already knows the distinction — for one gate only

**[`REPOSITORY_RELEASE_CHECKLIST.md`](../REPOSITORY_RELEASE_CHECKLIST.md), on DR:**

> ***"`make dr` aborting is not `make dr` failing, and the record must not say it was. An abort means the gate never evaluated the repository."***

⚠️ **That rule is written for DR and implemented for nothing.** **Runs 26 and 38 are recorded as `smoke` **failures** and read like **aborts**.** **So the 2.9% figure in [463](463-certification-architecture-assessment.md) may be a 0% failure rate and a 2.9% abort rate — and for a risk model those mean opposite things.**

**One is *"this gate catches things"*. The other is *"this gate is flaky."*** **A tier model built on the first when the truth is the second would demote the wrong gates.**

> ## **So the honest answer to *"what types of defects does each gate catch?"* is: the record cannot say, because it records an outcome without a cause.**
>
> ⚡ **This is now the first thing to fix, ahead of durations.** **A `cause` field — `passed · failed · aborted · skipped` — costs one enum and turns three ambiguous data points into evidence.**

---

# 1 · The ten questions, answered with what exists

| | Question | Answer today |
|---|---|---|
| **1** | **How long does each gate take?** | ⛔ **1 of 6.** Only `smoke` records its own duration — **p50 138s · p95 272s · max 4830s** |
| **2** | **How often does each fail?** | ✅ **Measured** — `smoke` 2/70, `mypy` 1/70, everything else 0 |
| **3** | **What does each catch?** | ⛔ **Unknown, and §0 is why** |
| **4** | **Which catch what lanes cannot?** | ✅ **`smoke`, uniquely.** It binds ports 3000/8000, which is *why* §20e makes it QE's — **and it is the only gate that has ever gone red** |
| **5** | **Which overlap?** | ⚡ **One exactly, and it is measurable — §2** |
| **6** | **Which protect architectural integrity?** | `lint-imports` *(35 contracts)* · `mypy --strict` *(762 files)* · the Security Invariants |
| **7** | **Which protect production stability?** | `smoke` *(the Infrastructure Contract)* · `make dr` · `baseline@1` |
| **8** | **Expensive and rarely run?** | **`make dr`** — unmeasured, once per cycle · **the frontend suite** — 1255 tests, **[B-123](../BUGS.md)**, run by nothing |
| **9** | **Always, regardless of change?** | **Every repository-wide guarantee**: the invariants, the import contracts, migration consistency, tenancy |
| **10** | **Selected by impact?** | Module suites · DR · prompt evaluation · migration reversibility |

---

# 2 · ⚡ The one real overlap, and it is not what a reader would guess

**`pyproject.toml`: `testpaths = ["modules", "signora_platform", "tests"]`.**
**`__main__.py` then runs `pytest --cov` — which collects `tests/security_invariants` — and separately runs `pytest tests/security_invariants`.**

> ## **The 389 Security Invariants execute twice in every certification.**

| | |
|---|---|
| **What the second run costs** | **A full re-execution of 19 invariant files** |
| **What it buys** | ⚡ **A *named gate* in the record.** `REQUIRED_GATES` contains `security-invariants`, so `missing_gates` can assert them specifically — **which is the absence-is-not-a-pass rule working** |
| ⛔ **What it does not buy** | **Any additional confidence.** The same assertions already ran, in the same process tree, minutes earlier |

> **So this is the only place in the whole assessment where cost can be removed with *zero* confidence loss** — **by deriving the invariant count from the first run rather than re-running it.** ⚠️ **And the constraint is absolute: the *gate must still appear in the record*.** **Removing the line, rather than the second execution, would delete a guarantee §11 calls permanent.**

---

# 3 · Certification taxonomy — by purpose

| | Purpose | Gates |
|---|---|---|
| **T1 · Development Quality** | *Is this code correct and consistent?* | `mypy --strict` · `tsc` · `eslint` · module suites |
| **T2 · Repository Integrity** | *Does the repository still agree with itself?* | `lint-imports` · `state-check` · `vocabulary-check` · `certification-guard` · **coverage floor** |
| **T3 · Architectural Governance** | *Do the boundaries still hold?* | `lint-imports` · the Change Budget · Context Definitions · [ADR](adr/) compliance |
| **T4 · Platform Safety** | *Can a tenant reach another tenant?* | **Security Invariants — 389** · RLS · `tenancy_policy.py` classification |
| **T5 · Operational Readiness** | *Does it start, serve and stay up?* | `make smoke` · health and readiness · migration reversibility |
| **T6 · Business Continuity** | *Does it survive a restart, and can it be restored?* | **`make dr`** · backup · restore |
| **T7 · Release Certification** | *Is this version fit to ship?* | Upgrade · rollback · cross-version · full-system |

> ⚠️ **T4 is the one that must never be tiered by cost.** **A tenancy failure is not a defect a customer reports; it is a defect a customer's competitor finds** — and §11 makes the invariants permanent for exactly that reason. **They stay at every level, and the *only* saving available is §2's double execution.**

---

# 4 · Certification profiles — and the repository already has five

⚡ **`CLAUDE.md` §20e's *"Which gates run when"* table is a profile model.** **Six moments, each with a declared gate set and a stated reason, ratified and in force.** **The proposal is not to invent one.**

| Proposed profile | §20e's moment | Status |
|---|---|---|
| **Developer** | ***During a slice*** — impacted suites · `mypy` · `tsc` · `eslint`. *"Speed is the point"* | ✅ **Exists, ratified.** ⛔ Unmeasured |
| **Lane** | ***Lane → QE*** — full module suite · impacted integration · `lint-imports` · `mypy --strict` · frontend · production build | ✅ **Exists, ratified.** ⚡ **And §0 suggests this is where the defects are actually caught** |
| **QE** | ***Lifecycle 1 + 2*** — everything, then `make certify` · migration reversibility · `make dr` | ✅ **Exists, ratified.** ⛔ Only `smoke` is timed |
| **Release** | ⛔ **No moment exists.** [ADR-0027](adr/0027-local-first-development.md) defers release to M14.5 | ⛔ **Genuinely absent — T7 has no home** |
| **Infrastructure** | ⛔ **No moment.** `make dr` sits inside the QE profile | ⛔ **Absent — §5** |

> ## **Three of five are ratified and unmeasured; two do not exist.**
>
> **So the work is not designing profiles. It is *declaring* the three that exist so their cost can be measured, and *creating* the two that do not.** ⚡ **And a profile nobody can measure is exactly the state §20e is in today: six moments, one timed gate between them.**

---

# 5 · Disaster Recovery — execution levels on recovery objectives

**DR's five stages restart PostgreSQL, Redis, the API, workers and the relay — and then re-assert isolation and ordering.**

| Level | Contents | Frequency | The risk it answers |
|---|---|---|---|
| **Continuous** | **Stage 5 alone** — isolation and ordering | **Every certification** | ⚡ **This is a *tenancy* assertion (T4), not continuity.** It needs no restart, and it is the one condition the Security Invariants never create |
| **Weekly** | **All five stages** | **Weekly** | **Restart survival is an infrastructure property. It cannot regress from a change to a module's domain layer** |
| **Infrastructure-change** | **All five stages** | **On any `infra/` or `signora_platform/db` change** | **The only change class that can plausibly break it** |
| **Release** | **Five stages + backup and restore** | **Before a release** | ⚠️ **[438 §0④](438-platform-initiatives.md): `make dr` proves *restart survival* and not *backup*, and a backup policy is a separate absence** |
| ⛔ **Daily** | — | **Not recommended** | **Nothing in 70 runs suggests a daily failure mode, and §20c-2 forbids a scheduler to run it** |

⚠️ **Every row above is conditional on a measurement nobody has taken.** **DR's runtime is recorded nowhere** — so *"expensive"* remains an assumption **in the brief and in this document alike.**

---

# 6 · Change-aware certification — under the invariant, not against it

> ***"Run everything that provides additional confidence. Not: run as little as possible."***

**Applied honestly, that invariant *shrinks* the change-aware opportunity, and saying so is the point.**

| Gate | Change-aware? |
|---|---|
| **Security Invariants** | ⛔ **Never.** T4 is repository-wide by definition |
| **`lint-imports`** | ⛔ **Never.** A contract is about the graph, not a file |
| **`mypy --strict`** | ⛔ **Never.** A type changes callers it does not name |
| **`smoke`** | ⛔ **Never.** It is the only gate that has ever gone red |
| **`pytest --cov`** | ⚠️ **The coverage *floor* is repository-wide** — a per-module run cannot enforce it |
| ✅ **Module suites, beyond the floor** | ✅ **Yes** — and [TASK-413](../BACKLOG.md) already prepares this |
| ✅ **`make dr` full** | ✅ **Yes** — §5 |
| ✅ **Migration reversibility** | ✅ **Yes** — migrations only |
| ✅ **Prompt evaluation** | ✅ **Yes** — prompt or model change |

> ## **Four of nine can be selected by impact. Five cannot, and four of those five are the cheap ones.**
>
> ⚡ **Which means change-aware certification is worth *far less* than it sounds** — **the gates that could be skipped are the ones that cost little, and the gates that cost most are repository-wide guarantees.** **The saving is real and it is not where the brief expects it.**

---

# 7 · The seven confidence lenses

| | Where it stands |
|---|---|
| **Developer experience** | ⚠️ **Unmeasured. Commit → feedback is not recorded**, and the Developer profile is ratified prose |
| **Implementation velocity** | ✅ **Not currently constrained by certification** — no lane has reported waiting on a gate; **both idle lanes are waiting on *rulings*** |
| **Repository confidence** | ✅ **High.** 3653 tests, 389 invariants, 35 contracts, 95.4% coverage, 70 recorded runs |
| **Release confidence** | ⛔ **Untested — T7 has no gates and no moment** |
| **Operational confidence** | ⚠️ **`smoke` is the only evidence, and it is the only gate that aborts** |
| **Infrastructure confidence** | ⚠️ **DR runs and is recorded nowhere** |
| **Customer confidence** | ⛔ ⚠️ **The frontend suite — 1255 tests — is in no gate** ([B-123](../BUGS.md)). **The layer a customer actually touches is the least verified** |

> **Two of seven are strong. Three are unmeasured. Two are absent.** **And the weakest is the one nearest the customer.**

---

# 8 · Long-term roadmap

| | Step | Why in this order |
|---|---|---|
| **1** | ⚡ **Record a *cause* per gate — `passed · failed · aborted · skipped`** | **§0. Three data points are currently ambiguous, and every later decision reads them** |
| **2** | **Record a duration per gate** | Six of nine metrics unblock |
| **3** | **[B-123](../BUGS.md) — gate the frontend suite** | **Customer confidence is the weakest lens, and tiering a suite that never runs is arranging nothing** |
| **4** | **Declare the three existing profiles** in a manifest, describing today exactly | **A manifest that first disagrees with reality is one nobody trusts** |
| **5** | **Remove the Security Invariants' double execution** — keep the gate line | **The only zero-confidence-loss saving in the assessment** |
| **6** | **Split DR on step 2's measurement**, and gate DR Smoke as T4 | Evidence, not anecdote |
| **7** | **Attach triggers to the four selectable gates** via [TASK-413](../BACKLOG.md) | The mechanism exists; the policy is §6 |
| **8** | **Create the Release and Infrastructure profiles** | **When M14.5 makes a release real** — [ADR-0027](adr/0027-local-first-development.md) |

---

# 9 · Recommendation

> ## **Certification is not currently slowing anybody down, and it cannot currently prove what it catches. Fix the second, and the first stays true as the repository grows.**

**Steps 1–3 are the whole of the near-term recommendation.** **They are two enum fields and one gate wiring, they change no behaviour, and without them every optimisation in this document is an opinion.**

⛔ **Demote nothing.** ⛔ **No scheduler** — §20c-2. ⛔ **And do not treat change-aware selection as the prize**: §6 measures it as small, because the expensive gates are precisely the ones that must always run.

---

# 10 · What this document did not do

**Nothing implemented · no gate changed · no `Makefile` touched · no manifest field added · no QE workflow modified · no lane named · no backlog row created.**

⚠️ **And it did not repeat [463](463-certification-architecture-assessment.md)'s central claim without re-testing it.** **That document reported `smoke` as the highest-value gate at a 2.9% failure rate. This one looked at what those failures *were* and found two aborts at stage 2 of 24** — **which may mean the opposite.** **The number was right; the conclusion drawn from it was not yet earned.**
