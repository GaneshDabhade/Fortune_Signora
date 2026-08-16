import { expect, type Page } from '@playwright/test';

/**
 * **Open an account whose record page actually renders its sections.**
 *
 * ## 🔴 Why this is a walk and not `rows.nth(1)`
 *
 * ⛔ **Not every seeded account has a score, and the record page short-circuits
 * when none does** — it renders *"Nothing has scored this account yet"* and
 * **no sections at all**, which is correct behaviour and not a defect.
 *
 * ⚠️ **A journey that clicks the first row is therefore green or red depending
 * on seed order**, which is a hidden input ([§2](../../../../CLAUDE.md)) — and
 * it is exactly how `account-360-research.spec.ts` first failed: it reached
 * `Sandgate Retail Systems`, an unscored account, and reported a missing
 * section that was never going to be there.
 *
 * ## ⚡ Two races, both already paid for once
 *
 * 📁 **This walk is `account-360-states.spec.ts`'s, extracted rather than
 * copied** — ⛔ a third hand-written version would be a third chance to
 * reintroduce the two races its comments record:
 *
 * ⓐ **Counting the table before it is visible** returns zero, so the loop never
 * runs and the helper blames the data for a list that was merely loading.
 *
 * ⓑ **Counting `#score` the instant the click resolves** returns zero while the
 * read is in flight, **so every account looks unscored** — the helper then
 * threw *"seed the Playground"* against a workspace holding eleven named,
 * scored accounts.
 *
 * ✅ **The wait is for EITHER answer** — the section, or the page's own
 * *"Nothing has scored this account yet"* — so an account that genuinely has no
 * score moves the loop on rather than timing out.
 */
export async function openScoredAccount(page: Page): Promise<string> {
  await page.goto('/accounts');
  await expect(page.getByRole('table')).toBeVisible();
  const count = await page.getByRole('table').getByRole('row').count();

  for (let row = 1; row < Math.min(count, 12); row += 1) {
    await page.goto('/accounts');
    await page.getByRole('table').getByRole('row').nth(row).getByRole('link').first().click();
    await expect(page).toHaveURL(/\/accounts\/[0-9a-f-]{8,}/);

    await Promise.race([
      page.locator('#score').waitFor({ timeout: 15_000 }).catch(() => undefined),
      page
        .getByText('Nothing has scored this account yet')
        .waitFor({ timeout: 15_000 })
        .catch(() => undefined),
    ]);

    if (await page.locator('#score').count()) return new URL(page.url()).pathname;
  }

  throw new Error(
    'No account in the first twelve rows renders its sections. Seed the Playground before running this journey.',
  );
}
