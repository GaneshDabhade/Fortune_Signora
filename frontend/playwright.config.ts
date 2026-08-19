import { defineConfig, devices } from '@playwright/test';

import { browserEnvironment, resolveAppUrl, resolveRunMode } from './tests/e2e/fixtures/environment';
import { OWNER, MEMBER, MUTATOR, storageStatePath } from './tests/e2e/fixtures/personas';

/**
 * End-to-end configuration.
 *
 * ## What this suite is for
 *
 * **Customer confidence, not code coverage.** Every spec answers *"can a real
 * customer complete this and trust the result?"* against the real application:
 * the real Better Auth tier, the real API, the real database, and the twelve
 * accounts the Playground put through the real pipeline. Nothing here mocks a
 * backend response, seeds a row, or mints a token by hand.
 *
 * It exists because the repository had 2000+ tests and none of them signed in.
 * The browser's only route to the API 404'd from M1.2 until an E2E test opened
 * a page and looked — every component proven, the composition between them
 * never exercised.
 *
 * ## Categories, so it can run at different cadences
 *
 * Tags in the title, selected with `--grep`:
 *
 *   `@smoke`      the shortest path that proves the product is alive
 *   `@journey`    a complete customer workflow, end to end
 *   `@regression` a defect that must not come back
 *   `@a11y`       keyboard, focus, labels, dialogs
 *
 * `npm run test:e2e:smoke` · `:journey` · `:a11y` · `npm run test:e2e`
 *
 * ## Authentication runs once, as a journey
 *
 * The `authenticate` project signs each persona in **through the form**, and
 * the rest of the suite reuses the resulting browser state. That is not a
 * bypass: it is one real sign-in instead of forty, and the sign-in itself is
 * asserted in `auth-journey.spec.ts` where it belongs.
 *
 * ## It drives a running application and says so
 *
 * No `webServer`: a lane already has its own dev server on its own port
 * (`docs/RUNNING.md` § Running a lane), and a config that started a second one
 * would bind a port that belongs to somebody else. `SIGNORA_APP_URL` selects
 * which — Lane B's is 3400 — and **there is no default**, because the previous
 * default was the product owner's review stack.
 *
 * ## Browsers
 *
 * **Chromium runs everywhere and is the suite's browser.** Firefox and WebKit
 * are opt-in projects rather than defaults: running three engines over every
 * journey triples a six-minute suite to buy a compatibility signal nobody has
 * asked a question about yet. `--project=firefox` when the question arises.
 *
 * **Headed is the DEFAULT, not a debugging flag** ([TASK-476](../docs/BACKLOG.md)).
 * `CLAUDE.md` §19 has said *"headed is the default mode for local development
 * and review"* since [D-134](../docs/DECISION_REGISTER.md), and this file said
 * the opposite until now. **The rule is what changed the code, not the other
 * way round.** `HEADLESS=1` for an unattended run; `HEADED=1` when you want the
 * demonstration's human pace. See `resolveRunMode()`.
 */

/**
 * **There is no default, deliberately.** It used to be `http://localhost:3000`
 * — the Human Review stack — and this suite *writes*. See
 * `tests/e2e/fixtures/environment.ts` for the whole reasoning.
 */
const APP_URL = resolveAppUrl();

/**
 * **Headed unless somebody said not to** — [TASK-476](../docs/BACKLOG.md).
 * The precedence, the reason `HEADED=1` beats `HEADLESS=1`, and why `slowMo`
 * rides on the explicit flag rather than the default all live beside the
 * function in `tests/e2e/fixtures/environment.ts`.
 */
const RUN_MODE = resolveRunMode();

/**
 * Firefox and WebKit, **absent unless asked for**.
 *
 * A listed project runs by default, so listing them would triple a six-minute
 * suite to answer a compatibility question nobody has asked — and would fail on
 * any machine without WebKit's forty system libraries. `E2E_BROWSERS=all` is
 * the one flag, and it covers the daily journey only: the point is *does the
 * product work in another engine*, not *does every assertion hold three times*.
 */
/**
 * **The specs that permanently mutate the persona they sign in as** — they
 * create an organization and the product offers no delete ([B-1017]).
 * **Declared once**: the `owner` project excludes them and the `mutating`
 * project selects them, and two copies of that list would eventually disagree
 * about which — leaving a spec in both projects or in neither.
 */
const MUTATING_JOURNEYS = /(organization-setup|onboarding-journey)\.spec\.ts/;

const OTHER_ENGINES =
  process.env.E2E_BROWSERS === 'all'
    ? (['firefox', 'webkit'] as const).map((engine) => ({
        name: engine,
        testMatch: /daily-usage\.spec\.ts/,
        dependencies: ['authenticate'],
        use: {
          ...devices[engine === 'firefox' ? 'Desktop Firefox' : 'Desktop Safari'],
          storageState: storageStatePath(OWNER.email),
        },
      }))
    : [];

export default defineConfig({
  testDir: './tests/e2e',
  // A journey crosses several screens and waits on a real pipeline read; 30s
  // was tuned for a suite that never signed in.
  timeout: 60_000,
  expect: { timeout: 15_000 },
  // **Deliberately serial.** The personas share one seeded organization, and a
  // workflow test that dismisses an account changes what a list test sees.
  // Parallelism here would buy seconds and cost determinism, and an
  // intermittently failing test is a defect in the test (CLAUDE.md §11).
  fullyParallel: false,
  workers: 1,
  // A `.only` left in a spec silently narrows the suite to one test while
  // still reporting green.
  forbidOnly: true,
  // **Zero.** A retry turns a race condition into an intermittent pass, which
  // is how a real defect becomes a flake nobody investigates.
  retries: 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  outputDir: 'test-results',

  use: {
    baseURL: APP_URL,
    // **A watchable run is a different product from a fast one** — and after
    // [TASK-476](../docs/BACKLOG.md) the watchable one is the default, because
    // `CLAUDE.md` §19 already said it was. `HEADLESS=1` opts out.
    headless: !RUN_MODE.headed,
    // **`env` is not decoration and its absence was a hidden input.** The suite
    // passed 119/119 in a terminal that happened to export `LD_LIBRARY_PATH`,
    // and could not launch a browser at all in one that did not — a variable
    // outside the declared contract deciding whether anything runs
    // (`CLAUDE.md` §2). `browserEnvironment()` supplies it when this machine
    // needs it and returns `undefined` when it does not.
    launchOptions: {
      env: browserEnvironment(),
      // ⛔ **`slowMo` follows the explicit `HEADED=1`, never the new default.**
      // 250ms on every action of every local run would turn a six-minute suite
      // into a gate nobody can afford — the reasoning is with `resolveRunMode`.
      ...(RUN_MODE.slowMo === undefined ? {} : { slowMo: RUN_MODE.slowMo }),
    },
    // Everything a failure needs, and nothing a pass pays for.
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
    screenshot: 'only-on-failure',
    // The product is built for a desktop seller's screen. Small-viewport
    // behaviour is asserted explicitly where it matters rather than globally,
    // because the sidebar is `hidden md:block` and every navigation assertion
    // would otherwise be about a breakpoint.
    viewport: { width: 1280, height: 900 },
  },

  projects: [
    {
      name: 'authenticate',
      testMatch: /.*\.setup\.ts/,
      use: { ...devices['Desktop Chrome'] },
    },
    {
      // Everything reachable without a session. Runs first and depends on
      // nothing, so a broken sign-in still reports a meaningful result.
      name: 'anonymous',
      // Workflow 1's own spec joins the anonymous project: signing in is by
      // definition something a signed-out person does, so it cannot run under
      // a project that arrives already authenticated (TASK-467, D-158).
      testMatch: /(auth-journey|workflow1-login)\.spec\.ts/,
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'owner',
      testIgnore: [
        /auth-journey\.spec\.ts/,
        /.*\.member\.spec\.ts/,
        /demo\//,
        // 📁 **[B-1017](../docs/BUGS.md)** — these two create organizations and
        // leave them, so they run as `MUTATOR` in the `mutating` project below.
        MUTATING_JOURNEYS,
      ],
      dependencies: ['authenticate'],
      use: {
        ...devices['Desktop Chrome'],
        storageState: storageStatePath(OWNER.email),
      },
    },
    {
      // **The Product Demonstration Suite** — a different product from the
      // regression suite, and separated because the goals genuinely conflict.
      //
      // A regression test wants to be fast, headless, and to assert the one
      // thing it is about. A demonstration wants to be **watched**: it moves at
      // a human pace, it narrates what it is doing, it records a video, and it
      // is a continuous story rather than a set of independent cases.
      //
      // **It does run in a normal suite, and that is deliberate.** A listed
      // project runs by default, and leaving it out would mean the
      // demonstration is only ever exercised on the day somebody puts it in
      // front of a customer — which is the one day it must not be broken.
      // 25 seconds on a seven-minute suite is cheap insurance.
      //
      // It is excluded from every *other* project, so it is demonstrated once
      // rather than counted as coverage of anything.
      name: 'demo',
      testMatch: /demo\/.*\.spec\.ts/,
      dependencies: ['authenticate'],
      // A demonstration that stops halfway is not a demonstration.
      timeout: 180_000,
      use: {
        ...devices['Desktop Chrome'],
        storageState: storageStatePath(OWNER.email),
        // **Always, not on failure.** The artifact is the point: this is meant
        // to be replayable by anybody on the team, and by somebody who was not
        // in the room.
        video: 'on',
        trace: 'on',
      },
    },
    ...OTHER_ENGINES,
    // **The responsive matrix — one project per breakpoint the design defines.**
    //
    // ⛔ **Before this existed the suite ran at a single 1280×900 viewport**,
    // and four of twenty-five specs set their own. **Three asserted measured
    // geometry.** So "responsive" was verified by reading class strings, which
    // is [B-175](../docs/BUGS.md)'s defect one level down: an assertion that
    // cannot fail when the thing it names actually breaks.
    //
    // ⚡ **The widths are the product's own**, from `tailwind.config.ts`, which
    // replaces Tailwind's defaults outright — `phone` · `smalllaptop` ·
    // `laptop` · `desktop`. They are not invented here and not copied from a
    // device list, because a breakpoint the design does not define is a width
    // nobody promised anything about.
    //
    // ⚠️ **`laptop` and `desktop` currently have zero `laptop:`/`desktop:`
    // consumers in `components/` or `app/`** — they run anyway, because the
    // invariants are about layout holding, not about a prefix being used.
    ...(
      [
        // ⛔ **Below the smallest named breakpoint, and this row is the one the
        // matrix was missing.** `phone: 640px` is a MIN-width, so a real
        // handset gets the UNPREFIXED styles and no project exercised them.
        //
        // ⚡ **[B-241](../docs/BUGS.md) needed exactly this viewport**: the rail
        // overflowed at `844` and fits at `900`, so a matrix whose shortest
        // screen was 900 tall could not reproduce it however many widths it ran.
        // **390×844 is the device Lane A found it on.**
        { name: 'handset', width: 390, height: 844 },
        { name: 'phone', width: 640, height: 900 },
        { name: 'smalllaptop', width: 1024, height: 800 },
        { name: 'laptop', width: 1280, height: 900 },
        { name: 'desktop', width: 1600, height: 1000 },
      ] as const
    ).map((breakpoint) => ({
      name: `layout-${breakpoint.name}`,
      testMatch: /layout-invariants\.spec\.ts/,
      dependencies: ['authenticate'],
      use: {
        ...devices['Desktop Chrome'],
        storageState: storageStatePath(OWNER.email),
        viewport: { width: breakpoint.width, height: breakpoint.height },
      },
    })),
    {
      /**
       * **The two journeys that permanently create organizations.**
       *
       * 🔴 **[B-1017](../docs/BUGS.md).** `organization-setup` and
       * `onboarding-journey` create an organization and leave it — correctly:
       * *"the product offers no delete and a test asserting one would be
       * asserting a path that does not exist."* Run on `OWNER`'s state, that
       * growth reached every later spec, `/` resolved to the organization
       * chooser, and **36 of 392 browser tests failed about nothing.**
       *
       * ✅ **A separate PERSONA rather than a separate ordering.** Ordering
       * needs `dependencies` on every project sharing `OWNER`'s state, and
       * Playwright skips a dependent when its dependency fails — so the
       * coverage would vanish exactly when the suite is red. **A silent cap is
       * worse than the contamination it replaces.**
       *
       * ⚡ **It is a second OWNER because Signora refuses `/settings` to a
       * member** — the client guard redirects and the server refuses the write
       * — so a member could not reach the screen under test at all.
       */
      name: 'mutating',
      testMatch: MUTATING_JOURNEYS,
      dependencies: ['authenticate'],
      use: {
        ...devices['Desktop Chrome'],
        storageState: storageStatePath(MUTATOR.email),
      },
    },
    {
      // The same product seen by somebody who administers nothing. A separate
      // project rather than a fixture, because the difference is the browser
      // state itself.
      name: 'member',
      testMatch: /.*\.member\.spec\.ts/,
      dependencies: ['authenticate'],
      use: {
        ...devices['Desktop Chrome'],
        storageState: storageStatePath(MEMBER.email),
      },
    },
  ],
});
