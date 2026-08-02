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

---|---|
| **Owner** | Lane A — `provider_platform` |
| **Severity** | 🟠 — unreachable today, 🔴 the moment a workspace watches two accounts |
| **Status** | `OPEN` |
| **Found** | `fba0647`, while answering `C-001` |

**Steps to reproduce.** Not reproducible today: nothing supplies a `subject` outside the simulation, and every scenario syncs one. It becomes reproducible the moment Commercial Profile's target-account list has two entries and Provider Platform consumes it.

**Expected.** Each watched account has its own incremental position, so syncing one does not affect what another fetches next.

**Actual.** `uq_provider_watermark_scope` is `(workspace_id, provider, capability)` — **there is no `subject`.** One watermark covers every account in a workspace for a given provider and capability, so syncing account A advances the position account B then reads, and B's next sync skips everything before that point. A customer would see one account richly enriched and another mysteriously thin, with nothing in the product explaining the difference.

**Why it has never bitten.** `RunProviderSync` has taken a `subject` since M2.1 and **nothing has ever supplied one** except the Provider Simulation Framework, which syncs the scenario's subjects through a single workspace and never re-reads a watermark across two of them in a way that would show it.

**The fix, for whoever takes it.** `subject` joins the unique key and the lookup. It is a migration and a widened `where` — the domain already carries the subject on every request, so nothing above the repository changes. **The same slice must build the `target_accounts_changed` consumer**, because that is what makes the defect reachable and it would be dishonest to fix one without the other.

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
| **Status** | **`FIXED`** — fixed by the QE lane under product-owner direction, 2026-08-01. **Awaiting verification by someone other than QE** |
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
| **Status** | `FIXED` — the rule that prevents it was ratified 2026-08-02 and is enforced by `infra/certification-guard.py`. **Awaiting verification by someone other than QE** |
| **Found** | `e44819b`, by `certification-guard.py --audit-main` on its first run — **against the commits QE had just written** |

**Steps to reproduce.** `python3 infra/certification-guard.py --audit-main`, with `RULE_RATIFIED_AT` set to the certified commit `f669172`.

**Expected.** Every commit on `main` is certified, or changes nothing executable.

**Actual.** Two Closeout commits — `b5cc283` and `e44819b` — each modified `infra/state-check.py`, which is executable code, while carrying a Closeout message. **They were promoted without passing through certification at all**, because Closeout runs after promotion by design.

**Why it happened, and why it is worth a row.** The commit-binding rule did not exist when they were written; under the previous reading, certification bound to a *tree* and Closeout was documentation. `state-check.py` was edited during Closeout because that is when its defect was found, which felt like documentation work and was not. **A repository-wide gate is exactly the kind of thing that gets edited at the moment it is being used**, so this will recur unless something refuses it.

**The fix is the rule.** `CLAUDE.md` §20e now binds certification to an immutable commit, and `certification-guard.py --audit-main` proves that every commit on `main` since ratification is either certified or **verifiably** docs-only — a fact about paths, not about the commit message. `infra/` is deliberately **not** in the permitted set: `smoke.sh`, `disaster-recovery.sh` and the compose files decide whether a gate passes.

**For whoever verifies it.** Run the audit; it must report zero violations. Then edit `infra/state-check.py`, commit it to `main` with a Closeout message, and confirm the audit refuses it. **A guard that cannot fail is documentation pretending to be code**, and this one was written by finding a real violation on its first run.

---

### B-013 · The worker and the relay cannot start from a production image

| | |
|---|---|
| **Module** | **none** — `apps/worker/` is composition-root production code, plus `backend/pyproject.toml` |
| **Current assignee** | **none — not assignable.** [C-010](LANE_COORDINATION.md) |
| **Severity** | 🔴 — **two of the six production services crash-loop.** Nothing deployed would process an event |
| **Status** | **`FIXED`** — fixed by QE under product-owner direction, 2026-08-02. **Awaiting verification by someone other than QE** |
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
