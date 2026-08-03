import { defineConfig, devices } from '@playwright/test';

import { resolveAppUrl } from './tests/e2e/fixtures/environment';
import { OWNER, MEMBER, storageStatePath } from './tests/e2e/fixtures/personas';

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
 * **Headed is a first-class mode, not a debugging flag.** `PWDEBUG`-style
 * headed runs are what make the demonstration suite watchable, and the whole
 * point of a demonstration is that somebody sees it: `HEADED=1`.
 */

/**
 * **There is no default, deliberately.** It used to be `http://localhost:3000`
 * — the Human Review stack — and this suite *writes*. See
 * `tests/e2e/fixtures/environment.ts` for the whole reasoning.
 */
const APP_URL = resolveAppUrl();

/**
 * Firefox and WebKit, **absent unless asked for**.
 *
 * A listed project runs by default, so listing them would triple a six-minute
 * suite to answer a compatibility question nobody has asked — and would fail on
 * any machine without WebKit's forty system libraries. `E2E_BROWSERS=all` is
 * the one flag, and it covers the daily journey only: the point is *does the
 * product work in another engine*, not *does every assertion hold three times*.
 */
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
    // **A watchable run is a different product from a fast one.** The
    // demonstration suite exists to be seen, and `HEADED=1` is what lets a
    // person watch Signora being used rather than read that it was.
    headless: process.env.HEADED !== '1',
    ...(process.env.HEADED === '1' ? { launchOptions: { slowMo: 250 } } : {}),
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
      testMatch: /auth-journey\.spec\.ts/,
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'owner',
      testIgnore: [/auth-journey\.spec\.ts/, /.*\.member\.spec\.ts/, /demo\//],
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
