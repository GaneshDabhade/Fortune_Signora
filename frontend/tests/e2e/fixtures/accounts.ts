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

/**
 * **Open an account that a provider has actually named, and return that name.**
 *
 * ## 🔴 Why this is not `.first()` and not `innerText`
 *
 * ⛔ **[B-1068](../../../../docs/BUGS.md) — the list's order is a hidden input.**
 * Every seeded entity shares one `created_at`, so `ORDER BY created_at, id`
 * decides on a **random UUID** and the first row changes on every reseed.
 *
 * ⚠️ **And an UNNAMED account is not merely a worse first row — it makes the
 * breadcrumb assertion fail on a correctly-behaving product.** 📁
 * `entity-name.tsx`:91 renders an unnamed account as its identifier **plus an
 * `sr-only` sentence inside the same link**:
 *
 * ```
 * 09cdf253<span class="sr-only"> — no source has named this account yet</span>
 * ```
 *
 * ⛔ **`textContent` includes that sentence; `Crumb.label` is a bare `string`
 * (`lib/shell/breadcrumb.ts`:37) and cannot carry it.** ⚡ **So the two surfaces
 * genuinely differ in what they can hold, and the crumb is right.**
 *
 * ## ⛔ Why the repair is not `innerText`
 *
 * **`innerText` omits `sr-only`, so switching to it makes the assertion pass** —
 * ⚠️ **and it passes because the assertion stopped reading half the element, not
 * because the product agrees with itself.** **A comparison that hides the
 * difference is the wrong repair.** *(Lane A, 2026-08-22.)*
 *
 * ✅ **So this resolves a row that HAS a name, where `textContent` and the crumb
 * can agree** — and leaves the unnamed case to a test written for it.
 *
 * ⛔ **It throws rather than skipping if nothing is named.** A workspace where no
 * provider has named anything is a real condition worth failing on, not an
 * `if (count > 0)` that reports green having asserted nothing.
 */
export async function openNamedAccount(page: Page): Promise<string> {
  await page.goto('/accounts');
  const links = page.locator('main a[href^="/accounts/"]');
  await expect(links.first()).toBeVisible({ timeout: 20_000 });

  const count = await links.count();
  for (let index = 0; index < Math.min(count, 12); index += 1) {
    const link = links.nth(index);
    // **The `sr-only` span is the marker, not a heuristic about the text.** An
    // unnamed account always carries it; a named one never does.
    if (await link.locator('.sr-only').count()) continue;

    const name = (await link.textContent())?.trim() ?? '';
    if (name === '') continue;

    await link.click();
    await page.waitForURL(/\/accounts\/[0-9a-f-]{36}/, { timeout: 30_000 });
    return name;
  }

  throw new Error(
    'No account in the first twelve rows carries a provider-supplied name. ' +
      'Seed the Playground before running this journey.',
  );
}
