import { expect, test } from '@playwright/test';

/**
 * **Account 360 · Research summary, walked as a customer walks it.**
 *
 * 📁 The finalized design, `Fortune Signora Account 360.dc.html`, section
 * `#research` — and its *Section states* panel: ***"Each of the 27 sections
 * above ships in all six states."***
 *
 * ## 🔴 What a browser is needed for, and a component test is not
 *
 * ⚡ **Three of these cannot be asserted anywhere else.**
 *
 * ⓐ **The fold survives a reload.** 📁 *"State persists per user per account
 * type."* ⛔ **A component test can prove `localStorage` was written; only a
 * real navigation proves the value is read back and applied** — and the read
 * happens in an effect after mount, which is exactly where that breaks.
 *
 * ⓑ **The expanded view is shareable.** 📁 *"keeps the URL so the expanded view
 * is shareable."* ⛔ **A shareable URL is a claim about a second visit**, and a
 * component holding a prop proves nothing about one.
 *
 * ⓒ **The section is reachable and headed.** 📁 *"every section is a labelled
 * region with a heading, reachable by landmark navigation"* — ⚡ **in every
 * state, collapsed included.**
 */

/**
 * ⚠️ **Reaches the record through `/accounts`, not through `/`.**
 *
 * ⛔ **`account-360.spec.ts`'s own helper goes via `/` and it does not work
 * here** — `resolveComposition` returns `activation` while `primaryRole` is
 * `null` on every session, so the authenticated root serves the setup
 * checklist and carries no account links at all. ⚡ **That is a route question
 * with the product owner and is deliberately not worked around in the
 * product** — this journey simply navigates the way `account-360-states.spec.ts`
 * already does.
 */
async function openAnAccount(page: import('@playwright/test').Page): Promise<string> {
  await page.goto('/accounts');
  await expect(page.getByRole('table')).toBeVisible();
  await page.getByRole('table').getByRole('row').nth(1).getByRole('link').first().click();
  await expect(page).toHaveURL(/\/accounts\/[0-9a-f-]{8,}/);
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  return new URL(page.url()).pathname;
}

test('@journey the research brief carries the design’s own title and structure', async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await openAnAccount(page);

  const main = page.getByRole('main');

  // 📁 **The design's title.** ⛔ **`Deeper research` was the previous
  // generation's wording and has no basis in the finalized design** — this
  // fails if it comes back.
  await expect(main.getByRole('heading', { name: 'Research summary' })).toBeVisible();
  await expect(main.getByText('Deeper research')).toHaveCount(0);

  // ⛔ **And the two headings the old two-list structure carried.** ⚡ **The
  // deterministic/inferred distinction did not disappear — it moved into the
  // cell** — but these exact strings must not survive beside the new grid.
  await expect(main.getByText('What was compared')).toHaveCount(0);
  await expect(main.getByText('What it means')).toHaveCount(0);

  // 📁 The design's subtitle, verbatim.
  await expect(
    main.getByText(/company, market and relationship research/i),
  ).toBeVisible();
});

test('@journey a folded research section still states its count, and stays folded', async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  const href = await openAnAccount(page);

  const disclosure = page.getByRole('button', { name: /research summary/i });
  await expect(disclosure).toHaveAttribute('aria-expanded', 'true');

  await disclosure.click();
  await expect(disclosure).toHaveAttribute('aria-expanded', 'false');

  // 🔴 📁 ***"A collapsed section still states its count and its worst status,
  // so collapsing never hides a risk."*** ⛔ **The summary is what survives the
  // fold** — a section folded to its heading alone is the one outcome
  // collapsing must never produce.
  const summary = page.locator('#research').getByText(
    /comparison|not researched yet|nothing to compare|could not finish|running/i,
  );
  await expect(summary.first()).toBeVisible();

  // ⓐ **The persistence claim, on a second visit rather than in a mock.**
  await page.goto(href);
  await expect(
    page.getByRole('button', { name: /research summary/i }),
  ).toHaveAttribute('aria-expanded', 'false');

  // ⚡ **Restore it**, so this journey leaves the account as it found it and a
  // later spec is not reading state this one wrote.
  await page.getByRole('button', { name: /research summary/i }).click();
  await expect(
    page.getByRole('button', { name: /research summary/i }),
  ).toHaveAttribute('aria-expanded', 'true');
});

test('@journey focus mode is in the URL, so the expanded view is shareable', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  const href = await openAnAccount(page);

  const focus = page.getByRole('button', { name: /open research in focus mode/i });
  await expect(focus).toBeVisible();
  await focus.click();

  // ⓑ 📁 ***"keeps the URL so the expanded view is shareable."*** ⚡ **The
  // parameter is the section law's `EXPANDED_PARAM`, which had no caller in the
  // product until this section used it.**
  await expect(page).toHaveURL(/[?&]section=research\b/);

  // 🔴 **Shareable means a SECOND visit lands expanded.** ⛔ Asserting the
  // parameter alone would prove the URL changed, never that anything reads it.
  await page.goto(`${href}?section=research`);
  await expect(page.getByRole('button', { name: /leave focus mode/i })).toBeVisible();

  // 📁 ***"Esc returns to the record at the same scroll position."***
  await page.keyboard.press('Escape');
  await expect(page.getByRole('button', { name: /open research in focus mode/i })).toBeVisible();
  await expect(page).not.toHaveURL(/[?&]section=research\b/);
});

test('@journey the research section is reachable by landmark, folded or not', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await openAnAccount(page);

  // ⓒ 📁 ***"Every section is a labelled region with a heading, reachable by
  // landmark navigation."*** ⚡ **A region is only labelled if the heading it
  // points at exists** — and the disclosure button lives INSIDE the heading
  // precisely so folding does not remove the section from the outline.
  const section = page.locator('#research');
  await expect(section).toHaveAttribute('aria-labelledby', 'research-title');
  await expect(page.locator('#research-title')).toBeVisible();

  await page.getByRole('button', { name: /research summary/i }).click();

  // ⛔ **Still headed, still labelled, still in the outline.**
  await expect(page.locator('#research-title')).toBeVisible();
  await expect(section).toHaveAttribute('aria-labelledby', 'research-title');

  await page.getByRole('button', { name: /research summary/i }).click();
});
