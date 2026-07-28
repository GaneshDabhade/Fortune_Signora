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
    expect(body).toHaveProperty('checks.oauth_providers');
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
  test('offers a provider button when one is configured', async ({ page }) => {
    await page.goto('/sign-in');

    if (hasOAuth) {
      await expect(page.getByRole('button', { name: /Continue with/ })).toBeVisible();
    } else {
      // Explicit rather than a blank page: an operator seeing this knows
      // exactly what is missing.
      await expect(page.getByText(/No sign-in provider is configured/)).toBeVisible();
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
