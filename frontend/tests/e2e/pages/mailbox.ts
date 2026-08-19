import { expect, type Page } from '@playwright/test';

/**
 * **The developer's mailbox — the only door §20e's test-data rule permits for
 * a journey that has to register a real person.**
 *
 * ⚡ **One copy, and it was two.** `security-center.spec.ts` and
 * `auth-credential-journeys.spec.ts` each held this function verbatim; the
 * diagnostic below had to be added to both, and adding it twice is how two
 * copies of one behaviour start to disagree ([§2](../../../CLAUDE.md)).
 */

/**
 * ⛔ **`/dev/mailbox` 404s unless `SIGNORA_AUTH_EMAIL_TRANSPORT=mailbox`**, and
 * the page is deliberately unreachable otherwise — it is a developer tool.
 *
 * 🔴 **[B-1026](../../../docs/BUGS.md).** Without that variable this helper
 * reported *"nothing was delivered to this address"* — **true, and it names the
 * wrong cause.** Six browser failures across two specs said the product had not
 * sent an email, when the product had never had anywhere to send one. **A red
 * line nobody can attribute costs a diagnosis**, which is the whole expense the
 * environment allocation exists to remove.
 */
async function refuseWithoutTheMailbox(page: Page): Promise<void> {
  const response = await page.goto('/dev/mailbox');
  if (response?.status() === 404) {
    throw new Error(
      '/dev/mailbox is not served, so no email can be read. This journey has to ' +
        'register a real person, and the mailbox is the only door §20e permits. ' +
        'Set SIGNORA_AUTH_EMAIL_TRANSPORT=mailbox on the frontend — the transport ' +
        "defaults to 'console', which prints and keeps nothing (B-1026).",
    );
  }
}

/**
 * **Which email a caller is waiting for**, when more than one could be there.
 *
 * 🔴 **Not optional politeness.** 📁 See `newestLinkFor` — without it, a
 * caller that has already received one email for an address gets that one back
 * the instant it asks, whether or not the email it TRIGGERED has arrived.
 */
export interface AwaitedEmail {
  /** What the link carries — `/reset/`, `verify-email`. */
  readonly matching: RegExp;
  /** How to name it when it never comes. */
  readonly describedAs: string;
}

/**
 * The newest link the mailbox holds for one address.
 *
 * ## 🔴 Pass `awaited` whenever the address may already have mail
 *
 * ⛔ **Without it this SAMPLES rather than waits.** ⚡ The mailbox is
 * newest-first, so the first row for an address is the newest **that has
 * arrived** — and an email sent a moment ago has not. **A caller that
 * registered and then requested a reset gets the VERIFICATION link back**,
 * navigates to it, and fails somewhere else entirely.
 *
 * 📁 **Measured on 2026-08-19**: `auth-credential-journeys.spec.ts:131` failed
 * at `getByLabel('New password')` having landed on *"You are not in an
 * organization yet"* — **the verification link, followed a second time.**
 * ⚠️ **It passes alone**, because alone the reset email wins the race.
 *
 * 📁 **[B-1029](../../../docs/BUGS.md)'s third class, named by Lane A**: *"a
 * test that samples before its own read lands, which only shows up when
 * something else is competing."* ⚡ Same shape as
 * [B-1032](../../../docs/BUGS.md), different clock.
 *
 * ✅ **With `awaited`, this waits for the email the caller actually triggered**
 * and says which one never came.
 */
export async function newestLinkFor(
  page: Page,
  email: string,
  awaited?: AwaitedEmail,
): Promise<string> {
  await refuseWithoutTheMailbox(page);

  const newestFor = () => page.locator('li, article, tr').filter({ hasText: email }).first();

  if (!awaited) {
    const row = newestFor();
    await expect(row, 'nothing was delivered to this address').toBeVisible();
    const href = await row.getByRole('link').first().getAttribute('href');
    expect(href, 'the delivered email carried no link').toBeTruthy();
    return href as string;
  }

  let delivered: string | null = null;
  await expect(async () => {
    // ⚡ **Reload, or the mailbox is a snapshot of when this page was opened.**
    await page.reload();
    const row = newestFor();
    await expect(row, 'nothing was delivered to this address').toBeVisible();
    delivered = await row.getByRole('link').first().getAttribute('href');
    expect(delivered, `no ${awaited.describedAs} arrived for this address`).toMatch(
      awaited.matching,
    );
  }).toPass({ timeout: 20_000 });

  return delivered as unknown as string;
}
