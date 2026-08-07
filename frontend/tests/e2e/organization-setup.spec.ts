/**
 * *Organization setup* — the administrative landing page, and the one screen
 * that has to be honest about what the product cannot do yet.
 *
 * **TASK-468**, against `docs/design-snapshot/screens/Workspace Setup.dc.html`.
 *
 * **What this journey exists to prove is the design's own rationale**:
 * *"Locked is shown, not hidden — removing them from the page makes
 * administrators think the product lost a feature."* A journey that only
 * created an organization would pass on a screen that silently dropped
 * region, URL, branding, domains and deletion — which is the failure the
 * rationale names.
 *
 * These write real data through the real API and are additive: an
 * organization is created and left, because the product offers no delete and
 * a test asserting one would be asserting a path that does not exist.
 */

import { expect, test } from './fixtures/signora';

const unique = () => `E2E Org ${Date.now()}`;

test.describe('a customer sets up an organization', () => {
  test('@regression /settings/organization opens on a direct load', async ({ page }) => {
    await page.goto('/settings/organization');
    await expect(page).toHaveURL(/\/settings\/organization$/, { timeout: 20_000 });
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });

  test('@regression Settings offers a way in', async ({ page }) => {
    // B-306's lesson: a screen reachable only by typing its URL is a screen
    // nobody finds. The reachability test asserts the link exists; this
    // asserts a person can actually follow it.
    await page.goto('/settings');
    await page.getByRole('link', { name: 'Organization setup' }).click();
    await expect(page).toHaveURL(/\/settings\/organization$/);
  });

  test('creates an organization and lands inside it', async ({ page }) => {
    const name = unique();
    await page.goto('/settings/organization');

    await page.getByLabel('Organization name').fill(name);
    await page.getByRole('button', { name: 'Create organization' }).click();

    // The organization the customer just made is the one they are now in —
    // the row's stated journey, and the half a creation form usually forgets.
    await expect(page.getByText(name).first()).toBeVisible({ timeout: 20_000 });
  });

  test('every capability is named, including the ones not built', async ({ page }) => {
    await page.goto('/settings/organization');

    for (const label of [
      'Organization URL',
      'Data region',
      'Logo',
      'Brand colour',
      'Delete this organization',
    ]) {
      await expect(page.getByText(label, { exact: true })).toBeVisible();
    }
  });

  test('offers no control for a capability the platform cannot answer', async ({
    page,
  }) => {
    await page.goto('/settings/organization');
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();

    // A region selector or a colour picker here would be mock business data
    // (§20c) — and worse than absent, because an administrator would use it
    // and believe the choice took effect.
    await expect(page.getByRole('combobox')).toHaveCount(0);
  });

  test('never shows the customer the platform word', async ({ page }) => {
    await page.goto('/settings/organization');
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();

    // ADR-0034, and C-239: the approved design says "workspace" throughout
    // and a customer may not be shown it.
    const body = await page.locator('main').innerText();
    expect(body.toLowerCase()).not.toContain('workspace');
  });
});
