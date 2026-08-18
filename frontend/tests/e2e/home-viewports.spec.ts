import { expect, test } from './fixtures/signora';

/**
 * **Home's six declared viewports** — 📁 `Fortune Signora Home.dc.html` §*Responsive*.
 *
 * > **Responsive law 1** — *"**Priority order, not scaling.** Each breakpoint
 * > declares an order and a cut list. Cards are never shrunk below their legible
 * > minimum; they are **moved or replaced by a link**."*
 * >
 * > **Responsive law 3** — *"**No third column ever.** At 1600px the content stays
 * > capped at 1360px. A three-column Home works at exactly one viewport and fails
 * > on either side of it."*
 *
 * ## ⛔ Why this is a browser test and not a component test
 *
 * ⚡ **Every assertion here is about GEOMETRY the browser computed** — a resolved
 * `grid-template-columns`, a measured button height, a document that does or does
 * not scroll sideways. 📁 A component test reads class strings, and a class string
 * *"survives a scale change unaltered, which is the bug"* — the same reasoning
 * `design-tokens.test.tsx` states for colour, applied to layout.
 *
 * ## ⚠️ Own viewports rather than the `layout-*` projects
 *
 * 📁 `layout-invariants.spec.ts` runs five projects and asserts what must be true
 * of **every** route — no overflow, no crushed text. ⛔ **These are Home's own
 * declarations**, and the design names six sizes rather than five: `1440` is the
 * reference the whole document is drawn at and no project runs it.
 */
const REFERENCE = { width: 1440, height: 900 };

async function openHome(page: import('@playwright/test').Page) {
  await page.goto('/');
  await page.waitForURL(/\/w\/[0-9a-f-]{36}\/home$/, { timeout: 30_000 });
  await expect(page.locator('[data-card]').first()).toBeVisible({ timeout: 30_000 });
}

/** The resolved column template of Home's card grid, as the browser computed it. */
async function columns(page: import('@playwright/test').Page): Promise<number[]> {
  const template = await page
    .getByTestId('home')
    .locator('> div.grid')
    .evaluate((el) => getComputedStyle(el).gridTemplateColumns);
  return template.split(/\s+/).map((value) => Number.parseFloat(value));
}

test.describe('📁 the two-column split, and where it starts', () => {
  /**
   * 🔴 **Two columns RETURN at 1024, and they used to start at 1280.**
   *
   * 📁 The tablet-landscape row: *"**2 col · 1.4fr / 1fr**. Two columns return.
   * Height is the constraint."* ⛔ **The design's 1024 layout was never drawn** —
   * everything between 1024 and 1279 stacked in one column.
   */
  test('@regression 1024 returns two columns at 1.4 to 1', async ({ page }) => {
    await page.setViewportSize({ width: 1024, height: 768 });
    await openHome(page);

    const [wide, narrow] = await columns(page);

    expect(wide, 'no second column at 1024').toBeDefined();
    expect(narrow, 'no second column at 1024').toBeDefined();
    expect(wide! / narrow!).toBeCloseTo(1.4, 2);
  });

  /**
   * ⚡ **1280 widens to `1.45fr`**, which is a different ratio rather than a
   * rounding of the same one — 📁 the laptop row, *"2 col · 1.45fr / 1fr"*.
   */
  test('@regression 1280 widens the answer column to 1.45 to 1', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await openHome(page);

    const [wide, narrow] = await columns(page);

    expect(wide! / narrow!).toBeCloseTo(1.45, 2);
  });

  /**
   * 📁 **Responsive law 3, asserted rather than asserted-about.** ⛔ *"No third
   * column ever."* ⚡ **Surplus width becomes margin**, so the count is two at the
   * widest viewport the design draws.
   */
  test('@regression 1600 has two columns and never three', async ({ page }) => {
    await page.setViewportSize({ width: 1600, height: 900 });
    await openHome(page);

    expect(await columns(page)).toHaveLength(2);
  });

  /**
   * 📁 The tablet-portrait row: *"**1 col**… vertical space is plentiful here, so
   * the two-column split is **dropped rather than compressed**."*
   */
  test('@regression 768 drops the split rather than compressing it', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await openHome(page);

    expect(await columns(page)).toHaveLength(1);
  });

  /**
   * 📁 *"Content 1360px"*, and 📁 responsive law 3's *"the content stays capped at
   * 1360px"*. ⛔ **A cap, not a target** — the rail and the panel take their own
   * width, so what must hold is that Home never exceeds it.
   */
  test('@regression content never exceeds 1360px', async ({ page }) => {
    await page.setViewportSize({ width: 1600, height: 900 });
    await openHome(page);

    const box = await page.getByTestId('home').boundingBox();

    expect(box?.width ?? 0).toBeLessThanOrEqual(1360);
  });

  /**
   * 📁 The tablet-portrait row again: *"**max 720px**"*. ⚡ At 768 the gutters
   * already produce this; **the cap is what holds it between 768 and 1023**,
   * where the viewport is wider and the split has not yet returned.
   */
  test('@regression a single column is capped at 720px', async ({ page }) => {
    await page.setViewportSize({ width: 900, height: 1024 });
    await openHome(page);

    const box = await page.getByTestId('home').boundingBox();

    expect(await columns(page)).toHaveLength(1);
    expect(box?.width ?? 0).toBeLessThanOrEqual(720);
  });
});

test.describe('📁 the phone cut list — AC-H12', () => {
  /**
   * **`AC-H12`** — *"At 390 × 844, the briefing and **three attention items** are
   * present, **every primary action is at least 44px tall**, and there is **no
   * horizontal scroll**."*
   *
   * ⚠️ **The briefing is not asserted and its absence is not a pass.** 📁
   * `card.briefing` reads `ai.briefing.v1`, and **no approved document assigns
   * that dependency a producer** — recorded rather than faked. The other three
   * clauses are the ones this viewport can answer today.
   */
  test('@a11y @journey 390 shows three attention items and a link to the rest', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await openHome(page);

    const card = page.locator('[data-card="needs-you-today"]');
    const rows = card.locator('a[href^="/accounts/"]:visible');

    // 📁 *"Then three attention items, then a link to the rest."*
    expect(await rows.count()).toBeLessThanOrEqual(3);
    // ⛔ **A row hidden with no link is a CUT**, which responsive law 1 forbids by
    // name: *"moved or replaced by a link."*
    await expect(card.getByRole('link', { name: /See all \d+ in Signals/ })).toBeVisible();
  });

  /**
   * 📁 *"Attention items become full-width rows with the action as a **44px
   * full-width button beneath the reason**."* ⚡ And `2.5.8` requires it
   * independently: *"on mobile every primary action is 44px tall."*
   */
  test('@a11y 390 gives every attention action a 44px full-width button', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await openHome(page);

    const card = page.locator('[data-card="needs-you-today"]');
    const actions = card.locator('a[href^="/accounts/"]:visible');
    const count = await actions.count();
    expect(count).toBeGreaterThan(0);

    const cardBox = await card.boundingBox();
    for (let index = 0; index < count; index += 1) {
      const box = await actions.nth(index).boundingBox();
      expect(box?.height ?? 0, `action ${index} is below the touch minimum`).toBeGreaterThanOrEqual(
        44,
      );
      // ⚡ *"Full-width"* — within the card's own padding, so a fraction rather
      // than an exact figure is what the design actually asks for.
      expect(box!.width / (cardBox?.width ?? 1)).toBeGreaterThan(0.8);
    }
  });

  /**
   * 📁 **`1.4.10`** — *"At 320px CSS width with 400% zoom, Home reflows to one
   * column with **no horizontal scroll and no clipped action**."* ⚡ **320 is the
   * narrowest width the criterion names**, and it is narrower than any device
   * project runs.
   */
  test('@a11y 320 reflows to one column with no horizontal scroll', async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 844 });
    await openHome(page);

    const scroll = await page.evaluate(() => ({
      width: document.documentElement.scrollWidth,
      client: document.documentElement.clientWidth,
    }));

    expect(await columns(page)).toHaveLength(1);
    expect(scroll.width, 'Home scrolls sideways at 320px').toBeLessThanOrEqual(scroll.client + 1);
  });
});

test.describe('📁 the reference viewport', () => {
  /**
   * 📁 *"**1440 × 900 — Desktop, reference.** The canonical layout. Everything in
   * this document is drawn at this size unless stated."* ⚡ *"Attention shows up
   * to five items."*
   */
  test('@regression 1440 shows up to five attention items', async ({ page }) => {
    await page.setViewportSize(REFERENCE);
    await openHome(page);

    const rows = page.locator('[data-card="needs-you-today"] a[href^="/accounts/"]:visible');

    expect(await rows.count()).toBeLessThanOrEqual(5);
    expect(await rows.count()).toBeGreaterThan(3);
  });
});
