/**
 * The sign-in screen, as the one place that knows how signing in works.
 *
 * **Extracted because there are now two callers, not because a page object was
 * owed one.** The journey fixture drives it and so does the endurance recorder,
 * and the flow has already changed once under everybody's feet: until
 * [B-304](../../../../docs/BUGS.md) every sign-in landed on a 404 because the
 * client redirected somewhere that had never existed. A second hand-written
 * copy of these five lines is a second thing to forget when that happens again.
 *
 * It takes a bare `Page`, so it works under the test runner and under the
 * Playwright *library* equally — which is the property that let the endurance
 * harness reuse the page objects instead of growing its own.
 */

import { expect, type Locator, type Page } from '@playwright/test';

import { PASSWORD, type Persona } from '../fixtures/personas';

/**
 * Get past *"Choose an organization"* the way a person does.
 *
 * 📁 **Rule 12 — *"enter the last used"*** — so a browser that has chosen once
 * is never asked again, and a fresh one always is. ⚡ **Whether it is asked at
 * all is a property of the DATABASE, not of the test**: dana belongs to the
 * Playground *and* to whatever `organization-setup.spec.ts` last created, so
 * the chooser appears on any workstation where that spec has run.
 *
 * ⛔ **The Playground by name, never the first row.** *"E2E Org …"* sorts ahead
 * of it, and choosing blindly captures the session into an empty organization
 * where every later assertion looks for data that is in the other one.
 *
 * ⚠️ **Extracted from `auth.setup.ts`, which had this and was the only caller
 * that did.** 🔴 A fresh sign-in anywhere else — `resilience`'s sign-out
 * journey is one — landed on the chooser and reported *"Home did not render"*,
 * which is true and is not what the journey is about.
 */
export async function chooseOrganization(page: Page): Promise<void> {
  await page.waitForURL(/\/workspaces$|\/w\/[0-9a-f-]+\/home$/, { timeout: 20_000 });
  if (new URL(page.url()).pathname !== '/workspaces') return;

  await expect(page.getByRole('heading', { name: 'Choose an organization' })).toBeVisible();
  const list = page.getByRole('list', { name: 'Your organizations' });
  const playground = list.getByRole('button', { name: /Playground/ });
  await ((await playground.count()) > 0 ? playground.first() : list.getByRole('button').first())
    .click();
  await page.waitForURL(/\/w\/[0-9a-f-]+\/home$/, { timeout: 20_000 });
}

export class SignInPage {
  constructor(private readonly page: Page) {}

  async open(): Promise<void> {
    await this.page.goto('/signin');
  }

  get email(): Locator {
    return this.page.getByLabel('Email');
  }

  get password(): Locator {
    return this.page.getByLabel('Password');
  }

  get submit(): Locator {
    return this.page.getByRole('button', { name: 'Sign in' });
  }

  /**
   * Sign in the way a customer does, and **wait on the destination**.
   *
   * The destination is the assertion: a sign-in that succeeds and lands
   * somewhere that does not exist is the exact shape of B-304, and a wait on a
   * timeout rather than on a URL would have reported it as green.
   */
  async signIn(persona: Persona): Promise<void> {
    await this.open();
    await this.email.fill(persona.email);
    await this.password.fill(PASSWORD);
    await this.submit.click();
    await this.page.waitForURL((url) => url.pathname === '/', { timeout: 20_000 });
  }
}
