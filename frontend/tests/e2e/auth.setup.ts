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
import { SignInPage } from './pages/signin';

async function signIn(page: import('@playwright/test').Page, persona: Persona) {
  // **The destination is the assertion**, and it lives in the page object.
  // Signing in navigated to `/workspaces` — a route that has never existed —
  // for every person who ever used this product, and nothing failed, because
  // nothing had ever signed in (B-304).
  await new SignInPage(page).signIn(persona);
  await expect(page.getByRole('heading', { name: 'Attention', level: 1 })).toBeVisible();
  await page.context().storageState({ path: storageStatePath(persona.email) });
}

setup('sign in as the owner', async ({ page }) => {
  await signIn(page, OWNER);
});

setup('sign in as a member', async ({ page }) => {
  await signIn(page, MEMBER);
});
