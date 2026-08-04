# 420 — Environment Management: a proposal, and the finding that changes it

> **Lane C — Product Office, 2026-08-04**, on the product owner's P0 proposal for an **Environment Management Platform (EMP)**. Prepared, not implemented. Measured against `origin/integration`.
>
> **The reuse audit ([L-1](../../ENGINEERING_LAWS.md)) comes first and is usually the whole finding.** It is here.

## 1 · The finding

> **EMP is not a new module. It is phase 3 of a framework that already exists, has two completed phases, and stalled for want of an owner rather than a design.**

**`infra/environments.py` opens with:** *"**Phase 1 of the Environment Framework**: the *model*, and nothing else. **No behaviour changes here** — no launcher, no compose, no seeding."*

**`infra/review.py` opens with:** *"**Phase 2 of the Environment Framework.** Phase 1 made an environment's identity derivable; this is **the first thing to consume a profile**… What the reviewer types is `make review`. No port, no database, no compose project, no environment variable, no second terminal."*

**Its lifecycle is already the one EMP asks for:**

```
prepare → validate → seed → present → record        …then end
```

> **Phase 2 built that lifecycle for exactly one profile. EMP is the request to have it for all of them.** That is not a new platform capability — **it is the third phase of an existing one, and naming it a module would obscure that.**

## 2 · Reuse audit — EMP's nine responsibilities against the repository

| EMP asks for | Already built | |
|---|---|---|
| **Environment profiles** | **`infra/environments.py`** — nine profiles, each with slot, purpose, owner, port slot, coexistence. **The allocation rule is executable rather than prose** | 🟩 |
| **Bootstrap** | **`infra/workstation.py`** — *"make this machine able to run Signora, and say what that cost"* · `postgres-init/*.sql` for the three roles · `docker-compose.yml` · `.prod.yml` | 🟠 |
| **Launch profiles** | **`make review`** launches. **`make up`/`down` run the prod-local stack.** `environment-lease.py` stops two operations owning one stack | 🟠 |
| **Demo dataset engine** | **`signora_platform/simulation/`** — `dataset.py`, `generators/{enrichment,intent}.py`, `clock.py`, versioned `datasets/{baseline,playground}@n.json` · `make demo-seed`, `demo-users`, `demo-narrate` · `infra/demo-users.json` | 🟩 |
| **Scenario management** | **`simulation/scenario.py`** · versioned `scenarios/*.json` · **Scenario Manifests** and a **13-scenario Phase 1 library** in [20-provider-simulation.md](20-provider-simulation.md) | 🟩 |
| **Mock platform** | **The Provider Simulation Framework** — five providers, `faults.py`, `delivery.py`, `safety.py`, `observability.py`. **Ollama is the development AI runtime** ([ADR-0028](adr/0028-model-runtime-by-environment.md)) | 🟩 |
| **Environment doctor** | **`workstation.py`** · **`reachability.py`** · `validate.py` · `state-check.py` · `runtime-composition.py` · `make smoke` | 🟠 |
| **Cleanup** | `make down -v` · `make test` truncates its target · **`disaster-recovery.sh`** for restore | 🟠 |
| **Migration strategy** | `doc-drift.py` · `unsaved.py` · `registers.py` · `release-preflight.py` | 🟠 |

**Nothing in EMP's nine is absent. Four are substantially built; five need extension.**

> **The repository is not short of environment capability. It is short of one launcher generalised across nine profiles, and an owner allowed to write it.**

## 3 · What is genuinely missing

| | Evidence |
|---|---|
| **A launcher for every profile except `review`** | **`make demo` prepares and then prints two commands to run by hand** — `uvicorn …` and `npm run dev`. `make review` needs neither. **The pattern exists; it was applied once** |
| **Profiles for `demo`, `qa`, `performance`, `preview`** | The nine that exist are `review`, `lane-a`…`lane-e`, `lane-qe`, `prod-local`, `docs`. **Demo runs inside a lane's allocation today** |
| **Scenario *lifecycle* verbs** | `load` and `seed` exist. **`reset`, `clone`, `snapshot`, `restore`, `cleanup` do not** — and `disaster-recovery.sh` restores a *database*, not a scenario |
| **Realistic enterprise scenarios** | **The 13 are provider-pathway scenarios** — hiring surge, funding round, intent cooling. **EMP asks for customer-shaped ones** — renewal, expansion, competitive loss, champion left. **A different axis over the same machinery** |
| **Mock CRM, email, calendar, search** | Providers are simulated; **customer-held systems are not**, and that is [C-326](../LANE_COORDINATION.md)'s port again |
| **A single doctor** | Five tools answer *"is this environment ready?"* and **no one command asks all five** |

## 4 · Why it must not be a module — the tests it fails

**A new bounded context is 🔴 and needs an ADR (`CLAUDE.md` §6). Applying the same tests that retired the Revenue Intelligence Platform ([408](408-revenue-intelligence-platform.md)):**

| Test | EMP |
|---|---|
| **Does it own an aggregate whose invariants nothing else can enforce?** | **No.** Environment identity is derived from an allocation table. `environment-lease.py` holds the one piece of state, and it is a **file lock, not an aggregate** |
| **Does it have a ubiquitous language the product speaks?** | **No.** *Profile*, *slot*, *lease*, *scenario* are engineering vocabulary. **No customer says them** ([ADR-0034](adr/0034-ubiquitous-language.md)) |
| **Does it own tables, events, RLS policies?** | **No, and it must not.** Seeding writes through **the same doors a customer uses** — §20e's test-data rule, and [20-provider-simulation.md](20-provider-simulation.md)'s *"never bypasses the Provider Port"* |
| **Would it live in `backend/modules/`?** | **No.** Every part of it is `infra/`, the `Makefile`, or `signora_platform/simulation/` — **and `signora_platform/` is frozen** (§20a) |

> **EMP is tooling, not a bounded context.** Making it a module would put developer experience inside the dependency graph, and **`modules/` would then contain something no customer can reach** — the exact inversion the module boundary exists to prevent.

**Recommended shape instead:**

> **Environment Framework, phase 3.** It keeps the name the repository already uses, inherits two completed phases, and needs **no ADR and no new bounded context** — which is the cheapest possible answer to a P0.

## 5 · The real blocker, and it is already on the queue

**`infra/`, the `Makefile` and repository process have no assignable lane.**

> **[C-010](../LANE_COORDINATION.md) / [TASK-006](../BACKLOG.md):** *"no lane is assignable to `apps/`, `signora_platform/` or repository process."* The backlog calls it **"the highest-value decision on this page"** and records that **four defects have already landed in that gap — B-007, B-012, B-013, B-014.**

**This proposal is the largest piece of work yet proposed for exactly that gap.** Phase 1 and phase 2 were written by whoever was nearest; **phase 3 is bigger than both and cannot be.**

> ✅ **Ruled 2026-08-04. C-010 is resolved and phase 3 has an owner: Lane C.** *"Do not create another engineering lane. Lane C's responsibilities are formally expanded to include Platform Foundation work that belongs to no product bounded context."* Recorded in [`CLAUDE.md`](../../CLAUDE.md) §20e.
>
> **So §8's slices are now claimable, and Lane C claims them like any other lane** — rowed on the board, validated and certified by QE. **Slices 1 and 3 depend on nothing.**

## 6 · Environment profile matrix

**Existing, from `infra/environments.py`:**

| Profile | Purpose | Coexists |
|---|---|---|
| `review` | Human product review — the only profile with a launcher | Yes |
| `lane-a` … `lane-e` · `lane-qe` | One per lane, own ports, database and Redis index | Yes |
| `prod-local` | 3100/8100, its own compose project | **No — nothing shared** |
| `docs` | Documentation | Yes |

**Proposed, and each needs a stated reason to exist:**

| Profile | Recommendation |
|---|---|
| **`demo`** | ✅ **Yes.** It runs inside a lane's allocation today, which is why `make demo` cannot launch cleanly |
| **`qa`** | ⚠️ **Probably not.** `make validate` already gives certification its own database. **Name what `qa` would do that `validate` does not** |
| **`performance`** | ⚠️ **Not yet.** §14 — performance work is justified by evidence, not intuition. **No triggers from [12-scalability.md](12-scalability.md) have fired** |
| **`preview`** | ⚠️ **Deferred.** Preview implies deployment; deployment is M14.5 |
| **`ci`** | ⛔ **Refused, and this is not a judgement call.** §20c-2: *"the correct quantity of CI is zero — not a smaller amount."* **A CI profile is the prohibited thing wearing a profile's name** |
| **`production`** | ⛔ **Not this repository's.** M14.5 provisions it; `prod-local` is the local stand-in |

## 7 · Bootstrap — the manual steps that remain

**Measured, not estimated.**

| | |
|---|---|
| **Works today** | `make workstation` installs and reports · `make up` runs the whole prod-local stack under a lease · `make review` is genuinely one command |
| **Manual** | **`make demo` prints two commands** and the reviewer runs them in two terminals · `.env` files hold a **generated RSA pair that is not reproducible** — `workstation.py` exists precisely because regenerating it *"mints tokens the API rejects with no clue why"* · signing in requires reading `RUNNING.md` for a password |
| **Convergence** | **Generalise `review.py`'s five-stage lifecycle across the profile table.** It already contains **no literal port** — *"the day the allocation changes, nothing here is edited"* — so the generalisation is mechanical rather than a redesign |

## 8 · Priority and slices

**Ordered by what unblocks the rest. No lane is named — C-010 decides that.**

| | Slice | Size | Depends on |
|---|---|---|---|
| **1** | **A `demo` profile in the allocation table** | Small | — |
| **2** | **Generalise the five-stage lifecycle beyond `review`**, starting with `demo` | Medium | 1 |
| **3** | **One `make doctor`** composing `workstation` · `reachability` · `state-check` · `runtime-composition` | Small | — |
| **4** | **Scenario `reset` and `cleanup`** — deterministic, through the same doors | Medium | 2 |
| **5** | **Customer-shaped scenarios** — renewal, expansion, competitive loss, champion left | Medium | 4, and **champion-left needs [O1](../DECISION_PACKS.md)** |
| **6** | **Scenario `snapshot` / `restore` / `clone`** | Large | 4 |
| **7** | Mock CRM | Large | **[C-326](../LANE_COORDINATION.md)** |

**Slices 1 and 3 are executable today and independent of everything.**

## 9 · What must not be built

| | Why |
|---|---|
| **A `modules/environment_management/`** | §4 — it is tooling, and `modules/` would then hold something no customer can reach |
| **Anything in `signora_platform/` beyond `simulation/`** | **Frozen** (§20a) |
| **A CI profile, or any scheduled/remote execution** | §20c-2, and the prohibition is absolute |
| **A seeding path that bypasses a business rule, the API, or the Provider Port** | §20e test-data rule. **Data arriving by a private door proves the door, not the product** |
| **A second mock framework** | The Provider Simulation Framework exists, with faults, delivery, safety and observability. **Extend it** |
| **A `performance` profile before a scalability trigger fires** | §14 |
