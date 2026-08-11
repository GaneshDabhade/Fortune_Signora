/**
 * **§07's search widens on focus, and only where there is room** —
 * [TASK-1474](../../../docs/BACKLOG.md).
 *
 * 🔴 **A browser is the only place this can be asserted.** ⚡ **The width is a
 * COMPUTED value at a real viewport**, and jsdom applies no CSS and lays nothing
 * out — ⛔ **the same reason [TASK-1461](../../../docs/BACKLOG.md)'s duplicated
 * navigation survived a suite that asserted the rail on every screen.**
 *
 * ⚠️ **Two-sided at both viewports**, which is the product owner's standard:
 * **a one-sided check passes on a search that is always 320px.**
 */
import { expect, test } from './fixtures/signora';

const SLOT = '[data-slot="search"]';

async function widthOf(page: import('@playwright/test').Page): Promise<number> {
  const box = await page.locator(SLOT).boundingBox();
  if (box === null) throw new Error('the search slot has no box');
  return Math.round(box.width);
}

test.describe('at 1600, where the design gives the field room', () => {
  test.use({ viewport: { width: 1600, height: 900 } });

  test('🔴 224 at rest, 320 on focus, and 224 again after', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('search', { name: 'Search Fortune Signora' })).toBeVisible();

    await expect.poll(() => widthOf(page)).toBe(224);

    await page.locator(SLOT).getByRole('combobox').focus();
    await expect.poll(() => widthOf(page)).toBe(320);

    // ⚡ **Blur by moving focus somewhere real**, as a person would.
    await page.getByRole('link', { name: 'Help and support' }).focus();
    await expect.poll(() => widthOf(page)).toBe(224);
  });
});

test.describe('at 1599, one pixel below the threshold', () => {
  test.use({ viewport: { width: 1599, height: 900 } });

  /**
   * 🔴 **The assertion an off-by-one fails.** ⛔ **`>= 1600` and `> 1600` differ
   * by exactly this test**, and 96px taken from the breadcrumb is what the
   * design is protecting at this band.
   */
  test('⛔ focus changes nothing, because there is no room', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('search', { name: 'Search Fortune Signora' })).toBeVisible();

    await expect.poll(() => widthOf(page)).toBe(224);

    await page.locator(SLOT).getByRole('combobox').focus();

    await expect.poll(() => widthOf(page)).toBe(224);
  });
});
