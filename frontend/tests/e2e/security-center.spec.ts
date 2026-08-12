/**
 * **Workflow 23 · the Security Center, in a browser** —
 * [TASK-1414](../../../docs/BACKLOG.md).
 *
 * 📁 **The row's Playwright coverage, both halves:**
 *
 * > ***"A person enrols a second factor end to end and the backup codes are
 * > shown exactly once"*** · ***"revoking a session actually ends it —
 * > asserted from the revoked session, not from the list."***
 *
 * ## 🔴 A fresh account, and the reason is a defect this lane filed
 *
 * ⛔ **These journeys must NOT run against a shared persona.** ⚡ **Enrolling a
 * second factor changes how that account signs in for every journey after it**,
 * and a failure between enrol and remove would leave it enabled — 📁 which is
 * exactly [B-245](../../../docs/BUGS.md), filed by this lane against its own
 * organization-setup journey: *"a journey cannot create an organization and
 * leave the environment as it found it."*
 *
 * ✅ **So this registers through `/register`, verifies through the developer's
 * mailbox, and signs in** — 📁 the door
 * [`auth-credential-journeys.spec.ts`](auth-credential-journeys.spec.ts)
 * already uses, and the only one [§20e](../../../CLAUDE.md)'s test-data rule
 * permits.
 *
 * ## ⚡ The test is a real authenticator app
 *
 * ⛔ **Nothing is mocked and no code is read out of a database.** **The secret
 * comes off the screen** — the manual key the design requires at every width —
 * **and the code is computed from it exactly as 1Password would.** ✅ **A
 * verification that passes here is one a phone would pass.**
 */
import { createHmac } from 'node:crypto';

import { expect, test } from './fixtures/signora';

/** ⚡ **A fresh identity per run** — registration is not idempotent. */
function newcomer(): { email: string; password: string } {
  const stamp = `${Date.now()}${Math.floor(Math.random() * 1000)}`;
  return { email: `e2e.security.${stamp}@signora.test`, password: 'Correct-Horse-Battery-7!' };
}

async function newestLinkFor(page: import('@playwright/test').Page, email: string) {
  await page.goto('/dev/mailbox');
  const row = page.locator('li, article, tr').filter({ hasText: email }).first();
  await expect(row, 'nothing was delivered to this address').toBeVisible();
  const href = await row.getByRole('link').first().getAttribute('href');
  expect(href, 'the delivered email carried no link').toBeTruthy();
  return href as string;
}

async function registerAndVerify(
  page: import('@playwright/test').Page,
  person: { email: string; password: string },
) {
  await page.goto('/register');
  await page.getByLabel('Full name').fill('E2E Security');
  await page.getByLabel('Work email').fill(person.email);
  await page.getByLabel(/^password$/i).fill(person.password);
  await page.getByRole('button', { name: 'Continue' }).click();
  await expect(page.getByText(/verify|check your email|sent/i).first()).toBeVisible({
    timeout: 20_000,
  });
  await page.goto(await newestLinkFor(page, person.email));
}

async function signIn(
  page: import('@playwright/test').Page,
  person: { email: string; password: string },
) {
  await page.goto('/signin');
  await page.getByLabel(/email/i).fill(person.email);
  await page.getByLabel(/^password$/i).fill(person.password);
  await page.getByRole('button', { name: /sign in|continue/i }).click();
  await expect(page).not.toHaveURL(/\/signin/, { timeout: 20_000 });
}

/**
 * ⚡ **RFC 6238, in the twenty lines it actually takes.** ⛔ **No dependency is
 * added for it** — the algorithm is a counter, an HMAC and a truncation, and a
 * package would be a supply-chain edge for something the standard library
 * already does.
 */
function totp(base32Secret: string, at: number = Date.now()): string {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
  let bits = '';
  for (const character of base32Secret.replace(/=+$/, '').toUpperCase()) {
    const index = alphabet.indexOf(character);
    if (index < 0) continue;
    bits += index.toString(2).padStart(5, '0');
  }
  const bytes = Buffer.from(
    (bits.match(/.{8}/g) ?? []).map((byte) => parseInt(byte, 2)),
  );

  const counter = Buffer.alloc(8);
  counter.writeBigUInt64BE(BigInt(Math.floor(at / 1000 / 30)));

  const digest = createHmac('sha1', bytes).update(counter).digest();
  const offset = (digest[digest.length - 1] as number) & 0x0f;
  const code =
    (((digest[offset] as number) & 0x7f) << 24) |
    (((digest[offset + 1] as number) & 0xff) << 16) |
    (((digest[offset + 2] as number) & 0xff) << 8) |
    ((digest[offset + 3] as number) & 0xff);

  return String(code % 1_000_000).padStart(6, '0');
}

test.describe('workflow 23 · the Security Center', () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  /**
   * 🔴 **The row's second assertion, and the one that is normally faked.**
   *
   * 📁 ***"revoking a session actually ends it — asserted from the revoked
   * session, not from the list."*** ⛔ **A row disappearing proves the screen
   * re-rendered.** ✅ **The revoked browser being turned away at the door
   * proves the token died.**
   */
  test('@journey revoking a session ends it, proven from the revoked session', async ({
    page,
    browser,
  }) => {
    const person = newcomer();
    await registerAndVerify(page, person);
    await signIn(page, person);

    // ⚡ **A second, genuinely separate browser** — a second tab would share the
    // cookie jar and prove nothing about a second token.
    const other = await browser.newContext();
    const otherPage = await other.newPage();
    await signIn(otherPage, person);

    await page.goto('/profile/security');
    const table = page.getByRole('table');
    await expect(table.getByRole('row')).toHaveCount(3);

    await table.getByRole('button', { name: 'Revoke' }).first().click();
    await expect(table.getByRole('row')).toHaveCount(2);

    // 🔴 **The assertion the row asked for**: the OTHER browser is now refused.
    await otherPage.goto('/profile/security');
    await expect(otherPage).toHaveURL(/\/signin/, { timeout: 20_000 });

    await other.close();
  });

  /**
   * 🔴 **Enrolment end to end, with the codes proven to appear exactly once.**
   *
   * ⚡ **Exactly once is asserted by leaving and coming back**, which is the
   * only way a browser can show it: 📁 *"this is the only screen that will ever
   * display them — Signora stores hashes, so it cannot show them again."*
   */
  test('@journey a person enrols a second factor and the backup codes are shown exactly once', async ({
    page,
  }) => {
    const person = newcomer();
    await registerAndVerify(page, person);
    await signIn(page, person);

    await page.goto('/profile/security');
    await page.getByRole('button', { name: 'Add a method' }).click();
    await page.getByLabel('Your password').fill(person.password);
    await page.getByRole('button', { name: 'Continue' }).click();

    // ♿ 📁 *"the QR pane always exposes the manual key, so enrolment never
    // depends on a camera or on seeing an image"* — and here it is the way in.
    const key = await page.getByTestId('manual-key').innerText();
    await page.getByRole('button', { name: 'I have added it' }).click();

    // ⚠️ **Typed, never `fill`ed.** ⛔ Each cell is `maxlength="1"`, so a `fill`
    // of six digits lands one digit and leaves the control disabled — **the
    // failure looked like a wrong code and was a wrong keystroke.**
    await page.getByLabel('Verification code, character 1 of 6').click();
    await page.keyboard.type(totp(key.replace(/\s/g, '')));
    await page.getByRole('button', { name: 'Verify and continue' }).click();

    const codes = page.getByTestId('backup-codes');
    await expect(codes).toBeVisible({ timeout: 20_000 });
    // 📁 *"Ten single-use codes."*
    await expect(codes.getByRole('listitem')).toHaveCount(10);

    await page.getByRole('button', { name: 'I have saved them' }).click();
    await page.getByRole('button', { name: 'Done' }).click();

    // 🔴 **Shown once.** ⛔ **Reloading is the obvious way somebody would try to
    // see them again**, and it must not work.
    await page.reload();
    await expect(page.getByTestId('backup-codes')).toHaveCount(0);
    await expect(page.getByTestId('factor-list')).toContainText('Authenticator app');
  });

  /**
   * ⛔ **The three cells that cannot answer are on the screen, in a browser.**
   *
   * ⚡ **The unit tests prove the rule; this proves the page renders it** —
   * 📁 and the sentence that must never appear is `Open alerts: none`.
   */
  test('@journey the posture strip never claims there are no open alerts', async ({ page }) => {
    const person = newcomer();
    await registerAndVerify(page, person);
    await signIn(page, person);

    await page.goto('/profile/security');

    const openAlerts = page.locator('[data-testid="posture-cell"][data-label="Open alerts"]');
    // ⛔ **The VALUE, not the paragraph.** ⚡ The explanation below it contains
    // the word *none* deliberately — *"It will not say none"* — so an assertion
    // over the whole cell would fail on the sentence that makes the promise.
    await expect(openAlerts.locator('dd > span').first()).toHaveText('Not known');
  });
});
