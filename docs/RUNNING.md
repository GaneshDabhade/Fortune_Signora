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

## Sample data — the Product Playground

`make demo` seeds **twelve accounts through the real pipeline**: provider simulation → ingestion → normalization → knowledge graph → observations → business events → signals → buying scores → opportunities.

**There is one product.** The seeder runs the same function the pipeline suite runs, over the `playground@1` scenario instead of `baseline@1`. No branch anywhere knows it is a playground; the only difference is which scenario file is named.

Twelve accounts, twelve *shapes* — a technology migration, a hiring surge, a provider disagreement, an acquisition, a rapid grower, a stale account, a false positive, a silent account, a rebranding, a contested account, a slow burn, and one that is cooling. Every company is fictional and every domain is on the RFC 2606 `.example` reserved TLD, so nothing here can be mistaken for a claim about a real business.

**Sign in once before seeding.** Better Auth owns users and hashes its own passwords, so the seeder cannot create one without either committing a credential or reaching into another system's schema. Sign in at <http://localhost:3000/sign-in>, then re-run `make demo-seed`; it enrols every signed-in user in the seeded workspace and prints what it did.

**Expect four qualified opportunities, not twelve.** The other eight do not meet the qualification threshold — the silent account has one attribute and nothing else, the false positive has loud intent with no corroboration, the stale one's evidence expired. **That is the product working.** A playground producing twelve qualified opportunities would be validating a list nobody will ever see.

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
- A name your providers **disagree** about shows an ⓘ naming who reported the one displayed. In the Playground this is **Fabrikam Industrial**.
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
- **Every Playground account reads "evidence expired", and two of the four are unnamed.** The simulated payloads describe events months in the past, so scoring asks its question *as of* a historical moment and the reading is expired by the time you look at it. The screens are correct; the scenario's dating is not, and the twelve temporal shapes it names are therefore not being demonstrated *(D17, D18)*.
- **`reasoning@1` has no released model**, so the Decision Package stage would refuse at runtime. It is not on either screen, so you will not see it — but the pipeline is not whole.
