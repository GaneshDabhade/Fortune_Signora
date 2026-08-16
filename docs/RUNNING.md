# Running Signora locally

> Written 2026-07-31, at M12.2. **Assume nothing is already running and nothing is already known.** Every command below is copy-pasteable from a fresh clone.

## What you need once

| | |
|---|---|
| **Docker** | for PostgreSQL and Redis |
| **[uv](https://docs.astral.sh/uv/)** | Python toolchain — the backend is never run with bare `python` |
| **Node 20+ / npm** | frontend |
| **`make`** | **every gate in this repository is invoked through it** — `make demo`, `make smoke`, `make test`, `make certify`, `make dr`. `sudo apt-get install make` (or `build-essential`) |
| **Ollama** *(optional)* | only for `make eval*`. **The app itself never calls a model.** |

Everything runs locally. There is no cloud environment and no remote gate ([ADR-0027](architecture/adr/0027-local-first-development.md)).

> **`make` matters more here than in most repositories.** Because the local run is the only run, a workstation without it cannot execute a single quality gate — and the Milestone Definition of Done (`CLAUDE.md` §19) contains steps nobody on that machine can perform. **Check it before your first slice:** `make --version`.
>
> **Install it rather than working around it** (`CLAUDE.md` §20e, *QE removes its own blockers*). A missing gate runner is a missing gate, not an inconvenience.
>
> **Without `sudo`, this works and needs no root:**
>
> ```bash
> apt-get download make                      # no root required
> dpkg -x make_*.deb /tmp/make-extract
> mkdir -p ~/.local/bin && cp /tmp/make-extract/usr/bin/make ~/.local/bin/
> make --version                             # ~/.local/bin is already on PATH for uv
> ```
>
> **Done on this workstation 2026-08-02**, which is how [B-011](BUGS.md) was closed. `bash infra/smoke.sh` also still works directly — which is exactly why the Makefile invokes its scripts that way — but it is the fallback, not the answer.

---

## Two operating modes, and they now run at the same time

**Added 2026-08-02 as *"mutually exclusive"*. Corrected 2026-08-03, when the product owner could not start a review because a leftover certification stack held both ports.**

> **They are no longer mutually exclusive, and this is the change that matters most in this file.** The local production stack moved to **3100/8100**. Human Review keeps **3000/8000**. **Proven rather than asserted**: the full 24-stage smoke test was run to completion while a live review session stayed healthy, and neither knew the other existed.

| | **Human Review Mode** | **QE Release Mode** |
|---|---|---|
| **Purpose** | Interactive product evaluation — *using* Signora | Repository validation and certification |
| **Started by** | **`make review`** — one command, ended by `make review-end` | `make smoke` · `make certify` · `make dr` |
| **Runs** | frontend · backend · Playground data | a self-contained stack the gates build themselves |
| **Ports** | **3000 / 8000** | **3100 / 8100** — *a different block, since 2026-08-03* |
| **Database** | `signora` | `signora` (smoke builds its own; `make test` truncates) |
| **Who** | the product owner, reviewing on `main` | QE |

> **The rule this now satisfies:** *every runnable environment must be independently startable, independently stoppable and independently disposable.* An environment that requires another to be stopped first is not isolated; it is merely documented.
>
> ### ⚙️ One stack per lane, from 2026-08-05 — read this before the port numbers below
>
> **436 change ② is built** (product owner: *"create separate environment for each lane so that nothing could be shared"*). **`infra/docker-compose.yml` no longer hard-codes `name: signora-v2` or its host ports** — both come from the environment this clone resolves to.
>
> ```bash
> python3 infra/environments.py --which     # which environment this clone is
> python3 infra/environments.py --exports   # its project name and host ports
> ```
>
> **Resolution order:** `SIGNORA_ENVIRONMENT` if set · else **the checked-out branch** (`lane-a-product-surface` → `lane-a`) · else **nothing**, and the historical shared stack is used and named out loud. **A wrong guess would point a suite at another lane's database**, which is the defect this change exists to end, so it does not guess.
>
> **PostgreSQL is `5432 + 100n`, Redis `6379 + 100n`, MinIO `9000/9001 + 100n`** — the same stride as web and API. **Slot 0 is unchanged**, so `review` still answers exactly where it always did.
>
> ⚠️ **The explicit `localhost:5432` examples further down this file are now correct only for slot 0.** `make` targets derive the port and need no edit; **hand-run commands do.** **Left for QE**, whose file this is — Lane C changed the mechanism and does not rewrite the runbook (§20e).
>
> ✅ **DISCHARGED 2026-08-15, cycle 233 — [B-1003](BUGS.md). Every example below derives; none quotes a port.** ⛔ **The note is KEPT rather than deleted**, because it records a warning that sat here, correctly addressed to QE, while QE cited this file to another lane without opening it. 📁 **The rule it produced: *citing is the failure mode; the note was fine.***

> **What is still shared is the machine.** Ports, databases, Redis indices and compose projects are isolated; RAM and CPU are not. `make release-preflight` reports memory pressure and names what holds it, because that is the one dimension nothing can allocate away.

### Check before you start — one second, not five minutes

```bash
make release-preflight
```

| Exit | Meaning |
|---|---|
| **0** `READY` | 3100/8100 free. QE Release Mode may begin |
| **3** `BLOCKED` | Something holds 3100/8100, or a documented prerequisite is missing |

> **Exit code 2 is retired.** It meant *"a Human Review session is active, and that is correct rather than a failure"* — a distinction that only existed because the two modes shared ports. **Nothing produces it now**, and a review session is simply not this gate's business.

**`make smoke` runs this automatically** and refuses immediately rather than failing slowly.

> **Never stop somebody else's review session to obtain a green pipeline.** QE's authority is to make a documented gate *runnable*, never to make it *pass* (`CLAUDE.md` §20e). A review session in progress is work, not an obstacle. **This is now easy to honour rather than a discipline to maintain** — the gate no longer wants those ports.

### Leaving Human Review Mode

```bash
make review-end
```

**It waits until the ports are actually free before saying so**, and prints which state it left the workstation in. That matters more than it sounds: the first version signalled the processes and returned immediately, so it announced *"ports are released"* while the sockets were still bound — and the reviewer's next command would have failed on a claim that was false when it was printed.

The backing services (`signora-v2-postgres-1`, `-redis-1`, `-minio-1`) are deliberately left running. **Release Engineering needs them** — the QE database lives in that PostgreSQL and the worker tests use that Redis — so stopping them turns a clean handover into a broken suite. `docker compose -f infra/docker-compose.yml down` if you really want them gone.

> **This section used to open *"three things are running, and there is no single command, which is exactly why this section exists."*** That was true, and it was the friction that made a review feel like an operations task. **The commands it described still work** — nothing about starting the two processes by hand has been withdrawn, and [§ Starting the two processes yourself](#starting-the-two-processes-yourself) keeps them for anyone who wants a foreground log.

### Who owns the environment, and when

**Ratified 2026-08-02, product owner.** The two modes need an owner at every moment, or the handover is an assumption two sessions make differently.

```
   review begins                    review ends                    next review
        │                                │                              │
        ▼                                ▼                              ▼
   ┌─────────────────────┐   ┌──────────────────────────────┐   ┌───────────
   │  Human Review owns  │   │  Release Engineering owns    │   │  Human …
   │  the environment    │   │  the environment             │   │
   └─────────────────────┘   └──────────────────────────────┘   └───────────
    Both run at once, on     Nobody has to wait, and
    3000/8000 and 3100/8100.  nobody stops anybody.
```

| | |
|---|---|
| **While a review is active** | **Human Review owns 3000/8000.** Release Engineering no longer waits for it — it owns 3100/8100 and the two do not meet |
| **Once the review concludes** | `make review-end` releases the ports and **waits until they are genuinely free** before saying so |
| **The signal** | **The reviewer says the review is complete.** Nothing infers it from an idle-looking port — a session paused for lunch looks identical to one that ended |

> **This section described a handover that no longer needs to happen.** It was written when the two modes shared ports; it is kept because the *ownership* question is still real — a review session is somebody's work — and only the waiting is gone.

**The transition back to Release Mode, performed by QE:**

```bash
make review-end                   # stops the tiers and waits for the ports
make release-preflight            # confirm, do not assume — expect: READY
```

**What QE does *not* stop: the development services** (`signora-v2-postgres-1`, `-redis-1`, `-minio-1`). They are `infra/docker-compose.yml`, **Release Engineering needs them** — the QE database `signora_lane_qe` lives in that PostgreSQL and the worker tests use that Redis — and stopping them turns a clean handover into a broken suite. **Only the two foreground review processes belong to the review.**

**Record the transition in the release log** (the Closeout commit), so a later reader can tell a deliberate handover from a session somebody killed.

### Before you finish for the day — `make unsaved`

```bash
make unsaved                        # this working copy
make unsaved ARGS=--workstation     # every Signora clone on this machine
```

**Awareness, not enforcement.** It always exits 0, no gate consults it, and nothing about it asks for smaller commits. It answers one question: *what would you lose if this disk died right now?*

**`.gitignore` is the classifier**, so anything it reports is non-disposable by the repository's own declaration — caches, `node_modules`, `.venv` and `.env` never appear.

Measured on 2026-08-03, minutes after a promotion: every branch on this workstation was pushed, and **27 untracked files across two lanes existed in exactly one physical location** — including an entire module carrying a prompt release and an evaluation dataset. Nothing was lost. That is the only reason this is a reminder rather than a retrospective ([`REPOSITORY_RESILIENCE.md`](REPOSITORY_RESILIENCE.md)).

> **Recoverable is enough.** A WIP commit on your lane branch, pushed. Not merged, not reviewed, not finished — and experimenting freely during a session is exactly what the rule permits.

> **`--workstation` surfaces other lanes' unsaved work, and that is all it does.** It is read-only. Work in another lane's clone is **that lane's to decide** — surfacing it is a finding to hand them, never a thing to fix for them (`CLAUDE.md` §20e).

---

### Lanes never collide with either mode

**A lane's ports start at 3300/8300** and are allocated in [§ Running a lane](#running-a-lane). **That table exists to keep this collision limited to the two modes above** — a lane running on its own row can develop right through a review session or a certification run, and neither notices.

---

## The short version

```bash
# 0 — configuration
cd frontend && npm install && cd ..
make workstation      # generates one key pair and writes both .env files

# 1 — everything else, in one command
make review
```

**That is the whole thing.** `make review` validates the workstation, brings up PostgreSQL and Redis, migrates the schema under the **owner** identity, creates **Better Auth's own tables**, creates **four sign-in accounts**, seeds **twelve accounts through the real pipeline**, starts both tiers, waits until each answers, opens the browser, and records the session.

It prints one card:

```
  ✓  Review environment ready

     Application   http://localhost:3000
     Build         certified, coverage 95.50% at `909374a21353`, +1 Closeout commit(s)
     Dataset       playground@2 — twelve accounts through the real pipeline
     Sign in as    dana.reyes@northwind.example
     Password      signora-demo-password
     Known issues  8 you could meet in the product: …
     When finished  make review-end
```

**No port, no database, no compose project, no environment variable, no second terminal.** Every value is derived from the `review` profile in `infra/environments.py`, so the day an allocation changes, nothing about this command changes with it.

**`make review-end` closes the session**, waits until the ports are genuinely free, and finalizes the record in `review/sessions/`. `--note` captures what you saw:

```bash
make review-end ARGS='--note "Timeline empty state reads oddly"'
```

**Every session leaves a record**: which commit, whether that commit was certified and at what coverage, which dataset, which accounts, the open defects a reviewer could meet, how long it ran, and the notes. It is how *"what exactly did we demonstrate, and when?"* is answered from evidence rather than memory. `make review-status` describes a live one.

**If the workstation is not ready it says so before doing anything** — a held port with the container that holds it named, a missing `.env.local`, an unreachable database — and starts nothing.

### Starting the two processes yourself

`make demo` does the preparation and stops, printing the two commands, for when you want a foreground log or a debugger attached:

```bash
# backend
# SIGNORA_JWT_PUBLIC_KEY is not set here: `npm run keys:generate` printed it and
# you pasted it into backend/.env two steps ago. Setting it on the command line
# would override that value — and it used to be set from a .dev-keys/ file that
# nothing in this repository has ever created, which silently emptied it (B-016).
eval "$(python3 infra/environments.py --exports)"

cd backend && SIGNORA_DATABASE_URL="postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:${SIGNORA_POSTGRES_PORT}/${SIGNORA_DATABASE}" \
  SIGNORA_REDIS_URL="redis://localhost:${SIGNORA_REDIS_PORT}/0" \
  SIGNORA_JWT_ISSUER="http://localhost:${SIGNORA_WEB_PORT}" \
  SIGNORA_JWT_AUDIENCE=signora-api \
  uv run uvicorn apps.api.main:create_app --factory --reload --port ${SIGNORA_API_PORT}

# frontend
cd frontend && npm run dev
```

**<http://localhost:3000>** → sign in as `dana.reyes@northwind.example`.

> **`make demo` alone currently fails on a clean workstation** — nothing loads `frontend/.env.local` for the two `tsx` setup scripts, so `npm run auth:migrate` refuses to start. That is **[B-105](BUGS.md)**, and it is why `make review` loads the file itself. Use `make review` until it is fixed.

> **`make test` truncates this same database.** Do not run it while reviewing, or the Playground disappears underneath you. Re-run `make demo-seed` afterwards.

---

## Signing in — the demo accounts

**Four accounts, created through Better Auth's own sign-up and verification routes.** Not a bypass and not a fixture: each was registered by the same handler the browser's form reaches, with a password Better Auth hashed and a verification token Better Auth minted. **They simply already exist.**

**Password for all four: `signora-demo-password`**

| Email | Persona | Role | What they can do |
|---|---|---|---|
| `dana.reyes@northwind.example` | Revenue Operations | **owner** | Everything, including Settings and adding members |
| `marcus.hale@northwind.example` | Sales Manager | member | Read and work accounts; **no Settings** |
| `priya.nair@northwind.example` | Account Executive | member | Read and work accounts |
| `sam.okafor@northwind.example` | Sales Development | member | Read and work accounts |

All four belong to the **Playground** organization and see the same twelve accounts. Sign in as two of them in different browsers to see an account *held by someone else* after one takes it on.

> **The screen says *organization*; the API says `workspace`.** One concept, two vocabularies, and the split is deliberate ([ADR-0034](architecture/adr/0034-ubiquitous-language.md)): a customer's company on Signora, and the tenancy boundary that isolates it. The translation happens in `frontend/` and never travels inward — every path below, the `workspace_id` column, the RLS scope and the JWT claim all keep the internal name, because *workspace* is precise about isolation in a way *organization* is not.

> **Signora has two roles — `owner` and `member` — not five.** The sales titles above are personas for review, not something the product models. A richer role model is a domain decision nobody has needed yet; see `04-modules.md`.

Addresses use the reserved `.example` TLD deliberately: it can never resolve, so a build that one day has a real email transport cannot mail a real person by accident. Both the accounts and their roles are declared once, in `infra/demo-users.json`, read by the script that creates them and the seeder that enrols them.

### Signing up as yourself instead

Register at **<http://localhost:3000/sign-up>**. Signora asks you to confirm your address before creating a session — `requireEmailVerification` is on, which is what makes `email_verified` a fact rather than something an identity provider asserted.

**The link is written to the dev server's output**, framed so it is hard to miss:

```
  ┌────────────────────────────────────────────────────────────────
  │  Verify this address to finish signing up
  │  you@example.com
  │
  │  http://localhost:3000/api/auth/verify-email?token=…
  └────────────────────────────────────────────────────────────────
```

**Nothing is bypassed and nothing is mocked.** Real token, real expiry, real route — only the transport is stdout instead of an email provider, which has not been chosen yet. The console transport **refuses to start** when `SIGNORA_ENVIRONMENT` names a deployed environment, because a reset link in a production log is a credential in a log file.

Forgot-password works the same way at **<http://localhost:3000/forgot-password>**. The reply is identical whether or not the address exists — that page is unauthenticated, and a message distinguishing the two would make it an enumeration oracle.

Re-run `make demo-seed` after registering, to be enrolled in the Playground.

### Adding Google or Microsoft

Both halves of a credential in `frontend/.env.local` and the button appears:

```
GOOGLE_CLIENT_ID=…
GOOGLE_CLIENT_SECRET=…
```

Both halves or neither — a half-configured provider renders a button that fails at the callback, which is worse than not offering it. **Whichever method somebody uses, Better Auth issues one session and the JWT carries no record of which** ([ADR-0033](architecture/adr/0033-authentication-methods.md)).

*(This replaces an earlier version of this document which said sign-in was **OAuth only**, and an earlier one still which said to "create an account with any email". The first was true when written; the second never was. Both are corrected here rather than deleted, because the sequence is the record.)*

---

## Running a lane

Three development lanes work the same repository at once (`CLAUDE.md` §20e). **Separate clones isolate the code; they do not isolate the database or the ports** — and a second `pytest` run against the shared database truncates another lane's rows mid-test, producing failures nobody can reproduce.

### The allocation convention — permanent

**This table records which SLOT each environment holds. Everything else is derived from it** — ⛔ **no lane types a port and no lane types a database name.**

```bash
eval "$(python3 infra/environments.py --exports)"
```

⚡ **That is the authoritative answer for the clone you are standing in**, resolved from `SIGNORA_ENVIRONMENT` if set, else the checked-out branch. **`SIGNORA_POSTGRES_PORT`, `SIGNORA_REDIS_PORT`, `SIGNORA_WEB_PORT`, `SIGNORA_API_PORT`, `SIGNORA_DATABASE` and `COMPOSE_PROJECT_NAME` all come from there.**

| Environment | Branch | Slot | Web | API | PostgreSQL | Redis | MinIO |
|---|---|---|---|---|---|---|---|
| **Human review** | `main` | **0** | 3000 | 8000 | **5432** | 6379 | 9000/9001 |
| **Production stack** *(smoke · dr · certify)* | any | — | 3100 | 8100 | *its own, inside its compose project* | *its own* | *its own* |
| **QE** | `lane-qe` | **1** | 3200 | 8200 | **5632** | 6579 | 9200/9201 |
| **Lane A — Product Surface** | `lane-a-product-surface` | **2** | 3300 | 8300 | **5732** | 6679 | 9300/9301 |
| **Lane B — Commercial Profile** | `lane-b-commercial-profile` | **3** | 3400 | 8400 | **5832** | 6779 | 9400/9401 |
| **Lane C** — *Product Office & Platform Foundation* | `lane-c` | **4** | 3500 | 8500 | **5932** | 6879 | 9500/9501 |
| **Lane D** | *unclaimed* | **5** | 3600 | 8600 | **6032** | 6979 | 9600/9601 |
| **Lane E** | *unclaimed* | **6** | 3700 | 8700 | **6132** | 7079 | 9700/9701 |
| **Demo** — *the seeded product, for a non-engineer* | any | **7** | 3800 | 8800 | **6232** | 7179 | 9800/9801 |

**Every environment's database is `signora`.** ⛔ **The NAME does not separate anything and never did** — [B-271](BUGS.md). **The PostgreSQL PORT is the separator**, because each environment runs its own cluster in its own compose project, and 📁 [483](architecture/483-environment-isolation-audit.md) is why: *"a PostgreSQL role is cluster-wide… per-database separation cannot reach a shared cluster; a separate cluster has separate roles."*

> 🔴 **This table used to carry a `Database` column of `signora_lane_a`, `signora_lane_qe`, `signora_lane_c` and no PostgreSQL or Redis PORT column at all.** ⛔ **Those databases were never created by any compose file** — the derivation named them and nothing made them. ⚡ **The table WAS the old one-server-many-databases model**, which is why two models coexisted for so long: `:324` below was not a stray stale example but an instance of what this table asserted.
>
> ⚠️ **Corrected 2026-08-15, cycle 233** ([B-1003](BUGS.md)), **after QE cited this file to a lane as the safe path around a data-destruction defect without opening it.** 📁 **The warning was already here, addressed to QE, at the top of this document.**
>
> ⛔ **The ports above are shown so a reader can sanity-check what they are connected to. They are NOT the source** — `infra/environments.py` is, `SLOT_STRIDE` is 100, and **if this table and the exports ever disagree, the exports are right and the disagreement is a defect to report.**

> **`lane-c` gained a runtime on 2026-08-05, and the row that said *none* was correct when it was written.** Lane C owned no module and needed no ports; **Platform Foundation changed that** — it now builds `infra/`, the launchers and the demo lifecycle, and cannot test a launcher it cannot run. **`demo` is a profile rather than a lane**, which is why it names no branch.
>
> **This table is a rendering of `infra/environments.py`, not an independent source.** `make environments ARGS="--check"` compares them and **named these two rows as QE's to write** — the derivation had them and the rendering did not. **When they differ, somebody edited the rendering** (§2).
| **Lane E** | *unclaimed* | 3700 | 8700 | `signora_lane_e` | 6 |

> **Lane C is allocated nothing, and that is correct.** It owns no production module and runs no production code, so it needs a clone, a branch, the documentation and repository access — **no ports, no database, no Redis index, no MinIO bucket, no compose project.** It is the first lane whose onboarding is *simpler* than the one before it, and the row records the absence so nobody allocates it a block out of symmetry.
>
> **The port block 3500/8500 stays free** for the next *implementation* lane, whenever one is created.

**The rule generating it:** web `3000 + 100n`, API `8000 + 100n`, database `signora_lane_<letter>`, Redis logical index `n`. One block of 100 per environment, so nothing collides and the arithmetic is obvious from any one row.

> **3000 and 8000 belong to human review on `main`, and to no lane.** This is a change, ratified 2026-08-01: Lane A previously held them, which put a feature lane and the product owner's demo stack on the same two ports. **Lane A moves to 3300/8300** and must update its `frontend/.env.local` and its API command. It also removes an ambiguity in `make smoke`, which binds 3000 and 8000 and could previously fail because of a *lane's* dev server without anything saying so ([B-002](BUGS.md)).

> **One Postgres, one Redis, many databases.** There is no second stack — Postgres holds as many databases as there are lanes, Redis distinguishes them by logical index, and nothing in the test path touches Redis today. The Redis column exists so that the first lane whose work does touch it is not the one that has to invent the scheme.

Three things per lane. ⛔ **Do not copy a port or a database name from anywhere, including the table above** — **derive them, every session, in the shell you are about to work in:**

```bash
eval "$(python3 infra/environments.py --exports)"
```

> 🔴 **Then CHECK, before anything destructive runs.** **If `SIGNORA_POSTGRES_PORT` is `5432` you are NOT on a lane branch** — that is human review's cluster, and the suite truncates every table after each test ([B-270](BUGS.md)). ⛔ **Stop, and set `SIGNORA_ENVIRONMENT` to your own environment.**
>
> ⚡ **`make` targets carry their own guard — `refuse-slot-0` — and an inline assignment in a recipe overrides an exported variable, so a poisoned shell is still safe there.** ⛔ **A hand-run command has no such guard**, which is the whole reason this section derives rather than quotes.

**1 — its own cluster**, once. ⚡ **Every environment runs its own PostgreSQL in its own compose project, and its database is always `signora`** — **there is nothing to create:**

```bash
env $(python3 infra/environments.py --exports | grep -v '^#') \
  docker compose -f infra/docker-compose.yml up -d --wait

cd backend && SIGNORA_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:${SIGNORA_POSTGRES_PORT}/${SIGNORA_DATABASE}" \
  uv run alembic upgrade head
```

> ⛔ **This step used to run `CREATE DATABASE signora_lane_b` against `localhost:5432/postgres`** — **slot 0's cluster.** ⚡ **That is where `signora_lane_a`, `signora_lane_b`, `signora_lane_qe` and `signora_validate_lanea` came from, and it is exactly where [B-270](BUGS.md)'s destructive fallback lands.** 📁 **The runbook was not merely mis-directing a lane at slot 0; it was instructing them to create the decoy there** ([B-1003](BUGS.md)).

**2 — point the tests at it.** **Three variables, and all three must be exported** — `backend/.env` is not enough, because `tests/conftest.py` reads `os.environ` directly:

```bash
export SIGNORA_TEST_APP_DATABASE_URL="postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:${SIGNORA_POSTGRES_PORT}/${SIGNORA_DATABASE}"
export SIGNORA_TEST_ADMIN_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:${SIGNORA_POSTGRES_PORT}/${SIGNORA_DATABASE}"
export SIGNORA_DATABASE_URL="postgresql+asyncpg://signora:signora@localhost:${SIGNORA_POSTGRES_PORT}/${SIGNORA_DATABASE}"
export SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1
```

> ⚠️ **The app role is `signora_app`, never the owner.** 📁 **`tests/conftest.py:106` refuses a connection with `BYPASSRLS`** — *"otherwise Row-Level Security is not enforced and isolation assertions are vacuous"* — **and it caught QE doing exactly that while validating this change.**

> ✅ **Confirm what you are actually connected to before trusting any of it.** ⚡ **`pg_database` is the only operand that cannot be stale:**
>
> ```bash
> psql "postgresql://signora:signora@localhost:${SIGNORA_POSTGRES_PORT}/postgres" \
>   -tAc "select datname from pg_database where datname not like 'template%'"
> ```

**Every test path honours the first two** — the fixtures, the API integration clients and the seeders all resolve the URL from one place in `tests/conftest.py`.

**The third is the one that catches people out.** `migrations/env.py` reads `SIGNORA_DATABASE_URL` from `os.environ` directly and never sees `backend/.env`, so a lane that sets only the first two gets three failures in `tests/integration/test_migration_runner.py` whose message — *"SIGNORA_DATABASE_URL must be set to run migrations"* — reads like a broken schema. Worse, set it to a *different* database and the migration runner locks one and migrates the other. That is [B-007](BUGS.md), and it is open — the documentation half is [B-003](BUGS.md).

**Verify before your first slice**, and do it by auditing rather than by watching row counts: `grep -rn "postgresql" --include=*.py backend/tests backend/apps backend/migrations | grep -v .venv`. Every hit must resolve from one of the variables above or be a deliberately unreachable address. **Differencing the other lanes' databases proves nothing** — they are written concurrently by their own sessions. Only `signora` must be provably untouched.

**3 — its own ports.** From the allocation table above:

```bash
cd frontend && npm run dev -- --port 3400
cd backend && uv run uvicorn apps.api.main:create_app --factory --reload --port 8400
```

Set `SIGNORA_API_URL` and `BETTER_AUTH_URL` to that lane's ports in its `frontend/.env.local`.

> **`make smoke` binds 3100 and 8100** since 2026-08-03, and no longer contends with human review or with any lane. [B-002](BUGS.md) described the old collision and is a record of what was true then, not a current limitation.

> **The Playground lives in `signora`, and no lane's tests may target it.** That is the whole point of steps 1 and 2: it is the database `make demo-seed` fills and the one you review the product in.

---

## When something does not work

> 🔴 **Three of the rows below share one rule, and it is worth reading before the table**: ⚡ ***realign before trusting a red.*** ⛔ **A stamped database, a stale workspace pointer and an exhausted swap file each produce a failure that looks like a defect in the code and is not.** 📁 **All three were found by lanes on 2026-08-16, all three cost time, and in the second case the product was working correctly the whole time.**

| What you see | What it is |
|---|---|
| Sign-in fails with a database error about `auth.user` | Better Auth's tables were never created. `cd frontend && npm run auth:migrate` — `make demo` does it for you |
| Signed in, but every screen is empty and the API 401s | No signing key. `npm run keys:generate` and put both halves where the table below says. `/api/health` reports `signing_keys: unavailable` |
| *"You are not part of an organization yet"* | You registered after the last seed. Re-run `make demo-seed` |
| The Playground is suddenly empty | `make test` truncates every table in the same database. Re-run `make demo-seed` |
| `/api/health` says `sign_in_methods: degraded` | Password sign-in is switched off and no OAuth credentials are set, so nobody can sign in |
| Migrations fail with a permissions error | They are running as `signora_app`. Schema changes execute only under the **owner** identity — pass `SIGNORA_DATABASE_URL` explicitly, as step 2 does |
| `ResolutionError: No such revision or branch '0060'` — or any revision the tree does not contain | 🔴 **Your DATABASE is stamped above your TREE.** Checking out a branch that adds a migration, running anything, then switching away leaves the stamp behind. ⛔ **It reads as a broken migration runner and it is a stamped database.** ✅ `alembic downgrade <the head your tree has>`, then re-run. ⚠️ **Found twice in one day by Lane C**, and it will reach anybody who touches a branch whose migration head differs from `integration`'s |
| A journey fails with *"table not found"* on a screen that looks fine | 🔴 **The screen is probably CORRECT and the assertion is wrong.** ⛔ **Repeated E2E runs leave the signed-in user's active workspace pointing at an `E2E Org …` that has no accounts** — and **zero rows renders the designed empty state, which is not a table.** ✅ Re-seed the Playground. 📁 **Found by Lane A after four Companies journeys failed against a working product** |
| A suite produces no output for many minutes | ⚠️ **Check memory before concluding it is slow.** ⛔ **A run producing NO bytes is indistinguishable from one producing them slowly**, and thrashing looks exactly like a long suite. 📁 **Lane A waited twenty minutes on a Playwright run that finished in 46 seconds once `next dev` was restarted.** ✅ `free -h` — if swap is exhausted, the suite is not the problem |

---

## Environment variables

**Backend** — every one is required; none has a default that would be safe in production.

| Variable | Local value |
|---|---|
| `SIGNORA_DATABASE_URL` | `postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:${SIGNORA_POSTGRES_PORT}/${SIGNORA_DATABASE}` — 🔴 **port `5432` is human review's cluster.** **Derive it.** ⛔ **This row read `localhost:5432/signora` until 2026-08-15 while the Redis row directly below already carried this warning** ([B-1003](BUGS.md)) |
| `SIGNORA_REDIS_URL` | `redis://localhost:${SIGNORA_REDIS_PORT}/0` — **port `6379` is human review's.** Derive it as above; the worker and relay refuse to start without it. ⚡ **Each environment runs its own Redis, so the logical INDEX no longer separates lanes — the port does** |
| `SIGNORA_JWT_PUBLIC_KEY` | the **public** half of a dev RSA pair |
| `SIGNORA_JWT_ISSUER` | `http://localhost:3000` |
| `SIGNORA_JWT_AUDIENCE` | `signora-api` |

`backend/.env.example` lists the full set. **Note the database user: `signora_app`, never the owner.** A service connected as the owner is exempt from Row-Level Security on every table it touches, which silently voids tenancy (CLAUDE.md §8).

**Frontend** — `frontend/.env.local`:

```
BETTER_AUTH_SECRET=<any string, local only>
BETTER_AUTH_URL=http://localhost:3000
SIGNORA_API_URL=http://localhost:8000
SIGNORA_JWT_PRIVATE_KEY=<the private half of the same pair>
```

**The signing key lives only in the frontend.** The Python tier holds the public half and can verify but never mint ([ADR-0026](architecture/adr/0026-jwt-boundary-architecture.md)).

---

## The Product Playground — what `make demo` showcases

`make demo` seeds **twelve accounts through the real pipeline**: provider simulation → ingestion → normalization → knowledge graph → observations → business events → signals → buying scores → opportunities.

**There is one product.** The seeder runs the same function the pipeline suite runs, over the `playground@2` scenario instead of `baseline@1`. No branch anywhere knows it is a playground; the only things that differ are which scenario file is named and where its timeline is anchored.

**Sign in once before seeding.** Better Auth owns users and hashes its own passwords, so the seeder cannot create one without either committing a credential or reaching into another system's schema. Register at <http://localhost:3000/sign-up>, then re-run `make demo-seed`; it enrols every signed-in user in the seeded organization and prints what it did.

### The twelve stories

Twelve companies you will recognise, and **twelve business situations that are entirely invented.** Nothing here was observed or reported, and none of it is a claim about any company's actual behaviour, plans, finances or purchasing intent. The dataset says so in its own body, so the notice travels with a screenshot.

| Account | The story | What the pipeline makes of it |
|---|---|---|
| **NVIDIA** | Hiring and revenue both moving | Expansion opportunity, on two independent grounds |
| **Databricks** | A round closed, and the hiring that follows one | Expansion opportunity · a funding line that counted **zero**, with its reason |
| **Snowflake** | An acquisition, and a live evaluation beside it | Active evaluation · consolidation underway |
| **Stripe** | Cutting headcount while evaluating AI tooling | **Contested** — both readings live, the minority marked |
| **Atlassian** | A security initiative | Active evaluation, from intent alone |
| **Figma** | Behavioural intent and nothing else | **Nobody has named it** — the row shows its real identifier |
| **HubSpot** | A marketing stack replaced two months ago | Displacement · modernization, at **recent** weight — and **cooling** |
| **Salesforce** | A new revenue leader | New decision maker — neutral, not expansionary |
| **Adobe** | An ERP replacement whose evidence has aged | **Ageing** evidence at 30% · a **disputed name** (registry vs trading) |
| **MongoDB** | An evaluation that has just passed its shelf life | **Stale** — correct when read, not refreshed since |
| **Datadog** | A reduction, with nothing pulling the other way | Contraction risk · **stale** |
| **Twilio** | The CFO departed | Decision maker departed — barely qualifying, and honest about it |

### What is demonstrated, and none of it is set

Every state below is produced by the pipeline from the dates in the scenario. **Not one is declared anywhere.**

- **Score spread 1–50**, not a wall of similar numbers.
- **Freshness varies on its own** — fresh (100%), recent (60%) and ageing (30%) all appear in the ledgers, because the narrative spans five months and the shortest relevance window is ninety days.
- **Current, cooling and stale** all occur. Opportunities are qualified against the scores as they stood five weeks ago, and the scheduled re-scoring last ran three days ago — so an account whose evidence expired inside that gap reads stale, exactly as a customer would see it.
- **All nine signal types** in the catalog fire, across all three postures.
- **All four identity states**: agreed, single-source, disputed, and nobody-has-named-it.
- **A line that counted zero**, with the reason it counted nothing.

---

## What you can see today

| Route | What it does |
|---|---|
| `/` | Overview — real empty states, no business data yet |
| **`/`** | **Attention.** Accounts ranked by live buying score, each naming **the hypothesis that most explains it** — *active evaluation*, *expansion opportunity*, *contraction risk* — plus how far it moved and how fresh the evidence is. This is the product's front door: the Overview page that used to sit here was retired at M12.3 ([D38](architecture/38-product-design-principles.md)) |
| **`/accounts/{accountId}`** | **The account brief.** The score and the arithmetic behind it, what changed since somebody committed, a grounded explanation, what to check before acting, every contributing line — and the controls to say what you decided. Opened by clicking an account name |
| `/settings` | Workspaces and members |

### The endpoints behind them

```
GET /workspaces/{workspace_id}/accounts
GET /workspaces/{workspace_id}/account-identities?ids=<uuid>&ids=<uuid>
GET /workspaces/{workspace_id}/accounts/{account_id}/score
GET /workspaces/{workspace_id}/accounts/{account_id}/opportunity
GET /workspaces/{workspace_id}/accounts/{account_id}/narration
GET /workspaces/{workspace_id}/accounts/{account_id}/validation
GET /workspaces/{workspace_id}/business-events/{event_id}
GET /workspaces/{workspace_id}/products
PUT /workspaces/{workspace_id}/products
```

All seven are documented at **<http://localhost:8000/docs>**.

### Expected behaviour — the list

- Accounts appear **most pressing first** — ranked by the *live* score, not the one that opened the opportunity.
- Each row shows **why now** (new evidence, a changed model, evidence ageing out), how far the score moved, and a badge only when the evidence is cooling or stale.
- A **contested** account ranks above a quiet one at the same score.
- Company names resolve in a **second request** and appear as they arrive; rows do not wait for them.
- A name your providers **disagree** about shows an ⓘ naming who reported the one displayed. In the Playground this is **Adobe** — the registry's name beside the trading one.
- An account nothing has named shows its **real identifier**, never a placeholder.
- **Clicking the name opens the brief.** Only the name — the rest of the row is not a link, and does not pretend to be.

### Expected behaviour — the brief

- **What changed leads.** *"Opened at 35, 5 weeks ago · −15 since"* — the movement since somebody committed, which is the one figure the list cannot show because it only knows about today.
- Under the account name, **what Signora has and has not decided**: *"Signora is tracking this · nobody has taken it yet."* Only `tracking` is machine-authored; every stage beyond it names a person.
- The score appears beside the two integers that produce it: **`68 of 120 points`**. Check it yourself: `score = min(100, points × 100 ÷ ceiling)`.
- **How long the reading is correct for** is stated — a buying score is exactly correct until its stated expiry, not merely recent. An expired reading is shown as expired rather than hidden.
- **Attention is split by posture** (expansion / risk / context) and never netted. Two accounts can score the same and mean opposite things.
- **Every line that produced the score is listed**, largest first, in the order the pipeline recorded — including lines that counted **zero**, with the reason they counted nothing.
- On a **contested** account, the lines disagreeing with the majority reading are marked, and a note says plainly that Signora has neither picked a side nor split the difference.
- **Every ledger line opens.** Click one and a dialog shows the provider readings beneath it — `29,000 → 34,000, CoreSignal, 25 Jul` — and names every provider that reported it. **This is the only content on the brief Signora did not write.**
- **Every narration citation opens too**, since M12.3's last slice. A sentence reading *"2 facts"* is a control: click it and you see **exactly what the model was given** — the summaries and figures that went into the prompt, in the words of the part of Signora that computed them. Requires `make demo-narrate` to have run.
- **And it says whether the explanation still holds.** The evidence is re-derived and compared against the digest recorded when the sentences were written. If the account has moved since, the dialog says so — *"a narration is never rewritten to catch up"* — rather than presenting today's facts as the ones the model saw.
- **"Before you act"** lists what to confirm for each live hypothesis, and hides *what it cannot tell you* behind a disclosure. **No model produced any of it** — it is the Signal Catalog's own guidance, versioned and reviewed like code, and it had never been displayed before M12.3.
- An account with no score shows a **designed empty state**, not an error.

### Your business — `/settings/products`

- **The first screen where you tell Signora something.** Everything else reports what the pipeline computed; this records what your company sells, and it is the input the pipeline has never had.
- **Add, edit and remove products.** Each change saves immediately as a **new version** of the catalog — nothing is edited, and the footer says which version is in force.
- **A product keeps its id when you rename it**, which is what will let an ICP or a priority cite it later and still resolve.
- **Open it in two browsers and save from both.** The second is refused with the version actually in force, rather than quietly overwriting the first — the failure a versioned catalog exists to make visible.
- **Owners only.** `/settings/*` is owner-guarded, and the server refuses a member's write independently with 403.

### Known limitations, and what is intentionally unfinished

- **Products are declared and nothing consumes them yet.** ICP, buying committee, priorities and the target account list are slices 2–5; the last of those is what finally gives Provider Platform a source for the companies it monitors.
- **No Decision Package on the brief.** `reasoning@1` has no released model, so there is nothing to show — deliberately not built around an unavailable capability.
- **No sort or filter controls.** A client-side sort would reorder only the loaded page while presenting it as the top of the whole list *(D4)*.
- **One page, no infinite scroll.** The cursor works; the UI does not page yet.
- **The ledger is only known to read well at a handful of lines.** A forty-line account has not been seen *(D16)*.
- **Eight of twelve accounts read "unchanged since".** Truthful — all the scenario's evidence arrives in one ingest, so after an opportunity opens the only thing that can happen is decay. The product's most encouraging story, *this account is heating up*, cannot be demonstrated at all *(D22)*.
- **Roughly ten of twelve accounts narrate.** The rest time out on a local 8B model and can be re-run — `make demo-narrate` is safe to repeat. A separate defect refuses any statement quoting a date in the first nine days of a month, because a zero-padded `01` in the evidence never matches a `1` in prose *(F-11)*.
- **The ledger repeats itself on a composite signal.** An account whose expansion rests on two grounds shows two identical sentences, because the line names the *hypothesis* and not the evidence beneath it *(D19)*.
- **`reasoning@1` has no released model**, so the Decision Package stage would refuse at runtime. It is not on either screen, so you will not see it — but the pipeline is not whole.

## The commit guard

**One line, once per clone:**

```bash
git config core.hooksPath infra/hooks
```

**It refuses a commit on `main` or `integration` that does not belong there** — a Closeout on the first, a claim on the second, and anything at all on a lane branch. It owns no rules of its own: `infra/certification-guard.py` already defines both, and the hook asks it rather than keeping a second copy.

**Why it exists.** Twice a commit landed on the wrong branch because the shell was on whatever branch the previous command left it — once on `main`, bypassing certification entirely. Neither was careless; each command was correct in isolation and neither checked where it was standing.

**Bypass with `git commit --no-verify`** when the commit genuinely is a Closeout or a claim, and say why in the message.
