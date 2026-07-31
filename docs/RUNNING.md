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
# 1 — infrastructure
docker compose up -d          # PostgreSQL on 5432, Redis on 6379

# 2 — schema
cd backend && uv run alembic upgrade head

# 3 — seed a workspace with real pipeline data   (see "Sample data" below)
cd backend && SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 \
  SIGNORA_DATABASE_URL=postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:5432/signora \
  uv run pytest tests/integration/test_api_accounts.py -q

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

## Sample data — and the honest caveat

**There is no `make demo` yet.** Today the only realistic data comes from the integration suite, which runs the *real* pipeline over the M2.0 baseline scenario and leaves its rows behind. Step 3 above is that: running the account tests seeds two accounts (`northwind`, `contoso`) with genuine business events, signals, buying scores and opportunities.

**This is unsatisfying and it is recorded as such.** The suite truncates tables between tests, so what survives is the last run's workspace — and you must sign in as a user who is a member of it, which the test creates rather than you. **See "Product Playground" below.**

---

## What you can see today

| Route | What it does |
|---|---|
| `/` | Overview — real empty states, no business data yet |
| **`/opportunities`** | **The attention list.** Accounts ranked by live buying score, each with why it surfaced, how far it moved, and how fresh the evidence is |
| `/settings` | Workspaces and members |

### The endpoints behind `/opportunities`

```
GET /workspaces/{workspace_id}/accounts
GET /workspaces/{workspace_id}/account-identities?ids=<uuid>&ids=<uuid>
```

Both are documented at **<http://localhost:8000/docs>**.

### Expected behaviour

- Accounts appear **most pressing first** — ranked by the *live* score, not the one that opened the opportunity.
- Each row shows **why now** (new evidence, a changed model, evidence ageing out), how far the score moved, and a badge only when the evidence is cooling or stale.
- A **contested** account ranks above a quiet one at the same score.
- Company names resolve in a **second request** and appear as they arrive; rows do not wait for them.
- A name your providers **disagree** about shows an ⓘ naming who reported the one displayed.
- An account nothing has named shows its **real identifier**, never a placeholder.

### Known limitations, and what is intentionally unfinished

- **Rows do not link anywhere.** The account brief is the next slice; a link to a page that does not exist is worse than none *(D3)*.
- **No sort or filter controls.** A client-side sort would reorder only the loaded page while presenting it as the top of the whole list *(D4)*.
- **One page, no infinite scroll.** The cursor works; the UI does not page yet.
- **`reasoning@1` has no released model**, so the Decision Package stage would refuse. It is not on this screen, so you will not see it — but the pipeline is not whole.

---

## Product Playground — recommended, not built

A stable demo dataset (Microsoft, Salesforce, Stripe, NVIDIA, Snowflake, Databricks, Atlassian, HubSpot) with believable signals and scores, behind one `make demo`, is **the right idea and the right time** — the current golden set has *two* structurally identical accounts, and `28-ai-platform.md` already records "variety 1" as the main caveat on every evaluation.

**One correction to the shape:** it should not be a parallel seeding system. The **Provider Simulation Framework** already owns this and was commissioned for exactly ten scenarios *"deepening each milestone"* — one exists. A demo dataset belongs there as scenarios, so it inherits the seeded determinism, the fault injector and the provenance fields rather than splitting them across two owners.

Scoped and recorded in [38-product-design-principles.md](architecture/38-product-design-principles.md) as **D9**; it is its own slice, not a side effect of this one.
