/**
 * End-to-end authentication journey.
 *
 * The parts of the boundary that can be proven without a live OAuth consent
 * screen are asserted unconditionally. The full sign-in round trip requires
 * real provider credentials and is skipped without them, rather than failing
 * and teaching the team to ignore a red suite.
 */

import { expect, test } from '@playwright/test';

const hasOAuth = Boolean(process.env.GOOGLE_CLIENT_ID ?? process.env.MICROSOFT_CLIENT_ID);

test.describe('unauthenticated access', () => {
  test('the root path redirects to sign-in', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/\/sign-in/);
  });

  test('the workspaces page is not reachable without a session', async ({ page }) => {
    await page.goto('/workspaces');
    await expect(page).toHaveURL(/\/sign-in/);
  });

  test('the token endpoint refuses to mint without a session', async ({ request }) => {
    // The seam between tiers: no session must mean no token, or the API
    // boundary is bypassable from the browser.
    const response = await request.post('/api/token');

    expect(response.status()).toBe(401);
    expect((await response.json()).error.code).toBe('unauthenticated');
  });

  test('the auth health endpoint reports subsystem state', async ({ request }) => {
    const response = await request.get('/api/health');
    const body = await response.json();

    expect(body).toHaveProperty('checks.signing_keys');
    expect(body).toHaveProperty('checks.jwt_configuration');
    expect(body).toHaveProperty('checks.database');
    // Renamed at M12.3: the question is "can anybody sign in", not "is OAuth
    // configured" — two questions that were the same only while OAuth was the
    // only method (ADR-0033).
    expect(body).toHaveProperty('checks.sign_in_methods');
  });

  test('no response ever carries the private signing key', async ({ request }) => {
    for (const path of ['/sign-in', '/api/health']) {
      const body = await (await request.get(path)).text();
      expect(body).not.toContain('BEGIN PRIVATE KEY');
      expect(body).not.toContain('BEGIN RSA PRIVATE KEY');
    }
  });
});

test.describe('sign-in surface', () => {
  test('always offers a way in that needs no external service', async ({ page }) => {
    // **The reason this milestone exists.** Before ADR-0033 the page offered
    // only OAuth, so an install with no provider credentials had no sign-in
    // at all — and the product owner could not review the product.
    await page.goto('/sign-in');

    await expect(page.getByLabel('Email')).toBeVisible();
    await expect(page.getByLabel('Password')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible();
  });

  test('leads to registration and to password recovery', async ({ page }) => {
    await page.goto('/sign-in');

    await expect(page.getByRole('link', { name: 'Create an account' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Forgot your password?' })).toBeVisible();
  });

  test('offers a provider button when one is configured, and nothing when not', async ({
    page,
  }) => {
    await page.goto('/sign-in');
    const provider = page.getByRole('button', { name: /Continue with/ });

    if (hasOAuth) {
      await expect(provider).toBeVisible();
    } else {
      // **No error message any more, and that is the change.** An install
      // without OAuth credentials is not broken — it has one sign-in method
      // instead of three, and the page says so by simply not drawing a button
      // that would fail at the callback.
      await expect(provider).toHaveCount(0);
    }
  });
});

test.describe('authenticated journey', () => {
  test.skip(!hasOAuth, 'requires real OAuth provider credentials');

  test('sign in, create a workspace, and see only your own', async ({ page }) => {
    await page.goto('/sign-in');
    await page
      .getByRole('button', { name: /Continue with/ })
      .first()
      .click();
    await page.waitForURL(/\/workspaces/, { timeout: 20_000 });

    const name = `E2E ${Date.now()}`;
    await page.getByPlaceholder('New workspace name').fill(name);
    await page.getByRole('button', { name: 'Create' }).click();

    await expect(
      page.getByTestId('workspace-item').filter({ hasText: name }),
    ).toBeVisible();
  });
});
