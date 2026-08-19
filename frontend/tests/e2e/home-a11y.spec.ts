import { expect, test } from './fixtures/signora';

/**
 * **Home's accessibility table** — 📁 `Fortune Signora Home.dc.html` §11, and the
 * keyboard table in §10.
 *
 * ## ⛔ Why these are browser assertions
 *
 * ⚡ **Every one is about the rendered document**: how many landmarks exist, what
 * order the headings come in, where focus lands, what Tab reaches next. 📁 A
 * component test renders one card in isolation and **cannot see the page these
 * criteria are about** — `1.3.1` is a statement about the whole `<main>`.
 */

async function openHome(page: import('@playwright/test').Page) {
  await page.goto('/');
  await page.waitForURL(/\/w\/[0-9a-f-]{36}\/home$/, { timeout: 30_000 });
  await expect(page.locator('[data-card]').first()).toBeVisible({ timeout: 30_000 });
  // The reads settle before structure is measured; a skeleton is not the card.
  await page.waitForLoadState('networkidle');
}

test.describe('📁 1.3.1 — one main, one h1, and a section per card', () => {
  /**
   * 📁 *"Home is one `<main>` with an **h1 naming the workspace**. Each card is a
   * `<section>` with its own **h2** in DOM order matching visual order at every
   * breakpoint."*
   */
  test('@a11y every card is exactly one section', async ({ page }) => {
    await openHome(page);

    const cards = page.locator('[data-card]');
    const count = await cards.count();
    expect(count).toBeGreaterThan(0);

    for (let index = 0; index < count; index += 1) {
      const card = cards.nth(index);
      const id = await card.getAttribute('data-card');
      // ⛔ **The card's own element IS the section.**
      expect(await card.evaluate((el) => el.tagName), `${id} is not a section`).toBe('SECTION');
      // 🔴 **And it contains no second one.** ⚠️ Several cards rendered their own
      // `<section>` inside Home's, which made two nested landmarks per card and
      // left the outer one carrying the name.
      expect(
        await card.locator('section').count(),
        `${id} nests a second section`,
      ).toBe(0);
    }
  });

  /**
   * 🔴 **`h2`, not `h3`.** ⛔ Under the page's `h1`, a card heading at `h3` skips
   * a level — which is `1.3.1`'s own defect, and it is what several cards did.
   */
  test('@a11y every card heading is an h2 under the page h1', async ({ page }) => {
    await openHome(page);

    await expect(page.getByRole('heading', { level: 1 })).toHaveCount(1);

    const cards = page.locator('[data-card]');
    for (let index = 0; index < (await cards.count()); index += 1) {
      const card = cards.nth(index);
      const id = await card.getAttribute('data-card');
      // ⚠️ **A card showing its error or forbidden panel has no h2 of its own** —
      // 📁 `SystemState` renders a region title as a `<p>` deliberately, *"the
      // ARIA dialog role carries an expectation this panel does not meet"* being
      // the same instinct. **Those cards are named by the section instead.**
      const headings = await card.locator('h1, h2, h3, h4, h5, h6').evaluateAll((els) =>
        els.map((el) => el.tagName),
      );
      for (const tag of headings) {
        expect(tag, `${id} has a ${tag} where the design says h2`).toBe('H2');
      }
    }
  });

  /**
   * ⛔ **DOM order is visual order.** 📁 *"…in DOM order matching visual order at
   * every breakpoint"* — ⚡ which is why the grid PLACES cards rather than
   * reordering them, and why the column pins are `col-start` rather than `order`.
   */
  test('@a11y DOM order matches visual order at the reference viewport', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await openHome(page);

    const boxes = await page.locator('[data-card]').evaluateAll((els) =>
      els.map((el) => {
        const rect = el.getBoundingClientRect();
        return { id: el.getAttribute('data-card'), top: Math.round(rect.top), left: Math.round(rect.left) };
      }),
    );

    // ⚡ **Reading order is rows then columns**, which is what a two-column grid
    // presents to somebody reading down the page.
    const visual = [...boxes].sort((a, b) => a.top - b.top || a.left - b.left);
    expect(boxes.map((b) => b.id)).toEqual(visual.map((b) => b.id));
  });
});

test.describe('📁 §10 — the keyboard table', () => {
  /**
   * 📁 *"**Enter Home** — focus lands on the h1, not the search field."*
   */
  test('@a11y focus lands on the h1, never the search field', async ({ page }) => {
    await openHome(page);

    const focused = await page.evaluate(() => ({
      tag: document.activeElement?.tagName,
      role: document.activeElement?.getAttribute('role'),
    }));

    expect(focused.tag, 'focus did not land on the page heading').toBe('H1');
  });

  /**
   * 📁 *"**Move between cards** — each card is a tab group. Tab enters, Tab exits
   * at the last control; **arrows do not move between cards**."*
   *
   * ⚡ **Satisfied by construction and asserted anyway.** ⛔ Nothing on Home binds
   * an arrow key, so the browser's own behaviour is the design's — **and this
   * fails the day something starts binding one**, which is the only way that
   * regression would ever be noticed.
   */
  test('@a11y arrows do not move focus between cards', async ({ page }) => {
    await openHome(page);

    // Tab into the first card's own controls.
    const card = page.locator('[data-card]').first();
    const control = card.locator('a, button').first();
    await control.focus();
    const before = await page.evaluate(() => document.activeElement?.outerHTML?.slice(0, 80));

    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('ArrowRight');

    const after = await page.evaluate(() => document.activeElement?.outerHTML?.slice(0, 80));
    expect(after, 'an arrow key moved focus').toBe(before);
  });

  /**
   * 📁 *"**Open the focused item** — activates the row's primary action, **not a
   * detail overlay**."*
   *
   * ⚡ The row's action is a link, so Enter navigates. ⛔ **What this rules out is
   * a dialog**: an overlay here would mean a keyboard reader could not reach the
   * account at all without a second decision.
   */
  test('@a11y @journey Enter on a row action opens the account, not an overlay', async ({
    page,
  }) => {
    await openHome(page);

    const action = page
      .locator('[data-card="needs-you-today"] a[href^="/accounts/"]')
      .first();
    await expect(action).toBeVisible({ timeout: 20_000 });
    const href = await action.getAttribute('href');
    await action.focus();
    await page.keyboard.press('Enter');

    await page.waitForURL(new RegExp(href!.replace(/\//g, '\\/')), { timeout: 20_000 });
    expect(await page.getByRole('dialog').count()).toBe(0);
  });
});

test.describe('📁 4.1.3 — entry announces once', () => {
  /**
   * 📁 *"Entry announces once: workspace, composition, attention count.
   * **Individual card arrivals announce nothing** — a screen-reader user hears
   * one sentence, not six."*
   *
   * ⛔ **One polite live region on the page, and it is the scope line.** ⚡ A card
   * that announced its own arrival would make entry six sentences, which is the
   * defect this criterion names.
   */
  test('@a11y one live region, and it is the scope line', async ({ page }) => {
    await openHome(page);

    const live = page.locator('main [aria-live]');
    expect(await live.count()).toBe(1);
    // ⚡ **Polite, never assertive** — arriving somewhere is not an interruption.
    await expect(live.first()).toHaveAttribute('aria-live', 'polite');
  });
});
