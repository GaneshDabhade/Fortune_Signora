/**
 * **Two gates a customer can actually reach** — [TASK-1467](../../../docs/BACKLOG.md).
 *
 * ⚠️ **The row named three screens and the reuse audit found one already
 * built**: 📁 `app/not-found.tsx` renders `SystemState state="404"`, shipped by
 * [TASK-1409](../../../docs/BACKLOG.md). ✅ **So the row shrank rather than
 * rebuilding a correct screen** ([D-229A](../../../docs/DECISION_REGISTER.md)
 * cuts both ways).
 *
 * 🔴 **The other two had a destination and no screen.** ⛔ **`/auth/locked` was
 * routed to by the entry engine and returned the 404 gate**
 * ([B-242](../../../docs/BUGS.md)); **`?error=403` was produced by the engine
 * and read by nothing.**
 */

import { expect, test } from './fixtures/signora';

test.describe('the locked-account gate', () => {
  /**
   * ⚡ **Signed-out, deliberately.** 📁 The entry engine sends somebody here
   * *instead of* signing them in — **so a test that visits it authenticated is
   * testing a state that cannot coexist with the screen.**
   */
  test.use({ storageState: { cookies: [], origins: [] } });

  test('🔴 it exists — it used to be the 404 gate', async ({ page }) => {
    await page.goto('/auth/locked');

    await expect(page.getByRole('heading', { name: 'This account is locked' })).toBeVisible();
    // ⛔ **The exact wrong answer this row removes.** ⚠️ **Somebody who cannot
    // sign in and reads *"that address does not lead anywhere"* concludes the
    // product is broken**, and there is no second place to find out.
    await expect(page.getByText(/does not lead anywhere/i)).toHaveCount(0);
  });

  test('✅ the way out is a password reset, and it works', async ({ page }) => {
    await page.goto('/auth/locked');

    await page.getByRole('link', { name: /reset your password/i }).click();

    // ⚡ **Followed rather than asserted as an `href`** — ⛔ a link to a route
    // that 404s is the defect this whole row is about, one level down.
    await expect(page).toHaveURL(/\/forgot-password/);
  });

  test('⛔ it prints no fact the platform does not publish', async ({ page }) => {
    await page.goto('/auth/locked');
    await expect(page.getByRole('heading', { name: 'This account is locked' })).toBeVisible();

    // 📁 The design draws *"Five failed attempts… at 09:02… unlocks at 09:17."*
    // 🔴 **`AccountStanding` is `'locked'` and nothing more.** ⚠️ **A wrong
    // unlock time is worse than none** — somebody told *"09:17"* waits until
    // 09:17, and if it was a guess they wait for nothing, twice.
    const body = await page.locator('body').innerText();
    expect(body).not.toMatch(/\b\d{1,2}:\d{2}\b/);
  });
});

test.describe('the 403 gate renders where the engine says to render it', () => {
  /**
   * 📁 **`lib/entry/rules.ts` rule 07 routes `INTENT_FORBIDDEN` to
   * `${intent.path}?error=403`** — ***"the 403 page for that object… Not Home,
   * not a silent redirect."***
   *
   * ⛔ **So this asserts the ENGINE'S OWN URL SHAPE**, not a route somebody
   * invented. ⚠️ **The parameter has been produced since the engine shipped and
   * read by nothing**, so a person following a deep link they could not open
   * got the brief's ordinary loading and then an outage-shaped failure.
   */
  test('🔴 ?error=403 on an account renders the refusal, not the brief', async ({ page }) => {
    await page.goto('/accounts/00000000-0000-0000-0000-000000000000?error=403');

    await expect(
      page.getByRole('heading', { name: /do not have access to this account/i }),
    ).toBeVisible();
  });

  test('⛔ it replaces the brief rather than sitting above it', async ({ page }) => {
    await page.goto('/accounts/00000000-0000-0000-0000-000000000000?error=403');
    await expect(
      page.getByRole('heading', { name: /do not have access to this account/i }),
    ).toBeVisible();

    // ⚡ **A refusal a reader can scroll past is a refusal they misread.**
    // 📁 [§20c](../../../CLAUDE.md): the client check is *"a courtesy, never
    // enforcement"* — **Casbin already refused, so there is no data here to
    // protect. What this protects is the reader's understanding.**
    await expect(page.getByText(/could not load/i)).toHaveCount(0);
    await expect(page.getByRole('button', { name: /take this account on/i })).toHaveCount(0);
  });

  test('✅ it names who can grant access rather than only refusing', async ({ page }) => {
    await page.goto('/accounts/00000000-0000-0000-0000-000000000000?error=403');

    // 📁 The rail's own rule, applied here: *"a person who is only refused asks
    // for the wrong thing or asks nobody."*
    await expect(page.getByText(/an owner or an admin can give you access/i)).toBeVisible();
  });

  test('✅ and it offers the list they CAN see', async ({ page }) => {
    await page.goto('/accounts/00000000-0000-0000-0000-000000000000?error=403');

    await page.getByRole('link', { name: /back to the accounts you can see/i }).click();

    await expect(page).toHaveURL(/\/accounts$/);
    await expect(page.getByRole('heading', { name: 'Companies', level: 1 })).toBeVisible();
  });
});
