/**
 * Signs each persona in, once, and keeps the browser state for the suite.
 *
 * **A real sign-in, not a shortcut.** The form is filled, the real Better Auth
 * route issues the session, and the destination is asserted — so the setup
 * project is itself the first proof that signing in works. If it stops
 * working, every downstream project reports *"authenticate failed"* rather
 * than forty confusing failures about missing data.
 *
 * The saved state is a session cookie a customer would hold. Nothing is
 * minted, forged or written directly.
 */

import { expect, test as setup } from '@playwright/test';

import { MEMBER, OWNER, storageStatePath, type Persona } from './fixtures/personas';
import { chooseOrganization, SignInPage } from './pages/signin';

async function signIn(page: import('@playwright/test').Page, persona: Persona) {
  // **The destination is the assertion**, and it lives in the page object.
  // Signing in navigated to `/workspaces` — a route that has never existed —
  // for every person who ever used this product, and nothing failed, because
  // nothing had ever signed in (B-304).
  await new SignInPage(page).signIn(persona);

  /**
   * ⚠️ **This asserted the Attention heading, and `/` no longer renders it.**
   * 📁 The Authenticated Entry document owns what happens after sign-in, and
   * this setup now walks its ladder as a customer does.
   *
   * 🔴 **The Playground personas belong to more than one organization and a
   * fresh browser has no last-used**, which is 📁 **rule 13 exactly**: *"several
   * memberships, no last-used → the chooser. **This is a first login with
   * multiple memberships and nothing else**."*
   *
   * ⚡ **That rule was unreachable until `/` started resolving** — the screen
   * that used to live there rendered regardless of how many organizations
   * somebody belonged to.
   *
   * ✅ **So the setup chooses one, which is what a person does**, and choosing
   * records the last-used — so every later entry in the suite takes 📁 rule 12
   * (*"enter the last used"*) rather than the chooser again.
   */
  // ⚠️ **Extracted to `chooseOrganization` — it was needed in a second place.**
  // 📁 A fresh sign-in anywhere in the suite meets the same chooser, and
  // `resilience`'s sign-out journey was failing on it.
  await chooseOrganization(page);

  // 📁 **Rule 24's destination**, however the ladder reached it.
  await page.waitForURL(/\/w\/[0-9a-f-]+\/home$/);
  await expect(page.getByTestId('home')).toBeVisible();
  await page.context().storageState({ path: storageStatePath(persona.email) });
}

setup('sign in as the owner', async ({ page }) => {
  await signIn(page, OWNER);
});

setup('sign in as a member', async ({ page }) => {
  await signIn(page, MEMBER);
});
