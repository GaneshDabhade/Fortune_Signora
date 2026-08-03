# `frontend/tests/` — what lives here, and who owns it

> **QE's**, except the component tests belonging to a module currently assigned to another lane. This file says which are which. The rules themselves are `CLAUDE.md` §11 and §20c, and [ADR-0023](../../docs/architecture/adr/0023-testing-strategy.md).

## Ownership follows the component, not the directory

`tests/components/` holds two different things under one name: business-component tests, and tests that police the foundation. **A component test belongs to whichever lane is currently assigned the module whose component it imports.**

| File | Belongs to | Covers |
|---|---|---|
| `attention` · `contributions` · `entity-name` · `evidence` · `narration` · `opportunity` · `sequence` · `validation` · `workflow` · `first-run` | the **product surface**'s assignee | `components/intelligence/`, `app/(app)/` |
| `products` | **`commercial_profile`**'s assignee | `components/commercial/` |
| `foundation` · `ui` · `no-workspace` | **QE** | the design system, the shell, `components/feedback/`, `components/workspace/` — frozen (§20c) |
| `design-tokens` · `no-mock-data` · `vocabulary` | **QE** | **governance tests.** They assert no literal colour, no mock business data, and no internal vocabulary on a screen |
| `unit/` | **QE** | the auth library — JWT minting, key generation, sign-in methods, auth events |
| `contract/mint-token.ts` | **QE** | mints a real token for the backend's cross-tier JWT test |
| `e2e/` | **QE**, except while the product owner has assigned End-to-End Product Validation to a lane — **Lane B holds it from 2026-08-03** ([C-308](../../docs/LANE_COORDINATION.md)) | Playwright, against the **real** application: real Better Auth, real API, real database, the seeded Playground. Seven specs, four cadences |

**The three governance tests are the enforcement behind three frozen decisions**, and are the reason those decisions are not merely documentation. `vocabulary.test.tsx` found a leak on its first run that a manual audit had missed ([ADR-0034](../../docs/architecture/adr/0034-ubiquitous-language.md)). Do not weaken one to make a component pass; the component is what is wrong.

## Where a new test goes

- **A component's own behaviour** → `components/`, belonging to that component's module.
- **A rule that must hold across every component, present and future** → a governance test, owned by QE. Ask whether it can fail: a scan that cannot fail is documentation pretending to be code.
- **A journey a customer performs across pages** → `e2e/`. This is where QE's exploratory findings become permanent, and it is the thinnest part of the suite today.
- **Never** a mock of business data. Screens without a shipped module behind them ship a designed empty state (§20c), and `no-mock-data.test.tsx` enforces it.

## Running it

```bash
cd frontend
npm install
npm run test          # vitest — unit and component
npm run typecheck     # tsc --noEmit
npm run lint
npm run test:e2e      # playwright; needs the app running
npm run build         # the production build is part of a lane's own gate
```

### Running the E2E suite

It drives a **running application with a seeded organization**, and it starts nothing itself — a lane already has its own dev server on its own port, and a config that started a second would bind a port belonging to somebody else.

```bash
# your lane's row of docs/RUNNING.md — database migrated, then:
cd frontend && SIGNORA_AUTH_DATABASE_URL=<your lane's auth URL> npm run demo:users
cd backend  && python -m tests.playground.seed        # with your lane's test URLs exported
npx playwright install chromium                       # once

SIGNORA_APP_URL=http://localhost:3400 npm run test:e2e            # everything
SIGNORA_APP_URL=http://localhost:3400 npm run test:e2e:smoke      # ~40s, the shortest proof the product is alive
                                       npm run test:e2e:journey   # complete customer workflows
                                       npm run test:e2e:regression # defects that must not come back
                                       npm run test:e2e:a11y      # keyboard, focus, labels, dialogs
```

**Pass `SIGNORA_AUTH_DATABASE_URL` explicitly to `demo:users`.** The scripts under `scripts/` do not read `.env.local`, and `loadAuthConfig()` supplies a working default — so an unset variable seeds a *different* database rather than failing (recorded as O-3 in [`49-end-to-end-product-validation.md`](../../docs/architecture/49-end-to-end-product-validation.md)).

**`SIGNORA_APP_URL` defaults to `http://localhost:3000`**, which belongs to human review and to no lane. Set it or the suite drives somebody else's stack.

Tests needing a real OAuth round trip skip when no provider credentials are configured; that skip is deliberate and visible. **Everything else runs everywhere**, because password sign-in needs no external service (ADR-0033) — which is the change that made an authenticated suite possible at all.

> **The backend's cross-tier JWT tests skip when `frontend/node_modules` is absent** — they shell out to `contract/mint-token.ts`. A backend run in a clone where `npm install` has never been executed reports six skips and still exits green, so a QE validation pass installs the frontend first.
