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

/**
 * 🔴 **`/` IS A REDIRECT, AND THIS SPEC MEASURED ACROSS IT** — the cause of
 * eighteen consecutive failures that four hypotheses could not explain.
 *
 * 📁 `app/(app)/page.tsx` is a **client-side** `router.replace` in an effect,
 * gated on `useEntryDecision()` → `useWorkspaces()` — **a network read.** ⚡ And
 * 📁 `app-shell.tsx:430` says what happens when it lands: ***"`main` — the
 * content region. **Receives focus on route change** and announces the new page
 * title."***
 *
 * ⛔ **So the sequence was: focus the field · the redirect resolves · the shell
 * moves focus to the content region for screen readers · the slot blurs ·
 * `searchFocused` returns to `false` · the width returns to 224 with nothing
 * left to put it back.**
 *
 * ✅ **The product is correct.** ⚠️ **Focusing the content region on a route
 * change is the accessibility behaviour, not a defect** — and every assertion
 * before the focus passed on **server-rendered markup with no JavaScript run at
 * all**, because `width: 224` is an inline style off `SEARCH_WIDTH.rest`. **The
 * spec waited for appearance, and appearance is free.**
 *
 * ⛔ **This is NOT navigating somewhere easier.** ⚡ It waits for the navigation
 * **this route performs** — the thing the spec always assumed and never said,
 * and which a faster machine completed before the first assertion. **That is
 * the eighteen passes, and why one tree gave opposite answers on different
 * days.**
 */
async function settled(page: import('@playwright/test').Page): Promise<void> {
  await page.goto('/');
  await page.waitForURL(/\/w\/.+\/home/);
}

test.describe('at 1600, where the design gives the field room', () => {
  test.use({ viewport: { width: 1600, height: 900 } });

  test('🔴 224 at rest, 320 on focus, and 224 again after', async ({ page }) => {
    await settled(page);
    /**
     * 🔴 **[B-1400](../../../docs/BUGS.md) — this asserted `'Search Fortune
     * Signora'`, and the shell has rendered `'Search Signora'` since
     * `aa1d4819`.** 📁 [§4](../../../CLAUDE.md) reserves the combined brand for
     * branding surfaces; **a search landmark inside the running application is
     * product speech.**
     *
     * ⛔ **The fix belongs HERE and never in `top-bar.tsx`** — `shell-a11y.test.tsx`
     * asserts the label IS `Search Signora` and is NOT `Search Fortune Signora`,
     * so changing the shell would satisfy this file by breaking that one and
     * breaching §4 to do it.
     *
     * ⚠️ **`aa1d4819` updated every test that could fail the build and missed
     * this one, because Playwright is in no certification gate** — the systemic
     * half is [B-131](../../../docs/BUGS.md) and QE's.
     */
    await expect(page.getByRole('search', { name: 'Search Signora' })).toBeVisible();

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
    await settled(page);
    await expect(page.getByRole('search', { name: 'Search Signora' })).toBeVisible();

    await expect.poll(() => widthOf(page)).toBe(224);

    const field = page.locator(SLOT).getByRole('combobox');
    await field.focus();

    /**
     * 🔴 **THE POSITIVE CONTROL, and it is the finding that outlived the
     * investigation it came from.**
     *
     * ⛔ **Without it this test asserts *"the width stayed 224"* — which is
     * ALSO what a lost focus event produces.** ⚡ **Four mechanisms were
     * proposed for the failure one test above — hydration ordering, redirect
     * timing, a remount, and the blur it turned out to be — and this assertion
     * would have been GREEN through every one of them**, sitting directly
     * beside the bug and reporting nothing.
     *
     * ✅ **Proving the field is focused is what separates *the rule holds* from
     * *the case never arose*.** 📁 The same job `openHomeWithRecents()`'s
     * `toHaveCount(5)` does for [B-1033](../../../docs/BUGS.md), and the class
     * QE recorded in [B-1073](../../../docs/BUGS.md).
     */
    await expect(field).toBeFocused();

    await expect.poll(() => widthOf(page)).toBe(224);
  });
});
