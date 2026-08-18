/**
 * The suite's own `test`, and the reasons it is not Playwright's.
 *
 * Three things every journey wants and none should repeat:
 *
 * 1. **The browser's console is evidence.** A screen that renders correctly
 *    while throwing in the console is a screen one refactor away from
 *    breaking, and a 404 on a data request is invisible in the DOM — which is
 *    exactly how `/api/proxy` survived from M1.2 to now. Collected on every
 *    test, asserted only where a test asks, so a noisy third-party warning
 *    cannot turn the whole suite red.
 *
 * 2. **Signing in is a journey, not a helper.** `signIn` drives the real form
 *    against the real authentication tier. Nothing here mints a token, writes
 *    a cookie, or reaches into Better Auth's tables.
 *
 * 3. **Page objects, only where they earn it.** One per screen, exposing what
 *    a customer can *do* rather than wrapping every locator. A page object
 *    that mirrors the DOM is a second copy of the markup that has to be
 *    maintained alongside it; these expose intent and let the specs use
 *    `getByRole` directly for anything one-off.
 */

import { test as base, expect, type Page } from '@playwright/test';

import { type Persona } from './personas';
import { AccountsPage } from '../pages/accounts';
import { BriefPage } from '../pages/brief';
import { BusinessPage } from '../pages/business';
import { SettingsPage } from '../pages/settings';
import { SignInPage } from '../pages/signin';

export interface ConsoleEvidence {
  /** `console.error` lines, and failed resource loads the browser reports. */
  readonly errors: readonly string[];
  /** Uncaught exceptions. Always a defect; never a third-party warning. */
  readonly exceptions: readonly string[];
  /** Every non-2xx/3xx response the page received, as `status method path`. */
  readonly failedRequests: readonly string[];
}

export interface SignoraFixtures {
  console: ConsoleEvidence;
  signIn: (persona: Persona) => Promise<void>;
  accounts: AccountsPage;
  brief: BriefPage;
  settings: SettingsPage;
  business: BusinessPage;
}

function watch(page: Page): ConsoleEvidence {
  const errors: string[] = [];
  const exceptions: string[] = [];
  const failedRequests: string[] = [];

  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text());
  });
  page.on('pageerror', (error) => exceptions.push(String(error)));
  page.on('response', (response) => {
    if (response.status() < 400) return;
    const url = new URL(response.url());
    // Only our own origin. A blocked analytics beacon from somewhere else is
    // not this product's defect.
    if (url.origin !== new URL(page.url() || url.origin).origin) return;
    failedRequests.push(
      `${response.status()} ${response.request().method()} ${url.pathname}`,
    );
  });

  return { errors, exceptions, failedRequests };
}

export const test = base.extend<SignoraFixtures>({
  console: async ({ page }, use, testInfo) => {
    const evidence = watch(page);
    await use(evidence);
    // Attached rather than asserted: a failure elsewhere is far easier to
    // diagnose with the console beside the trace, and attaching costs nothing
    // when the test passed.
    if (evidence.errors.length || evidence.exceptions.length) {
      await testInfo.attach('browser-console', {
        body: JSON.stringify(evidence, null, 2),
        contentType: 'application/json',
      });
    }
  },

  // The flow itself lives in `pages/signin.ts`, because the endurance
  // recorder signs in too and a second copy of it is a second thing to forget
  // the next time the redirect changes (B-304).
  signIn: async ({ page }, use) => {
    const signInPage = new SignInPage(page);
    await use((persona: Persona) => signInPage.signIn(persona));
  },

  accounts: async ({ page }, use) => use(new AccountsPage(page)),
  brief: async ({ page }, use) => use(new BriefPage(page)),
  settings: async ({ page }, use) => use(new SettingsPage(page)),
  business: async ({ page }, use) => use(new BusinessPage(page)),
});

export { expect };
