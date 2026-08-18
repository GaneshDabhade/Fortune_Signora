/**
 * **Home and the brief describe the same account.**
 *
 * 🔴 **This spec compared the ATTENTION LIST's rows to the brief, and that
 * screen is retired.** ⛔ **It is not re-pointed at Companies**, and the reason
 * is a fact about the product rather than about the test: 📁
 * `app/(app)/accounts/page.tsx` says so in the page — *"a Signora score is not
 * on this list yet… a score column that has no source"* — **so the comparison
 * this file was built on has no surface left that makes both halves of it.**
 *
 * ⚠️ **Two of its four tests filtered rows for `Cooling` and `Contested`
 * badges and skipped when none was found.** ⛔ **Against Companies they would
 * skip forever** — 📁 [§2](../../../CLAUDE.md), *a guard that cannot fail is
 * documentation pretending to be code* — **so they are removed rather than
 * left to report green.**
 *
 * ✅ **What survives is the claim the current design does make**: 📁 Home's
 * `card.attention` raises accounts *"each with a reason"*, and the brief is
 * where that account is explained. **The two must be about the same company,
 * and the brief must have the score the card ranked it by.**
 */

import { expect, test } from './fixtures/signora';

/** The accounts Home is raising, with the link into each. */
async function raised(page: import('@playwright/test').Page) {
  const card = page.locator('[data-card="needs-you-today"]');
  await expect(card).toBeVisible({ timeout: 20_000 });
  await expect(card.locator('a[href^="/accounts/"]').first()).toBeVisible({ timeout: 20_000 });

  return card.locator('a[href^="/accounts/"]').evaluateAll((links) =>
    links.map((link) => ({
      href: link.getAttribute('href') ?? '',
      // The account's name is the row's own heading, not the link's label —
      // the link says "Open the account" on every row.
      name: (link.closest('div')?.querySelector('span')?.textContent ?? '').trim(),
    })),
  );
}

async function openHome(page: import('@playwright/test').Page): Promise<void> {
  await page.goto('/');
  await page.waitForURL(/\/w\/[0-9a-f-]+\/home$/, { timeout: 30_000 });
}

test.describe('Home and the brief describe the same account', () => {
  test('@journey an account Home raises has the score it was ranked by', async ({
    page,
    brief,
  }) => {
    await openHome(page);
    const items = await raised(page);
    expect(items.length).toBeGreaterThan(0);

    // Three rather than one: a single sample can agree by accident.
    for (const item of items.slice(0, 3)) {
      await page.goto(item.href);
      // ⛔ **This is the assertion, not a wait.** 📁 Home's card reads the open
      // signal queue and ranks by what it costs to ignore — **so every account
      // it raises is one Signora has scored**, and a brief with no score would
      // mean the card offered work the product cannot explain.
      await brief.waitForScore();
    }
  });

  test('@journey the name Home shows is the name on the brief', async ({ page, brief }) => {
    /**
     * ⚡ **Read from the BRIEF and checked back on Home**, rather than scraped
     * off the card. ⛔ **Home does not block on names** — 📁 the card's own
     * rule: *"the count and the question are the decision, and blocking on a
     * label would trade the decision for the word"* — **so a name read off the
     * card the moment it renders can legitimately be absent.** ✅ The brief's
     * heading is a resolved name or a stated absence, and it is the stable end
     * of the comparison.
     */
    await openHome(page);
    const items = await raised(page);
    expect(items.length).toBeGreaterThan(0);

    let compared = 0;
    for (const item of items.slice(0, 3)) {
      await page.goto(item.href);
      await brief.waitForScore();
      /**
       * ⚠️ **Wait for the NAME, not for the score.** 📁 The brief *"does not
       * block on"* the identity read — the score arrives first and the heading
       * is empty until the name lands. ⛔ Reading it the moment the score
       * appears returns `""` on every account, which is what this assertion
       * did before it was measured.
       */
      const heading = page.locator('main h1').first();
      await expect(heading).not.toBeEmpty({ timeout: 20_000 });
      const name = (await heading.innerText()).trim();
      if (name.length < 3 || /unnamed/i.test(name)) continue;

      await openHome(page);
      const card = page.locator('[data-card="needs-you-today"]');
      await expect(card.getByText(name, { exact: false }).first()).toBeVisible({
        timeout: 20_000,
      });
      compared += 1;
    }

    expect(compared, 'no account Home raised had a resolved name on its brief').toBeGreaterThan(0);
  });
});
