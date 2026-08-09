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

import { type Locator, type Page } from '@playwright/test';

import { PASSWORD, type Persona } from '../fixtures/personas';

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
