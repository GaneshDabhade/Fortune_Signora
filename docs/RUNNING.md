# Running Signora locally

> Written 2026-07-31, at M12.2. **Assume nothing is already running and nothing is already known.** Every command below is copy-pasteable from a fresh clone.

## What you need once

| | |
|---|---|
| **Docker** | for PostgreSQL and Redis |
| **[uv](https://docs.astral.sh/uv/)** | Python toolchain — the backend is never run with bare `python` |
| **Node 20+ / npm** | frontend |
| **Ollama** *(optional)* | only for `make eval*`. **The app itself never calls a model.** |

Everything runs locally. There is no cloud environment and no remote gate ([ADR-0027](architecture/adr/0027-local-first-development.md)).

---

## The short version

```bash
# 0 — configuration
cp backend/.env.example backend/.env         # local values only; never committed
cp frontend/.env.example frontend/.env.local
cd frontend && npm install && npm run keys:generate   # paste both halves in — see below

# 1 — everything else, in one command
make demo
```

`make demo` brings up PostgreSQL and Redis, migrates the schema under the **owner** identity, creates **Better Auth's own tables**, creates **four sign-in accounts**, and seeds **twelve accounts through the real pipeline**.

Then start the two processes and open the product:

```bash
# backend
cd backend && SIGNORA_DATABASE_URL=postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:5432/signora \
  SIGNORA_REDIS_URL=redis://localhost:6379/0 \
  SIGNORA_JWT_PUBLIC_KEY="$(cat .dev-keys/public.pem)" \
  SIGNORA_JWT_ISSUER=http://localhost:3000 \
  SIGNORA_JWT_AUDIENCE=signora-api \
  uv run uvicorn apps.api.main:app --reload --port 8000

# frontend
cd frontend && npm run dev
```

**<http://localhost:3000>** → sign in as `dana.reyes@northwind.example`.

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

Three things per lane, all environment variables. **Substitute your lane's row from the table in step 3.**

**1 — its own database**, once. **All three already exist and are migrated to head**, so this is only needed for a lane added later:

```bash
cd backend
uv run python -c "
import asyncio, asyncpg
async def main():
    c = await asyncpg.connect('postgresql://signora:signora@localhost:5432/postgres')
    await c.execute('CREATE DATABASE signora_lane_b OWNER signora')
    await c.close()
asyncio.run(main())"

SIGNORA_DATABASE_URL=postgresql+asyncpg://signora:signora@localhost:5432/signora_lane_b \
  uv run alembic upgrade head
```

**2 — point the tests at it.** In that lane's shell or `backend/.env`:

```bash
export SIGNORA_TEST_APP_DATABASE_URL=postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:5432/signora_lane_b
export SIGNORA_TEST_ADMIN_DATABASE_URL=postgresql+asyncpg://signora:signora@localhost:5432/signora_lane_b
```

**Every test path honours these** — the fixtures, the API integration clients and the seeders all resolve the URL from one place in `tests/conftest.py`. **Verify before your first slice:** run any integration test and confirm rows moved in your database and not in `signora`.

**3 — its own ports and database.** One block of 100 per lane, so nothing collides:

| Lane | Branch | Web | API | Test database |
|---|---|---|---|---|
| A — Product Surface | `lane-a-product-surface` | 3000 | 8000 | `signora_lane_a` |
| B — Commercial Profile | `lane-b-commercial-profile` | 3100 | 8100 | `signora_lane_b` |
| QE | `lane-qe` | 3200 | 8200 | `signora_lane_qe` |



```bash
cd frontend && npm run dev -- --port 3100
cd backend && uv run uvicorn apps.api.main:app --reload --port 8100
```

Set `SIGNORA_API_URL` and `BETTER_AUTH_URL` to that lane's ports in its `frontend/.env.local`.

**One Postgres, one Redis, many databases.** There is no second stack — Postgres holds as many databases as there are lanes, and nothing in the test path touches Redis today.

> **`make smoke` binds ports 3000 and 8000.** It cannot run while any dev server holds them — stop **every** lane's dev server first. Worth knowing before a milestone gate, because the failure reads as *"stack did not reach healthy"* rather than *"a port is in use"*.

> **The Playground lives in `signora`, and no lane's tests may target it.** That is the whole point of steps 1 and 2: it is the database `make demo-seed` fills and the one you review the product in.

---

## When something does not work

| What you see | What it is |
|---|---|
| Sign-in fails with a database error about `auth.user` | Better Auth's tables were never created. `cd frontend && npm run auth:migrate` — `make demo` does it for you |
| Signed in, but every screen is empty and the API 401s | No signing key. `npm run keys:generate` and put both halves where the table below says. `/api/health` reports `signing_keys: unavailable` |
| *"You are not part of an organization yet"* | You registered after the last seed. Re-run `make demo-seed` |
| The Playground is suddenly empty | `make test` truncates every table in the same database. Re-run `make demo-seed` |
| `/api/health` says `sign_in_methods: degraded` | Password sign-in is switched off and no OAuth credentials are set, so nobody can sign in |
| Migrations fail with a permissions error | They are running as `signora_app`. Schema changes execute only under the **owner** identity — pass `SIGNORA_DATABASE_URL` explicitly, as step 2 does |

---

## Environment variables

**Backend** — every one is required; none has a default that would be safe in production.

| Variable | Local value |
|---|---|
| `SIGNORA_DATABASE_URL` | `postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:5432/signora` |
| `SIGNORA_REDIS_URL` | `redis://localhost:6379/0` |
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
