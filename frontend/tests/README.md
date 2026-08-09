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
| `e2e/` | **QE**, except while the product owner has assigned End-to-End Product Validation to a lane — **Lane B holds it from 2026-08-03** ([C-308](../../docs/LANE_COORDINATION.md)) | Playwright, against the **real** application: real Better Auth, real API, real database, the seeded Playground. Fifteen specs, four cadences |
| `review/` | the same as `e2e/` | **The review instrument, and not a test.** `make review-product` walks the product headed at human pace and reads every screen back as text. **It asserts nothing and can never fail** — findings go to [`PRODUCT_EXPERIENCE.md`](../../docs/PRODUCT_EXPERIENCE.md) by human judgement |
| `endurance/` | the same as `e2e/` | **A working day in one tab.** Not a test — a long-running recorder plus pure trend arithmetic. `make endurance`. Its unit tests live in `unit/endurance/`, because the arithmetic deserves a test that needs no browser |

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

**From the repository root, and this is the way to run it:**

```bash
make e2e                    # re-seeds, then the whole suite
make e2e-quick              # no re-seed, for iterating on one spec
make e2e-smoke              # ~40s, the shortest proof the product is alive
make product-demo           # watch Signora being used, headed, at human pace
make product-demo-record    # the same, keeping the video and trace
make e2e ARGS="--grep @a11y"

make endurance                       # 20 minutes in one tab
make endurance MINUTES=480           # a working day
```

### Headed is the default, and that is the rule rather than a preference

**Every one of the commands above opens a browser you can watch** ([TASK-476](../../docs/BACKLOG.md)). `CLAUDE.md` §19 has said *"headed is the default mode for local development and review"* since [D-134](../../docs/DECISION_REGISTER.md), and the config said the opposite until this row — **headless, with `HEADED=1` opting in.** The sentence is what changed the code.

**The purpose is not debugging.** [D-134](../../docs/DECISION_REGISTER.md) makes a headed run a **handover gate**, and *"the purpose is not verification — the assertions already did that. It is continuous product review."* Transitions, empty states, error states and loading states are what a lane is meant to see, and **a gate you have to remember to opt into is not a gate.**

| | |
|---|---|
| *nothing set* | **Headed, at full speed** — the default |
| `HEADED=1` | Headed **and slowed to a human pace.** `make product-demo` sets it |
| `HEADLESS=1` · `HEADED=0` | **No window.** For a run nobody is watching |

⛔ **`HEADED=1` wins if both are set.** `HEADLESS` describes an environment and is the kind of thing a shell exports and forgets; `HEADED=1` is an intent, on the command that carries it — and a demonstration that silently ran headless would lose the only thing it exists for. The precedence is pinned in `tests/unit/run-mode.test.ts`.

⚠️ **`make product-demo-record` was headless and is now headed**, because it does not set either flag. **It still records** — video and trace are the demo project's, not the mode's — **but it needs `HEADLESS=1` to run unattended**, and the `Makefile` is `platform_foundation`'s. **Requested from Lane C as [C-260](../../docs/LANE_COORDINATION.md); one line, and this row may not write it.**

⛔ **Nothing keys off `CI`, `DISPLAY` or `SIGNORA_ENVIRONMENT`.** Certification runs on the same machine as development (§20c-2 — *the correct quantity of CI is zero*), so an environment variable cannot separate them, and **a `DISPLAY` probe would be exactly the hidden input `browserEnvironment()` exists to remove.**

**`make endurance` is deliberately not part of `make e2e`.** It answers the one question a seven-minute suite cannot — what a tab looks like after an afternoon — and a check nobody can afford to run is a check that gets skipped. It **observes and never asserts**; the judgement is `tests/endurance/trend.ts`, which is pure arithmetic with twenty unit tests behind it and no browser. Samples are appended as they are taken, so a session killed at hour six still has hours one to five.

**All of them run inside `infra/environment-lease.py`, unchanged.** Two browser runs against one database truncate each other mid-suite — the same failure that made cycle 25 record *"134 passed"* against a suite of 2589 ([`RELEASE_ENGINEERING.md`](../../docs/RELEASE_ENGINEERING.md) §7). The lease already prevents it.

**`make e2e` re-seeds first, deliberately.** The workflow journeys record real decisions, which changes what the next run reads. `make e2e-quick` skips it.

Set `E2E_URL` and `E2E_DB` if your lane's row is not Lane B's.

<details><summary>First-time setup, once per clone</summary>

```bash
cd frontend && SIGNORA_AUTH_DATABASE_URL=<your lane's auth URL> npm run demo:users
npx playwright install chromium
npx playwright install firefox        # optional: E2E_BROWSERS=all
sudo npx playwright install-deps webkit   # WebKit needs 40 system libraries
```
</details>

**`SIGNORA_APP_URL` has no default and never will.** It used to be `http://localhost:3000` — Human Review's stack — and **this suite writes**: products, watched companies, and permanent attributed decisions. It now refuses to start without an explicit URL, and refuses ports 3000/8000 outright. See `tests/e2e/fixtures/environment.ts`.

**Pass `SIGNORA_AUTH_DATABASE_URL` explicitly to `demo:users`.** The scripts under `scripts/` do not read `.env.local`, and `loadAuthConfig()` supplies a working default — so an unset variable seeds a *different* database rather than failing (recorded as O-3 in [`480-end-to-end-product-validation.md`](../../docs/architecture/480-end-to-end-product-validation.md)).

**`SIGNORA_APP_URL` defaults to `http://localhost:3000`**, which belongs to human review and to no lane. Set it or the suite drives somebody else's stack.

Tests needing a real OAuth round trip skip when no provider credentials are configured; that skip is deliberate and visible. **Everything else runs everywhere**, because password sign-in needs no external service (ADR-0033) — which is the change that made an authenticated suite possible at all.

> **The backend's cross-tier JWT tests skip when `frontend/node_modules` is absent** — they shell out to `contract/mint-token.ts`. A backend run in a clone where `npm install` has never been executed reports six skips and still exits green, so a QE validation pass installs the frontend first.
