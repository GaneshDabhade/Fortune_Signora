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

## Verified

*None yet.*

## Won't fix

*None yet.*
