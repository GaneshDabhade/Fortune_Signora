# Bug register

> **The single register.** Not a file per bug, not scattered TODOs. **Any lane opens a row; QE reconciles the register at every promotion** (`CLAUDE.md` §20e). A lane edits only the `Status` of a bug it has fixed.
>
> **Why this file exists.** Open defects had no home. They were split between `39-product-review-findings.md` (a *dated record of reviews*, append-only, and not a feature lane's to edit) and `PROJECT_STATUS.md`'s known-limitations table. Neither can carry a row whose status changes, and a review finding is not the same thing as a defect with an owner and a fix. This file replaces that responsibility rather than adding one.

## How it works

**Any lane opens. The module's current assignee fixes. QE verifies and closes** — never the lane that fixed it.

**A defect belongs to a module, not to a lane.** The module is permanent; the lane assigned to it rotates (`CLAUDE.md` §20e). A row therefore names **the module**, and whoever is currently assigned it resolves the defect. A row whose module has no current assignee waits for one — which is not the same as being unowned.

**Reporting is every lane's duty, not only QE's.** Finding a defect outside your assignment is not permission to fix it — it is an obligation to record it, with every field below filled, before carrying on inside your Change Budget. **Only QE sets `VERIFIED`.**

> **No defect disappears because the lane that found it could not fix it.** That is the single failure this register exists to prevent, and it is the one a busy lane commits by accident — in a comment, in a commit message, in an intention to come back.

**Before starting any slice, a lane reads every `OPEN` and `FIXING` row** (`CLAUDE.md` §20e, *Startup*). Rows against the module it is assigned are fixed first, or deferred **with the reason stated in the commit message**. Silence reads as *nobody looked*.

> **Finding a bug never grants implementation ownership.** *Discovery* decides who reports it; **the affected module decides who fixes it.** They are rarely the same lane, and that is the point. Ownership moves only by explicit reassignment, never by having noticed.

**A defect is not a dependency.** If your work is blocked because another module has not yet built or agreed something, that is a coordination item — [`LANE_COORDINATION.md`](LANE_COORDINATION.md) — not a bug. A bug is something that behaves wrongly today.

### Defects in code that belongs to no module

`signora_platform/**` (frozen, §20a), `apps/` (the composition root) and the frontend foundation (§20c) are not modules, so no assignment reaches them. **QE cannot fix them either — it changes no production code.**

Such a row names the code, records **Current assignee: none — not assignable**, and **waits for the product owner**. It is never quietly adopted by whoever is nearest.

**This gap appeared on 2026-08-01** when the Integrator role was absorbed into QE. [B-007](#b-007--the-migration-runner-locks-one-database-and-migrates-another) is its first instance, and [C-010](LANE_COORDINATION.md) is the item that will resolve it — deciding how unassignable code gets assigned is an architectural decision, not a lane's to make.

**`integration` never fast-forwards to `main` with an open 🔴.** That is the one blocking rule; 🟠 and below are the product owner's call.

| Severity | Meaning |
|---|---|
| 🔴 | Blocks a milestone |
| 🟠 | Wrong behaviour a customer would hit |
| 🟡 | Wrong but survivable |
| 🟢 | Cosmetic |

| Status | Meaning |
|---|---|
| `OPEN` | Reproduced, not started |
| `FIXING` | The current assignee is on it |
| `FIXED` | Lane says done, with a regression test |
| `VERIFIED` | QE reproduced the fix. **Only QE sets this** |
| `WONTFIX` | Deliberate, with the reason stated |

**Where the regression test goes:** the affected module's suite, written by the lane that fixes it — never this file. The rule requiring one is `CLAUDE.md` §11.

**Bug ids are `B-nnn`, allocated sequentially and never reused.** A finding from a product review keeps its `R-` id there and gets a `B-` row here only if it is a defect rather than an improvement.


## How the registers were reconciled, 2026-08-02

**Two lanes allocated `B-003`…`B-006` independently while the repository ran on two baselines.** The rows promoted to `main` keep their numbers; **QE renumbered the later set**, which is this file's stated rule for an id collision.

| Was, on `lane-qe` | Is now | Why |
|---|---|---|
| `B-001` · `B-002` | — | The same two defects as the promoted rows. The duplicates were dropped, not renumbered |
| `B-003` the migration runner | **[B-007](#b-007--the-migration-runner-locks-one-database-and-migrates-another)** | Renumbered. It is the **code** half of promoted [B-003](#b-003--a-lane-following-runningmd-exactly-cannot-run-its-own-suites), which is the documentation half |
| `B-004` the truncation claim | **[B-008](#b-008--the-suite-says-it-truncates-every-table-and-truncates-five)** | Renumbered |
| `B-005` the documented API command | **[B-009](#b-009--the-documented-command-for-starting-the-api-cannot-start-the-api)** | Renumbered |
| `B-006` orphaned narrations | **[B-010](#b-010--re-seeding-the-playground-orphans-every-narration-silently)** | Renumbered |
| `B-007` `make` absent | **[B-011](#b-011--make-is-not-installed-on-this-workstation--not-a-repository-defect)** | Renumbered, and resolved on the workstation |

**No row was lost and none was silently merged.** An id, once promoted, is never reused for a different defect.

---

## Open

### B-022 · `make certify` inherits the database environment, and silently measures less when it is absent

| | |
|---|---|
| **Module** | Repository tooling — `Makefile`, the `certify` target |
| **Current assignee** | **none — not assignable.** [C-010](LANE_COORDINATION.md), and the fourth defect to land in that gap |
| **Severity** | 🟠 — the gate reports a number that looks like a regression and is actually a misconfiguration. **It does not fail; it under-measures** |
| **Status** | `OPEN` |
| **Found** | 2026-08-02, by QE, certifying `c3435a0` — it cost two full gate runs before the cause was clear |

**Steps to reproduce.** From a shell without the lane database variables:

```bash
make certify
#   pytest              2238 passed          ← 110 fewer than the suite has
#   coverage            94.34%               ← below the 95% floor
#   security-invariants 337 invariants       ← 17 fewer
#   scenario            164 assertions       ← 15 fewer
#   NOT CERTIFIED
```

Then, same commit, same tree, with the three variables [`RUNNING.md`](RUNNING.md#running-a-lane) requires:

```bash
export SIGNORA_TEST_APP_DATABASE_URL=… SIGNORA_TEST_ADMIN_DATABASE_URL=… SIGNORA_DATABASE_URL=…
make certify
#   pytest 2348 · coverage 95.57% · 354 invariants · 179 assertions · CERTIFIED
```

**Expected.** A gate either runs or refuses to run. **`make certify` has no options, deliberately** (§20e) — *"a mode that skipped a gate would produce a run that cannot certify, and a command whose convenient path yields worthless evidence teaches people to use it."* An environment that silently deselects 110 tests is exactly that mode, arrived at by omission.

**Actual.** The target is `cd backend && SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 uv run python -m tests.certification` — it sets one variable and inherits three. Without them the database-backed tests deselect, and **every gate reports a smaller, plausible number.** Nothing says *"the database was not reachable"*; it says `NOT CERTIFIED · coverage 94.34% is below 95.0%`, which reads as a coverage regression somebody introduced.

**Why it is worth a row rather than a note to self.** This is the failure mode §2 names directly: **the repository asserted something untrue about itself, in the one artifact whose entire purpose is being trustworthy.** The misconfigured run wrote a manifest entry recording `commit c3435a0 · coverage 94.34 · tree_clean true` — a measurement of a broken instrument, indistinguishable to every future reader from a measurement of the repository. That entry was discarded and this row is what replaces it; **the finding is durable, the false number is not.**

**And the part that makes this worth acting on rather than re-documenting.** [`REPOSITORY_RELEASE_CHECKLIST.md`](REPOSITORY_RELEASE_CHECKLIST.md) **already carries the warning**, in bold, directly above the `make certify` line, with measured evidence from earlier the same day: *"the same commit certified 2223/94.36% against the shared default and 2325/95.59% against the lane's own database. A gate pointed at the wrong database is not a gate."*

**QE read that checklist, wrote that warning, and still ran the gate wrong** — because the variables were exported in one shell and `make certify` was invoked from another. **A rule that its own author violates within hours, while looking at it, is not a rule that needs restating; it is a rule that needs replacing with a check.** The fix is a preflight in the target, not a stronger sentence in the runbook.

**Fix.** Make the target fail loudly when the variables are absent, rather than proceeding with a partial selection — a preflight that asserts reachability and exits non-zero with the missing variable named. **Do not fix it by hardcoding a lane's database into the `Makefile`**: the file is shared, and every lane has its own (`RUNNING.md` § *Running a lane*).

**Second-order finding, and the more interesting one.** The first run left `certification/manifest.json` modified, which made the tree dirty, which failed the *next* run's cleanliness check — so one misconfiguration cost two runs rather than one. **The certification record lives in the tree it certifies.** That is precisely the assumption [ADR-0039](architecture/adr/0039-release-engineering-model.md) §II-3.2 identifies as the root of the divergence chain, arriving here as an ordinary operational nuisance. **It is evidence for that ADR, not a reason to act on it** — recorded and left alone, per the governance bar.

**Recovered 2026-08-02, by an audit of the register.** This row was written at Closeout `7a08922`, reached `main`, and then **vanished from both branches** — removed without record when `integration` was rebased in the following cycle. **Nobody noticed; an audit found it.** That is the point: a defect that leaves the register is indistinguishable from one that was never reported. Same failure mode as [B-017](BUGS.md), now applied to the register that exists to prevent it.

---


### B-026 · The repository does not own its line endings, and depends on every contributor's git config

| | |
|---|---|
| **Module** | Repository configuration — a missing `.gitattributes` |
| **Current assignee** | **none — not assignable.** [C-010](LANE_COORDINATION.md) |
| **Severity** | 🟡 — **latent, not active.** Nothing is broken today; the exposure is real and cheap to close |
| **Status** | `OPEN` |
| **Found** | 2026-08-02, by QE, investigating a suspected line-ending problem at the product owner's request |

**First, the honest correction.** **There is no CRLF problem in this repository today**, and QE did not report one. The investigation was asked for on the assumption that a CRLF observation had been made; it had not. What the investigation *did* find is the condition that would produce one.

**Measured.**

```bash
ls .gitattributes                              # No such file
git config --get core.autocrlf                 # unset
git ls-files --eol | awk '{print $1}' | sort | uniq -c
#   824 i/lf        ← every text file is LF in the index
#   102 i/none      ← binary
```

**Expected.** A repository states its own line-ending policy, so that a clone behaves identically on Linux, macOS, WSL and Windows regardless of who configured what.

**Actual.** **No `.gitattributes` exists.** Normalisation depends entirely on each contributor's `core.autocrlf`, which on this workstation is unset — and unset is only safe *because the workstation is Linux*. **A Windows contributor with git's default `core.autocrlf=true` would commit CRLF into `infra/smoke.sh` and `infra/disaster-recovery.sh`**, and a shell script with CRLF line endings fails with `bad interpreter: /bin/bash^M` — an error that names neither the file's real problem nor the machine that caused it.

**Why it matters more here than in most repositories.** Under [ADR-0027](architecture/adr/0027-local-first-development.md) **the local run is the only run**, and `smoke.sh` and `disaster-recovery.sh` are two of the gates that decide whether anything ships. **A line-ending accident in those two files disables certification for whoever receives it**, with a message that reads like a broken interpreter rather than a checkout artifact.

**Smallest sufficient fix, recommended and deliberately not implemented.** A single `.gitattributes` at the repository root:

```gitattributes
* text=auto eol=lf
*.sh text eol=lf
*.png binary
*.jpg binary
*.ico binary
```

`* text=auto eol=lf` makes the repository — not the contributor — the authority: LF in the index and LF in every working tree. The explicit `*.sh` line is redundant under it and is kept because **the two files whose corruption would be most expensive should be the two nobody has to reason about.**

**Why the repository should own this rather than documenting it** (§2): a rule kept by every contributor configuring their client correctly is a rule that will be broken by the first person who does not, and the failure lands on somebody else's machine. **This is convention replaced by enforcement**, which is the substitution the repository already prefers everywhere else.

**Scheduled, not deferred indefinitely** (product owner, 2026-08-02). **Apply during a maintenance cycle when no feature branch is open** — the fix is a content no-op today, but `.gitattributes` changes how git *normalises* on checkout, and landing it while two lanes hold long branches invites merge churn for no benefit. **The board shows when that window is open:** every lane `AVAILABLE`.

**One caveat for whoever implements it.** Adding `.gitattributes` to a repository that is already uniformly LF is a no-op for content — verified above, 824 of 824 text files are already `i/lf` — so **no renormalisation commit is needed and none should be made.** If that ever stops being true, `git add --renormalize .` is the mechanism, and it must be its own commit.


### B-024 · The credential store that must not be readable has no tests at all

| | |
|---|---|
| **Module** | `integrations` · `timeline` |
| **Current assignee** | **Lane B**, feature lead for both |
| **Severity** | 🟠 — it rejected a Release Candidate, and one file of it is security-relevant |
| **Status** | **`FIXED`** — Lane B, 2026-08-02. All four named files at **100%**; three real defects came out from under it. **`VERIFIED` is QE's to set** |
| **Found** | 2026-08-02, by QE, certifying `9ba0ea6` — **the candidate was rejected and abandoned** |

**Steps to reproduce.**

```bash
cd backend && uv run pytest --cov -q
# FAIL Required test coverage of 95.0% not reached. Total coverage: 94.79%
# 2460 passed          ← every test passes; nothing is broken
uv run coverage report --skip-covered --sort=miss | tail -8
```

**Expected.** Coverage at or above the 95% floor.

**Actual.** **94.79%**, and the gap is concentrated in the two newest modules:

| File | Cover | Missed |
|---|---|---|
| `modules/integrations/infrastructure/secrets.py` | **0%** | **34** |
| `modules/integrations/infrastructure/repository.py` | **35%** | 26 |
| `modules/timeline/interface/handlers.py` | **0%** | 11 |
| `modules/timeline/infrastructure/repository.py` | **52%** | 9 |
| `modules/integrations/application/queries.py` | 90% | 8 |

**88 of the repository's 491 missed statements — 18% — sit in two modules built in the last two days.**

**The percentage is the least interesting part of this row.** `secrets.py` is **0% covered**, and the commit that introduced it is titled *"a credential that is not readable"*. **A guarantee about credential confidentiality that no test exercises is a guarantee nobody has checked** — §11 requires the failure paths, and §2 is explicit that a guard which cannot fail is documentation pretending to be code. `timeline/interface/handlers.py` at 0% is the module's event-consumption path, which is how every entry it will ever hold gets there.

**This was predicted, and the prediction is in the record.** Coverage fell 95.57 → 95.37 → 95.19 → 95.16 across four cycles, and cycle 15's Closeout stated the failure mode exactly: *"the next sizeable slice lands the repository below the floor, and a candidate is rejected for coverage rather than for a defect."* **The gate did its job.**

**Second rejection, 2026-08-02 — candidate `a2ca53d`, and nothing moved.** M13-S05, M13-S06 and the M13 module review landed on `integration` in between and **touched no backend file**: the frontend suite grew 511 → 595, the backend stayed at 2460 and coverage stayed at **94.79%**, to the statement.

```
modules/integrations/infrastructure/secrets.py     34  34   0%   ← unchanged
modules/integrations/infrastructure/repository.py  43  26  35%   ← unchanged
modules/timeline/interface/handlers.py             11  11   0%   ← unchanged
modules/timeline/infrastructure/repository.py      21   9  52%   ← unchanged
```

**The `tests/integrations/` files are not new.** `test_connection.py` arrived with S01, `test_queries.py` with S02, `test_connect.py` with S04 — all before the first rejection. **No test has been added against any of the four files above since this row was opened.**

**Two candidates have now been rejected for one unfixed defect.** `9ba0ea6` and `a2ca53d`, both abandoned, both correctly. **Nothing on `integration` can certify until these four files are covered**, which is the shared-base pattern again — now at **three occurrences**, counting [B-023](BUGS.md).

### Candidate `d758754` — NOT CERTIFIED, 2026-08-02

| | |
|---|---|
| **Release Candidate** | ❌ **NOT CERTIFIED.** **Disposition: permanently abandoned** — `d758754` will never be promoted to `main` |
| **Implementation** | **IN PROGRESS — not rejected.** Lane B's work stands and moved the number. The resulting commits form a **new** candidate; **no implementation effort is discarded** |
| **Next action** | **Lane B** — cover `modules/timeline/interface/handlers.py`, push. **QE pins and certifies the new snapshot immediately** |

### Third rejection, and it is 0.02% away

**Real progress, and the number says so.** `secrets.py` went **0% → 61%** (34 missed → 12); the suite grew 2460 → 2476; coverage moved **94.79% → 94.98%**. Lane B did the work this row asked for.

**It is short by 0.02 percentage points — roughly three statements.** Two files carry what remains:

| File | Cover | Missed | |
|---|---|---|---|
| `modules/timeline/interface/handlers.py` | **0%** | **11** | **Covering this file alone clears the floor with room to spare** |
| `modules/integrations/infrastructure/repository.py` | 35% | 26 | The larger gap, and not needed to certify |

**`timeline/interface/handlers.py` is the recommendation, and not because it is the cheapest.** It is the module's **event-consumption path** — the route by which every entry Timeline will ever hold arrives. **It has never been executed by a test**, and Timeline is already promoted and on `main`.

**Three candidates now rejected on this row** — `9ba0ea6`, `a2ca53d`, `d758754` — all abandoned, all correctly. **The trend is toward resolution rather than away from it**, which is why this is a progress note rather than a second escalation.

### Escalation — 2026-08-02

**This defect has now blocked two consecutive certification cycles and is a repository bottleneck.**

| | |
|---|---|
| **Cycles blocked** | **2** — cycle 16 (`9ba0ea6`) and cycle 17 (`a2ca53d`), both rejected and abandoned |
| **Work waiting** | **9 commits on `integration`** cannot promote · **25 commits on `lane-a-product-surface`** sit behind the same base, **none of which touch `integrations` or `timeline`** |
| **Owner** | **Lane B**, feature lead for both modules |
| **Progress** | **None measurable.** Between the two rejections Lane B shipped M13-S05, M13-S06 and the M13 module review — **all frontend and documentation, no backend file touched.** The four named files are unchanged to the statement |
| **Is it a bottleneck?** | **Yes.** Two lanes' finished work is unreleasable, and the repository has not promoted since `3451f8b` |

**Recorded, not editorialised.** Lane B may have reasons for the sequencing that QE cannot see, and finding a defect outside one's assignment is an obligation to report rather than a licence to prioritise somebody else's queue. **What QE will not do is normalise the repetition:** a second identical rejection is reported as an escalation, not as *"candidate rejected again."*

**Not to be fixed by lowering the floor**, and not by adding assertions that execute lines without testing behaviour. The two 0% files are the work; the percentage follows.

### Fix — Lane B, 2026-08-02

**QE's escalation was accurate and its last sentence was the important one.** The percentage was never the defect; the two 0% files were. **Three real defects were sitting under them, and every one would have reached a customer.**

| # | Defect | Why no existing test could see it |
|---|---|---|
| 1 | **Every connection insert would have failed.** `connected_account.created_by` and `updated_by` are `NOT NULL`; nothing supplied them. **The first customer to connect anything would have hit it** | Every repository test used a fake, and **a fake cannot refuse an insert** |
| 2 | **The write order violated the foreign keys.** `ConnectSystem` wrote credential material before the connection it references. Both `integration_secret` and `integration_grant` have an FK to `connected_account` | Same — the doubles accepted any order, and one unit test *asserted* the wrong one |
| 3 | **`ConnectionNotFound` escaped as a `500`.** It had no entry in the central error mapping, so a caller naming another organization's connection was told the platform had broken rather than being refused | No test had ever called the route with a connection id it could not see |

**Fixes.** `ConnectedAccount` and `IntegrationGrant` gain a required `actor_id` with **no default** — the rule `next_state` already follows — which makes `ConnectInput.actor_id` load-bearing after four slices of being declared and never read, and answers *"who disconnected our CRM?"* at the only moment the answer exists. `created_by` is never reassigned on update, so a later disconnection cannot destroy the record of who connected it. The write order is now connection → material → grant → connection, with the row landing in `AUTHORIZING` first, which **preserves the property the old ordering was protecting**: a partial failure leaves *"you started this and did not finish"*, never *Ready to use* over a credential that does not exist. `modules/integrations/interface/errors.py` maps `ConnectionNotFound` to **404, never 403**.

**Tests — 42 added, all against real PostgreSQL as `signora_app`:**

| File | What it proves |
|---|---|
| `tests/integration/test_integrations_persistence.py` | A connection survives the schema · who connected it is not overwritten by who disconnected it · the unique identity constraint is live · **the material is not what lands in the column** · a rotated key refuses rather than resolving to something · purging actually removes it · another organization's credential is invisible under RLS |
| `tests/integration/test_timeline_persistence.py` | The projection path end to end · redelivery losing the race against a unique index · **ties broken identically by PostgreSQL and by the cursor** — the unit suite pages against a fake that reimplements the same rule, so only the database can prove they agree |
| `tests/integration/test_api_connections.py` | Authorization at the route: a member may read and **may not** disconnect · 404-never-403 · the disconnect names its caller · nothing is advertised as `connectable` before it is |

**Measured on the fixed tree**, `HEAD` of `lane-b-commercial-profile`:

```
2518 passed        (was 2460, then 2476)
Required test coverage of 95.0% reached. Total coverage: 95.69%     (was 94.79%, then 94.98%)
```

| File | Before | After |
|---|---|---|
| `modules/integrations/infrastructure/secrets.py` | **0%** | **100%** |
| `modules/integrations/infrastructure/repository.py` | 35% | **100%** |
| `modules/timeline/interface/handlers.py` | **0%** | **100%** |
| `modules/timeline/infrastructure/repository.py` | 52% | **100%** |

`mypy --strict` clean · `lint-imports` 34 kept, 0 broken · frontend `tsc` clean, 616 tests.

**The general lesson, recorded because it will recur:** a fake that reimplements a rule can only ever agree with itself. Where the rule lives in the database — a constraint, an ordering, a keyset predicate, RLS — the test has to be there too. Written up in [41-integrations.md §10](architecture/41-integrations.md).

### B-025 · A coverage failure is reported as a test failure, and names the wrong gate

| | |
|---|---|
| **Module** | Repository tooling — `backend/tests/certification/` |
| **Current assignee** | **none — not assignable.** [C-010](LANE_COORDINATION.md) |
| **Severity** | 🟡 — diagnosis only; the certification decision was correct |
| **Status** | `OPEN` |
| **Found** | 2026-08-02, by QE, reading the rejection of `9ba0ea6` |

**Steps to reproduce.** Certify a commit whose coverage is below the floor.

```
❌ pytest — 2457 passed
❌ smoke  — 3 stages in 93s
Coverage 94.79%

Why this run does not certify
  · gate 'pytest' failed: 2457 passed        ← reads as a test failure
  · coverage 94.79% is below 95.0%           ← the actual cause
```

**Expected.** A failing gate names what actually failed (§10, *failure attribution must be truthful* — *"an incorrect attribution is worse than none, because it misdirects the investigation"*).

**Actual.** `pytest` is invoked with `--cov`, so `--cov-fail-under` makes it exit non-zero when coverage is short. The harness reads the exit code and marks the **pytest** gate failed, printing *"2457 passed"* as its reason — **a failure message whose entire content is a success count.** The same defect is then reported twice, once under a name that is not responsible.

**It cost real time here.** The first reading was *"three tests are failing"* — 2460 in a direct run against 2457 here — and diagnosing that took a second full suite run to establish that **nothing was broken at all.**

**Fix.** Either run coverage as its own gate and drop `--cov-fail-under` from the pytest invocation, or report the pytest gate as passed-with-coverage-short. **Do not merely reword the message**: the gate is currently wrong about which component failed, not just unclear.


### B-027 · The connect screen promises a disconnect that does not exist

| | |
|---|---|
| **Module** | `integrations` — `frontend/components/integrations/connect-panel.tsx` |
| **Current assignee** | **Lane B**, M13's owner |
| **Severity** | 🟠 — **the product asserts a capability it does not have**, to a customer who is deciding whether to trust it with their CRM |
| **Status** | **`FIXED`** — Lane B, 2026-08-02. Disconnect is a lifecycle, not a button; all three gaps closed. **`VERIFIED` is QE's** |
| **Found** | 2026-08-02, by Lane B, in M13's end-to-end module review — **in its own slice** |

**Steps to reproduce.** Open the connect panel for any system. Read the section headed *If you change your mind*:

> *"You can disconnect {name} at any time from this page. Signora stops reading from it immediately."*

**Expected.** A way to disconnect.

**Actual.** There is none. `ConnectionState.DISCONNECTED` exists, `UNUSABLE_STATES` contains it, the query layer treats it as *not broken*, and the Connection Center renders it as *Turned off* — and **no use case transitions to it.** `grep` for a caller finds only comments.

**This is the principle Lane B proposed in [C-017](LANE_COORDINATION.md) violated by Lane B's own copy**: *a surface never advertises a capability the system cannot execute*. It is the more embarrassing kind of instance — the sentence exists precisely to reduce a customer's hesitation before they commit, so it is doing persuasive work that the product cannot back.

**Two related gaps found in the same review, recorded here rather than as separate rows** because one fix closes all three:

**`EncryptedSecretStore.purge_for` is never called.** It exists so that disconnecting removes credential material rather than merely forgetting the pointer — which is the compliance finding from M13's own architecture review, arriving as unreached code.

**`SecretUndecryptable` is raised and never caught.** A rotated or wrong key surfaces as an unhandled exception rather than as a connection a customer is told to reconnect.

**The fix, for whoever takes it — which is Lane B.** A `DisconnectSystem` use case transitioning to `DISCONNECTED`, revoking the grant, calling `purge_for`, and an endpoint plus a control behind it. **The copy is not the thing to change**: the promise is the right promise, and the product should keep it.

### Fix — Lane B, 2026-08-02

**The copy was not changed.** The promise was right; the software now keeps it.

| | |
|---|---|
| **Verification performed** | The disconnect lifecycle against the conditions that make it matter, not the path where everything works |
| **Result** | **`PASS`** — 436 tests including the full Security Invariants suite, 76 of them this module's |
| **Commands executed** | `pytest tests/security_invariants tests/integrations` · `mypy --strict` · `lint-imports` · OpenAPI route check |
| **Lifecycle** | **Not advanced.** `VERIFIED` is QE's |

**Three rules, each because the obvious implementation gets it wrong.**

**A vendor cannot block a disconnect.** Revocation is attempted, its failure recorded, never propagated. Withdrawing access is what somebody does *in a hurry* — a disconnect that failed because HubSpot was down would hold a security action hostage to the system it protects them from. Tested with a revoker that raises.

**Material is destroyed, not orphaned.** `purge_for` is called unconditionally, so *"Signora can no longer read from this"* is true rather than believed.

**It is idempotent.** A second disconnect is a customer clicking twice; it changes nothing and does not move the first one's record.

**`NoRevoker` reports failure rather than success**, because claiming a revocation that never happened would tell a customer their access was withdrawn at the vendor while the credential is still live there — the more dangerous of the two lies. The response carries `revoked_at_provider` so the screen can say so.

**`SecretUndecryptable` now subclasses `SecretNotFound`**, and resolution raises `CredentialUnreadable`. A rotated key and a purged secret are the same fact above the adapter — *this connection has to be made again* — which is something a customer can act on, unlike a stack trace.

### A lifecycle gap the fix's own tests found

**An abandoned half-finished connection could not be disconnected.** `AUTHORIZING` permitted only `CONNECTED` and `NOT_CONNECTED`, so a customer who closed the tab mid-flow had a row reading *Not finished* that nothing could clear. Found by a parameterised test asserting every state can be left, not by reading the table — **which is the argument for that test existing.**

---

### B-023 · `tsc --noEmit` fails on the Timeline feed tests, and the suite that passes cannot see it

| | |
|---|---|
| **Module** | `timeline` — `frontend/tests/components/timeline-feed.test.tsx` |
| **Current assignee** | **Lane B**, Timeline's feature lead |
| **Severity** | 🟠 — a stated Completion gate fails on `integration`. **Two characters to fix; it is blocking four finished slices** |
| **Status** | **`FIXED`** — Lane B, 2026-08-02. A narrowing guard, not a cast; all four gates re-run. **`VERIFIED` is QE's to set** |
| **Found** | 2026-08-02, by QE, validating snapshot `7df2073` at lifecycle stage 1 |

**Steps to reproduce.**

```bash
cd frontend && npx tsc --noEmit
# tests/components/timeline-feed.test.tsx(79,19): error TS2345:
#   Argument of type 'HTMLElement | undefined' is not assignable to 'HTMLElement'.
# tests/components/timeline-feed.test.tsx(80,19): error TS2345: (same)
```

**Expected.** `tsc --noEmit` clean. It is named in `CLAUDE.md` §20e *Completion* step 2 — *"its module suite, impacted integration tests, `mypy --strict`, `lint-imports`, frontend suite, production build"* — and in *Which gates run when* for both the lane's hand-off and QE's validation.

**Actual.** `screen.getAllByRole('listitem')` returns `HTMLElement[]`, and under `noUncheckedIndexedAccess` the elements `items[0]` and `items[1]` are `HTMLElement | undefined`. `within()` will not take that.

**Fix.** Assert the shape the test already depends on — the two `listitem` elements it just rendered — rather than widening a type. A local `const [first, second] = screen.getAllByRole('listitem')` with an explicit `expect(first).toBeDefined()`, or an index guard, keeps the test honest about what it is asserting.

**Why the other gates missed it, which is the part worth keeping.** **Vitest passed — 488 tests, including these two — and `npm run build` passed.** Vitest transpiles without full type checking, and the Next.js production build type-checks *application* sources rather than the test tree. **So the only gate that can see this class of defect is the one that was run last**, and a lane running its suite and its build would reasonably believe it was green.

**Not a governance proposal, an observation for the record** (governance is frozen, and this has happened once): the lane-side gate list and the order it is run in are what caught this, and they caught it only at QE. If it recurs, the cheap structural answer is that `tsc` runs *before* the suite rather than after, so the fast feedback comes first.

**Escalated 2026-08-02: it is not blocking one candidate, it is blocking the pipeline.**

### Fix — Lane B, 2026-08-02

| | |
|---|---|
| **Verification performed** | The four Completion gates, re-run in full |
| **Result** | **`PASS`** — `tsc --noEmit` clean · 488 frontend tests · `eslint` clean · production build clean |
| **Commands executed** | `npx tsc --noEmit` · `npx vitest run` · `npx eslint tests/components/timeline-feed.test.tsx` · `npm run build` |
| **Environment** | Lane B clone, rebased on `integration` |
| **Lifecycle** | **Not advanced.** `VERIFIED` is QE's |

**A guard that narrows, not a cast.** `expect(first).toBeDefined()` satisfies a reader and narrows nothing — TypeScript does not learn from a matcher — so it would have needed `!` beside it, which is a type escape wearing an assertion's clothes. `if (!first || !second) throw` narrows properly, states what the test already depends on, and fails with a readable message if the feed ever renders no rows.

**QE's diagnosis of why the other gates missed it is correct, and Lane B can add the specific error.** The gates were run in the order they are listed, and `tsc` was run **before** this test file existed — the component was type-checked, the test was added afterwards, and only Vitest and the build ran again. Both pass: Vitest transpiles without type-checking and the Next.js build type-checks application sources rather than the test tree.

**So the ordering observation is right and the mechanism is narrower than a habit:** any gate run before the last file is written is a gate that did not run. Re-running the full set at hand-off is what catches it, and that is what was skipped here.

The defect is on `integration`, and **every branch cut from `integration` inherits it.** Verified:

```bash
git show origin/lane-a-product-surface:frontend/tests/components/timeline-feed.test.tsx | sed -n '79p'
#   expect(within(items[0]).getByText(...))     ← the same two lines
```

**Lane A's six unrelated slices — PS-01, PS-02, PP-01, PP-02, PP-04, PP-05 — cannot certify either**, and nothing in them touches Timeline. A two-character type error in one lane's test file is holding two lanes' finished product work.

**This is the clearest evidence the repository has produced for [ADR-0039](architecture/adr/0039-release-engineering-model.md) §II-2, assumption 2** — *validation happens after merge* — and for what that assumption costs. A candidate validated **before** entering the shared line fails alone; a defect that reaches the shared line **fails everything downstream of it, forever, until somebody fixes it.** Recorded as evidence. **Not acted on** — the ADR is a north star, the governance bar is unmet at one occurrence, and the fix here is Lane B's.

| | |
|---|---|
| **Module** | Repository tooling — `Makefile`, the `certify` target |
| **Current assignee** | **none — not assignable.** [C-010](LANE_COORDINATION.md), and the fourth defect to land in that gap |
| **Severity** | 🟠 — the gate reports a number that looks like a regression and is actually a misconfiguration. **It does not fail; it under-measures** |
| **Status** | `OPEN` |
| **Found** | 2026-08-02, by QE, certifying `c3435a0` — it cost two full gate runs before the cause was clear |

**Steps to reproduce.** From a shell without the lane database variables:

```bash
make certify
#   pytest              2238 passed          ← 110 fewer than the suite has
#   coverage            94.34%               ← below the 95% floor
#   security-invariants 337 invariants       ← 17 fewer
#   scenario            164 assertions       ← 15 fewer
#   NOT CERTIFIED
```

Then, same commit, same tree, with the three variables [`RUNNING.md`](RUNNING.md#running-a-lane) requires:

```bash
export SIGNORA_TEST_APP_DATABASE_URL=… SIGNORA_TEST_ADMIN_DATABASE_URL=… SIGNORA_DATABASE_URL=…
make certify
#   pytest 2348 · coverage 95.57% · 354 invariants · 179 assertions · CERTIFIED
```

**Expected.** A gate either runs or refuses to run. **`make certify` has no options, deliberately** (§20e) — *"a mode that skipped a gate would produce a run that cannot certify, and a command whose convenient path yields worthless evidence teaches people to use it."* An environment that silently deselects 110 tests is exactly that mode, arrived at by omission.

**Actual.** The target is `cd backend && SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 uv run python -m tests.certification` — it sets one variable and inherits three. Without them the database-backed tests deselect, and **every gate reports a smaller, plausible number.** Nothing says *"the database was not reachable"*; it says `NOT CERTIFIED · coverage 94.34% is below 95.0%`, which reads as a coverage regression somebody introduced.

**Why it is worth a row rather than a note to self.** This is the failure mode §2 names directly: **the repository asserted something untrue about itself, in the one artifact whose entire purpose is being trustworthy.** The misconfigured run wrote a manifest entry recording `commit c3435a0 · coverage 94.34 · tree_clean true` — a measurement of a broken instrument, indistinguishable to every future reader from a measurement of the repository. That entry was discarded and this row is what replaces it; **the finding is durable, the false number is not.**

**And the part that makes this worth acting on rather than re-documenting.** [`REPOSITORY_RELEASE_CHECKLIST.md`](REPOSITORY_RELEASE_CHECKLIST.md) **already carries the warning**, in bold, directly above the `make certify` line, with measured evidence from earlier the same day: *"the same commit certified 2223/94.36% against the shared default and 2325/95.59% against the lane's own database. A gate pointed at the wrong database is not a gate."*

**QE read that checklist, wrote that warning, and still ran the gate wrong** — because the variables were exported in one shell and `make certify` was invoked from another. **A rule that its own author violates within hours, while looking at it, is not a rule that needs restating; it is a rule that needs replacing with a check.** The fix is a preflight in the target, not a stronger sentence in the runbook.

**Fix.** Make the target fail loudly when the variables are absent, rather than proceeding with a partial selection — a preflight that asserts reachability and exits non-zero with the missing variable named. **Do not fix it by hardcoding a lane's database into the `Makefile`**: the file is shared, and every lane has its own (`RUNNING.md` § *Running a lane*).

**Second-order finding, and the more interesting one.** The first run left `certification/manifest.json` modified, which made the tree dirty, which failed the *next* run's cleanliness check — so one misconfiguration cost two runs rather than one. **The certification record lives in the tree it certifies.** That is precisely the assumption [ADR-0039](architecture/adr/0039-release-engineering-model.md) §II-3.2 identifies as the root of the divergence chain, arriving here as an ordinary operational nuisance. **It is evidence for that ADR, not a reason to act on it** — recorded and left alone, per the governance bar.

---

### B-021 · The coordination register's `Closed` section holds only open items, and every closed one sits above it

| | |
|---|---|
| **Module** | **none** — [`LANE_COORDINATION.md`](LANE_COORDINATION.md) |
| **Current assignee** | **QE**, at the next cycle's stage-3 reconciliation — the register is QE's to reconcile at merge |
| **Severity** | 🟠 — two tools report *"3 closed"*, and the true figure is *"0 closed, 2 answered and misfiled"* |
| **Status** | **`FIXED`** — QE, 2026-08-02. By the time it was fixed the heading sat above **five** open items, not three. **Awaiting verification by a lane other than QE** |
| **Found** | 2026-08-02, by QE, reading C-020 and noticing it was filed under `Closed` while marked `OPEN` |

**Steps to reproduce.**

```bash
awk '/^## C-/{i=$0} /^\| \*\*Status\*\*/{print i" -> "$0}' docs/LANE_COORDINATION.md
python3 infra/kpi.py | grep Coordination      # 18 · 3 closed
```

**Expected.** Items under `## Closed` are closed. `state-check` and `kpi` both count *"items appearing after the `## Closed` heading"*, so that heading is load-bearing.

**Actual.** The section is inverted. **The three items below `## Closed` — C-015, C-017, C-020 — are all `OPEN`**, including the one blocking all of M7. **The two carrying `ANSWERED` — C-001, ratified as ADR-0036, and C-016 — are above it.** Lanes append new items at end of file, which has been past the heading since it was introduced.

**Consequence beyond the count.** The rule this heading serves is *"a register that only grows has become the discussion log it is not allowed to be"* — and `state-check` only fires that finding when **zero** items are closed. Three phantom closures have kept it silent across every cycle since. **A check whose input is wrong is not a check** (§2).

**Fix.** Move `## Closed` to end of file and relocate C-001 and C-016 beneath it. **Deliberately deferred to the next cycle rather than done now**: Lane A's branch adds 196 lines to this file, and reordering it today would hand that lane a conflict for no gain. It is reconciled where reconciliation belongs — stage 3, with the lane's changes in hand.

---

### B-020 · `state-check` reads a task id anywhere in a board row, including the explanation of why a lane *cannot* take it

| | |
|---|---|
| **Module** | Repository tooling — `infra/state-check.py`, rule 5c(a) |
| **Current assignee** | **Lane B**, inside [TASK-005](BACKLOG.md) — that task is *"`state-check` learns the backlog"*, and this is the same code |
| **Severity** | 🟡 — advisory output only, but it is the failure mode that teaches people to ignore an advisory |
| **Status** | `OPEN` |
| **Found** | 2026-08-02, by QE, writing a board row that explained which tasks Lane B could **not** claim |

**Steps to reproduce.** Put a task id in a row's `Next action` cell for a lane that does not hold it, then:

```bash
python3 infra/state-check.py
#  ·  TASK-002 is claimed by Lane A and Lane B at once.
```

**Expected.** A task is *claimed* by the lane whose **`Task` column** names it.

**Actual.** `board_rows` scans the entire line — `re.findall(r"\bTASK-(\d+)\b", row)` — so a row saying *"Lane A holds TASK-002, which is why I am idle"* registers as a competing claim. The contested-claim check then fires on the one arrangement it should read as correct.

**Fix.** Read the `Task` column only: split the row on `|` and take the second field, exactly as the lane name is already taken from the first. The prose in the remaining cells is explanation, not assertion.

**Why it is worth fixing rather than working around.** The board's own rule is *"a row names a `TASK-nnn`"* precisely so that *"are these the same task?"* is a fact. **A checker that punishes precise prose pushes rows toward vague prose**, which costs the board the property the ids were introduced to give it — and today's workaround was exactly that: the ids were removed from Lane B's cell to silence a check that was wrong.

---

### B-019 · The constitution's branch table now says two different things about `integration`

| | |
|---|---|
| **Module** | **none** — `CLAUDE.md`, on `lane-a-product-surface` only. It has not reached `main` |
| **Current assignee** | **Lane A**, to remove during the B-018 rebase — it is that lane's edit |
| **Severity** | 🟠 — a governing rule that contradicts itself is followed differently by two readers |
| **Status** | **`VERIFIED`** — QE, 2026-08-02, reproduced from the original steps rather than the diff: the duplicate row is gone and the survivor is the correct one, retaining the claim-commit exception. **The `BACKLOG.md` half remains the product owner's** |
| **Found** | 2026-08-02, by QE, reading `16896ca` during validation |

**Steps to reproduce.**

```bash
git show origin/lane-a-product-surface:CLAUDE.md | grep -c '^| `integration` | Permanent'
# 2
```

**Expected.** One row per branch in the *Branches and promotion* table. **Truth has exactly one authoritative representation** (§2).

**Actual.** `16896ca` **appended** revised `integration` and `lane-*` rows instead of replacing the originals, so the table carries both. They disagree on the rule that matters most: the surviving original says *"a lane may fast-forward `integration` with a claim-only commit — that is the arbitration point, and it is the only exception"*, and the addition says *"**QE only.** A lane rebases and pushes."* **The first is correct and load-bearing** — it is what makes the Task Claim Protocol atomic, and `certification-guard.py --audit-claims` enforces it. The second would silently disable claim arbitration.

**Fix.** Keep the original `integration` row verbatim, including the claim-commit exception. Keep the *new* `lane-*` row, which is the one this refinement actually changed. Delete the other two.

**The finding underneath it, and it is larger than the table.** `CLAUDE.md` is 🔴 in the Change Budget and *"Product owner"* in *Shared files have one owner*, and `16896ca`, `f262d2c` and `835388f` wrote 74 lines of it from a feature lane. **The content is not the problem** — it matches what the product owner has since ratified, and *Continuous execution* is a genuine improvement. **The concurrency is:** two sessions editing the constitution on separate branches produced a contradiction that neither could see, and no gate reads that file.

**The same branch does it a second time, in [`BACKLOG.md`](BACKLOG.md).** `f28792d` **inserts two new `READY` tasks** — TASK-018 and TASK-019, PP-02 and PP-03 — and moves TASK-015 out of `BLOCKED`. The rule is explicit: *"a lane never reorders, reprioritizes, removes, or inserts `READY` work without the product owner"*, and *"a lane writes **only** its claim"*. **Again the content looks right**: all three derive from the ratified [ADR-0036](architecture/adr/0036-target-account-contract.md), and TASK-015's unblocking is argued rather than waived — its blocker is being built by the same lane in the same effort.

**Both need the product owner, not QE.** Either the rows are ratified where they stand, or Lane A withdraws them and they are re-entered by their owner. **QE will not decide it**, and will not certify the branch while it is undecided — a lane that can add its own `READY` work has taken priority, however good the work is.

---

### B-018 · Lane A's branch carries two of Lane B's pre-rebase commits and will not fast-forward

| | |
|---|---|
| **Module** | **none** — repository process. The affected branch is `lane-a-product-surface` |
| **Current assignee** | **Lane A** — it is that lane's rebase, and §20e reserves conflict resolution to the lane that is rebasing |
| **Severity** | 🟠 — four finished slices, two of them executable and substantial, cannot be validated |
| **Status** | `OPEN` |
| **Found** | 2026-08-02, by QE, taking `1a348ef` into lifecycle stage 1 |

**Steps to reproduce.**

```bash
git fetch origin
git merge-base --is-ancestor origin/integration origin/lane-a-product-surface   # exit 1
git log --oneline origin/integration..origin/lane-a-product-surface | tail -2
#   945e120 M7 returns to WAITING, and Lane B rescans rather than waits
#   a599201 Claim M7 — Timeline, and why it cannot start
```

**Expected.** A branch handed to QE fast-forwards onto `integration` (§20e, *Completion* step 3: the lane rebases and resolves its own conflicts).

**Actual.** The branch's merge base with `integration` is `f80f57d` — a `main` commit from an earlier Closeout — and it carries **two commits that belong to Lane B**: `a599201` and `945e120`, the M7 claim and its release. Both are already on `integration` under different hashes (`4c4b0d3`, `0a86d7a`), rebased there when QE integrated them. Replaying the branch therefore replays two commits whose content is already present, and `a599201` conflicts in [`ACTIVE_ASSIGNMENTS.md`](ACTIVE_ASSIGNMENTS.md) and [`LANE_COORDINATION.md`](LANE_COORDINATION.md).

**The fix is two commands, and it is Lane A's.**

```bash
git checkout lane-a-product-surface
git rebase origin/integration      # git skips 945e120 automatically
git rebase --skip                  # a599201 — Lane B's, already on integration
```

**Then re-run the gates on the rebased branch** (*Completion* step 4 — rebasing changes the program), push, and set the row back to `IN VALIDATION`. **The implementation area does not move**: Product Surface and Provider Platform stay with Lane A throughout.

**Two findings worth carrying, both larger than the rebase.**

**One — a lane branch acquired another lane's commits.** It happened at `6eb8cb0`, where Lane A branched from a point that already held Lane B's unrebased claim rather than from `integration`. Startup step 1 exists to prevent exactly this, and the cost is invisible until the branch is handed over — nothing fails while the lane is working. **Worth checking at push time rather than at merge time**, which is a `state-check` rule somebody could write.

**Two — this is what the certified-commit rule looks like from the other side.** QE rebases lanes onto `integration` at merge, so a lane branching from another lane's *pre-merge* commit is building on a tree that will never exist again. **Branch from `integration`, always** — never from another lane's branch, however current it looks.

---

### B-017 · A lane's merged slice disappeared from `integration`, and the backlog reoffers it

| | |
|---|---|
| **Module** | **none** — repository process |
| **Current assignee** | **none — not assignable.** [C-010](LANE_COORDINATION.md) |
| **Severity** | 🟠 — work was lost from the integration line, and the queue now offers a task that was built |
| **Status** | `OPEN` |
| **Found** | 2026-08-02, by Lane B, on the startup workflow for its next assignment |

**Steps to reproduce.** On `integration` at `f80f57d`:

```bash
git merge-base --is-ancestor 9c32daa origin/integration   # exit 1
grep -c "5d — the collision" infra/state-check.py          # 0
ls backend/tests/test_claim_collisions.py                  # No such file
```

**Expected.** `9c32daa` — *TASK-005, state-check reads the claims that have not merged yet* — was committed, pushed to `lane-b-commercial-profile`, and fast-forwarded onto `integration` (`c8a16c0..9c32daa`). It should be on `integration` or deliberately superseded with that recorded.

**Actual.** It is on neither. `integration` was rebuilt: Lane B's two TASK-001 commits were **rebased** and survive as `a062adf` and `cc9a320`, and the **two TASK-005 commits were dropped** — the claim (`626e343`) and the implementation (`9c32daa`). Nothing records the decision.

**Nothing is unrecoverable.** `9c32daa` is intact on `origin/lane-b-commercial-profile` and, incidentally, on `origin/lane-a-product-surface`, which rebased onto it.

**Why it is worth a row rather than a shrug.** [`BACKLOG.md`](BACKLOG.md) now reads `TASK-005 · READY`, with the note *"what remains is the id-level checking"* — **which is what `9c32daa` implemented, with twelve tests.** The next lane to run the Task Claim Protocol will claim it and build it again. That is the duplicate implementation the protocol exists to prevent, arriving through the register instead of through a race.

**It may well have been deliberate, and that is the point.** QE's `e1d2fa6` fixed the same problem better — claims now go to `integration`, which is the option Lane B recommended first in its own C-019 — and with claims in one place a cross-branch detector is largely redundant. **If TASK-005 was superseded, the defect is only that nothing says so**: a lane cannot tell a supersession from a lost commit, and the two call for opposite responses.

**For whoever takes it.** Decide TASK-005's real state and record it: `DONE` (superseded, with `e1d2fa6` named), or `READY` with `9c32daa` cherry-picked back, or `READY` with its note corrected so it no longer asks for work that exists. **Also worth a rule:** when a Closeout rebuild drops a lane's commit, the drop is named in the Closeout message — the rebuild is legitimate, the silence is not.

---


### B-015 · The certification audit passes vacuously in every lane's clone

| | |
|---|---|
| **Module** | **none** — repository process, `infra/certification-guard.py` |
| **Current assignee** | **none — not assignable.** [C-010](LANE_COORDINATION.md), and this is a fifth defect in that gap |
| **Severity** | 🟠 — **the audit reports success while examining nothing.** No history is wrong today; the check that would notice is inert wherever a lane runs it |
| **Status** | **`FIXED`** — QE, 2026-08-02. **Awaiting verification by somebody other than QE** |
| **Found** | `a9cc204`, by Lane B while verifying [B-014](#b-014--two-commits-reached-main-outside-certification-and-nothing-noticed) under [TASK-001](BACKLOG.md) |

**Steps to reproduce.** From any feature lane's clone, on a lane branch:

```bash
python3 infra/certification-guard.py --audit-main
```

**Expected.** The 12 commits promoted since ratification are audited, as they are when the same logic runs against the ref holding the promoted history.

**Actual.**

```
audit — no commit has been promoted since the rule was ratified.
```

**Exit code `0`.** Nothing was examined and the run reports success.

**The cause is one word.** [`certification-guard.py:162`](../infra/certification-guard.py#L162) resolves the range `f"{RULE_RATIFIED_AT}..main"`, and `main` is the **local** ref. Line 165 does the same for `_is_ancestor(c, "main")`.

**A feature lane's local `main` is always stale, by design.** A lane never checks out `main` and never promotes to it — QE does, on its own clone. This clone's `main` sits at `f996a42`, **35 commits behind `origin/main`**, and `f996a42..` contains none of the promoted work, so the range is empty and the audit short-circuits on `if not commits`.

**Proof it is the ref and not the history.** The same script with `main` → `origin/main`, changed nowhere else, reports `12 commit(s) … 0 violations. The guarantee holds.` The audit is correct; it is pointed at the wrong ref.

**Why it is worth a row.** This is the failure mode [B-014](#b-014--two-commits-reached-main-outside-certification-and-nothing-noticed)'s own text names — *a guard that cannot fail is documentation pretending to be code* — reappearing one level up. The guard **can** fail, and does when it sees the real history; but every lane that runs it as documented gets a green result that means nothing, and a green result is the one nobody investigates. It is **Decorative Logic** in the sense `CLAUDE.md` §2 defines: removing the check would not change the property it appears to protect, for the people most likely to run it.

**The fix, for whoever takes it.** Resolve the promoted ref explicitly rather than trusting a local branch name — `origin/main`, or a `--ref` argument, or `git rev-parse --verify` on both and prefer the one that is ahead. **And make the empty range loud rather than silent:** *"no commit has been promoted"* and *"the ref you gave me has no promoted commits on it"* are different facts, and today they print the same sentence and the same exit code. The second should be an error.

**Not fixed here.** `infra/` has no assignable lane ([C-010](LANE_COORDINATION.md)) and Lane B is verifying, not fixing. Reported rather than repaired, which is the correct alternative to touching another owner's file.

---

### B-016 · The documented startup command reads a key file nothing creates

| | |
|---|---|
| **Module** | repository documentation — [`docs/RUNNING.md:54`](RUNNING.md) |
| **Current assignee** | **QE** — `RUNNING.md` is QE's (`CLAUDE.md` §20e) |
| **Severity** | 🟡 — the API still starts; the key is silently empty, and the symptom appears later as *"signed in, every screen empty, everything 401s"* |
| **Status** | **`FIXED`** — QE, 2026-08-02. **Awaiting verification by somebody other than QE** |
| **Found** | `a9cc204`, by Lane B while verifying [B-009](#b-009--the-documented-command-for-starting-the-api-cannot-start-the-api) under [TASK-001](BACKLOG.md) |

**Steps to reproduce.** From a fresh clone, follow [`RUNNING.md`](RUNNING.md) exactly: `cp backend/.env.example backend/.env`, `npm install`, `npm run keys:generate`, `make demo`. Then copy the documented backend command, which contains:

```bash
SIGNORA_JWT_PUBLIC_KEY="$(cat .dev-keys/public.pem)" \
```

**Expected.** The public key, as the preceding steps produced it.

**Actual.** `cat: .dev-keys/public.pem: No such file or directory`, and `SIGNORA_JWT_PUBLIC_KEY` is set to the **empty string**. The API starts anyway — `Application startup complete` — so nothing announces the problem at the moment it is caused.

**`.dev-keys/` is never created by anything in this repository.** It appears exactly once, in that command. [`frontend/scripts/generate-keys.ts`](../frontend/scripts/generate-keys.ts) does not write PEM files — it prints `SIGNORA_JWT_PRIVATE_KEY=` and `SIGNORA_JWT_PUBLIC_KEY=` lines to paste into `frontend/.env.local` and `backend/.env`, which is what the setup step above tells the reader to do. **The command is a leftover from a file-based mechanism that no longer exists.**

**The sharp edge, and it is stated as an inference rather than a measurement.** The reader has just pasted the correct key into `backend/.env`. An environment variable set on the command line takes precedence over a `.env` value in pydantic-settings, so **the documented command plausibly overrides a correctly configured key with an empty one** — turning a working setup into the 401 symptom that [`RUNNING.md:203`](RUNNING.md) already has a troubleshooting row for. **Lane B did not verify the override**, only that the file is absent and the variable ends up empty. Confirming it is the fix's first step.

**The fix, for whoever takes it.** Delete the `SIGNORA_JWT_PUBLIC_KEY` line from the command block — the key is already in `backend/.env` by then, which is the mechanism `keys:generate` actually implements. **Same class as [B-009](#b-009--the-documented-command-for-starting-the-api-cannot-start-the-api), in the same command block:** *"every command below is copy-pasteable from a fresh clone"*, and one line of it is not.

**Fixed 2026-08-02.** The line is gone from the command block, with a comment beside it saying why it is absent — the key reaches the backend through `backend/.env`, which is the mechanism `keys:generate` actually implements. **`.gitignore` gains `*.pem` and `.dev-keys/`** so that a reader who creates the directory by hand, as Lane B did while verifying, cannot commit a private key. **Lane B's inference about the override was not tested by QE either**, and the fix does not depend on it: a variable read from a file that does not exist is wrong regardless of precedence.

**A second, smaller note for the same fix.** `.gitignore` covers `.env` and `.env.*` but has **no entry for `.dev-keys/` or `*.pem`**. Nothing creates that directory today, so nothing is at risk — but a reader who takes the command literally and creates it by hand, as Lane B did while verifying, ends up with an **RSA private key as an untracked, unignored file**. If the command block keeps any reference to a key directory, the ignore rule belongs with it (`CLAUDE.md` §13).

---

### B-002 · `make smoke` cannot run while any dev server is up

| | |
|---|---|
| **Owner** | Lane QE |
| **Severity** | 🟡 |
| **Status** | `OPEN` |
| **Found** | `73d1c28` |

**Steps to reproduce.** Start `npm run dev` (port 3000). Run `make smoke`.

**Expected.** Either a green run, or a failure that names the cause.

**Actual.** `✗ stack did not reach healthy` at stage 2. The real cause — `failed to bind host port 0.0.0.0:3000: address already in use` — is only visible in `docker compose logs`, and the reported message sends the reader looking at the application.

**Why it matters more now.** With three lanes there are more dev servers running more of the time, and `make smoke` is a QE gate on `integration`. Documented in `docs/RUNNING.md`; the honest fix is a preflight port check in `infra/smoke.sh`, which is QE's own file.

---

### B-003 · A lane following `RUNNING.md` exactly cannot run its own suites

| | |
|---|---|
| **Owner** | Integrator — `docs/RUNNING.md` |
| **Severity** | 🟡 |
| **Status** | `OPEN` |
| **Found** | `960b604`, by Lane B at the start of a slice |

**Steps to reproduce.** Follow [RUNNING.md § Running a lane](RUNNING.md#running-a-lane) exactly — export `SIGNORA_TEST_APP_DATABASE_URL` and `SIGNORA_TEST_ADMIN_DATABASE_URL`, nothing else. Then run the impacted suites the way §20e requires during a slice: `cd backend && uv run pytest tests/<module>`.

**Expected.** The suite runs against the lane's own database.

**Actual.** Every test errors in setup with `RuntimeError: This suite TRUNCATES every table after each test. Set SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1…`, and `tests/integration` additionally fails to **collect** — `test_worker_retry.py` builds `Settings()` at import time and raises a Pydantic `ValidationError` without `SIGNORA_DATABASE_URL`.

**Why it is a documentation defect rather than a code one.** Both variables are correct and deliberate — the truncation guard exists because the invariants once emptied a real stack. They are documented in `docs/SESSION_HANDOFF.md` §Local prerequisites and set by `make test`. But **a lane does not run `make test`** (it truncates the wrong database and §20e forbids repository-wide gates during a slice), and `RUNNING.md` is the document a lane is told is authoritative for its environment. The two disagree, and the lane-facing one is the incomplete one.

**The fix, for whoever takes it.** Add both to step 2 of § Running a lane, beside the two already there. No code change:

```bash
export SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1
export SIGNORA_DATABASE_URL=postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:5432/signora_lane_<x>
```

**Not a defect, checked while reproducing:** Redis needs no per-lane database. `RUNNING.md` already states *"one Postgres, one Redis, many databases — nothing in the test path touches Redis today"*, and that is still true.

---

### B-004 · `provider_watermark` cannot tell two target accounts apart

| | |
|---|---|
| **Owner lane** | **Lane A** |
| **Affected module** | `provider_platform` — `provider_watermark`, migration `0007` |
| **Severity** | 🟠 unreachable today · 🔴 the moment a workspace watches two accounts |
| **Status** | `OPEN` |
| **Found** | `f6b6a41`, while answering [`C-001`](LANE_COORDINATION.md#c-001--the-target-account-contract) |
| **Fix belongs to** | The slice that builds the `target_accounts_changed` consumer. **Not to be fixed opportunistically** — the consumer is what makes it reachable, and fixing one without the other leaves a schema change nothing exercises |

**Trigger conditions.** All three must hold, and none does yet:

1. Commercial Profile publishes a target-account list with **two or more entries** in one workspace (M12.5 slice 5);
2. Provider Platform consumes it and runs a sync **per subject** (Lane A, unbuilt);
3. A second sync runs for the same `(provider, capability)` in that workspace — that is, the **second account is fetched at all**.

**Steps to reproduce.** Not reproducible today, and the reason is the interesting part: `RunProviderSync` has accepted a `subject` since M2.1 and **nothing has ever supplied one** except the Provider Simulation Framework, which drives every subject through one scenario without ever re-reading a watermark between two of them. Once the trigger conditions hold: declare accounts *A* and *B*, sync *A*, then sync *B* against the same provider and capability.

**Expected.** Each watched account carries its own incremental position, so what has been fetched for *A* has no effect on what is fetched next for *B*.

**Actual.** `uq_provider_watermark_scope` is `(workspace_id, provider, capability)` — **there is no `subject` in the key, and none in the row.** One watermark covers every account in the workspace for that provider and capability. Syncing *A* advances the position that *B*'s next sync reads as its `since`, so *B* fetches only what changed after *A*'s run and **silently skips its own history**.

**Impact.** A customer sees one account richly enriched and another mysteriously thin, with **nothing in the product explaining the difference** — no error, no warning, no gap in the evidence drawer, because from the pipeline's point of view the provider simply returned little. It degrades every stage downstream: fewer claims, fewer observations, fewer business events, a lower buying score, and an account that looks genuinely quiet rather than under-fetched. **It is a data-completeness defect that presents as a commercial conclusion**, which is the worst way for one to present in this product.

The cost is also asymmetric: a full re-fetch after the fix recovers it, but every conclusion drawn in the meantime was drawn on partial evidence and was shown to a customer as though it were not.

**The fix, for whoever takes it.** `subject` joins the unique constraint and the lookup. The domain already carries the subject on every `ProviderRequest`, so nothing above the repository changes — it is a migration and a widened `where`. The same slice must build the consumer, per *Fix belongs to* above.


---

### B-005 · Removing a product locks the customer out of the ideal customer, committee and focus

| | |
|---|---|
| **Owner** | **Lane B** — `commercial_profile` (frontend) |
| **Severity** | 🟠 — wrong behaviour a customer would hit, with no way out through the product |
| **Status** | `FIXED` — awaiting QE. All three editors, one shared rule, and a mutation check |
| **Found** | `80d9511`, by Lane B in the slice-4 product review |

**Steps to reproduce.** Declare two products. Describe an ideal customer for both. Remove the second product from the catalog. Now edit the *first* product's ideal customer and save.

**Expected.** The edit saves. The removed product's profile is history, and history does not block a new declaration.

**Actual.** `422 icp_unknown_product` — *"you cannot describe who buys a product you have not said you sell"* — naming a product **that is no longer on the screen**. The customer cannot clear it either: the remove path re-sends the whole declaration too. **The section is unusable until the product is added back.**

**Why.** All three editors send *everything stored*, which is correct for a whole-statement `PUT`, and render only entries whose product is in the current catalog. The two diverge the moment a product is removed. The server is behaving correctly — the client is sending a declaration the customer cannot see.

**Observed, not inferred.** Rendering `IcpEditor` with a catalog of one product and a declaration holding two profiles — one for the surviving product, one for a removed one — then clicking *Remove the description for Revenue Cloud*:

```
ON SCREEN:            removed product NOT visible
SENT product_ids:     ["eeeeeeee-…"]      ← only the removed product's profile
SENT the removed one? true
```

The request the customer's click produces consists **entirely of a declaration for a product that no longer exists**. Their own edit is discarded from the payload and the invisible one is all that is sent, so the server refuses the whole request. It is not merely a confusing message: the visible work is dropped before it leaves the browser.

**Affects identically:** the ideal customer, the buying committee, and the focus.

**Fixed.** `components/commercial/catalog-scope.tsx` holds the rule once — *the catalog is the authority on which declarations still exist* — and all three editors read `kept` rather than what they were handed. An orphaned entry is **dropped and announced**: `DroppedWithTheirProduct` says it before the save, and says the version holding it is kept, because dropping it quietly would have been a second and quieter defect.

**Regression tests** in each editor's own suite, plus a **mutation check**: reintroducing the defect in `icp.tsx` alone makes `B-005 · is never sent back to the server` fail, and restoring it makes it pass. A guard that cannot fail is documentation pretending to be code.

---

### B-006 · Three of the four sections vanish silently when their query fails

| | |
|---|---|
| **Owner** | **Lane B** — `commercial_profile` (frontend) |
| **Severity** | 🟡 |
| **Status** | `FIXED` — awaiting QE. Page-level test, the same shape as D36's |
| **Found** | `80d9511`, by Lane B in the slice-4 product review |

**Steps to reproduce.** Make `GET /workspaces/{id}/icp` fail — stop the API after the catalog has loaded, or block the request.

**Expected.** A message saying the ideal customer could not be loaded, in the same words the catalog already uses: *a fault in Signora, not a missing declaration*.

**Actual.** The section is simply absent. The customer sees Products and nothing else, with no explanation — **an outage is indistinguishable from a feature they do not have.**

**Why.** `settings/products/page.tsx` renders each section on `data && <query>.data`, and only the catalog's `isError` produces copy. The other three queries' error states are never read.

**Fixed.** Each of the four sections reports its own failure through a page-local `CouldNotLoad`, in wording that distinguishes *Signora failed* from *you never declared one* and states that nothing has been lost.

**Regression test** is `frontend/tests/components/your-business.test.tsx` — **page-level deliberately**, because the defect never lived in a component and every component test passed throughout its life. The same reasoning as `first-run.test.tsx` and D36.

---

---

### B-007 · The migration runner locks one database and migrates another

| | |
|---|---|
| **Module** | **none** — `apps/migrate/` is composition-root production code |
| **Current assignee** | **none — not assignable.** See *[Defects in code that belongs to no module](#defects-in-code-that-belongs-to-no-module)* and [C-010](LANE_COORDINATION.md) |
| **Severity** | 🟠 — three tests fail on the documented setup path today; the split-brain case is latent |
| **Status** | `OPEN` |
| **Found** | `f996a42`, during the QE lane's first full-suite run |

**Steps to reproduce.** From a fresh clone, follow [`RUNNING.md`](RUNNING.md) exactly: `cp backend/.env.example backend/.env`, then `make test`.

**Expected.** A green suite. `backend/.env` is the documented way to configure the backend, and `SIGNORA_DATABASE_URL` is in `.env.example`.

**Actual.** Three failures in `tests/integration/test_migration_runner.py::TestConcurrencySafety`, all ending in `RuntimeError: SIGNORA_DATABASE_URL must be set to run migrations.` Exporting the same variable into the shell makes all three pass.

**The cause is one fact with two authorities.** `apps/migrate/main.py::_run_with_lock` takes the advisory lock on a connection built from `settings.database_url` — which pydantic-settings resolves from the environment **or `backend/.env`**. It then calls `_upgrade_to_head()`, which builds a fresh `Config("alembic.ini")` and lets [`migrations/env.py:57`](../backend/migrations/env.py#L57) resolve the URL again, from `os.environ` **only**. The settings object governs the lock; the environment variable governs the migration, and nothing reconciles them.

Three consequences, in ascending order of seriousness:

1. **Configured by `.env` alone** — the documented path — the lock is taken and the migration then fails.
2. **Configured by both, disagreeing** — which is exactly what a three-lane repository invites — the runner serialises on database A and migrates database B. The concurrency guarantee the module exists to provide is void, and silently.
3. **`SIGNORA_DATABASE_URL` is a third lane variable that [`RUNNING.md` § Running a lane](RUNNING.md#running-a-lane) does not mention.** It lists two. A lane that sets only those two runs these tests against whatever the shared default names.

**Why the suite has been green anyway.** `SESSION_HANDOFF.md` §1 documents the variable as a shell export, and every run so far has been from a shell that had it. Nothing asserts the two resolutions agree, so the day they disagree there is no test to notice.

**Half of this is now closed.** [`RUNNING.md` § Running a lane](RUNNING.md#running-a-lane) lists all three variables and says why the third cannot live in `backend/.env` (2026-08-01, product-owner direction). **The row stays `OPEN` because the defect is the code, not the documentation** — one fact still has two authorities, and documenting a trap is not removing it.

**For whoever takes it.** One authority. `_upgrade_to_head` should be handed the URL the lock was taken on rather than re-deriving it — `alembic.ini`'s `sqlalchemy.url` is settable from `Config` in-process. The regression test is the one this bug describes: set the two to different databases and assert the runner refuses rather than proceeds.

---

---

### B-008 · The suite says it truncates every table, and truncates five

| | |
|---|---|
| **Module** | shared test infrastructure — `backend/tests/conftest.py` |
| **Current assignee** | QE |
| **Severity** | 🟡 — no test is known to fail because of it; the false claim is the confirmed defect |
| **Status** | `OPEN` |
| **Found** | `f996a42`, during the QE lane's first full-suite run |

**Steps to reproduce.** Record `select count(*) from claim` in the target database. Run the suite. Record it again.

**Expected.** The number the suite started with. `require_explicit_consent_to_truncate` refuses to run at all unless you confirm the database is disposable, and the reason it gives is *"This suite TRUNCATES every table after each test."*

**Actual.** It grows, permanently. `signora_lane_qe` went from **1 row to 15,931** across one run, and `signora_lane_a` currently carries 22,795 rows of accumulated residue. `clean_database` truncates `membership, workspace, outbox_event, processed_event, dead_letter_event CASCADE` — **five of the schema's thirty-one tables** — and `membership` is the only table in the database with a foreign key to `workspace`, so `CASCADE` reaches nothing else.

**Why it matters, in order.**

1. **The claim is false where a developer reads it** — in the `RuntimeError` that gates the whole suite, and repeated in [`RUNNING.md`](RUNNING.md) (*"`make test` truncates every table in the same database"*). The practical advice there is still right for the wrong reason: truncating `workspace` does empty the Playground's screens.
2. **Residue is a hidden input** (`CLAUDE.md` §2). Every run starts from the accumulated state of every previous run. Tests pass today because each mints a fresh `workspace_id` and the queries are workspace-scoped — an accidental guarantee, not an enforced one.
3. Lane databases grow without bound.

**For whoever takes it.** Truncate the tables the suite actually writes, or state honestly what is cleaned and why the rest need not be. **Do not widen the truncation without running the suite twice in one database** — a test that has been passing on residue will fail, and that failure is the finding.

---

---

### B-009 · The documented command for starting the API cannot start the API

| | |
|---|---|
| **Module** | repository documentation — `docs/RUNNING.md`, `Makefile`, `README.md` |
| **Current assignee** | QE |
| **Severity** | 🟠 — it stopped a reviewer at the first step, and the error did not name the cause |
| **Status** | **`FIXED`** — fixed by the QE lane under product-owner direction, 2026-08-01. **Independent verification complete — result `PASS`**, Lane B, [TASK-001](BACKLOG.md), evidence below. **`VERIFIED` is QE's to set** |
| **Found** | `f996a42`, QE lane, first attempt to start the product |

**Steps to reproduce.** Run `make demo`. Copy the command it prints — the same one in [`RUNNING.md`](RUNNING.md) lines 41 and 153:

```bash
cd backend && uv run uvicorn apps.api.main:app --reload --port 8000
```

**Expected.** A running API. `RUNNING.md` opens with *"Assume nothing is already running and nothing is already known. Every command below is copy-pasteable from a fresh clone."*

**Actual.**

```
ERROR:    Error loading ASGI app. Attribute "app" not found in module "apps.api.main".
```

`apps/api/main.py` exports **only the factory** `create_app(settings=None)`; there is no module-level `app`. The working invocation exists and is used everywhere a machine reads it — `backend/Dockerfile:78` and `infra/docker-compose.prod.yml:92` both say `apps.api.main:create_app --factory`. **Only the three places a human reads are wrong**, which is exactly why no gate catches it: `make smoke` starts the API from the container command.

Three sites: `docs/RUNNING.md:41`, `docs/RUNNING.md:153`, `Makefile:80`. `README.md` sends the reader to the first of them.

**Why it matters beyond the typo.** *Every completed slice is demoable by a non-engineer* is binding from M12.3 (`CLAUDE.md` §2), and the instructions for the demonstration do not work. A reviewer who has never seen this repository gets an ASGI import error and no route to the answer — the correct form is only discoverable by reading a Dockerfile.

**The fix.** `uv run uvicorn apps.api.main:create_app --factory --reload --port 8000`, in all three places. Verified working against the Playground during this review.

**The regression test.** `backend/tests/test_documented_commands.py` extracts every `apps.api.main:<target>` from `RUNNING.md`, the `Makefile`, the `Dockerfile` and `docker-compose.prod.yml`, and asserts each target exists on the real module and is invoked with `--factory` when it is one. **Proven to fail:** reintroducing `:app` in the `Makefile` produced `Makefile:80 tells a reader to start the API at 'apps.api.main:app', which does not exist`. A control test fails if the pattern ever stops matching, so the file cannot quietly become decoration.

**Two notes on the resolution, both deliberate.**

**When the fix was written the three sites were Integrator-owned**, and QE edited them under explicit product-owner direction. Later the same day the Integrator role was absorbed into QE and the files became QE's outright, so the exception is now moot — recorded because the sequence is the record, not because it is still needed.

**QE fixed this, so QE may not close it.** `VERIFIED` is set by someone else reproducing the original steps from a clean shell — not by reading the diff, and not by the lane that wrote the fix. **The role merge does not dissolve this rule**; it is the one place QE genuinely needs a second pair of eyes.

### Verification report — Lane B, 2026-08-02, [TASK-001](BACKLOG.md)

| | |
|---|---|
| **Verification performed** | Reproduce the documented startup from the original steps on a clone with no prior setup |
| **Result** | **`PASS`** |
| **Commands executed** | `cp backend/.env.example backend/.env` · the [`RUNNING.md:57`](RUNNING.md) command block verbatim · `curl localhost:8000/health` · `SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 uv run pytest tests/test_documented_commands.py` |
| **Environment** | Lane B clone at `a9cc204`; Python tier local, PostgreSQL and Redis in Docker; no `backend/.env` and no `.dev-keys/` at the start |
| **Defects discovered** | [B-016](#b-016--the-documented-startup-command-reads-a-key-file-nothing-creates) — the same command block reads a key file nothing creates |
| **Lifecycle** | **Not advanced.** `VERIFIED` is QE's to set on this evidence |

**From the original steps, never from the diff.** This clone had no `backend/.env` and no `.dev-keys/`, so the starting point was genuinely the one a new reviewer has.

| Check | Result |
|---|---|
| `apps/api/main.py` exports a module-level `app` | **No** — parsed the module: `create_app` only. The original command would still fail, which is why the fix was to the documentation |
| The **documented** command from [`RUNNING.md:57`](RUNNING.md), copy-pasted with its env block | **Started.** `Application startup complete`, no `Error loading ASGI app` |
| `GET /health` | **`200`** · `{"status":"ok","environment":"local"}` |
| All five `apps.api.main:` sites agree | **Yes** — `RUNNING.md:57`, `RUNNING.md:187`, `Makefile:80`, `Dockerfile:78`, `docker-compose.prod.yml:92`, every one `create_app` with `--factory` |
| `backend/tests/test_documented_commands.py` | **11 passed** |

**One thing the verification hit that is not this bug.** The regression test errors with `RuntimeError: This suite TRUNCATES every table…` unless `SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1` is set — **even though it touches no database**, being pure static analysis of documentation. A session-scoped fixture applies the guard to the whole suite. Harmless once known, and adjacent to [B-003](#b-003--a-lane-following-runningmd-exactly-cannot-run-its-own-suites). **Not opened as a defect** — the guard is correct and deliberately broad; recorded so the next person to run this file in isolation is not stopped by it.

---

---

### B-010 · Re-seeding the Playground orphans every narration, silently

| | |
|---|---|
| **Module** | the Playground — `backend/tests/playground/` · the *"stale versus absent"* half is the product surface |
| **Current assignee** | QE · Lane A for the brief half |
| **Severity** | 🟠 — M12.3's headline feature cannot be demonstrated at all |
| **Status** | `OPEN` |
| **Found** | `f996a42`, QE lane, first review pass over the Playground |

**Steps to reproduce.** `make demo-narrate`, confirm a brief narrates, then `make demo-seed`. Open any account brief.

**Expected.** *"Roughly ten of twelve accounts narrate"* ([RUNNING.md](RUNNING.md)), each with citations that open — the M12.3 slice.

**Actual.** `GET /workspaces/{w}/accounts/{a}/narration` returns **404 for all twelve**, measured 2026-08-01:

```
  ---> 0 of 12 accounts narrate
```

**And the narrations are not missing — they are orphaned.** `ai_narration` holds **748 rows** across **215 distinct subjects**, the newest written 2026-08-01 19:29, roughly an hour before this review. **Not one of them names a current account.** A re-seed mints new entity identifiers; a narration is an immutable historical fact keyed to the identifier it was written against, so it correctly survives and correctly stops resolving. Nothing says so on any screen or in any document.

**The same mechanism has left the Playground enormous.** `signora` carries **1,054,673 rows — 70,129 entities and 11,140 opportunities for a twelve-account demo.** Seeding clears the same five tables [B-008](#b-008--the-suite-says-it-truncates-every-table-and-truncates-five) describes and leaves every derived generation behind. The Playground is a haystack containing the demo.

**For whoever takes it.** Three separable pieces, and the first is worth doing alone:

1. **Say so.** `demo-narrate` must follow *every* `demo-seed`, not just the first. That is a `RUNNING.md` line, and QE's to write.
2. **The brief should distinguish *not narrated yet* from *narrated against evidence that no longer resolves***. The dialog already refuses to present today's facts as the ones the model saw ([D42](architecture/39-product-review-findings.md)); this is the same honesty one level up, and it is Lane A's.
3. **Do not "fix" it by deleting narrations.** A materialized AI artifact is a historical fact and is immutable (`CLAUDE.md` §2). The residue is a seeding question, not a retention one.

---

---

### B-014 · Two commits reached `main` outside certification, and nothing noticed

| | |
|---|---|
| **Module** | **none** — repository process |
| **Current assignee** | **none — not assignable.** [C-010](LANE_COORDINATION.md) |
| **Severity** | 🟡 — the changes were small, reviewed and correct; **the process gap is the defect** |
| **Status** | `FIXED` — the rule that prevents it was ratified 2026-08-02 and is enforced by `infra/certification-guard.py`. **Independent verification complete — result `PASS` on both cases**, Lane B, [TASK-001](BACKLOG.md), evidence below. **`VERIFIED` is QE's to set**, and [B-015](#b-015--the-certification-audit-passes-vacuously-in-every-lanes-clone) should be read before it is |
| **Found** | `e44819b`, by `certification-guard.py --audit-main` on its first run — **against the commits QE had just written** |

**Steps to reproduce.** `python3 infra/certification-guard.py --audit-main`, with `RULE_RATIFIED_AT` set to the certified commit `f669172`.

**Expected.** Every commit on `main` is certified, or changes nothing executable.

**Actual.** Two Closeout commits — `b5cc283` and `e44819b` — each modified `infra/state-check.py`, which is executable code, while carrying a Closeout message. **They were promoted without passing through certification at all**, because Closeout runs after promotion by design.

**Why it happened, and why it is worth a row.** The commit-binding rule did not exist when they were written; under the previous reading, certification bound to a *tree* and Closeout was documentation. `state-check.py` was edited during Closeout because that is when its defect was found, which felt like documentation work and was not. **A repository-wide gate is exactly the kind of thing that gets edited at the moment it is being used**, so this will recur unless something refuses it.

**The fix is the rule.** `CLAUDE.md` §20e now binds certification to an immutable commit, and `certification-guard.py --audit-main` proves that every commit on `main` since ratification is either certified or **verifiably** docs-only — a fact about paths, not about the commit message. `infra/` is deliberately **not** in the permitted set: `smoke.sh`, `disaster-recovery.sh` and the compose files decide whether a gate passes.

**For whoever verifies it.** Run the audit; it must report zero violations. Then edit `infra/state-check.py`, commit it to `main` with a Closeout message, and confirm the audit refuses it. **A guard that cannot fail is documentation pretending to be code**, and this one was written by finding a real violation on its first run.

### Verification report — Lane B, 2026-08-02, [TASK-001](BACKLOG.md)

| | |
|---|---|
| **Verification performed** | The audit against the promoted history, **and a deliberate violation to prove the guard can refuse one** |
| **Result** | **`PASS`** on both cases — 0 violations on real history; `REFUSED` with exit `1` on the probe |
| **Commands executed** | `python3 infra/certification-guard.py --audit-main` · in a throwaway clone: `git branch -f main 2c35d86`, an edit to `infra/state-check.py`, `git commit -m "Repository Closeout — a probe that must be refused"`, the audit again |
| **Environment** | A **throwaway clone** under the session scratchpad, deleted afterwards. **The probe was never committed to this repository and never pushed** |
| **Defects discovered** | [B-015](#b-015--the-certification-audit-passes-vacuously-in-every-lanes-clone) — the audit examines nothing, and reports success, wherever a lane runs it |
| **Lifecycle** | **Not advanced.** `VERIFIED` is QE's to set, and B-015 should be read first |

**Both halves run, and the negative case is the one that matters.** The violation was committed in a **throwaway clone** under the session scratchpad, never in the working repository and never pushed; the clone was deleted afterwards.

| Case | Result |
|---|---|
| **Positive** — audit against the promoted `main` (`2c35d86`) | **12 commits since ratification · 0 violations.** 4 certified · 7 inside a certified snapshot · 1 Closeout. *"The guarantee holds"*, exit `0` |
| **Negative** — `infra/state-check.py` edited, committed to `main` with a Closeout subject | **`REFUSED — 1 commit(s) reached main uncertified`**, naming the commit and the offending path, **exit `1`** |

**The guard can fail, and does.** It identified `infra/state-check.py` as executable despite the Closeout message, which is the precise distinction the fix exists to draw — a fact about paths, not about the commit subject.

**The claim in this row is therefore true**, and the property it asserts about `main` holds today.

> **But the verification also found the guard reporting a clean pass while examining nothing** — see **[B-015](#b-015--the-certification-audit-passes-vacuously-in-every-lanes-clone)**. That is a new defect in the fix's *reliability*, not a retraction of the fix: the guarantee above was confirmed by running the same logic against the ref that actually holds the promoted history.

---

### B-013 · The worker and the relay cannot start from a production image

| | |
|---|---|
| **Module** | **none** — `apps/worker/` is composition-root production code, plus `backend/pyproject.toml` |
| **Current assignee** | **none — not assignable.** [C-010](LANE_COORDINATION.md) |
| **Severity** | 🔴 — **two of the six production services crash-loop.** Nothing deployed would process an event |
| **Status** | **`FIXED`** — fixed by QE under product-owner direction, 2026-08-02. **Independent verification complete — result `PASS`**, Lane B, [TASK-001](BACKLOG.md), evidence below. **`VERIFIED` is QE's to set** |
| **Found** | `3f4e988`, by QE at lifecycle stage 1, the first `make smoke` run since 2026-07-31 |

**Steps to reproduce.** `make smoke`.

**Expected.** Twenty-one stages green.

**Actual.** `✗ relay is 'restarting', expected running` at stage 2. Both the worker and the relay restart forever:

```
File "/app/apps/worker/subscriptions.py", line 27, in <module>
    import httpx
ModuleNotFoundError: No module named 'httpx'
```

**The cause is one line in the wrong list.** `httpx>=0.27` is declared in `[dependency-groups].dev` of [`backend/pyproject.toml`](../backend/pyproject.toml), and [`backend/Dockerfile:40`](../backend/Dockerfile#L40) installs with `uv sync --locked --no-dev`. **Production code imports it at module scope** — `apps/worker/main.py:15` and `apps/worker/subscriptions.py:27`, and every AI Platform adapter besides. It is a runtime dependency that has always been classified as a test one; nothing noticed because the API imports it lazily and **the worker had no module-scope import until `subscriptions.py` arrived**.

**Why no test caught it.** Every suite runs in the dev environment, where `httpx` is present — it is what `pytest` uses for the API client. **Only `make smoke` builds the production images**, and `make smoke` had not run since 2026-07-31: it was blocked on this workstation first by a missing `make` ([B-011](#b-011--make-is-not-installed-on-this-workstation--not-a-repository-defect)) and then by a dev server holding port 3000 ([B-002](#b-002--make-smoke-cannot-run-while-any-dev-server-is-up)).

**This is what [B-012](#b-012--main-was-advanced-by-a-merge-commit-through-a-github-pull-request) cost, made concrete.** The change reached `main` through a pull request rather than through the lifecycle, so the gate that exists to catch exactly this never ran. **The defect is not that somebody wrote the import; it is that the promotion skipped stage 1.**

**For whoever takes it.** Move `httpx` from `[dependency-groups].dev` into `[project].dependencies`, `uv lock`, rebuild. It is not a new dependency — it is an approved one filed under the wrong heading, so this is a classification fix rather than an adoption ([ADR-0024](architecture/adr/0024-code-quality-and-static-analysis.md) is untouched). **The regression test is `make smoke` itself**, which is now the only thing that proves the production image can start — and it must run before every promotion, which is lifecycle stage 1.

**Fixed 2026-08-02.** `httpx>=0.27` moved into `[project].dependencies` with the reason recorded beside it, `uv lock` re-run, and **`make smoke` passes end to end — 21 stages, 125s**, having failed at stage 2 immediately before. Not a new dependency and no ADR required: it was an approved one filed under the wrong heading. **QE applied it under explicit product-owner direction**, because `apps/` and `pyproject.toml` have no assignable lane ([C-010](LANE_COORDINATION.md)) — and **QE may not verify its own fix.**

### Verification report — Lane B, 2026-08-02, [TASK-001](BACKLOG.md)

| | |
|---|---|
| **Verification performed** | A full `make smoke` run — the regression test this bug names as its own |
| **Result** | **`PASS`** — `PLATFORM SMOKE TEST PASSED`, 128s, 24 stage headings, zero failures |
| **Commands executed** | `bash infra/smoke.sh` |
| **Environment** | Lane B clone at `a9cc204`; production images built from the tree; ports 3000 and 8000 confirmed free first; `make` absent ([B-011](#b-011--make-is-not-installed-on-this-workstation--not-a-repository-defect)) |
| **Defects discovered** | None |
| **Lifecycle** | **Not advanced.** `VERIFIED` is QE's to set on this evidence |

**The regression test for this bug is `make smoke` itself**, as the fix says, so the verification is a full run from the original step. `make` is absent on this workstation ([B-011](#b-011--make-is-not-installed-on-this-workstation--not-a-repository-defect), `WONTFIX`), so it ran as `bash infra/smoke.sh` — the same script the target invokes.

**`PLATFORM SMOKE TEST PASSED` — 128s, 24 stage headings, zero failures.**

| The stage that failed before | Result |
|---|---|
| Stage 1 — images | ✓ API, worker, relay and frontend images built |
| **Stage 2 — startup** | ✓ **No `relay is 'restarting'`.** This is the exact assertion that failed |
| Stage 12 — event bus, relay, workers | ✓ workers consuming without error · ✓ **relay running without error**, having survived the database restart in stage 6 |
| Stage 15 — Security Invariants | ✓ 354 passed against the running stack |

**The two services that crash-looped now start from a production image and process events**, which is the property the bug says was broken. Nothing was read from the diff: the run builds the images from the tree and starts them.

---

### B-012 · `main` was advanced by a merge commit through a GitHub pull request

| | |
|---|---|
| **Module** | **none** — repository process, not code |
| **Current assignee** | **none — not assignable.** The process is the product owner's and QE's; see [C-010](LANE_COORDINATION.md) |
| **Severity** | 🟠 — no code is wrong; the repository's history and its stated invariant disagree |
| **Status** | `FIXED` — the branches were reconciled 2026-08-02. **Awaiting verification by someone other than QE** |
| **Found** | `d54f55b`, by QE while beginning a promotion |

**Steps to reproduce.** `git log --format='%h %p %s' -1 main` at `d54f55b`.

**Expected.** One parent. `CLAUDE.md` §20e: *"Fast-forward only, everywhere. No merge commits. `main` advances only from `integration`."*

**Actual.** Two parents — `d54f55b` is *Merge pull request #1 from GaneshDabhade/integration*, created on GitHub at 04:09 on 2026-08-02.

**What it cost.** `integration` then advanced three commits without the merge, so **`main` stopped being an ancestor of `integration`** and no fast-forward was possible in either direction. The next promotion could not have happened without either a second merge commit or a rewrite — which is exactly the state the fast-forward rule exists to prevent. It also crossed [ADR-0027](architecture/adr/0027-local-first-development.md): GitHub is version control, backup and future collaboration, and **a `git push` performs one action**. A pull request is a workflow, and the workflow is local.

**The reconciliation.** On the product owner's direction, **`integration` was rebased onto `main`** (`e1a34a6 053aa70 4d5f19f` → `bdb014f 5b1e388 3f4e988`) and force-pushed. `main`'s history was left untouched, including the merge commit — *correct a claim about the present; date a record of the past*. Lanes A and B rebase onto the new `integration` at their next startup, which their startup sequence already requires.

**Why it stays open as a record.** The merge is still in `main`'s history and always will be. This row is what explains it to whoever finds it, and the fix is procedural: **`main` moves by `git merge --ff-only` from `integration`, run locally by QE, and by nothing else.**

### Verification — Lane B, 2026-08-02. **Evidence only; the status is deliberately unchanged**

**This row is in the same condition as the three in [TASK-001](BACKLOG.md) — `FIXED` by QE, awaiting somebody else — but the task names three, and a lane does not widen `READY` work.** So the checks were run and recorded; **setting the status is left to the product owner or QE.**

| Check | Result |
|---|---|
| Merge commits on `main` since the reconciliation (`e44819b..origin/main`) | **None.** History is linear |
| `origin/main` and `origin/integration` related by fast-forward | **Yes** — `integration` is exactly 1 ahead, and that one is this task's claim commit |

**The reconciliation held**, and the condition that made the next promotion impossible is gone. The merge commit itself remains in history, as this row says it always will.

---

### B-017 · `state-check` reads the history table as a second claim

| | |
|---|---|
| **Module** | Repository tooling — `infra/state-check.py` |
| **Current assignee** | **Lane B** — it holds [TASK-005](BACKLOG.md), which added this check and is `IN VALIDATION` |
| **Severity** | 🟡 — advisory output only; nothing is blocked. **But it is a false positive that now fires on every completed task**, and an advisory nobody believes is worse than none |
| **Status** | `OPEN` |
| **Found** | `bff371b`, by Lane A while rescanning the backlog after TASK-004 |

**Steps to reproduce.** Have one task appear both in `ACTIVE_ASSIGNMENTS.md`'s **Current** table and in its **Recently completed** table. Run `python3 infra/state-check.py`.

**Expected.** Nothing. One lane holds the task; the second mention is history, and the two tables are different sections with different meanings.

**Actual.**

```
  ·  TASK-001 is claimed by B and Lane B at once. The Task Claim Protocol
     requires the later claim to be abandoned (CLAUDE.md §20e).
```

**Why.** `board_rows` selects **every** line in the file starting `| ` that contains `TASK-`, so it reads *Recently completed* as claims. The two tables also spell the lane differently — `Lane B` in Current, `B` in Recently completed — so the same lane compares unequal and looks like two lanes racing.

**Why it matters.** The check exists to make *"two lanes claimed one task"* a fact a machine can decide. **It now reports that fact falsely, on the most ordinary state the board has** — a task that was completed. The next real collision will arrive in a report that already contains one, and it will be read as more noise.

**For whoever takes it.** Scope the scan to the **Current** section, the way [`state-check.py`'s handoff check is already scoped](../infra/state-check.py) — *"scoped to the `Current` section deliberately"* is a comment that file already carries about a different check. **Do not fix it by renaming the column in one of the tables**: the section a row is in is what decides its meaning, and matching on lane spelling would leave the check reading history as intent.

---

---

## Verified

### B-001 · `signal_profile` reads the wrong row as "current"

| | |
|---|---|
| **Owner** | Lane A — `signal_engine` |
| **Severity** | 🟠 — latent today, 🔴 the moment the signal profile gets a write path |
| **Status** | **`VERIFIED`** — QE, 2026-08-02. Reproduced on `6aadea9`: `tests/signal_engine/test_profile_currency.py` writes a superseding version and asserts `current()` returns it, across all three tables, and passes in the promoted tree. Migration `0023` |
| **Found** | `1ae600d`, while building `commercial_profile` |

**Steps to reproduce.** Write a `SignalProfile` at version 1. Write a second superseding it (`supersedes = <v1 id>`). Call `SqlProfileRepository.current(workspace_id)`.

**Expected.** Version 2 — the profile in force.

**Actual.** Version 1, permanently. `current()` selects `WHERE supersedes IS NULL`, and on an immutable table the row with a null `supersedes` is the **first** version; the *new* row is the one that names its predecessor. `uq_signal_profile_current`, the partial unique index, is built on the same inverted assumption.

**Why it has never bitten.** Nothing has ever written a second profile version — there is no API and no UI, and every test writes v1. **It becomes reachable the moment a customer can edit their relevance profile**, which is Lane B's territory but Lane A's module.

**The fix, for whoever takes it.** `product_catalog` (migration `0019`) solves the same problem by reading `MAX(version)` and letting `uq_(workspace_id, version)` be the concurrency control — no partial index, no `UPDATE` grant needed. Same shape applies here.


## Won't fix

*None yet.*

### B-011 · `make` is not installed on this workstation — *not a repository defect*

| | |
|---|---|
| **Module** | none — the developer workstation |
| **Severity** | — |
| **Status** | `WONTFIX` — **reclassified 2026-08-01, product owner** |
| **Found** | `f996a42`, QE lane, adding a `make` target |

**What was observed.** No `make` on this machine: absent from `/usr/bin`, `/bin`, `/usr/local/bin` and `/snap/bin`; `dpkg -l` shows neither `make` nor `build-essential`. Every documented gate — `make demo`, `make smoke`, `make test`, `make certify`, `make dr`, `make eval` — fails with `command not found`.

**Why it is not a repository defect.** The Makefile is correct and every recipe it names resolves: `infra/smoke.sh`, `infra/disaster-recovery.sh` and the four `uv run python -m …` entry points all exist and were exercised directly during this slice. **Nothing in the repository is wrong; a required tool is missing from one machine.** Leaving a permanent bug row for a local environment would make the register describe workstations rather than the product.

**Where it went instead.** [`RUNNING.md` § What you need once](RUNNING.md) now lists `make` as a prerequisite, with the reason it matters more here than elsewhere: under [ADR-0027](architecture/adr/0027-local-first-development.md) the local run is the only run, so a missing gate runner is a missing gate.

**Resolved on the workstation, 2026-08-02.** GNU Make 4.4.1 installed to `~/.local/bin/make` **without root** — `apt-get download make`, `dpkg -x`, copy the binary — after `sudo` proved to require interactive authentication. Every documented gate now runs as written; the recipe is in [`RUNNING.md`](RUNNING.md).

**And it produced a rule.** The product owner ratified `CLAUDE.md` §20e *QE removes its own blockers* the same day: **when a documented prerequisite is missing and installing it is within QE's authority, QE installs it rather than stopping the workflow**, and escalates only when the OS, policy or an unavailable dependency genuinely refuses. Leaving a gate unrun because a tool needed installing is not an acceptable outcome.

**Kept as a row rather than deleted** because the finding was real and the reasoning that reclassified it is worth being able to find. *Correct a claim about the present; date a record of the past.*
