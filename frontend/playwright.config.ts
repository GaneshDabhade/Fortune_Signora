import { defineConfig, devices } from '@playwright/test';

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
 * which — Lane B's is 3400.
 */

const APP_URL = process.env.SIGNORA_APP_URL ?? 'http://localhost:3000';

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
      testIgnore: [/auth-journey\.spec\.ts/, /.*\.member\.spec\.ts/],
      dependencies: ['authenticate'],
      use: {
        ...devices['Desktop Chrome'],
        storageState: storageStatePath(OWNER.email),
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
