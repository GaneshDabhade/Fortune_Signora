# 483 · Environment isolation audit — is the lease still justified?

**Lane C · Product Office · 2026-08-07.** **[D-146](../DECISION_REGISTER.md), product owner.**

> ⛔ **No redesign here.** [D-146](../DECISION_REGISTER.md) asked one question first — *"determine whether the current lease mechanism is still justified or whether it has become obsolete"* — **and everything below is measured on this workstation rather than reasoned from the documents.**

---

# 0 · The answer, before the evidence

> ## ⛔ **The hypothesis in [D-146](../DECISION_REGISTER.md) is wrong, and the real answer is better news.**
>
> **The lease is *not* protecting a shared certification stack. The stacks are already isolated — three separate PostgreSQL clusters are running right now.** ⚡ **It serializes lanes because its resource key is an unexpanded shell variable.**

**`_resource()` reads the `name:` line of `infra/docker-compose.yml` with a regex. That line is:**

```yaml
name: ${COMPOSE_PROJECT_NAME:-signora-v2}
```

⛔ **Docker Compose expands that. The regex does not.** **So every clone that does not export `COMPOSE_PROJECT_NAME` computes the *literal string* as its resource name** — and they all compute the same one.

**The live lease file on this workstation, at the moment of writing, is the proof:**

```
$XDG_RUNTIME_DIR/signora-leases/${COMPOSE_PROJECT_NAME:-signora-v2}.lease

{"clone": "/home/ganesh/Projects/Signora-QE", "label": "certify",
 "resource": "${COMPOSE_PROJECT_NAME:-signora-v2}", "pid": 3650551}
```

⚡ **QE holds a lease keyed to a name that identifies no stack, and every lane contends with it.**

> ⚠️ **And the intended default is unreachable.** `_resource()` reads `COMPOSE_PROJECT_NAME or _compose_project_from_file() or "signora-v2"`. **The middle term returns a truthy literal**, so the `"signora-v2"` fallback can never be taken.

---

# 1 · Current architecture — measured, not described

## 1a · What is actually running

| Container | Host port | Slot | Owner |
|---|---|---|---|
| `signora-v2-postgres-1` · `-redis-1` · `-minio-1` | **5432** · 6379 · 9000/9001 | **0** | Human review |
| `signora-lane-qe-postgres-1` · `-redis-1` · `-minio-1` | **5632** · 6579 · 9200/9201 | **2** | QE |
| `signora-lane-b-postgres-1` · `-redis-1` · `-minio-1` | **5832** · 6779 · 9400/9401 | **4** | Lane B |

✅ **Three separate PostgreSQL *clusters*, not three databases on one.** ⚡ **That distinction is the whole of it, and [`infra/environments.py`](../../infra/environments.py) states why in its own words:**

> *"A PostgreSQL **role** is cluster-wide: two suites reaching `ALTER ROLE` collide however many databases they own, which is what aborted cycle 57. **Per-database separation cannot reach a shared cluster; a separate cluster has separate roles.**"*

⛔ **Lane A has no stack running.** **Nine containers exist; none is `signora-lane-a-*`.**

## 1b · What each resource's isolation status actually is

| Resource | Isolated? | How |
|---|---|---|
| **PostgreSQL** | ✅ **Per slot** | Own cluster on `5432 + 100n` — own roles, own `alembic_version`, own everything |
| **Redis** | ✅ **Per slot** | Own instance on `6379 + 100n` *(not merely a logical index — an instance)* |
| **MinIO / object storage** | ✅ **Per slot** | Own instance on `9000/9001 + 100n` |
| **Ports — web / API** | ✅ **Per slot** | `3000 + 100n` / `8000 + 100n`, allocated in [`environments.py`](../../infra/environments.py) |
| **Docker network** | ✅ **Per project** | Compose creates one network per project; three projects, three networks |
| **Backend / frontend processes** | ✅ **Per lane** | Host processes on the lane's own ports, in the lane's own clone |
| **Seeded / demo data** | ✅ **Per slot** | It lives in the slot's own database |
| **Test artifacts · logs** | ✅ **Per clone** | Written under the clone's own tree |
| ⛔ **The lease** | 🔴 **NO — one key for every clone** | **The defect in §0** |
| ⛔ **`pytest`'s default database** | 🔴 **NO — hardcoded to slot 0** | **§1c** |
| **Mail server** | ⚪ **Not applicable** | ⛔ **There is none.** No `mailpit`/`mailhog` container, no SMTP service in either compose file. **Email verification is exercised through the token in the URL** |
| **Review deployment (3000/8000)** | ⚪ **Shared by design** | **Host processes on `main`, not containers.** [`RUNNING.md`](../RUNNING.md): *"3000 and 8000 belong to human review, and to no lane"* |
| **The production stack (`signora-prod`)** | ✅ **Its own project** | `name: signora-prod`, fixed — **the one compose file whose name is a literal and therefore correct** |

## 1c · The second defect, and it is why Lane C may not run the suite

**[`backend/tests/conftest.py`](../../backend/tests/conftest.py) line 54:**

```python
"postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:5432/signora"
```

⛔ **`localhost:5432/signora` is slot 0 — the human-review database.** ⚡ **So a lane running bare `pytest` without exporting `SIGNORA_DATABASE_URL` truncates *human review's* data, not its own** — `clean_database` is autouse and truncates every table after each test.

⚠️ **This is the real reason behind Lane C's standing prohibition on running the suite**, which this office had been carrying as *"the only PostgreSQL on this workstation is the demo stack."* ⛔ **That sentence is wrong twice over: there are three clusters, and `5432` is human review rather than the demo.** **Corrected here.**

---

# 2 · Why the lease exists at all, and why that reason is still sound

⛔ **The lease is not obsolete and should not be removed.** **[`environment-lease.py`](../../infra/environment-lease.py) argues its own case correctly:**

> *"RE-02 was written as a lock around `make certify`, and challenging it showed that would not have prevented the incident it came from. Cycle 25's contaminated run happened because `make smoke` and `make down` ran **beside** a certification. **A certify-lock would have permitted every command that actually did the damage.**"*

✅ **So the lease belongs to the environment rather than to a command — and that is right.** ⚡ **Two operations must not drive one stack at once, whichever commands they are.** **The mechanism is sound; only its key is broken.**

---

# 3 · Was this an intentional architectural decision?

> ## ⚠️ **No. It is a ruling that was requested and never given, overtaken by facts.**

**[436 §163](436-execution-isolation.md) put exactly this to the product owner:**

> *"**① Approve change ② — four container sets on one workstation — or refuse it and take serialisation instead.** **This is the only one with a cost you should weigh rather than delegate.**"*

| 436's change | What it does | Status |
|---|---|---|
| **①** The lease moves to the workstation | `environment-lease.py` | ✅ **Shipped** |
| ⛔ **②** **The compose project comes from the allocation** | `docker-compose.yml`, `Makefile` | 🔴 **"Lane C — awaiting your ruling"** |
| **③** `make test` acquires the lease | `Makefile` | ✅ **Shipped** |
| **③b** Bare `pytest` refuses under a held lease | `conftest.py` | ⚠️ **QE, unshipped** |
| **④** Certification asserts its own isolation | `backend/tests/certification/` | ⚠️ **QE, unshipped** |

⚡ **Change ② is the one that fixes the lease key. It was never ruled on.** ⛔ **Meanwhile the container sets were built anyway** — QE and Lane B are running theirs — **so the workstation now sits in a half-state the plan never described: isolated stacks, one shared lease key.**

> **That is the honest characterisation D-146 asked for: not an architectural decision, and not merely an implementation gap.** ⚡ **A decision was correctly escalated, the world moved past it, and nobody re-asked.** ⛔ **[C-427](../LANE_COORDINATION.md)'s exact shape: a blocker is recorded once and re-read many times, and nothing re-tests one.**

---

# 4 · Hardware — measured, and it is not the constraint

| | |
|---|---|
| **Total RAM** | **15 GB** |
| **Nine containers, three stacks** | ⚡ **1,323 MiB — about 8%** |
| **Per stack** | **QE 106 MiB · slot 0 400 MiB · Lane B 798 MiB** *(Lane B's is inflated by a live workload)* |
| **A fourth stack for Lane A** | **~150–800 MiB, by those three observations** |

⛔ **The 10 GB in use is host processes — dev servers, editors, language servers — not containers.** ✅ **Adding Lane A's stack is affordable.** ⚡ **436 asked the product owner to weigh a cost that measurement now shows is small.**

**The genuine machine constraints, stated separately as [D-146](../DECISION_REGISTER.md) asks:**

| | |
|---|---|
| ⚪ **One Docker daemon** | **Not a constraint** — projects are isolated within it, and this is how the three stacks already coexist |
| ⚪ **Fixed port space** | **Not a constraint** — the `+100n` stride allocates ten slots and six are unused |
| 🟡 **One review deployment (3000/8000)** | ⚡ **A real shared resource, and correctly so**: it is the product owner's demo of `main`, and there is only one `main` |
| 🟡 **Disk** | **Each PostgreSQL cluster carries its own volume.** Not measured here; worth watching rather than acting on |

---

# 5 · Deliverables

## 5a · Current environment architecture

**Per-slot isolation, deployed for three of five environments, with one shared lease key defeating it and one hardcoded test default bypassing it.**

## 5b · Intended future architecture

⚡ **Unchanged from [436](436-execution-isolation.md) — this audit proposes nothing new.** **Every environment is a Compose project named from [`environments.py`](../../infra/environments.py); each holds its own PostgreSQL cluster, Redis, MinIO, ports, data and artifacts; the lease is per project and arbitrates only within one stack.**

## 5c · What should remain serialized

| | |
|---|---|
| ✅ **Operations against one stack** | **`certify`, `smoke`, `dr`, `up`, `down`, `test`, `e2e` on the *same* project.** ⛔ **Cycle 25 is the evidence and it has not expired** |
| ✅ **The human-review deployment** | **One `main`, one demo, 3000/8000** |
| ⛔ **Nothing else** | **Certification does not need exclusivity over the *workstation*** — it needs exclusivity over **`signora-prod`**, which is its own project and already named literally |

> ⚡ **Answering [D-146](../DECISION_REGISTER.md)'s certification question precisely:** **exclusivity is required, and its scope is one Compose project rather than the machine.** **Certification runs against `signora-prod` — a production-equivalent stack it builds and tears down — and two certifications, or a certification beside a `make down`, would contaminate each other.** ⛔ **That is a genuine architectural requirement.** ✅ **It does not extend to a lane running its own suite in its own cluster.**

## 5d · What should become fully parallel

**Every lane's `make test`, `make e2e`, dev servers, seeding and Playwright execution — against its own slot.** ⛔ **Today all of them contend with certification for one lease.**

## 5e · Concrete implementation steps

| # | Step | Where | Owner | Size |
|---|---|---|---|---|
| **1** | ⚡ **Expand the variable, or stop reading the file.** `_compose_project_from_file()` returns a literal `${…}`; it must either expand it or return `None` so the real default is reached | [`environment-lease.py`](../../infra/environment-lease.py) | **Lane C** | ⚡ **One function. The single highest-value change in this audit** |
| **2** | **Export `COMPOSE_PROJECT_NAME` from the allocation** in every `make` target that drives a stack — 436's change ② | `Makefile`, [`environments.py`](../../infra/environments.py) | **Lane C** | **Small** — `environments.py` already emits the line |
| **3** | ⛔ **Remove the hardcoded `localhost:5432` default** from `conftest.py`, or make it refuse rather than default | [`conftest.py`](../../backend/tests/conftest.py) | ⚠️ **QE** — it changes startup for every lane | **Small, high blast radius** |
| **4** | **Bring up Lane A's stack** (slot 3 — 5732/6679/9300) | `make environments` | **Lane A**, once ② lands | **Minutes** |
| **5** | **436 ③b and ④** — bare `pytest` refuses under a held lease; certification asserts its own isolation | `conftest.py`, `backend/tests/certification/` | ⚠️ **QE** | **Already scoped in 436** |

⛔ **Steps 1 and 2 are this office's and need no ruling** — **they make the lease do what it already claims to do.** ⚠️ **Step 3 is QE's and touches every lane's startup.** ⚡ **Step 4 costs a few hundred megabytes, which §4 measures rather than estimates.**

---

# 6 · What this audit did not do

⛔ **It did not measure disk**, and each cluster carries a volume.
⛔ **It did not test whether two lanes' suites actually pass concurrently** once the key is fixed — **that is the proof, and it belongs to whoever ships step 1.**
⛔ **It changed nothing.** ⚡ **[D-146](../DECISION_REGISTER.md) said *"do not redesign anything yet"*, and the finding is small enough that the fix is a repair rather than a redesign.**
