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
    // ⚠️ **Repaired, not rewritten.** Workflow 1 renamed this link to the
    // design's wording and left this assertion naming the old one, which no
    // substring match rescues — `Forgot your password?` is not inside
    // `Forgot password?`. **Found by extending this file rather than by a
    // gate**, which is the same class as the dead `/sso` link Workflow 1
    // shipped: a suite that never runs cannot report its own staleness.
    await expect(page.getByRole('link', { name: 'Forgot password?' })).toBeVisible();
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

/**
 * **Workflow 2 · Registration** — [TASK-485](../../../docs/BACKLOG.md), screen
 * `06 · Create account`.
 *
 * ⚡ **Extends this file rather than replacing it**, which the row states in
 * terms. The sign-in journeys above are untouched.
 */
test.describe('Workflow 2 · creating an account', () => {
  test('the screen the design draws is the screen that renders', async ({ page }) => {
    await page.goto('/sign-up');

    await expect(page.getByRole('heading', { name: 'Create your account' })).toBeVisible();
    // *"Step 1 of 2 · takes about a minute"* — the design's own subtitle, and
    // the reason the button says **Continue** rather than *Create account*.
    await expect(page.getByText('Step 1 of 2 · takes about a minute')).toBeVisible();
    await expect(page.getByLabel('Full name')).toBeVisible();
    await expect(page.getByLabel('Work email')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Continue' })).toBeVisible();
  });

  test('the strength meter answers the password as it is typed', async ({ page }) => {
    await page.goto('/sign-up');
    const meter = page.getByRole('meter', { name: 'Password strength' });

    await expect(meter).toHaveAttribute('aria-valuenow', '0');
    await page.getByLabel('Password', { exact: true }).fill('Correct-Horse-9');
    await expect(meter).toHaveAttribute('aria-valuenow', '3');
  });

  test('⛔ the strength list reports and never gates', async ({ page }) => {
    // **`lib/auth/password.ts`: *length is the only requirement*.** A long
    // all-lowercase password satisfies one rule of three and must still be
    // accepted, because refusing it would be this screen inventing a security
    // rule the platform deliberately does not have.
    await page.goto('/sign-up');

    await page.getByLabel('Password', { exact: true }).fill('anappleadayxx');
    await expect(page.getByRole('meter', { name: 'Password strength' })).toHaveAttribute(
      'aria-valuenow',
      '1',
    );
    await expect(page.getByRole('button', { name: 'Continue' })).toBeEnabled();
  });

  test('⛔ no rule is drawn that nothing checks', async ({ page }) => {
    // The design's fourth rule needs Better Auth's `haveIBeenPwned` plugin,
    // which is a server hook and outside this row's budget. Raised, not drawn.
    await page.goto('/sign-up');
    await expect(page.getByText(/breach/i)).toHaveCount(0);
  });

  test('the agreement is stated, and it leads nowhere it cannot', async ({ page }) => {
    // **The line is required and the destinations do not exist** — the
    // design's own markup points both words at `#legal`, and no legal route
    // or configured URL exists in this repository. **Two dead links is what
    // Workflow 1 had to repair**, so the sentence renders and the words are
    // not links.
    await page.goto('/sign-up');

    await expect(
      page.getByText('By continuing you agree to the Terms and Privacy Notice.'),
    ).toBeVisible();
    await expect(page.getByRole('link', { name: 'Terms' })).toHaveCount(0);
    await expect(page.getByRole('link', { name: 'Privacy Notice' })).toHaveCount(0);
  });

  test('the product mark is the way back, since the design gives no other', async ({ page }) => {
    await page.goto('/sign-up');
    await page.getByRole('link', { name: 'Fortune Signora' }).click();
    await expect(page).toHaveURL(/\/welcome$/);
  });

  test('@journey a person creates an account and reaches verification', async ({ page }) => {
    // **The journey the row names.** A fresh address each run, because the
    // account it creates is real — Better Auth is untouched and there is no
    // development-only registration path (D-156, D-158).
    const address = `marta.${Date.now()}@northwind.example`;

    await page.goto('/sign-up');
    await page.getByLabel('Full name').fill('Marta Reinhardt');
    await page.getByLabel('Work email').fill(address);
    await page.getByLabel('Password', { exact: true }).fill('Correct-Horse-9');
    await page.getByRole('button', { name: 'Continue' }).click();

    await page.waitForURL(/\/verify-email/, { timeout: 30_000 });
    // The address travels, so screen 07 can say which mailbox to open.
    await expect(page).toHaveURL(new RegExp(encodeURIComponent(address).replace(/\./g, '\\.')));
  });
});

/**
 * **Workflow 3 · Email Verification** — [TASK-486](../../../docs/BACKLOG.md),
 * screen `07 Verify email`.
 *
 * ⛔ **The design's six digit boxes are not here and one test says so.**
 * `lib/auth/server.ts` sends a link, `better-auth/plugins/email-otp` is
 * installed and unregistered, and no endpoint would accept a typed code —
 * [C-241](../../../docs/LANE_COORDINATION.md).
 */
test.describe('Workflow 3 · verifying an email', () => {
  const ADDRESS = 'm.reinhardt@northwind.com';
  const verify = `/verify-email?email=${encodeURIComponent(ADDRESS)}`;

  test('the screen names the address it sent to', async ({ page }) => {
    await page.goto(verify);

    await expect(page.getByRole('heading', { name: 'Verify your email' })).toBeVisible();
    await expect(page.getByText(ADDRESS, { exact: false })).toBeVisible();
    await expect(page.getByLabel('Work email')).toHaveValue(ADDRESS);
  });

  test('⛔ no code boxes, because nothing would verify them', async ({ page }) => {
    await page.goto(verify);

    // One field — the editable address — and not six.
    await expect(page.getByRole('textbox')).toHaveCount(1);
    await expect(page.getByText(/6-digit|six-digit/i)).toHaveCount(0);
  });

  test('the resend offers a way out to a different address', async ({ page }) => {
    // The design's own line under the control.
    await page.goto(verify);
    await page.getByRole('link', { name: 'Use a different email' }).click();
    await expect(page).toHaveURL(/\/sign-up$/);
  });
});

/**
 * **Workflow 4 · Forgot Password** — [TASK-487](../../../docs/BACKLOG.md),
 * screen `08 Reset your password`.
 *
 * 🔴 **The row names the assertion: the response must be identical for a known
 * and an unknown address.** That is an account-enumeration property, on the
 * one page nobody has to authenticate to reach.
 */
test.describe('Workflow 4 · asking for a reset link', () => {
  test('the screen the design draws is the screen that renders', async ({ page }) => {
    await page.goto('/forgot-password');

    await expect(page.getByRole('heading', { name: 'Reset your password' })).toBeVisible();
    await expect(page.getByLabel('Work email')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Send reset link' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Back to sign in' })).toBeVisible();
  });

  test('🔴 a known and an unknown address get the same answer', async ({ page }) => {
    const answers: string[] = [];
    for (const address of ['m.reinhardt@northwind.com', 'nobody.at.all@northwind.example']) {
      await page.goto('/forgot-password');
      await page.getByLabel('Work email').fill(address);
      await page.getByRole('button', { name: 'Send reset link' }).click();
      answers.push(((await page.getByRole('status').textContent()) ?? '').trim());
    }
    expect(answers[0]).toBe(answers[1]);
    expect(answers[0]).toMatch(/if an account exists/i);
  });

  test('the expiry it prints is the expiry the platform has', async ({ page }) => {
    // resetPasswordTokenExpiresIn defaults to 3600 and is not configured, so
    // the link lives an hour. The design says thirty minutes — C-243.
    await page.goto('/forgot-password');
    await page.getByLabel('Work email').fill('m.reinhardt@northwind.com');
    await page.getByRole('button', { name: 'Send reset link' }).click();

    await expect(page.getByRole('status')).toContainText('expires in an hour');
  });
});
