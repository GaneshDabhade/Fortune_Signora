import { expect, test } from '@playwright/test';

import { openScoredAccount } from './fixtures/accounts';

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

test('@journey the research brief carries the design’s own title and structure', async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await openScoredAccount(page);

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
  await openScoredAccount(page);

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

  // ⓐ 🔴 **The design asks for persistence and this page cannot yet give it,
  // so the journey asserts the BOUNDARY rather than the wish.**
  //
  // 📁 The design: *"State persists per user per account type."* ⛔ **The
  // account TYPE is not published to this page** — `useAccounts` returns
  // `AccountAttention` and `useAccountIdentities` returns `AccountIdentity`,
  // and neither carries `kind` ([B-261](../../../docs/BUGS.md)). ⚡ **So
  // `page.tsx` passes `kind={null}`, which the collapse law reads as *persist
  // nothing* rather than *persist wrongly***: a preference filed under a
  // guessed type is one a rep cannot get back.
  //
  // ✅ **This asserts the withholding is real**, not that persistence works.
  // ⛔ **And it FAILS the day `kind` becomes available** — which is when this
  // block should become the second-visit assertion it was first written as,
  // rather than quietly continuing to pass against a capability that arrived.
  const persisted = await page.evaluate(() =>
    Object.keys(window.localStorage).filter((key) => key.includes(':a360:collapse:')),
  );
  expect(
    persisted,
    'the collapse law now has an account kind to key on — restore the second-visit assertion',
  ).toEqual([]);

  // ⚡ **Unfold it again in the same visit** — ⛔ nothing carries across a
  // reload while the key cannot be built, so this is the whole round trip
  // available today.
  await disclosure.click();
  await expect(disclosure).toHaveAttribute('aria-expanded', 'true');
});

test('@journey focus mode is in the URL, so the expanded view is shareable', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  const href = await openScoredAccount(page);

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
  await openScoredAccount(page);

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
