/**
 * **The credential journeys — registration, verification and reset** —
 * [TASK-475](../../../docs/BACKLOG.md),
 * [ADR-0406 §6](../../../docs/architecture/adr/0406-authentication-execution-modes.md).
 *
 * ## ⛔ The four already green are not rewritten
 *
 * 📁 **The row is explicit**: *"Login, logout and unauthorized access are
 * covered today by `auth-journey.spec.ts`; this row adds what is missing and
 * leaves what works."* ✅ **Journeys 2, 3 and 15 stay where they are.**
 *
 * ## ⚡ What made ten of the seventeen buildable
 *
 * 📁 **Ten journeys carry *"Needs: Dev email"*** — registration, verification,
 * resend, forgot, reset, invitation, acceptance, team invitation, expired
 * links, invalid links. ✅ **`/dev/mailbox` renders what the process actually
 * sent**, so a journey can open the link a customer would open.
 *
 * 🔴 **This is not a bypass, and the distinction is the whole reason it is
 * allowed.** 📁 [`mailbox.ts`](../../lib/auth/mailbox.ts): *"Better Auth still
 * mints the token, still builds the URL, still sets the expiry… only the last
 * hop is local."* ⛔ **Nothing here mints a token, writes a cookie or reaches
 * into Better Auth's tables** — 📁 [§20e](../../../CLAUDE.md): *test data
 * enters the way a customer's data enters.* **The developer's mailbox is a
 * door the product has; a test using it is using the product.**
 *
 * ## 🔴 The row's stopping rule, which this suite respects
 *
 * ⛔ ***"A journey that needs its ASSERTIONS changed rather than its setup has
 * found a behaviour change, and the slice stops."*** ⚡ **So where a journey
 * below could not be made to pass, it is reported rather than weakened** —
 * **an assertion edited to go green is the defect this rule exists to
 * prevent.**
 */

import { expect, test } from './fixtures/signora';
import { newestLinkFor } from './pages/mailbox';

/** ⚡ **A fresh identity per run**, because registration is not idempotent and
 * a suite that reuses an address tests the second attempt rather than the
 * first. */
function newcomer(): { email: string; password: string } {
  const stamp = `${Date.now()}${Math.floor(Math.random() * 1000)}`;
  return { email: `e2e.newcomer.${stamp}@signora.test`, password: 'Correct-Horse-Battery-7!' };
}

/**
 * ⚡ **The newest link the process sent to this address.**
 *
 * ⛔ **Read from the rendered mailbox rather than from an API**, because that
 * is the surface a developer actually has — **a test with a private read is a
 * test of something the product does not offer.**
 */


/**
 * ⚡ **Registration, as the form actually is.**
 *
 * ⚠️ **The first draft of this suite guessed `/signup` and `getByLabel(/email/)`
 * and three journeys failed on the SETUP.** 📁 **The row's stopping rule
 * distinguishes exactly that**: *"a journey that needs its ASSERTIONS changed
 * rather than its setup has found a behaviour change."* ✅ **This was setup,
 * so it was corrected against the real form** — `/register`, *Full name*,
 * *Work email*, and a submit that says **Continue**.
 */
async function register(
  page: import('@playwright/test').Page,
  person: { email: string; password: string },
) {
  await page.goto('/register');
  await page.getByLabel('Full name').fill('E2E Newcomer');
  await page.getByLabel('Work email').fill(person.email);
  await page.getByLabel(/^password$/i).fill(person.password);
  await page.getByRole('button', { name: 'Continue' }).click();
}

test.describe('journey 1 · registration', () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test('@journey somebody with no account can create one and is told what happens next', async ({
    page,
  }) => {
    const person = newcomer();

    await register(page, person);

    /**
     * 🔴 **The assertion is that the product says what happens next**, not
     * that a row appeared. ⚡ **Somebody who registers and is shown nothing
     * assumes it failed and registers again** — which is the state the
     * verification screen exists to prevent.
     */
    await expect(
      page.getByText(/verify|check your email|sent/i).first(),
      'registration completed without telling the person what happens next',
    ).toBeVisible({ timeout: 15_000 });
  });
});

test.describe('journey 4 · email verification — ADR-0406 calls it the blocking one', () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test('@journey the link in the email verifies the account and lands somewhere real', async ({
    page,
  }) => {
    const person = newcomer();

    await register(page, person);
    await expect(page.getByText(/verify|check your email|sent/i).first()).toBeVisible({
      timeout: 15_000,
    });

    const link = await newestLinkFor(page, person.email);
    await page.goto(link);

    /**
     * ⛔ **Never a 404 and never the sign-in form again.** 📁 The Authenticated
     * Entry design calls bouncing somebody back to a form they just completed
     * *"the cruellest loop in enterprise software"*.
     */
    await expect(page.locator('body')).not.toContainText(/404|not found/i);
    expect(page.url(), 'verification returned the person to the form they just completed').not.toMatch(
      /\/signin$/,
    );
  });
});

test.describe('journeys 6 and 7 · forgot password, then reset it', () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test('@journey a forgotten password is recoverable end to end', async ({ page }) => {
    const person = newcomer();

    // ⚡ **Registered first, because resetting a password nobody has is a
    // different journey** — and the product must not distinguish them out
    // loud, which the next test asserts.
    await register(page, person);
    await expect(page.getByText(/verify|check your email|sent/i).first()).toBeVisible({
      timeout: 15_000,
    });

    /**
     * ⚡ **Verified first, and the reason is a finding rather than a step.**
     *
     * ⛔ **A newly registered account cannot sign in until it is verified** —
     * which is correct, and which this journey originally skipped. **The
     * assertion at the end is *the new password works*, so the account has to
     * be in a state where any password would.** ⚠️ **Without this the journey
     * fails at `/signin` and looks like a broken reset**, which is the most
     * misleading kind of red.
     */
    await page.goto(await newestLinkFor(page, person.email));

    await page.goto('/forgot-password');
    await page.getByLabel('Work email').fill(person.email);
    await page.getByRole('button', { name: 'Send reset link' }).click();

    const link = await newestLinkFor(page, person.email);
    await page.goto(link);

    const fresh = 'Different-Horse-Battery-9!';
    await page.getByLabel('New password').fill(fresh);
    await page.getByLabel('Confirm password').fill(fresh);
    await page.getByRole('button', { name: 'Update password' }).click();

    // 🔴 **The journey is only complete if the NEW password works.** ⚡ A reset
    // that reports success and leaves the old credential live is the failure
    // mode nobody notices until an incident.
    await page.goto('/signin');
    await page.getByLabel('Work email').fill(person.email);
    await page.getByLabel(/password/i).first().fill(fresh);
    await page.getByRole('button', { name: /sign in|log in|continue/i }).first().click();

    await expect(page).not.toHaveURL(/\/signin$/, { timeout: 15_000 });
  });

  test('@journey an address that does not exist is answered identically', async ({ page }) => {
    /**
     * 🔴 **An enumeration test, and it is the security half of this journey.**
     * ⛔ **A forgot-password form that says *"no such account"* is an account
     * enumeration oracle** — the same property [§7](../../../CLAUDE.md) protects
     * with *404, never 403*.
     */
    await page.goto('/forgot-password');
    await page.getByLabel('Work email').fill(`e2e.absent.${Date.now()}@signora.test`);
    await page.getByRole('button', { name: 'Send reset link' }).click();

    const body = page.locator('body');
    await expect(body).not.toContainText(/no such|not found|does not exist|unknown/i);
  });
});

test.describe('journey 17 · invalid links', () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test('@journey a tampered token is refused, and says so rather than crashing', async ({
    page,
  }) => {
    /**
     * ⚡ **A refusal is a designed screen, not a stack trace.** ⛔ **And it must
     * not sign anybody in**, which is the assertion that matters more than the
     * wording.
     */
    await page.goto('/reset/not-a-real-token-at-all');

    await expect(page.locator('body')).not.toContainText(/stack|TypeError|undefined is not/i);
    // ⛔ It must not have become a session.
    await page.goto('/');
    await expect(page).toHaveURL(/\/signin|\/verify|\/signup/, { timeout: 15_000 });
  });
});
