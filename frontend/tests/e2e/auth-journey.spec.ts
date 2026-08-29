/**
 * End-to-end authentication journey.
 *
 * The parts of the boundary that can be proven without a live OAuth consent
 * screen are asserted unconditionally. The full sign-in round trip requires
 * real provider credentials and is skipped without them, rather than failing
 * and teaching the team to ignore a red suite.
 */

// 🔴 **The suite's own `test`, not Playwright's** —
// [C-109](../../../docs/LANE_COORDINATION.md). ⛔ **This file signs in on
// nearly every test and imported the bare object**, so it got none of the
// suite's fixtures — including the one that waits out the product's rate
// limiter. ⚡ **Measured: it fails inside the suite and passes alone in 2.7s.**
import { expect, test } from './fixtures/signora';

import { OWNER, PASSWORD } from './fixtures/personas';
import { chooseOrganization } from './pages/signin';

/**
 * **Walk the design's ladder to Home, as a customer does** —
 * 📁 `Fortune Signora Authenticated Entry.dc.html`.
 *
 * ⚠️ **`/` used to RENDER the attention list**, so every sign-in test could
 * assert one heading and stop. ✅ **It resolves now**, and 📁 which rule fires
 * depends on the person: rule 11 enters a sole organization directly; **rule 13
 * shows the chooser to somebody with several and no last-used** — *"this is a
 * first login with multiple memberships and nothing else."*
 *
 * ⛔ **Both are correct outcomes**, so this accepts either and finishes where
 * the ladder finishes: 📁 rule 24's Home.
 */
async function reachMorning(page: import('@playwright/test').Page): Promise<void> {
  /**
   * 🔴 **This was a second implementation of `chooseOrganization`, and the
   * weaker one** — 📁 [B-281](../../../docs/BUGS.md), [§2](../../../CLAUDE.md).
   *
   * ⛔ **It clicked `.first()`.** ⚡ **`chooseOrganization` prefers the row
   * named *Playground*** — the seeded organization the account-backed
   * assertions are written against — **and falls back to the first only when
   * there is no such row.**
   *
   * ⚠️ **That difference is invisible until somebody has two organizations**,
   * which is the ordinary state after any journey that creates one. **Then
   * `.first()` is whichever the newest-first list happens to lead with**, and
   * a signed-in person lands in an empty organization with a perfectly good
   * `home` test id — **so this helper reported success and every assertion
   * after it failed on absent data.**
   *
   * ⛔ **Which is exactly the order-dependence B-281 records**: *"it passes in
   * isolation and fails in a full run."* ⚡ **Nothing about the ordering was
   * mysterious — the helper's answer depended on how many organizations
   * earlier specs had left behind.**
   */
  await chooseOrganization(page);
  await expect(page.getByTestId('home')).toBeVisible();
}

const hasOAuth = Boolean(process.env.GOOGLE_CLIENT_ID ?? process.env.MICROSOFT_CLIENT_ID);

test.describe('unauthenticated access', () => {
  test('the root path redirects to sign-in', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/\/signin/);
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
      await expect(page).toHaveURL(/\/signin/);
    });
  }

  test('@regression an account brief is closed without a session', async ({ page }) => {
    // Guarded by the same server-side layout check, and worth its own case:
    // it is the one authenticated route a customer would paste to a colleague.
    await page.goto('/accounts/00000000-0000-4000-8000-000000000000');
    await expect(page).toHaveURL(/\/signin/);
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
    for (const path of ['/signin', '/api/health']) {
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
    await page.goto('/signin');

    await expect(page.getByLabel('Email')).toBeVisible();
    await expect(page.getByLabel('Password')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible();
  });

  test('leads to registration and to password recovery', async ({ page }) => {
    await page.goto('/signin');

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
    await page.goto('/signin');
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
    await page.goto('/signin');
    await page.getByLabel('Email').fill(OWNER.email);
    await page.getByLabel('Password').fill(PASSWORD);
    await page.getByRole('button', { name: 'Sign in' }).click();

    // **The regression.** Every sign-in landed on `/workspaces`, which returns
    // *"That address does not lead anywhere"*. The password form's own
    // `router.push('/')` never fixed it: the vendor navigates to its
    // `callbackURL` and wins.
    //
    // ⚠️ **`/` is the shell's entry resolver now**, so it forwards rather than
    // renders. 📁 **Which rule fires depends on the person's memberships**, and
    // this persona belongs to more than one organization with nothing recorded
    // in a fresh browser — **rule 13, the chooser** — so *the morning* is
    // reached the way a customer reaches it.
    await reachMorning(page);
  });

  test('@regression the wrong password is refused without saying which half was wrong', async ({
    page,
  }) => {
    await page.goto('/signin');
    await page.getByLabel('Email').fill(OWNER.email);
    await page.getByLabel('Password').fill('not-the-password');
    await page.getByRole('button', { name: 'Sign in' }).click();

    const message = page.getByText(/That email and password do not match an account./);
    await expect(message).toBeVisible();
    // An address-enumeration oracle is the failure this wording exists to
    // prevent: the same sentence must answer *no such account* too.
    await expect(page).toHaveURL(/\/signin/);
  });

  test('@regression an address nobody has registered gets the same answer', async ({
    page,
  }) => {
    await page.goto('/signin');
    await page.getByLabel('Email').fill('nobody.at.all@northwind.example');
    await page.getByLabel('Password').fill(PASSWORD);
    await page.getByRole('button', { name: 'Sign in' }).click();

    await expect(
      page.getByText(/That email and password do not match an account./),
    ).toBeVisible();
  });

  test('signing out ends the session and the product is closed again', async ({ page }) => {
    await page.goto('/signin');
    await page.getByLabel('Email').fill(OWNER.email);
    await page.getByLabel('Password').fill(PASSWORD);
    await page.getByRole('button', { name: 'Sign in' }).click();
    // ⚠️ **`/` forwards now** — the shell's entry resolver replaces it with the
    // resolved workspace's Home, so the root path is never a resting state.
    await reachMorning(page);

    /**
     * 🔴 **[B-249](../../../docs/BUGS.md), third and fourth instances.** ⛔ **The
     * row named two journeys and there were four**: `Sign out` moved into the
     * account menu with the address, in the same change
     * ([TASK-1440](../../../docs/BACKLOG.md)), and
     * [`account-menu.tsx`](../../components/shell/account-menu.tsx) gates its
     * contents on `open`.
     *
     * ⚡ **Recorded rather than quietly fixed**: the row's own point is that the
     * cause is a CLASS, not an accident — **and a class whose census was short
     * by two is worth saying out loud.**
     */
    await page.getByRole('button', { name: /^Account menu for / }).click();
    await page.getByRole('button', { name: 'Sign out' }).click();
    await page.waitForURL(/\/signin/, { timeout: 20_000 });

    // Not merely redirected — the session is gone, so the seam between the
    // tiers refuses to mint a token for it.
    const token = await page.request.post('/api/token');
    expect(token.status()).toBe(401);
  });
});

test.describe('the OAuth round trip', () => {
  test.skip(!hasOAuth, 'requires real OAuth provider credentials');

  test('@journey a provider sign-in reaches the same morning', async ({ page }) => {
    await page.goto('/signin');
    await page
      .getByRole('button', { name: /Continue with/ })
      .first()
      .click();
    // The same destination as a password sign-in, deliberately: the session is
    // identical and the token carries no record of the method (ADR-0033).
    await reachMorning(page);
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
    await page.goto('/register');

    await expect(page.getByRole('heading', { name: 'Create your account' })).toBeVisible();
    // *"Step 1 of 2 · takes about a minute"* — the design's own subtitle, and
    // the reason the button says **Continue** rather than *Create account*.
    await expect(page.getByText('Step 1 of 2 · takes about a minute')).toBeVisible();
    await expect(page.getByLabel('Full name')).toBeVisible();
    await expect(page.getByLabel('Work email')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Continue' })).toBeVisible();
  });

  test('the strength meter answers the password as it is typed', async ({ page }) => {
    await page.goto('/register');
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
    await page.goto('/register');

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
    await page.goto('/register');
    await expect(page.getByText(/breach/i)).toHaveCount(0);
  });

  test('the agreement is stated, and it leads nowhere it cannot', async ({ page }) => {
    // **The line is required and the destinations do not exist** — the
    // design's own markup points both words at `#legal`, and no legal route
    // or configured URL exists in this repository. **Two dead links is what
    // Workflow 1 had to repair**, so the sentence renders and the words are
    // not links.
    await page.goto('/register');

    await expect(
      page.getByText('By continuing you agree to the Terms and Privacy Notice.'),
    ).toBeVisible();
    await expect(page.getByRole('link', { name: 'Terms' })).toHaveCount(0);
    await expect(page.getByRole('link', { name: 'Privacy Notice' })).toHaveCount(0);
  });

  test('the product mark is the way back, since the design gives no other', async ({ page }) => {
    await page.goto('/register');
    await page.getByRole('link', { name: 'Fortune Signora' }).click();
    await expect(page).toHaveURL(/\/welcome$/);
  });

  test('@journey a person creates an account and reaches verification', async ({ page }) => {
    // **The journey the row names.** A fresh address each run, because the
    // account it creates is real — Better Auth is untouched and there is no
    // development-only registration path (D-156, D-158).
    const address = `marta.${Date.now()}@northwind.example`;

    await page.goto('/register');
    await page.getByLabel('Full name').fill('Marta Reinhardt');
    await page.getByLabel('Work email').fill(address);
    await page.getByLabel('Password', { exact: true }).fill('Correct-Horse-9');
    await page.getByRole('button', { name: 'Continue' }).click();

    await page.waitForURL(/\/verify/, { timeout: 30_000 });
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
  const verify = `/verify?email=${encodeURIComponent(ADDRESS)}`;

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
    await expect(page).toHaveURL(/\/register$/);
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

/**
 * ⚡ **180 seconds, and it is a budget rather than a tolerance** —
 * 📁 [B-1030](../../../docs/BUGS.md).
 *
 * **These journeys cross `/forget-password` and `/request-password-reset`,
 * whose Better Auth bucket is `3 per 60 seconds`** — not the 10-second one the
 * sign-in paths use. ⚡ **The suite's rate-limit fixture waits a refusal out
 * rather than being refused by it, and its worst case is two waits of
 * `window + 1`** — **122 seconds before the third attempt**, which cannot fit
 * in the 60-second default.
 *
 * ⛔ **This weakens nothing.** **Every assertion in the block is unchanged**;
 * only how long the runner is willing to wait for a real control moves. 📁 The
 * alternative — configuring the window per environment — is product code and
 * the product owner's ([C-109](../../../docs/LANE_COORDINATION.md) option ②).
 *
 * ⚠️ **Cost, stated rather than hidden**: a run that actually hits the limiter
 * spends that time waiting. **A run that does not is unaffected.**
 */
test.describe('Workflow 4 · asking for a reset link', () => {
  test.describe.configure({ timeout: 180_000 });

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
    // C-243, ruled D-185 §1: resetPasswordTokenExpiresIn is 1800, so the
    // design's own sentence is now the true one. This read "an hour" until
    // 2026-08-08 and was correct then — nothing had configured the value.
    await page.goto('/forgot-password');
    await page.getByLabel('Work email').fill('m.reinhardt@northwind.com');
    await page.getByRole('button', { name: 'Send reset link' }).click();

    await expect(page.getByRole('status')).toContainText('expires in 30 minutes');
  });
});

/**
 * **Registration → Verification → Login** — [TASK-484](../../../docs/BACKLOG.md)'s
 * second journey, delivered **as far as this environment can carry it**.
 *
 * ### ⛔ Why the last hop is not here, verified rather than assumed
 *
 * **The verification link is written to the dev server's stdout** — that is
 * `lib/auth/email.ts`'s console transport, the only one a lane runs. ⚠️ **And
 * `playwright.config.ts` deliberately declares no `webServer`**, because a
 * lane already owns its dev server on its own port — **so the runner does not
 * hold that process's output and cannot read the link.**
 *
 * ⛔ **The three ways to fake it are all refused.** Minting a token in the
 * test forges a credential; seeding a pre-verified account skips the gate the
 * journey exists to prove; tailing a log file is not a customer journey.
 * **[D-151](../../../docs/DECISION_REGISTER.md) ④ is explicit — real tokens,
 * real URLs, real expiry.**
 *
 * ✅ **[TASK-474](../../../docs/BACKLOG.md) is the capability that closes it**
 * — the developer mailbox, `READY` on `lane-c-sync` and `SEQUENCED` on
 * `integration`.
 *
 * ⚡ **What is asserted instead is the half that needs no mailbox and carries
 * the security meaning: the gate is real.** `requireEmailVerification: true`,
 * so a fresh account must not reach a session — **and that is the property a
 * regression would actually break.**
 */
test.describe('Registration → Verification → Login', () => {
  test('@journey an unverified account cannot sign in, which is the gate working', async ({
    page,
  }) => {
    const address = `marta.${Date.now()}@northwind.example`;
    const password = 'Correct-Horse-9';

    await page.goto('/register');
    await page.getByLabel('Full name').fill('Marta Reinhardt');
    await page.getByLabel('Work email').fill(address);
    await page.getByLabel('Password', { exact: true }).fill(password);
    await page.getByRole('button', { name: 'Continue' }).click();
    await page.waitForURL(/\/verify/, { timeout: 30_000 });

    // The account now exists and is unverified. Signing in must fail, and
    // must fail without saying which half was wrong.
    await page.goto('/signin');
    await page.getByLabel('Work email').fill(address);
    await page.getByLabel('Password', { exact: true }).fill(password);
    await page.getByRole('button', { name: 'Sign in' }).click();

    // ⛔ **Never inside the product.** A session before verification would
    // make `requireEmailVerification` decorative.
    await expect(page).toHaveURL(/\/signin/);
    await expect(page.getByTestId('home')).toHaveCount(0);
  });
});

/**
 * **The development mailbox** — [TASK-474](../../../docs/BACKLOG.md).
 *
 * ⚠️ **In this file, not its own, and that is the `owner`/`anonymous` lesson
 * again**: `playwright.config.ts` gives the `anonymous` project a
 * `testMatch` of `auth-journey|workflow1-login`, so a new spec file is
 * collected by no project and reports *"No tests found"* rather than failing.
 *
 * ⛔ **Skipped unless the mailbox is the transport.** The page 404s otherwise,
 * by design, and a test that demanded it would be asserting a configuration
 * rather than a behaviour.
 */
test.describe('the development mailbox', () => {
  test('@journey a registration lands a real, openable link in it', async ({ page }) => {
    const probe = await page.goto('/dev/mailbox');
    test.skip(probe?.status() === 404, 'requires SIGNORA_AUTH_EMAIL_TRANSPORT=mailbox');

    const address = `marta.${Date.now()}@northwind.example`;
    await page.goto('/register');
    await page.getByLabel('Full name').fill('Marta Reinhardt');
    await page.getByLabel('Work email').fill(address);
    await page.getByLabel('Password', { exact: true }).fill('Correct-Horse-9');
    await page.getByRole('button', { name: 'Continue' }).click();
    await page.waitForURL(/\/verify/, { timeout: 30_000 });

    await page.goto('/dev/mailbox');
    const entry = page.locator('li', { hasText: address });
    await expect(entry).toBeVisible();

    // ⚡ **The link is real and openable** — that is the row's whole ask, and
    // the token is Better Auth's own.
    //
    // 🔴 **[B-244](../../../docs/BUGS.md): this asserted `/verify?token=`, which
    // is the *"we have sent you a link"* screen** — 📁
    // [`app/(auth)/verify/page.tsx`](../../app/\(auth\)/verify/page.tsx) reads
    // `email` and consumes no token. ⛔ **Had the assertion been satisfied, the
    // email would have carried the customer to a screen that cannot verify
    // them.** ✅ **Better Auth's own route is what ships**, which verifies and
    // then lands them in the product.
    await expect(entry.getByRole('link')).toHaveAttribute(
      'href',
      /\/api\/auth\/verify-email\?token=/,
    );
  });
});
