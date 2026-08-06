# 463 · Certification architecture — a risk-based model, assessed against 70 recorded runs

**Lane C · Product Office · 2026-08-06.** **[D-096](../DECISION_REGISTER.md). A governance and architecture exercise: nothing is implemented, and certification remains QE's to operate.**

> **Lane C prepares; QE runs the gates.** §20e: *"a defect in a gate that stops QE certifying is QE's to fix"*, and **every change proposed here is QE's to make or refuse.**

**Evidence base: `certification/manifest.json`, 70 runs, 2026-07-31 → 2026-08-05.**

---

# 0 · Three findings that reshape the brief

## ① Disaster Recovery is already outside `make certify`

**`backend/tests/certification/record.py`:**

> **`REQUIRED_GATES = frozenset({"pytest", "mypy", "tsc", "import-linter", "security-invariants", "smoke"})`**

**DR is not among them, and `make certify` never invokes it.** **It runs because [`REPOSITORY_RELEASE_CHECKLIST.md`](../REPOSITORY_RELEASE_CHECKLIST.md) has a tick-box and `CLAUDE.md` §20e names it in stage 2** — **a runbook step, not an automated gate.**

> **So the brief's primary motivation is half-true.** **DR is not run "after every small change" by the certification command; it is run once per *cycle* by a person following a checklist.** **The optimisation available is real and it is smaller than it looks — and knowing which it is changes the recommendation.**

## ② ⚠️ DR's result is in no certification record

**Six gate names have ever been written to the manifest. None is DR.**

**[ADR-0032](adr/0032-release-certification.md) calls that file *"durable evidence that a specific commit satisfied the repository's guarantees under stated conditions."*** **A guarantee QE runs every cycle, whose outcome the evidence does not contain, is either not a guarantee or not evidenced** — and both readings are governance defects rather than performance ones.

> ⚡ **This has to be settled before any tiering, because a tier model assigns validations to levels and DR is currently in no level at all.**

## ③ The failure data says something the brief did not anticipate

| Gate | Runs | Failures | Rate |
|---|---|---|---|
| **`smoke`** | 70 | **2** | **2.9%** |
| **`mypy`** | 70 | **1** | **1.4%** |
| `import-linter` | 70 | 0 | 0.0% |
| **`pytest`** *(3653 tests)* | 70 | **0** | **0.0%** |
| **`security-invariants`** *(389)* | 70 | **0** | **0.0%** |
| `tsc` | 29 | 0 | 0.0% |
| `baseline@1` scenario | 70 | 0 | 0.0% |

> ## **The two most expensive gates have never failed at certification. Three of 70 runs failed at all.**
>
> **And the reason is not that the tests are weak — it is §19**: ***"Quality is the lane's, before it is QE's."*** **A lane runs `pytest`, `mypy` and `lint-imports` on its rebased branch before handing over, so by certification those gates are re-running work that already passed.**
>
> ⚡ **The gate that fails is the one a lane *cannot* run.** **`smoke` binds ports 3000 and 8000, which is why §20e makes it QE's** — **and it is the only gate with a meaningful failure rate.**

**That is the empirical basis for a risk model, and it is the opposite of the intuitive one: value at certification time is not a gate's importance, it is the probability it catches something the lane could not.**

---

# 1 · Current certification inventory

| Validation | Where it runs | Recorded? | Cost | Failures |
|---|---|---|---|---|
| **`pytest --cov`** | `make certify` | ✅ | **3653 tests, the largest single cost** | 0/70 |
| **Security Invariants** | `make certify` | ✅ | 389 invariants, a subset re-run | 0/70 |
| **`mypy --strict`** | `make certify` | ✅ | 762 files | 1/70 |
| **`lint-imports`** | `make certify` | ✅ | 35 contracts | 0/70 |
| **`tsc --noEmit`** | `make certify` | ✅ **since run 42** | Low | 0/29 |
| **`make smoke`** | `make certify` | ✅ | **24 stages · p50 138s · p95 272s · max 4830s** | **2/70** |
| **`baseline@1` scenario** | `make certify` | ✅ | 190 assertions | 0/70 |
| **`make dr`** | **The runbook, by hand** | ⛔ **No** | **5 stages: PostgreSQL · Redis · API · workers+relay · isolation-and-ordering** | **Unmeasured** |
| **Migration reversibility** | The runbook, by hand | ⛔ **No** | Unmeasured | Unmeasured |
| **`state-check`** | Closeout | ⛔ No | Seconds | Advisory |
| **`certification-guard`** | Promotion | ⛔ No | Seconds | Blocking |
| **Frontend suite** *(1255)* | ⛔ **Nothing** | ⛔ No | Unmeasured | **[B-123](../BUGS.md)** |

> ⚠️ **Three validations named in governance are recorded nowhere, and one — the frontend suite — runs nowhere at all.** **A tier model that assigns levels to validations must first agree on which validations exist.**

---

# 2 · Risk classification matrix

**Scored on what the evidence supports: *can a lane run it* · *has it caught anything* · *what does it cost* · *is it unique*.**

| Validation | Lane can run it | Caught | Cost | Unique confidence | **Tier** |
|---|---|---|---|---|---|
| **`lint-imports`** | ✅ | 0/70 | **Seconds** | ✅ **Nothing else asserts the graph** | **P0** |
| **`mypy --strict`** | ✅ | 1/70 | Low | ✅ | **P0** |
| **`tsc`** | ✅ | 0/29 | Low | ✅ | **P0** |
| **Security Invariants** | ✅ | 0/70 | Medium | ✅ **Deliberately overlapping, and §11 says that is the point** | **P0 — never demoted** |
| **`pytest --cov`** | ✅ | 0/70 | **Highest** | ✅ | **P0**, and §3 |
| **`make smoke`** | ⛔ **No — it binds 3000/8000** | **2/70** | **p95 272s** | ✅ **The Infrastructure Contract has no other check** | **P0 — the highest-value gate by evidence** |
| **`baseline@1`** | ⛔ Needs a stack | 0/70 | Medium | ✅ End-to-end lifecycle | **P0** |
| **Migration reversibility** | ✅ | Unmeasured | Low | ✅ | **P1 — migrations only** |
| **`make dr`** | ⛔ | **Unmeasured** | **5 restart stages** | ⚠️ **§3** | **Split — §3** |
| **Frontend suite** | ✅ | **Never run** | Unmeasured | ✅ | **P0 once gated — [B-123](../BUGS.md)** |

> ⛔ **Nothing is demoted out of P0 on this evidence.** **A 0% failure rate is not a case for removal** — it is what a gate looks like when the lanes are doing §19 properly, and **the moment it stops running, the lane's incentive to run it first goes with it.**

---

# 3 · Disaster Recovery — the split, and the argument for it

**What DR asserts, from its five stages: PostgreSQL, Redis, the API, workers and the relay each survive a restart, and *isolation and ordering hold afterwards*.**

> ⚡ **The fifth stage is the one that matters, and it is not about recovery.** **It re-asserts RLS isolation and event ordering after a restart** — **a tenancy guarantee, checked in the one condition the Security Invariants never create.**

| | Contents | When | Why |
|---|---|---|---|
| **DR Smoke** | **Stage 5 alone** — isolation and ordering, against the already-running stack | ✅ **Every certification** | **It is a tenancy assertion, it needs no restart, and tenancy is the guarantee this repository can least afford to lose quietly** |
| **DR Full** | **All five stages** | **Weekly, and after any `infra/` or `signora_platform/db` change** | **Restart survival is an *infrastructure* property. It cannot regress from a change to a module's domain layer, and nothing in 70 runs suggests otherwise** |
| **Release DR** | **DR Full + backup and restore** | **Before a release** | **[438 §0④](438-platform-initiatives.md) already records that `make dr` proves restart survival and *not backup*, and that a backup policy is a separate absence** |

> ⚠️ **The recommendation is conditional on a measurement nobody has taken.** **DR's runtime is not recorded**, so *"expensive"* is an assumption in the brief and in this document alike. **Finding ② must be fixed first: record DR's result and duration in the manifest, then split on evidence.** **Splitting a gate whose cost is unmeasured would be optimising by anecdote.**

---

# 4 · Trigger-based certification — and the metadata already exists

**The brief asks whether repository metadata can decide which suites are required. It can, and four of the five inputs are already published.**

| Input | Status |
|---|---|
| **Module ownership** | ✅ [`modules.toml`](../coordination/modules.toml) — paths per module |
| **Dependency graph** | ✅ **35 `lint-imports` contracts**, machine-readable in `pyproject.toml` |
| **Public contracts** | ✅ Every module's `public/` |
| **Architecture boundaries** | ✅ The Change Budget, and [`vocabulary.toml`](../coordination/vocabulary.toml) |
| **Which suite covers which module** | ⛔ **Missing. This is the only gap** |

> ## **A trigger is `git diff --name-only` ∩ `modules.toml` paths → the suites that own those modules.**
>
> **`infra/validate.py` already does change-aware selection** — **[TASK-413](../BACKLOG.md) is *"change-aware validation: `frontend/`-only skips `dr`"* and it is `SEQUENCED` today.** ⚡ **The trigger mechanism is already prepared work; what this assessment adds is the *policy* it should express.**

---

# 5 · Certification Manifest — it exists, and the proposal is an extension

⚡ **`certification/manifest.json` is already a manifest**: per run it records commit, gates with pass and detail, scenarios, coverage, conditions, tools and `tree_clean`. **`REQUIRED_GATES` and `missing_gates` already make *absence a failure rather than a silence*.**

**What the brief asks for is a *suite* manifest beside the *run* manifest** — declaring, per suite: purpose · tier · estimated runtime · affected modules · trigger condition · release requirement · infrastructure requirement · frequency.

| | |
|---|---|
| ✅ **Reuse** | **The run manifest's shape, `REQUIRED_GATES`' absence-is-failure rule, and `modules.toml`'s path form** |
| ⚠️ **The rule that keeps it honest** | ***A suite absent from the manifest does not run.*** **The inverse — a suite that runs but is not declared — is exactly finding ②**, and a manifest that permits it is documentation again |
| ⛔ **Not a scheduler** | **§20c-2 is absolute.** ***"Nightly"* and *"weekly"* are a human running a command on a day**, and a manifest that implied automation would be CI by another name |

---

# 6 · Metrics — and most of them cannot be measured today

**The brief asks for seven. Here is what the repository can actually produce.**

| Metric | Available? |
|---|---|
| **Failure detection rate by tier** | ✅ **Today** — §0③, and it is the strongest signal in this document |
| **Suite growth** | ✅ **1825 → 3653 tests in 70 runs — it doubled in five days** |
| **`smoke` duration** | ✅ **p50 138s · p95 272s · max 4830s** — the only gate recording its own runtime |
| **Average certification duration** | ⛔ **Not recorded.** `certified_at` is a timestamp, not a duration |
| **P50/P95 certification time** | ⛔ **Not recorded** |
| **% skipped by trigger rules** | ⛔ **No trigger rules exist yet** |
| **Cost per suite** *(CPU/RAM/DB/tokens)* | ⛔ **Nothing measures it.** ⚠️ **AI tokens are the exception — `InferenceUsage` records them per call already** |
| **Commit → developer feedback** | ⛔ **Not recorded** |
| **Regressions escaping P0/P1** | ⛔ **Unmeasurable until tiers exist** |

> ## **Two of nine are measurable today, and the cheapest change in this whole assessment is the one that fixes six of them.**
>
> **Record a duration per gate in the run manifest.** **One field, in a record that already exists, and it turns *"certification is slow"* from an impression into a series.** ⚡ **This office would recommend it even if the tier model were rejected entirely** — **because every argument in the brief, including the brief's own premise, currently rests on an unmeasured cost.**

---

# 7 · Migration plan — four steps, in dependency order

| | Step | Why first |
|---|---|---|
| **1** | **Record duration per gate, and record DR at all** | ⚡ **Everything else is optimisation without a baseline.** Closes finding ② |
| **2** | **Declare the suite manifest** — describing what runs *today*, changing nothing | **A manifest that first disagrees with reality is a manifest nobody trusts** |
| **3** | **Split DR on the measurement from step 1**, and gate DR Smoke | Finding ①, on evidence rather than assumption |
| **4** | **Attach triggers to P1 suites, via [TASK-413](../BACKLOG.md)** | The mechanism exists; only the policy is new |

⛔ **[B-123](../BUGS.md) is not in this plan and should precede all of it**: **the frontend suite is in no gate at all**, and **tiering a suite that never runs would be arranging validations that do not happen.**

---

# 8 · Recommendation

> ## **Adopt the tier model. Demote nothing yet. Measure first.**

**The brief's objective — confidence over execution time — is right, and the evidence says the current cost is concentrated in one place and the current *risk* in another.**

| | |
|---|---|
| ✅ **Adopt** | **The P0–P3 vocabulary, the suite manifest, and trigger-based selection via [TASK-413](../BACKLOG.md)** |
| ✅ **Do now** | **Record duration and DR** — one field, and it unblocks six of nine metrics |
| ⚠️ **Do next** | **Split DR into Smoke / Full / Release**, ⛔ **but only after its cost is measured** |
| ⛔ **Do not** | **Demote `pytest` or the Security Invariants.** **Their 0% failure rate is §19 working, not redundancy** — and a gate removed is an incentive removed |
| ⛔ **Do not** | **Introduce any scheduler.** §20c-2: *"the correct quantity of CI is zero"* |

> **And the honest headline: the certification command runs six gates, three of 70 runs failed, and the two gates the brief would most want to trim have never caught anything at certification — because the lanes catch it first.** **The velocity problem this brief anticipates is real and it is mostly *ahead* of the repository rather than inside it.** **Which is the right moment to design for it, and the wrong moment to cut anything.**

---

# 9 · What this document did not do

**Nothing implemented · no gate changed · no Makefile touched · no manifest field added · no lane named · no backlog row created.**

⚠️ **And it corrected its own measurement once.** **The first pass reported *"zero failures across 70 runs"* — because it read `gates` as a dict when it is a list, so it never iterated.** **The manifest's own `_comment` says failed runs are recorded, and three are.** **A finding that would have argued for demoting every gate came from a bug in the tool that produced it.**
