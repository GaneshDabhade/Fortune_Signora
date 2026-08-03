/**
 * End-to-end authentication journey.
 *
 * The parts of the boundary that can be proven without a live OAuth consent
 * screen are asserted unconditionally. The full sign-in round trip requires
 * real provider credentials and is skipped without them, rather than failing
 * and teaching the team to ignore a red suite.
 */

import { expect, test } from '@playwright/test';

import { OWNER, PASSWORD } from './fixtures/personas';

const hasOAuth = Boolean(process.env.GOOGLE_CLIENT_ID ?? process.env.MICROSOFT_CLIENT_ID);

test.describe('unauthenticated access', () => {
  test('the root path redirects to sign-in', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/\/sign-in/);
  });

  /**
   * **This asserted `/workspaces`, a route that has never existed.** A 404 is
   * not a redirect, so the test was wrong — and it passed for three slices
   * because Playwright's browsers were never installed and the suite never
   * ran. Both halves of that are the finding.
   *
   * The property it meant to assert is that **every** authenticated route is
   * closed without a session, so it now asserts exactly that, over the real
   * ones.
   */
  for (const path of ['/', '/settings', '/settings/products', '/settings/connections']) {
    test(`${path} is not reachable without a session`, async ({ page }) => {
      await page.goto(path);
      await expect(page).toHaveURL(/\/sign-in/);
    });
  }

  test('@regression an account brief is closed without a session', async ({ page }) => {
    // Guarded by the same server-side layout check, and worth its own case:
    // it is the one authenticated route a customer would paste to a colleague.
    await page.goto('/accounts/00000000-0000-4000-8000-000000000000');
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

/**
 * **This describe block used to be the only authenticated test in the
 * repository, and it had never run.**
 *
 * It was skipped without OAuth credentials — which no local install has — and
 * ADR-0033 added password sign-in without anybody noticing that the skip now
 * hid a journey every install *could* exercise. Underneath the skip it waited
 * for `/workspaces` and clicked a `workspace-item` test id, neither of which
 * has ever existed, so it would have failed on its first line if it had ever
 * been reached.
 *
 * It is replaced by a sign-in that needs no external service, because there is
 * now one that needs none. What OAuth genuinely adds — the provider round trip
 * — stays skipped without credentials, and only that.
 */
test.describe('signing in', () => {
  test('@smoke a person with an address and a password reaches their morning', async ({
    page,
  }) => {
    await page.goto('/sign-in');
    await page.getByLabel('Email').fill(OWNER.email);
    await page.getByLabel('Password').fill(PASSWORD);
    await page.getByRole('button', { name: 'Sign in' }).click();

    // **The regression.** Every sign-in landed on `/workspaces`, which returns
    // *"That address does not lead anywhere"*. The password form's own
    // `router.push('/')` never fixed it: the vendor navigates to its
    // `callbackURL` and wins.
    await page.waitForURL((url) => url.pathname === '/', { timeout: 30_000 });
    await expect(page.getByRole('heading', { name: 'Attention', level: 1 })).toBeVisible();
  });

  test('@regression the wrong password is refused without saying which half was wrong', async ({
    page,
  }) => {
    await page.goto('/sign-in');
    await page.getByLabel('Email').fill(OWNER.email);
    await page.getByLabel('Password').fill('not-the-password');
    await page.getByRole('button', { name: 'Sign in' }).click();

    const message = page.getByText(/That email and password do not match an account./);
    await expect(message).toBeVisible();
    // An address-enumeration oracle is the failure this wording exists to
    // prevent: the same sentence must answer *no such account* too.
    await expect(page).toHaveURL(/\/sign-in/);
  });

  test('@regression an address nobody has registered gets the same answer', async ({
    page,
  }) => {
    await page.goto('/sign-in');
    await page.getByLabel('Email').fill('nobody.at.all@northwind.example');
    await page.getByLabel('Password').fill(PASSWORD);
    await page.getByRole('button', { name: 'Sign in' }).click();

    await expect(
      page.getByText(/That email and password do not match an account./),
    ).toBeVisible();
  });

  test('signing out ends the session and the product is closed again', async ({ page }) => {
    await page.goto('/sign-in');
    await page.getByLabel('Email').fill(OWNER.email);
    await page.getByLabel('Password').fill(PASSWORD);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await page.waitForURL((url) => url.pathname === '/');

    await page.getByRole('button', { name: 'Sign out' }).click();
    await page.waitForURL(/\/sign-in/, { timeout: 20_000 });

    // Not merely redirected — the session is gone, so the seam between the
    // tiers refuses to mint a token for it.
    const token = await page.request.post('/api/token');
    expect(token.status()).toBe(401);
  });
});

test.describe('the OAuth round trip', () => {
  test.skip(!hasOAuth, 'requires real OAuth provider credentials');

  test('@journey a provider sign-in reaches the same morning', async ({ page }) => {
    await page.goto('/sign-in');
    await page
      .getByRole('button', { name: /Continue with/ })
      .first()
      .click();
    // The same destination as a password sign-in, deliberately: the session is
    // identical and the token carries no record of the method (ADR-0033).
    await page.waitForURL((url) => url.pathname === '/', { timeout: 30_000 });
    await expect(page.getByRole('heading', { name: 'Attention', level: 1 })).toBeVisible();
  });
});
