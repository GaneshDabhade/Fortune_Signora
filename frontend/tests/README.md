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
| `e2e/` | **QE** | Playwright. The authentication journey today |

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

`test:e2e` reads `SIGNORA_APP_URL` and defaults to `http://localhost:3000` — **set it to your lane's port** (QE: `3200`) or it drives whatever is on 3000. Tests needing a real OAuth round trip skip when no provider credentials are configured; that skip is deliberate and visible.

> **The backend's cross-tier JWT tests skip when `frontend/node_modules` is absent** — they shell out to `contract/mint-token.ts`. A backend run in a clone where `npm install` has never been executed reports six skips and still exits green, so a QE validation pass installs the frontend first.
