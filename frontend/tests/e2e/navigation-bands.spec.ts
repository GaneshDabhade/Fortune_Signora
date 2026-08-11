/**
 * **One navigation, in a real browser, at all four of the design's bands** —
 * [TASK-1461](../../../docs/BACKLOG.md).
 *
 * ## 🔴 Why this journey exists and the component test does not replace it
 *
 * ⛔ **jsdom applies no CSS.** ⚡ **Every rule this row turns on is a media
 * query** — `smalllaptop:static`, `smalllaptop:visible`, `smalllaptop:hidden` —
 * **so the component test can assert the class and only a browser can assert
 * the effect.** 📁 The row's own instruction, from the product owner: *"do not
 * interpret 'Playwright passes' as evidence that responsive behaviour is
 * correct"* — **which is why the widths are enumerated rather than sampled.**
 *
 * ## ⚠️ Every locator here is a DOM locator, deliberately
 *
 * 🔴 **`getByRole` cannot see a `display:none` node** — it is removed from the
 * accessibility tree — **so a role query would have resolved exactly one
 * navigation while the page carried two, which is how the defect survived.**
 * 📁 [B-180](../../../docs/BUGS.md) is the same trap from QE's side: a
 * `querySelector` returned the 0×0 one and the guard could not fail anywhere.
 */

import { expect, test } from './fixtures/signora';

/** 📁 **The App Shell's `breakpoints` table, one width from each band.** */
const BANDS = [
  { name: 'Tablet & phone — < 1024px', width: 390, height: 844, sheet: true },
  { name: 'Small laptop — 1024–1279', width: 1024, height: 800, sheet: false },
  { name: 'Laptop — 1280–1599, the reference layout', width: 1280, height: 900, sheet: false },
  { name: 'Desktop — ≥ 1600px', width: 1600, height: 1000, sheet: false },
];

const PRIMARY = 'nav[aria-label="Primary"]';

for (const band of BANDS) {
  test.describe(band.name, () => {
    test.use({ viewport: { width: band.width, height: band.height } });

    test('🔴 the page carries exactly one Primary navigation', async ({ page }) => {
      await page.goto('/');
      await expect(page.getByRole('heading', { name: 'Attention', level: 1 })).toBeVisible();

      // ⛔ **`page.locator`, not `getByRole`** — see the note above. **This is
      // the assertion that measured 2 before the row.**
      await expect(page.locator(PRIMARY)).toHaveCount(1);
    });

    test('⛔ and nothing is fixed across the bottom of the viewport', async ({ page }) => {
      await page.goto('/');
      await expect(page.getByRole('heading', { name: 'Attention', level: 1 })).toBeVisible();

      // 📁 **The deleted bar was `position: fixed; bottom: 0` and full width.**
      // ⚡ **Measured rather than matched on a class**, because the defect a
      // customer met was geometric: the last row of the attention list sat
      // underneath it.
      const overlaps = await page.evaluate(() => {
        const h = window.innerHeight;
        return [...document.querySelectorAll('body *')].filter((el) => {
          const style = getComputedStyle(el);
          if (style.position !== 'fixed' || style.visibility === 'hidden') return false;
          const box = el.getBoundingClientRect();
          return box.height > 0 && box.width > 200 && Math.abs(box.bottom - h) < 2;
        }).length;
      });
      expect(overlaps).toBe(0);
    });
  });
}

test.describe('below 1024 the rail is a sheet, opened from the top bar', () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test('📁 the design\'s trigger exists and the rail is not on screen until it is pressed', async ({
    page,
  }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Attention', level: 1 })).toBeVisible();

    // ⛔ **The rail is present in the DOM and NOT visible** — `visibility:
    // hidden` is what keeps it out of the tab order while it is off-canvas.
    await expect(page.locator(PRIMARY)).toHaveCount(1);
    await expect(page.locator(PRIMARY)).toBeHidden();

    await page.getByRole('button', { name: 'Open navigation' }).click();

    await expect(page.locator(PRIMARY)).toBeVisible();
    // 🔴 **Opening it must not produce a second one.**
    await expect(page.locator(PRIMARY)).toHaveCount(1);
  });

  test('✅ the sheet is on screen rather than off its left edge', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Open navigation' }).click();
    await expect(page.locator(PRIMARY)).toBeVisible();

    // ⚠️ **A transform that never ran would leave the box at a negative `x`
    // and `toBeVisible()` would still pass**, because visibility is not
    // position. **So the geometry is asserted.**
    //
    // 🔴 **`toPass`, and the reason was measured rather than anticipated**:
    // ⛔ **the first version read the box once and got `x = -125.8`.** ⚡ **Not a
    // defect in the sheet — `visibility` flips on the same frame the class
    // changes, while the 200ms slide is still running**, so `toBeVisible()`
    // resolves mid-animation. ⚠️ **The single read was asserting against a
    // transient state**, which is the flake this file would otherwise have
    // shipped to QE. 📁 The same shape `keyboard-map.spec.ts` already uses for
    // the rail's collapse.
    await expect(async () => {
      const box = await page.locator(PRIMARY).boundingBox();
      expect(box?.x).toBeGreaterThanOrEqual(0);
      expect(box?.width).toBeGreaterThan(100);
    }).toPass();
  });

  test('✅ a destination in the sheet navigates, and the sheet closes behind it', async ({
    page,
  }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Open navigation' }).click();

    await page.getByRole('navigation', { name: 'Primary' }).getByRole('link', { name: 'Settings' }).click();

    await expect(page).toHaveURL(/\/settings/);
    // ⛔ **A sheet left open covers the screen somebody just asked for**, which
    // on a phone reads as the link not working.
    await expect(page.locator(PRIMARY)).toBeHidden();
  });

  /**
   * 🟢 **[B-240](../../../docs/BUGS.md) closes here, and this is the assertion
   * that closes it.**
   *
   * ⛔ **`Shortcuts` was unreachable below 1024** — the rail's utility group had
   * no phone surface, because the bottom bar rendered anchors and this entry
   * opens an overlay. ⚠️ **The lane then wrote a plausible reason for the
   * accident** — *"a reference on a device with no keyboard cannot help
   * anybody"* — 📁 **which the design never says.**
   *
   * ✅ **The sheet is the whole rail, utilities included**, exactly as the band
   * describes it, **so the gap closes at its cause rather than by a sixth
   * control being added to a surface the design replaced.**
   */
  test('🟢 the rail\'s utilities come with it — B-240', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Open navigation' }).click();

    const sheet = page.getByRole('navigation', { name: 'Primary' });
    await expect(sheet.getByRole('button', { name: 'Shortcuts' })).toBeVisible();

    await sheet.getByRole('button', { name: 'Shortcuts' }).click();

    await expect(page.getByRole('heading', { name: 'Keyboard shortcuts' })).toBeVisible();
  });

  test('✅ Escape closes it', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Open navigation' }).click();
    await expect(page.locator(PRIMARY)).toBeVisible();

    await page.keyboard.press('Escape');

    await expect(page.locator(PRIMARY)).toBeHidden();
  });

  test('✅ the backdrop closes it', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Open navigation' }).click();
    await expect(page.locator(PRIMARY)).toBeVisible();

    // ⚡ **Clicked far to the right of a 232px sheet**, so this is the backdrop
    // and never the sheet itself.
    await page.mouse.click(340, 400);

    await expect(page.locator(PRIMARY)).toBeHidden();
  });

  test('🔴 the content region is not covered, and its last row is reachable', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Attention', level: 1 })).toBeVisible();

    // 📁 **This is what `pb-20` was buying and no longer has to.** ⚡ **The
    // check is that `main`'s own bottom edge is not hidden behind anything** —
    // the defect the removed padding existed to work around.
    const clear = await page.evaluate(() => {
      const main = document.querySelector('main');
      if (main === null) return false;
      const box = main.getBoundingClientRect();
      const y = Math.min(box.bottom - 2, window.innerHeight - 2);
      const hit = document.elementFromPoint(box.left + box.width / 2, y);
      return main.contains(hit) || hit === main;
    });
    expect(clear).toBe(true);
  });
});

test.describe('at and above 1024 the rail is in flow and the trigger is gone', () => {
  test.use({ viewport: { width: 1280, height: 900 } });

  test('⛔ no sheet trigger is offered where the rail is already visible', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Attention', level: 1 })).toBeVisible();

    await expect(page.locator(PRIMARY)).toBeVisible();
    await expect(page.getByRole('button', { name: 'Open navigation' })).toBeHidden();
  });

  test('✅ the rail sits beside the content rather than over it', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator(PRIMARY)).toBeVisible();

    const nav = await page.locator(PRIMARY).boundingBox();
    const main = await page.locator('main').boundingBox();

    // 📁 **The design's word for the ≥1024 rail is a COLUMN.** ⛔ **A sheet that
    // failed to return to flow would overlap `main` entirely**, which is the
    // one regression this direction of the change could introduce.
    expect(nav === null ? 0 : nav.x + nav.width).toBeLessThanOrEqual((main?.x ?? 0) + 1);
  });
});
