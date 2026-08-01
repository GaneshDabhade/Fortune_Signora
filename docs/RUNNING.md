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
cp backend/.env.example backend/.env      # local values only; never committed

# 1 — infrastructure
docker compose -f infra/docker-compose.yml up -d --wait   # PostgreSQL 5432, Redis 6379

# 2 — schema, run under the *owner* identity, never the runtime one
cd backend && SIGNORA_DATABASE_URL=postgresql+asyncpg://signora:signora@localhost:5432/signora \
  uv run alembic upgrade head

# 3 — seed the Product Playground: twelve accounts through the real pipeline
make demo-seed                # or `make demo`, which does steps 1–3 for you

# 4 — backend
cd backend && SIGNORA_DATABASE_URL=postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:5432/signora \
  SIGNORA_REDIS_URL=redis://localhost:6379/0 \
  SIGNORA_JWT_PUBLIC_KEY="$(cat .dev-keys/public.pem)" \
  SIGNORA_JWT_ISSUER=http://localhost:3000 \
  SIGNORA_JWT_AUDIENCE=signora-api \
  uv run uvicorn apps.api.main:app --reload --port 8000

# 5 — frontend
cd frontend && npm install && npm run dev
```

Then open **<http://localhost:3000/opportunities>**.

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

## Login

Sign-in is Better Auth in Next.js. On a local stack, use the sign-in page at <http://localhost:3000/sign-in> and create an account with any email — there is no seeded user, because seeding one would put a credential in the repository.

**After signing in, create a workspace** from Settings. A workspace is the tenancy boundary; nothing is visible without one.

---

## The Product Playground — what `make demo` showcases

`make demo` seeds **twelve accounts through the real pipeline**: provider simulation → ingestion → normalization → knowledge graph → observations → business events → signals → buying scores → opportunities.

**There is one product.** The seeder runs the same function the pipeline suite runs, over the `playground@2` scenario instead of `baseline@1`. No branch anywhere knows it is a playground; the only things that differ are which scenario file is named and where its timeline is anchored.

**Sign in once before seeding.** Better Auth owns users and hashes its own passwords, so the seeder cannot create one without either committing a credential or reaching into another system's schema. Sign in at <http://localhost:3000/sign-in>, then re-run `make demo-seed`; it enrols every signed-in user in the seeded workspace and prints what it did.

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
| **`/opportunities`** | **The attention list.** Accounts ranked by live buying score, each with why it surfaced, how far it moved, and how fresh the evidence is |
| **`/opportunities/{accountId}`** | **The account brief.** The score, the arithmetic behind it, and every line that produced it. Opened by clicking an account name on the list |
| `/settings` | Workspaces and members |

### The endpoints behind them

```
GET /workspaces/{workspace_id}/accounts
GET /workspaces/{workspace_id}/account-identities?ids=<uuid>&ids=<uuid>
GET /workspaces/{workspace_id}/accounts/{account_id}/score
```

All three are documented at **<http://localhost:8000/docs>**.

### Expected behaviour — the list

- Accounts appear **most pressing first** — ranked by the *live* score, not the one that opened the opportunity.
- Each row shows **why now** (new evidence, a changed model, evidence ageing out), how far the score moved, and a badge only when the evidence is cooling or stale.
- A **contested** account ranks above a quiet one at the same score.
- Company names resolve in a **second request** and appear as they arrive; rows do not wait for them.
- A name your providers **disagree** about shows an ⓘ naming who reported the one displayed. In the Playground this is **Adobe** — the registry's name beside the trading one.
- An account nothing has named shows its **real identifier**, never a placeholder.
- **Clicking the name opens the brief.** Only the name — the rest of the row is not a link, and does not pretend to be.

### Expected behaviour — the brief

- The score appears beside the two integers that produce it: **`68 of 120 points`**. Check it yourself: `score = min(100, points × 100 ÷ ceiling)`.
- **How long the reading is correct for** is stated — a buying score is exactly correct until its stated expiry, not merely recent. An expired reading is shown as expired rather than hidden.
- **Attention is split by posture** (expansion / risk / context) and never netted. Two accounts can score the same and mean opposite things.
- **Every line that produced the score is listed**, largest first, in the order the pipeline recorded — including lines that counted **zero**, with the reason they counted nothing.
- On a **contested** account, the lines disagreeing with the majority reading are marked, and a note says plainly that Signora has neither picked a side nor split the difference.
- An account with no score shows a **designed empty state**, not an error.

### Known limitations, and what is intentionally unfinished

- **Neither screen leads to an action.** Assign, move stage and dismiss are M12.3 *(D3, D15)*. No disabled control is drawn in their place.
- **A citation cannot be followed yet.** Each ledger line carries its signal and business-event identifiers, and there is nowhere to click them until M12.3 builds evidence resolution. They are on the wire, not on the screen.
- **No narration or Decision Package on the brief.** The remaining M12.2 scope.
- **No sort or filter controls.** A client-side sort would reorder only the loaded page while presenting it as the top of the whole list *(D4)*.
- **One page, no infinite scroll.** The cursor works; the UI does not page yet.
- **The ledger is only known to read well at a handful of lines.** A forty-line account has not been seen *(D16)*.
- **The ledger repeats itself on a composite signal.** An account whose expansion rests on two grounds shows two identical sentences, because the line names the *hypothesis* and not the evidence beneath it *(D19)*.
- **`reasoning@1` has no released model**, so the Decision Package stage would refuse at runtime. It is not on either screen, so you will not see it — but the pipeline is not whole.
