# 466 · Certification parallelism — the gate dependency graph, and what may safely overlap

**Lane C · Product Office · 2026-08-06.** **[D-101](../DECISION_REGISTER.md).** Extends [463](463-certification-architecture-assessment.md) and [465](465-certification-strategy.md).

> ***"Parallel execution is encouraged. Shared mutable execution environments are not."***

**Prepared, not implemented.** ⛔ **No gate changed · no `Makefile` touched · no `__main__.py` edited.** **QE owns certification implementation and operational execution; this is the architecture and the operating model.**

---

# 0 · ⚡ The finding that revises my own two prior recommendations

**[465 §9](465-certification-strategy.md) said *record a cause* and *record a duration*, as if neither existed. Half of both already do, and I measured the wrong file.**

| | |
|---|---|
| **What [463](463-certification-architecture-assessment.md) and [465](465-certification-strategy.md) both read** | **`certification/manifest.json`** — **71 runs.** Gates carry **`name · passed · detail`** and nothing else. **No cause. No duration. Zero occurrences of `duration`, `elapsed`, `started_at` in the whole file** |
| ⚡ **What neither read** | **`attempts.py`** — a **git-ignored operational log**, deliberately separate, and it already carries **`duration_s`** and **three outcomes** |

**`attempts.stability()`, verbatim:**

```python
aborted=len(started - set(finished)),
```

> ## ⚡ **An abort is already detected — and by a better mechanism than the enum I proposed.**
>
> **It is *derived from absence*: an attempt that wrote `started` and never wrote `finished` aborted.** **An enum can be set wrongly; a missing record cannot lie about itself.** **That is [P-A](../DOMAIN_DISCOVERY_REGISTER.md) implemented correctly, two documents before I recommended inventing it.**

**And the file's own docstring says why the manifest could never have shown this:**

> *"A run that hangs, is killed, or crashes never reaches `append()`. **A 22-minute hang against an exited database left no record in any file.**… That 100% was survivorship bias, not a measurement."*

## So what is actually missing is smaller and more precise

| | Level | State |
|---|---|---|
| ✅ **Outcome** | **Run** | **`certified · failed · aborted`** — built, and abort is derived |
| ⛔ **Outcome** | ⚡ **Gate** | **`passed: bool`, and nothing else.** **This is the real gap** |
| ✅ **Duration** | **Run** | **`duration_s`** — built |
| ⛔ **Duration** | ⚡ **Gate** | **Absent. Only `smoke` carries a time, inside free text**: *"24 stages in 140s"* |
| ⛔ **`skipped`** | **Both** | **Does not exist at either level** |

> ⚠️ **And the run level cannot rescue the gate level, which is why [465 §0a](465-certification-strategy.md) still stands.** **The three recorded `smoke`/`mypy` failures were runs that *finished*** — they wrote `outcome: failed` with `failing_gates: ["smoke"]`. **The run concluded; the gate never evaluated the repository.** **Nothing distinguishes *smoke found a defect* from *smoke never came up*, and the run-level abort check cannot see it.**

---

# 1 · The gate dependency graph, measured from `__main__.py`

**Every gate, its command, and what it actually contends for.**

| Gate | Command | Database | Fixed ports | Mutates |
|---|---|---|---|---|
| **`migrations`** | `alembic upgrade head` | ⚡ **writes schema** | — | **The schema. Fatal, and first** |
| **`pytest`** *(+ coverage + `security-invariants`)* | `uv run pytest --cov` | 🔴 **exclusive** | — | ⚡ **`TRUNCATE`s every table after each test** · **`pg_authid`, cluster-wide** |
| **`mypy`** | `uv run mypy --strict .` | ⛔ **none** | ⛔ | `.mypy_cache/` — its own path |
| **`import-linter`** | `uv run lint-imports` | ⛔ **none** | ⛔ | **nothing** |
| **`tsc`** | `npx tsc --noEmit` | ⛔ **none** | ⛔ | **nothing** — `--noEmit` |
| **`smoke`** | `bash ./infra/smoke.sh` | **its own stack** | 🔴 **3000 · 8000** | **Docker compose project** |
| **`scenarios`** | pytest, scenario suite | 🔴 **exclusive** | — | rows |

```
  migrations ──┬──────────────────────────────────────────────▶ pytest ──▶ scenarios
               │                                                  (database-exclusive, serial)
               │
               └── ⚡ independent of migrations entirely ──▶ mypy
                                                          ──▶ import-linter     ⟩ no DB, no ports,
                                                          ──▶ tsc              ⟩ no shared state

  smoke ─────────────────────────────────────────────────────▶ (environment-exclusive, alone)
```

> ## ⚡ **The three static gates do not depend on `migrations` at all.**
>
> **They are pure static analysis over the source tree.** **Today they run *after* `pytest` for no reason other than the order the function calls appear in** — `__main__.py` lines 269–278, six sequential statements.

---

# 2 · Three concurrency classes

| Class | Gates | Rule |
|---|---|---|
| ✅ **S — static** | **`mypy` · `import-linter` · `tsc`** | **Fully concurrent — with each other and with everything else.** **No database, no port, no shared mutable state.** Each writes only its own cache path |
| 🔴 **D — database-exclusive** | **`pytest` · `scenarios`** | **Strictly serial, after `migrations`.** The suite truncates every table between tests; two readers of one database destroy each other |
| 🔴 **E — environment-exclusive** | **`smoke`** | **Alone.** Binds 3000 and 8000 and raises a full compose stack |

## May execute concurrently

> ## **`mypy` ∥ `import-linter` ∥ `tsc`, and all three in the shadow of `pytest`.**

**Four gates where there are now six sequential steps.** ⛔ **Nothing is skipped, nothing is sampled, no gate's scope narrows** — the same six verdicts are produced, in less wall-clock time. **That is the only optimisation shape the invariant permits**: *run everything that provides additional confidence.*

## Must remain sequential

| | Why, and it is not caution |
|---|---|
| **`migrations` before class D** | ⚡ **Already enforced and fatal.** *"A suite run against an unmigrated database fails in hundreds of places for one reason, and the reason is the least visible line in that output"* |
| **`pytest` before `scenarios`** | **One database, and `pytest` truncates it** |
| **`smoke` alone** | **3000 and 8000 are fixed and singular.** **And this is [B-118](../BUGS.md)'s exact class** — the `Makefile` already records *"pressure from another environment turned a 130s smoke run into a 320s one"* |

---

# 3 · ⛔ Parallel `pytest` — refused today, and the blocker is not the database

**`pytest-xdist` is the obvious candidate and it is the one that would reproduce cycle 57.**

**Two independent obstacles, and the second is the one that matters:**

| | |
|---|---|
| ① **The suite truncates** | `conftest.py`: *"This suite **TRUNCATES every table after each test**."* **Workers sharing one database annihilate each other's rows.** ✅ **Solvable — a database per worker**, which is *more* isolation and therefore aligned with the directive |
| ⚡ ② **A PostgreSQL ROLE is cluster-wide** | ⛔ **Not solvable by a database per worker.** `test_database.py:77` executes **`ALTER ROLE signora_app BYPASSRLS`** — and `pg_authid` is shared by every database in the cluster |

> ## **Cycle 57 aborted on exactly this: `ALTER ROLE signora_app NOBYPASSRLS` — *tuple concurrently updated*.**
>
> **The repository already recorded the cause, in [`test_environment_allocation.py`](../../backend/tests/certification/test_environment_allocation.py)'s own docstring, and in the notice at the head of all three lane queues.**

**So parallel `pytest` needs *both* a database per worker *and* the cluster-mutating invariants pinned to a single worker** — `--dist loadgroup` with an `xdist_group` mark on the role tests. **Buildable, and it is the highest-complexity item in this document for a saving nobody has measured.**

⛔ **Recommendation: not now.** **It is the one proposal here that could weaken isolation if it were got subtly wrong**, and the directive is explicit: ***"never trade execution isolation for marginal runtime improvements."*** **Revisit when a per-gate duration proves `pytest` is the wall-clock problem.**

---

# 4 · Resource utilisation

| Class | CPU | Memory | I/O | Contends with |
|---|---|---|---|---|
| **`mypy`** | **1 core, saturated** | **High** — a full type graph over 765 files | Cache reads | ⛔ **nothing** |
| **`import-linter`** | 1 core | Low | Source reads | ⛔ **nothing** |
| **`tsc`** | 1 core | Moderate | Source reads | ⛔ **nothing** — a different toolchain, a different tree |
| **`pytest`** | 1 core + PostgreSQL | Moderate | 🔴 **database, heavily** | **Itself, and `scenarios`** |
| **`smoke`** | **Many** — a whole stack | **High** | Docker, network | 🔴 **Every port-bound thing on the workstation** |

> ⚡ **Class S is three single-core, non-database workloads.** **On any developer machine with four cores they genuinely run at once** — this is not oversubscription dressed as parallelism.
>
> ⚠️ **`mypy`'s memory is the one thing to watch**, and it is the reason to measure before adopting rather than after.

---

# 5 · Expected runtime improvement — stated as unknown, because it is

> ## ⛔ **This document will not give you a number, and that refusal is the point.**

**The whole measured evidence available:**

| | |
|---|---|
| ✅ **`smoke`** | **140s** — *"24 stages in 140s, slowest 2. Startup 20s"*. **The only gate duration in the repository**, and it is inside a free-text string |
| ✅ **Run total** | **`duration_s`, in the git-ignored attempts log** |
| ⛔ **`pytest` · `mypy` · `import-linter` · `tsc` · `scenarios`** | **Unmeasured. All five** |

**The saving from class S is bounded above by `min(pytest, mypy + import-linter + tsc)`** — **and four of those five terms are unknown**, so the expression cannot be evaluated. ***"I want optimization based on evidence rather than intuition."***

> **The shape is knowable even where the size is not**: **three gates move out of the critical path into `pytest`'s shadow.** **If they are cheap, the saving is small and the change is still free. If they are expensive, the saving is large.** **Which of those is true is one field away and has never been recorded.**

---

# 6 · Confidence impact

| | |
|---|---|
| ✅ **Class S concurrency** | ⚡ **Zero change, and provably.** **The same three commands, the same arguments, the same tree, the same six verdicts.** **Concurrency changes when a gate runs, never what it evaluates** |
| ✅ **Determinism** | **Unaffected.** **No class S gate reads mutable state any other gate writes** — that is the definition of the class, not a hope about it |
| ✅ **Reproducibility** | **Preserved exactly.** **The manifest schema does not change**, so a record produced under concurrent execution is comparable with all 71 sequential ones. ⚡ **This is the property that makes the change safe to roll back** |
| ⚠️ **Failure attribution** | **The one thing that genuinely changes.** **Three gates failing at once produce interleaved output**, and *"which gate said that?"* becomes harder. **Mitigated by capturing each gate's output separately** — which the code already does, since `_run()` returns per-gate output |
| 🔴 **Parallel `pytest`** | ⛔ **Not zero, and that is why §3 refuses it.** A worker collision produces a failure that **looks like a repository defect** — the most expensive failure mode a gate has |

---

# 7 · Implementation complexity

| Change | Complexity | Shape |
|---|---|---|
| ⚡ **Per-gate duration and cause** | 🟢 **Smallest, and it precedes everything** | **Two fields on `GateResult`.** **`_run()` is already the single choke point every gate passes through** — one `perf_counter()` either side of one function |
| **Class S concurrency** | 🟢 **Small** | **`concurrent.futures.ThreadPoolExecutor`, three submissions.** ⚡ **Every gate is a `subprocess` call, so the GIL is irrelevant** — the threads are waiting on processes |
| **Class S overlapping `pytest`** | 🟠 **Moderate** | The same executor, with `pytest` submitted alongside. **Output interleaving is the only real work** |
| **DR as its own profile** | 🟠 **Moderate** | [465 §5](465-certification-strategy.md) |
| **Parallel `pytest`** | 🔴 **High** | Per-worker databases · `xdist_group` on the cluster-mutating invariants · a per-worker allocation the lease understands |

> ⚡ **The ordering is not a preference.** **The first row makes rows 2–5 measurable.** **Adopting any of them first means adopting an optimisation whose benefit cannot be stated** — which is the assumption-driven change the directive rules out.

---

# 8 · Rollback strategy

> ## **Every proposal here is revertible by one commit, and none leaves a trace in the record.**

| | |
|---|---|
| ✅ **The manifest schema is unchanged by concurrency** | **A run executed concurrently is byte-comparable with a sequential one.** **So rollback needs no data migration and invalidates no prior certification** |
| ✅ **The change is one call site** | **Six sequential statements become one executor block in `__main__.py`.** **Reverting restores the sequence exactly** |
| ⚡ **The trigger to roll back is stated in advance** | **Any gate producing a different verdict under concurrency than under sequence.** **That is a defect in the concurrency, never a finding about the repository** — and it is checkable by running both on one commit |
| ⚠️ **Per-gate fields are additive** | **A reader tolerating their absence reads all 71 existing runs and every new one.** **Rolling back the writer leaves the field absent, not wrong** |

**For the two field additions, rollback is the weaker direction and worth naming: once durations exist, arguments start depending on them.** ⛔ **That is not a reason to defer them — it is the reason to add them before anything else, so no argument is made without them.**

---

# 9 · Recommendation, in order

| | | |
|---|---|---|
| **1** | ⚡ **A duration and a cause per gate** | 🟢 **Two fields at one choke point.** **Everything below is unquantified until this lands** |
| **2** | **`mypy` ∥ `import-linter` ∥ `tsc`** | 🟢 **Zero confidence change, provable.** The cheapest real saving available |
| **3** | **Class S in `pytest`'s shadow** | 🟠 **Same guarantee, one more step** |
| **4** | ⏸ **DR as its own profile** | [465 §5](465-certification-strategy.md) |
| **5** | ⛔ **Parallel `pytest`** | 🔴 **Not until 1 proves it is the wall-clock problem** |

⛔ **And unchanged from [465](465-certification-strategy.md): demote nothing · no scheduler (§20c-2) · [B-123](../BUGS.md) still precedes the roadmap**, because a frontend suite in no gate is a validation that does not happen, and parallelising the gates that *do* run does not touch it.

## For QE, who owns the implementation

**Every item above is QE's to accept, reorder or refuse** (§20e — *a change to what a gate means is a slice*). **What this office asserts is the graph and the classes; what it does not assert is that any of it is worth doing before it is measured.**

⚠️ **One correction QE should have plainly**: **[463](463-certification-architecture-assessment.md) and [465](465-certification-strategy.md) both measured `manifest.json` and reported the repository as recording no cause and no duration.** **`attempts.py` already records both at run level, and derives aborts better than the enum [465](465-certification-strategy.md) proposed.** **The gate-level gap is real; the run-level gap was mine.**

---

# 10 · What this document did not do

**Nothing implemented · no gate changed · no `Makefile` touched · no `__main__.py` edited · no manifest field added · no QE workflow modified · no lane named · no backlog row created.**

⚡ **And it found its own two prior documents wrong before extending them.** **Both asserted the repository records no gate cause and no duration. Both had read one file and there are two** — and the second one had solved the harder half first.
