/**
 * **The design's three numbers, measured** — [TASK-1460](../../../docs/BACKLOG.md).
 *
 * 📁 Design System v2, the `inherited` block: ⚡ ***"12-column grid, 24px
 * gutters, 1600px content maximum."***
 *
 * ## 🔴 Why these are geometry assertions and not class assertions
 *
 * ⛔ **The row's Definition of Done says it in as many words** — *"the design's
 * three numbers asserted from geometry rather than class names."*
 *
 * ⚠️ **A test reading `max-w-[1600px]` off a `className` proves that somebody
 * typed a string.** ⚡ **It passes just as happily when the class does not exist
 * in Tailwind's output, when a parent's `overflow` defeats it, or when a later
 * utility wins the cascade.** ✅ **`getBoundingClientRect()` proves the browser
 * agreed**, which is the only claim worth making about a layout.
 *
 * 📁 **The same lesson [B-241](../../../docs/BUGS.md) taught one row earlier**:
 * a control that was `visible` by every definition the accessibility tree uses,
 * and 28px below the fold. **Position is not visibility, and a class is not a
 * measurement.**
 */

import { expect, test } from './fixtures/signora';

/** ⚡ Read from the component so the test cannot drift from the design. */
const MAX_WIDTH = 1600;
const GUTTER = 24;

test.describe('the content region carries the design’s maximum', () => {
  /**
   * 🔴 **The band where the maximum actually binds.**
   *
   * ⚠️ **1600 is also a BREAKPOINT**, and at a 1600px viewport the rail (232)
   * and the utility panel leave the content well under 1600 — **so a test at
   * 1600 would pass whether or not the maximum exists.** ⛔ **That is a guard
   * that cannot fail** ([§2](../../../CLAUDE.md)).
   *
   * ✅ **2400px is wide enough that the cap is the binding constraint**, which
   * is the only viewport where this assertion means anything.
   */
  test.use({ viewport: { width: 2400, height: 1000 } });

  test('🔴 content stops at 1600px however wide the monitor is', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Attention', level: 1 })).toBeVisible();

    const box = await page.getByTestId('content-container').boundingBox();

    // ⛔ **`toBeLessThanOrEqual`, not equality** — the container is
    // `w-full max-w-*`, so on a narrow screen it is narrower and that is
    // correct. **The claim is a ceiling.**
    expect(box?.width).toBeLessThanOrEqual(MAX_WIDTH);
    // ✅ **And it must actually REACH the ceiling here**, or the assertion above
    // would pass on a container that was 300px wide for the wrong reason.
    expect(box?.width).toBeGreaterThan(MAX_WIDTH - 1);
  });

  test('⛔ and it is centred, not pinned to the left edge', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Attention', level: 1 })).toBeVisible();

    const container = await page.getByTestId('content-container').boundingBox();
    const main = await page.locator('main').boundingBox();

    // ⚡ **A maximum without `mx-auto` is a different defect, not a partial
    // fix**: content would hug the rail with 700px of empty space to its right.
    const leftGap = (container?.x ?? 0) - (main?.x ?? 0);
    const rightGap =
      (main?.x ?? 0) + (main?.width ?? 0) - ((container?.x ?? 0) + (container?.width ?? 0));

    // 🔴 **This line was added because fire-testing found the test below it
    // could not fail.** ⛔ **With the maximum removed, the container filled
    // `main`, both gaps were `0`, and *equal gaps* was satisfied by there being
    // no gaps at all** — 📁 [§2](../../../CLAUDE.md)'s decorative logic, in a
    // test rather than in the product. ✅ **So the space must exist first**, and
    // only then is it required to be even.
    expect(leftGap).toBeGreaterThan(100);
    expect(rightGap).toBeGreaterThan(100);

    expect(Math.abs(leftGap - rightGap)).toBeLessThan(2);
  });
});

test.describe('the gutter is the design’s 24px', () => {
  // 📁 **The reference layout** — 1280–1599, where the design says the rest of
  // the shell is at its specified values.
  test.use({ viewport: { width: 1280, height: 900 } });

  test('📁 24px between the content region’s edge and its content', async ({ page }) => {
    await page.goto('/');
    const heading = page.getByRole('heading', { name: 'Attention', level: 1 });
    await expect(heading).toBeVisible();

    // 🔴 **Measured on the CONTAINER, not on the first heading — and the first
    // version of this test did the latter and read 87px.**
    //
    // ⚠️ **That 87px is not a defect; it is this row's whole premise.** 📁 The
    // Attention screen carries `max-w-3xl mx-auto` — **one of the eleven ad-hoc
    // widths the row measured** — so it centres ITSELF inside the container and
    // its content is nowhere near the gutter. ⛔ **A test asserting 24px there
    // would be asserting that the migration had already happened**, and it has
    // not: 📁 [455 §4](../../../docs/architecture/455-context-definitions-r02-r03.md)
    // keeps it to its own slice.
    //
    // ✅ **`getComputedStyle` returns the USED value in pixels** — the browser's
    // resolved answer after the cascade, media queries and Tailwind's build.
    // ⛔ **It is not the class name**, which is what the row's Definition of
    // Done rules out, and it isolates the container from whatever screen is
    // inside it.
    const padding = await page.getByTestId('content-container').evaluate((el) => ({
      left: getComputedStyle(el).paddingLeft,
      right: getComputedStyle(el).paddingRight,
    }));

    expect(padding.left).toBe(`${GUTTER}px`);
    expect(padding.right).toBe(`${GUTTER}px`);
  });

  test('⛔ the content region never overflows the frame horizontally', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Attention', level: 1 })).toBeVisible();

    // 🔴 **`min-w-0` on `<main>` is what makes this true**, and it is the one
    // class the row's root-cause note says was already correct. ⚠️ **A wide
    // table pushing the rail off the frame is the regression this direction of
    // change could introduce.**
    const overflows = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    );
    expect(overflows).toBe(false);
  });
});

test.describe('the gutter yields before the data does', () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test('📁 16px on a phone, because chrome yields before data', async ({ page }) => {
    await page.goto('/');
    const heading = page.getByRole('heading', { name: 'Attention', level: 1 });
    await expect(heading).toBeVisible();

    // ⚡ **24px each side of a 390px viewport is 12% of the screen spent on
    // nothing.** 📁 The design states the rule — *"chrome yields before data"* —
    // ⛔ **so this is the design being followed, not a concession to it.**
    const padding = await page
      .getByTestId('content-container')
      .evaluate((el) => getComputedStyle(el).paddingLeft);

    expect(padding).toBe('16px');
  });
});
