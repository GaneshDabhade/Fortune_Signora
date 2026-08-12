/**
 * **§03 · §09 · §14 — the App Shell values the design states exactly** —
 * [TASK-1414 → TASK-1462](../../../docs/BACKLOG.md).
 *
 * 🔴 **Every assertion here is GEOMETRY, never a class name.**
 *
 * ⚠️ **The row is explicit about why**: *"every value in §03, §09 and §14 is
 * asserted from geometry rather than from a class name."* ⛔ **A test that
 * asserts `max-w-xl` passes while the palette is 576px and the design says
 * 640** — **which is exactly the defect this row exists to close**, and
 * exactly what a class-name assertion cannot see.
 */
import { expect, test } from './fixtures/signora';

test.describe('§09 · the command palette', () => {
  test('@journey it is anchored at 14% of the viewport height and is 640px wide', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('/');

    await page.keyboard.press('Meta+k');
    const palette = page.getByRole('dialog');
    await expect(palette).toBeVisible();

    const box = await palette.boundingBox();
    expect(box, 'the palette has no geometry').toBeTruthy();

    // 📁 *"640px, anchored at 14vh, modal elevation."*
    expect(Math.round(box!.width)).toBe(640);
    expect(Math.round((box!.y / 900) * 100)).toBe(14);
  });
});

test.describe('§12 · the assistant drawer', () => {
  /**
   * 🔴 **The number the row listed as *verified* and which was never set.**
   *
   * ⚡ **`copilot.tsx` quoted §12's *"non-modal 420px drawer"* in its own
   * header and passed no width**, so the panel opened at whatever the shell
   * gave it. ⛔ **A test reading the doc comment would have agreed with the
   * row; a test reading the geometry does not.**
   */
  test('@journey it opens at the 420px the design states', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('/');

    await page.getByRole('button', { name: 'Ask Signora' }).click();
    const panel = page.getByRole('complementary', { name: 'Ask Signora' });
    await expect(panel).toBeVisible();

    const box = await panel.boundingBox();
    expect(Math.round(box!.width)).toBe(420);
  });
});
