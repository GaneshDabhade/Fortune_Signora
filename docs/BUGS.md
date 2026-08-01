# Bug register

> **The single register.** Not a file per bug, not scattered TODOs. Owned by the **QE lane** (`CLAUDE.md` §20e); a feature lane edits only the `Status` of a bug it has fixed.
>
> **Why this file exists.** Open defects had no home. They were split between `39-product-review-findings.md` (a *dated record of reviews*, append-only, integrator-owned) and `PROJECT_STATUS.md`'s known-limitations table. Neither can carry a row whose status changes, and a review finding is not the same thing as a defect with an owner and a fix. This file replaces that responsibility rather than adding one.

## How it works

**QE opens. The owning lane fixes. QE verifies and closes** — never the lane that fixed it.

**Any lane may open a bug** it finds outside its own budget — that is the correct alternative to fixing another lane's module. **Only QE sets `VERIFIED`.**

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
| `FIXING` | The owning lane is on it |
| `FIXED` | Lane says done, with a regression test |
| `VERIFIED` | QE reproduced the fix. **Only QE sets this** |
| `WONTFIX` | Deliberate, with the reason stated |

**A bug fixed without a regression test is not fixed** (§11). The test goes in the owning module's suite, written by the lane that fixes it.

**Bug ids are `B-nnn`, allocated sequentially and never reused.** A finding from a product review keeps its `R-` id there and gets a `B-` row here only if it is a defect rather than an improvement.

---

## Open

### B-001 · `signal_profile` reads the wrong row as "current"

| | |
|---|---|
| **Owner** | Lane A — `signal_engine` |
| **Severity** | 🟠 — latent today, 🔴 the moment the signal profile gets a write path |
| **Status** | `FIXED` — `0023`, and it was in **three** tables. See `25-signal-engine.md` |
| **Found** | `1ae600d`, while building `commercial_profile` |

**Steps to reproduce.** Write a `SignalProfile` at version 1. Write a second superseding it (`supersedes = <v1 id>`). Call `SqlProfileRepository.current(workspace_id)`.

**Expected.** Version 2 — the profile in force.

**Actual.** Version 1, permanently. `current()` selects `WHERE supersedes IS NULL`, and on an immutable table the row with a null `supersedes` is the **first** version; the *new* row is the one that names its predecessor. `uq_signal_profile_current`, the partial unique index, is built on the same inverted assumption.

**Why it has never bitten.** Nothing has ever written a second profile version — there is no API and no UI, and every test writes v1. **It becomes reachable the moment a customer can edit their relevance profile**, which is Lane B's territory but Lane A's module.

**The fix, for whoever takes it.** `product_catalog` (migration `0019`) solves the same problem by reading `MAX(version)` and letting `uq_(workspace_id, version)` be the concurrency control — no partial index, no `UPDATE` grant needed. Same shape applies here.

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

## Verified

*None yet.*

## Won't fix

*None yet.*
