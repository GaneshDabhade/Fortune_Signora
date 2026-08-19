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

/** The newest link the mailbox holds for one address. */
export async function newestLinkFor(page: Page, email: string): Promise<string> {
  await refuseWithoutTheMailbox(page);

  // ⚠️ **The mailbox is newest-first**, which its own store documents, so the
  // first row mentioning this address is the one just sent.
  const row = page.locator('li, article, tr').filter({ hasText: email }).first();
  await expect(row, 'nothing was delivered to this address').toBeVisible();
  const href = await row.getByRole('link').first().getAttribute('href');
  expect(href, 'the delivered email carried no link').toBeTruthy();
  return href as string;
}
