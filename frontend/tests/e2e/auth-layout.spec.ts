/**
 * **The authentication card's layout, measured rather than described** —
 * [B-175](../../../docs/BUGS.md).
 *
 * ## 🔴 Why this file exists, in QE's words
 *
 * > ***"The repair is not 'add a check that every prefix resolves'. It is that
 * > a test asserting layout must assert the COMPUTED result, not the class
 * > attribute — the attribute is an input to the framework, and testing an
 * > input proves the caller's intent rather than the product's behaviour."***
 *
 * ⛔ **Five assertions in `auth-shell.test.tsx` passed on the commit that broke
 * every authentication screen** ([B-424](../../../docs/BUGS.md)). ⚡ **They
 * asserted that a class string contained a substring**, and the strings were
 * still there after `theme.screens` stopped defining the prefixes — **so the
 * utilities compiled to nothing and the assertions stayed true.**
 *
 * 🔴 **And renaming them does not fix them.** 📁 The row says so directly:
 * *"the five tests will go green again the moment the classes are renamed,
 * while proving no more than they do today… this row closes when a layout
 * assertion reads the computed result."*
 *
 * ## ⚡ So it runs in a browser, because nothing else can answer
 *
 * ⛔ **jsdom has no stylesheet and no layout engine**, so `getComputedStyle`
 * there returns what was set inline and nothing else. **A component test
 * cannot tell whether a Tailwind utility emitted CSS** — ✅ **a real browser
 * with the real build can, and that is the only place this question has an
 * answer.**
 *
 * ⚠️ **Each assertion below compares the SAME element across two widths.**
 * ⛔ **An absolute value would pin a design decision** — *the radius is 12px* —
 * **and this is about whether the band applies at all**, which is what broke.
 */

import { expect, test } from './fixtures/signora';

/** 📁 The design's floor: `phone` is 640, so 500 is below it and 900 above. */
const BELOW_PHONE = { width: 500, height: 900 };
const ABOVE_PHONE = { width: 900, height: 900 };
/** 📁 `smalllaptop` is 1024. */
const ABOVE_SMALL_LAPTOP = { width: 1200, height: 900 };

test.describe('🔴 B-175 · the authentication card responds, and the test can tell', () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test('@journey the card gains its rounded plane above the phone floor', async ({ page }) => {
    /**
     * ⚡ **`phone:rounded-xl` is one of the five B-175 names.** ⛔ **On the
     * broken commit the class was present and the corner was square** — and
     * the component test said the layout was fine.
     */
    await page.setViewportSize(BELOW_PHONE);
    await page.goto('/signin');
    /**
     * ⚡ **Located the way the component test locates it** — two levels up from
     * the `<h1>` — ⛔ **rather than by the class under test.** **A selector
     * built from `phone:rounded-xl` would find the element only when the class
     * is present, so the test would pass by not running.**
     */
    const card = page.getByRole('heading', { level: 1 }).locator('xpath=../..');
    await expect(card).toBeVisible();

    const squared = await card.evaluate((el) => getComputedStyle(el).borderTopLeftRadius);

    await page.setViewportSize(ABOVE_PHONE);
    const rounded = await card.evaluate((el) => getComputedStyle(el).borderTopLeftRadius);

    // 🔴 **The whole point**: the two widths must differ. If the utility emits
    // no CSS they are identical, and this fails — which is what should have
    // happened on the commit that broke it.
    expect(
      { squared, rounded },
      'the card renders identically above and below the phone floor, so the responsive rule emits no CSS',
    ).not.toEqual({ squared: rounded, rounded });
    expect(parseFloat(rounded)).toBeGreaterThan(parseFloat(squared));
  });

  test('@journey the frame takes its top spacing above the phone floor', async ({ page }) => {
    // ⚡ `phone:pt-24`, another of the five.
    await page.setViewportSize(BELOW_PHONE);
    await page.goto('/signin');
    const main = page.getByRole('main');

    const tight = parseFloat(await main.evaluate((el) => getComputedStyle(el).paddingTop));

    await page.setViewportSize(ABOVE_PHONE);
    const roomy = parseFloat(await main.evaluate((el) => getComputedStyle(el).paddingTop));

    expect(roomy, 'padding-top does not change across the phone floor').toBeGreaterThan(tight);
  });

  test('@journey the frame centres its content on a small laptop', async ({ page }) => {
    /**
     * ⚡ **`smalllaptop:justify-center`** — 📁 the assertion that used to read
     * `toMatch(/lg:/)` under the name *"centred on a desktop"* **while nothing
     * was centred.**
     */
    await page.setViewportSize(ABOVE_PHONE);
    await page.goto('/signin');
    const main = page.getByRole('main');

    const top = await main.evaluate((el) => getComputedStyle(el).justifyContent);

    await page.setViewportSize(ABOVE_SMALL_LAPTOP);
    const centred = await main.evaluate((el) => getComputedStyle(el).justifyContent);

    expect(centred, 'the frame does not centre at the small-laptop band').toBe('center');
    expect(top, 'it was already centred below the band, so the rule proves nothing').not.toBe(
      'center',
    );
  });
});
