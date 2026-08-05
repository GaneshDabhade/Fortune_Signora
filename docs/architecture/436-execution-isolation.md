# 436 · Execution isolation — the allocation exists and nothing enforces it

**Lane C · Platform Foundation · 2026-08-05.** Raised to Lane C by the product owner: *"treat this as a repository execution infrastructure issue rather than merely a testing inconvenience… the solution should not be a manual convention. It should be enforced mechanically wherever possible."*

**Covers [B-317](../BUGS.md) and [B-118](../BUGS.md)** — one problem at two scopes.

> **The finding, before the detail.** **This repository already allocates every isolation the directive asks for.** `infra/environments.py` derives a database, an auth database, a Redis index, a bucket and **a compose project** for each of nine environments. **Three of those allocations are ignored by the code that would have to honour them, and the one enforcement mechanism is scoped to the wrong object.**
>
> **So this is an enforcement problem wearing a design problem's clothes.** The answer is to make existing allocations bind — not to build an isolation system.

## The two defects are one defect at two radii

| | Scope | What collides |
|---|---|---|
| **[B-317](../BUGS.md)** | **Inside one clone** | `make test` and bare `pytest` take no lease, so a second run truncates the first's fixtures mid-suite |
| **[B-118](../BUGS.md)** | **Across clones** | Every lane's `docker compose` targets **one project**, so all four share one PostgreSQL server — one connection pool, one lock manager |

**B-118 is the one that matters**, and QE's evidence is the reason: validating the same commit twice, minutes apart, produced **40 failed** and then **238 failed**, with 21 `DeadlockDetectedError` and 13 `InvalidCatalogNameError`.

> **The failures land in modules the slice never touches and name plausible causes.** A lane reading that list chases a phantom in its own code; QE reading it files a defect against a lane that did nothing wrong. **That is worse than a failing test, because a failing test is information.**

---

# The eight mechanisms, measured

| # | Mechanism | State at `8966354` | Verdict |
|---|---|---|---|
| **1** | **Environment leasing** | `infra/environment-lease.py` exists and works. Used by `certify` · `smoke` · `dr` · `up` · `down` · `e2e` | ⚠️ **Wrong scope** — see below |
| **2** | **Workspace isolation** | Four separate clones on separate paths | ✅ **Already true** |
| **3** | **Database isolation** | A distinct database **name** per environment | ⚠️ **Partial — one server** |
| **4** | **Redis isolation** | An index allocated per environment; `redis_url` is configurable | ❔ **Unverifiable from this clone** |
| **5** | **Compose project isolation** | `compose_project = signora-<name>` is **derived and never used** | ❌ **The root cause** |
| **6** | **Automatic lock acquisition** | Opt-in, per Makefile target. `pytest` bypasses it entirely | ❌ **B-317** |
| **7** | **Queueing for exclusive resources** | The lease **refuses**; it does not queue | ✅ **Correct, and deliberately** |
| **8** | **Deterministic certification** | Not guaranteed | ❌ **B-118 is the proof** |

## ❌ 5 · The compose project is allocated and nothing reads it

**`infra/docker-compose.yml` line 6:** `name: signora-v2` — **hard-coded, one project.**
**`infra/environments.py`:** `compose_project` → `signora-lane-a`, `signora-lane-b`, `signora-qe`, …
**Repository-wide search for `COMPOSE_PROJECT_NAME`: no results.**

> **Two containers of the same name in two projects are two containers; in one project they are one.** That sentence is `environments.py`'s own docstring, on the property nothing consumes.

**The module already knew.** Its header records the gap in the present tense: *"**Two projects exist, both fixed and singleton**, so a review stack and a certification run are structurally the same project and cannot coexist regardless of ports."*

**So B-118's root cause was documented inside the allocator before it was observed in the wild** — and I extended that file on 2026-08-04 without acting on it.

## ⚠️ 1 · The lease is scoped to the clone; the resource is scoped to the workstation

```python
LEASE: Final = REPO_ROOT / ".environment-lease"
```

**Every clone has its own lease file, so no clone can see another's.** Lane A holding the environment is invisible to QE, by construction.

> **The module's own reasoning is right and its scope is wrong.** It argues — correctly — that *"the lease belongs to the environment, not to a command"*, because cycle 25 was contaminated by `smoke` and `down` running *beside* a certification rather than by a second `certify`. **The same argument, applied once more, says the lease belongs to the *workstation*, not to the clone**: the contended object is one PostgreSQL server, and it does not become four because four directories reference it.

**It was correct when written.** There was one clone.

## ✅ 7 · Refusing rather than queueing is right, and should stay

**The directive lists queueing, and I recommend against it as the default.** A queued `certify` starts later against a tree that has moved, and **a gate that waits looks identical to a gate that hung.** *"Prevention rather than detection"* is the lease's stated principle and it is the correct one.

**Recommend instead:** refuse by default, with an explicit `--wait <seconds>` a caller may opt into. **Bounded, visible, and never the default.**

---

# What to change — four changes, in dependency order

## ① The lease moves to the workstation *(🟢 · closes B-118's arbitration half)*

**`LEASE` becomes a workstation-scoped path keyed by the contended resource**, not by the clone — `${XDG_RUNTIME_DIR:-/tmp}/signora/<compose-project>.lease`. **Every clone computes the same path for the same resource and a different path for different ones**, so the lease starts arbitrating exactly what is shared.

**The holder record already carries what a second lane needs** — pid, label, start time. It gains the clone path, because *"leased by `certify`"* is not actionable when four checkouts can say it.

## ⚡ Cycle 57 settled the argument for ②, and it is not the argument I made

**2026-08-05, certifying change ① itself:**

```
sqlalchemy.exc.InternalError: tuple concurrently updated
[SQL: ALTER ROLE signora_app NOBYPASSRLS]
```

> **A PostgreSQL role is cluster-wide.** Two suites reaching `ALTER ROLE` together collide **however many databases they each own.**

**I argued for ② on connection pools, lock managers and `DROP DATABASE WITH FORCE` — all of which are contention.** **`ALTER ROLE` is not contention. It is a shared object that per-database isolation cannot separate at all**, and no amount of care inside a database reaches it.

**That changes what the two options actually offer:**

| | `ALTER ROLE` collisions |
|---|---|
| **The lease alone** (serialised runs) | **Prevented** — one suite at a time, so nothing collides |
| **Change ②** (a cluster per lane) | **Impossible** — separate clusters have separate roles |
| **Today** | **Live.** It aborted a certification |

**So both options still work, and the choice is unchanged in shape — but the thing being bought is larger than I described.** ② does not merely reduce interference; **it removes a class of shared object the lease can only ever serialise around.**

## ⚠️ And change ① has a bootstrap window, which QE found by hitting it

> **A workstation lease only excludes clones that hold it.** QE's tree carried the fix; **Lane A's did not, because it is not promoted.** QE took a workstation-scoped lease, Lane A took a repository-scoped one, and **two leases over one resource exclude nobody.**

**This is not fixable from inside the fix, and it is worth saying why rather than attempting it.** The old lease lives at `REPO_ROOT/.environment-lease` — **a clone that has not rebased looks only inside itself.** Nothing a new clone writes can be seen by it. **Compatibility in that direction does not exist.**

**So the window closes by sequencing, not by code:** **every lane rebases onto the promoted fix before running a suite.** Until then, contention persists **and looks exactly like the fix not working** — which is the failure mode QE named and the reason this is recorded here rather than left to be rediscovered.

> **A resource-level probe would close it durably** — asking PostgreSQL who else is connected, rather than asking a lease file. **Not proposed.** It is speculative work against a transient window, **and change ② makes it moot**: separate clusters have nothing to probe.

## ② The compose project comes from the allocation *(🟠 · closes B-118)*

**`name: signora-v2` is removed and the project name is passed per invocation** from `environments.py`. **Each lane then has its own PostgreSQL container, Redis and MinIO** — and the deadlocks, the missing catalogs and the mid-operation disconnects stop being possible rather than becoming rarer.

> ⚠️ **This is the change with real cost and it should not be pretended otherwise.** Four PostgreSQL containers instead of one, four Redis, four MinIO — **memory and disk on one workstation.** Migrations run four times. `RUNNING.md` becomes four stacks. **The product owner should approve this specifically**, because *"it is enforced mechanically"* and *"the workstation can carry it"* are different claims and only the first is mine to make.

**The narrower alternative, if that cost is refused:** keep one PostgreSQL and **give certification an exclusive lease on the server** (change ①), so runs serialise instead of isolating. **Deterministic, and slower.** Isolation buys parallelism; the lease alone buys only correctness.

## ③ `make test` and `pytest` acquire the lease *(🟢 · closes B-317)*

**`make test` gains `environment-lease.py run test --`, exactly as five targets already do.** Bare `pytest` cannot be intercepted by a Makefile, so **`tests/conftest.py` refuses to start when the lease is held by another pid** — the same session-scoped guard that already refuses to truncate without `SIGNORA_ALLOW_DESTRUCTIVE_TESTS`.

> **That guard is the precedent and it is the right shape**: the suite already knows how to refuse to run somewhere it would do damage.

## ④ Certification asserts its own isolation *(🟢)*

**A certification records the compose project and the lease holder it ran under**, and **refuses when another clone holds the resource.** A number measured during contention is not a number, and QE has already declined to publish one — **this makes that judgement mechanical rather than a discipline QE has to keep exercising.**

---

# What this does not propose

| | Why |
|---|---|
| **A CI runner, a scheduler, a queue service** | **§20c-2 is absolute.** *"The correct quantity of CI is zero."* This is a lock and a project name, not a build system |
| **Per-test database creation** | Already tried at a different level — **the disposable database per run is exactly what looked like isolation and was not** |
| **A second datastore for lease state** | **Principle 6.** A file is the right size for this |
| **A convention in `RUNNING.md`** | **The directive rules it out and it is right to.** A convention that has to be remembered has already failed once per lane |

# The decision asked of the product owner

**① Approve change ② — four container sets on one workstation — or refuse it and take serialisation instead.** **This is the only one with a cost you should weigh rather than delegate.**
**② Confirm B-317 and B-118 move to Lane C** as Platform Foundation. Both currently read `QE`, and QE raised B-118 while blocked by it.

## ⚠️ Correction, 2026-08-05 — two of these four are not Lane C's to make

**This document said changes ①, ③ and ④ *"need no ruling — they are `infra/`, `Makefile` and test infrastructure under [D-022](../DECISION_REGISTER.md)"*. That was wrong about ownership, written by the office that has spent two days correcting other people's ownership rows.**

| | Change | Lives in | Whose |
|---|---|---|---|
| **①** | The lease moves to the workstation | `infra/environment-lease.py` | ✅ **Lane C — shipped** |
| **②** | The compose project comes from the allocation | `infra/docker-compose.yml`, `Makefile` | **Lane C — awaiting your ruling** |
| **③** | `make test` acquires the lease | `Makefile` | ✅ **Lane C — shipped** |
| **③b** | Bare `pytest` refuses under a held lease | **`backend/tests/conftest.py`** | ⚠️ **QE.** Changes startup for every lane on every targeted run |
| **④** | Certification asserts its own isolation | **`backend/tests/certification/`** | ⚠️ **QE.** It is the instrument QE certifies with |

> **D-022 gives this lane `infra/`, the `Makefile` and repository tooling. It does not give it the certification package or the suite's fixtures**, and *"test infrastructure"* was a phrase broad enough to hide the difference from me while I wrote it.

**So the split is two and two.** **Lane C's half is one shipped change and one ruling.** **QE's half is designed here in full — including the `signora_certify_selftest01` naming in [B-118](../BUGS.md) — and scheduled by QE.**

**That is the same rule Lane B applied to [B-117](../BUGS.md) in this office's file and Lane A applied to `opportunity_engine` in [B-103](../BUGS.md) this morning.** **A document proposing work in another lane's files is a recommendation, however correct** — and this one had quietly promoted itself to a plan.
