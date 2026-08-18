/**
 * **The nine screens draw their width from the primitive** —
 * [TASK-1464](../../../docs/BACKLOG.md).
 *
 * 🔴 **Measured at 1280 AND at 2400**, which the row insists on and explains:
 * ⛔ ***"1280 alone passes on a screen that has no maximum at all."***
 *
 * ⚡ **The two viewports test opposite failures.** **At 1280 a screen that kept
 * its fixed `max-w-3xl` looks almost right**; **at 2400 a screen with no
 * constraint at all runs to the edge of the monitor.** ✅ **Only a screen
 * inheriting the primitive passes both.**
 */
import { expect, test } from './fixtures/signora';

/**
 * 📁 **The design's numbers** — *"12-column grid, 24px gutters"* — applied to
 * **the content region's own measured width.**
 *
 * ⚠️ **The first version of this computed the expectation from the VIEWPORT and
 * was wrong by 183px at 1280.** 🔴 **The content region is not the viewport**:
 * the rail takes 232px beside it, and at 2400 the container's own 1600px
 * maximum hides that entirely — **so the arithmetic agreed at one viewport and
 * disagreed at the other, which is exactly the trap the row's two-viewport
 * rule exists to catch.**
 *
 * ✅ **Deriving from the measured container states the real claim**: *eight of
 * the twelve tracks of whatever the content region is*, ⛔ **and it stops the
 * test encoding an assumption about the shell's chrome.**
 */
function expectedWidth(containerWidth: number): number {
  const inner = containerWidth - 48; // 📁 24px gutter each side
  const track = (inner - 11 * 24) / 12;
  return 8 * track + 7 * 24;
}

const SCREENS = [
  /**
   * ⚠️ **`/attention`, and it was never Home.** 📁 The Authenticated Entry
   * document gives `/` to the shell's resolver, so `/` no longer renders a
   * product surface at all — **but this row measured the ATTENTION screen's
   * reading column the whole time**, because that is what used to live there.
   *
   * ⛔ **Renaming it to Home would be worse than leaving it wrong.** 📁 Home is
   * a card composition with its own cap (contract 21, *"content is capped at
   * 1360px"*), **not the eight-of-twelve reading measure this file asserts** —
   * `Columns` has exactly one consumer, `reading-column.tsx`, and Home is not
   * it. **The row is corrected to name the screen it actually measures.**
   */
  { path: '/attention', name: 'Attention' },
  { path: '/business', name: 'Business' },
  { path: '/help', name: 'Help' },
  { path: '/settings', name: 'Settings' },
  { path: '/settings/team', name: 'Team' },
  { path: '/settings/products', name: 'Products' },
  { path: '/settings/organization', name: 'Organization' },
  { path: '/settings/connections', name: 'Connections' },
];

for (const viewport of [1280, 2400]) {
  test.describe(`at ${viewport}`, () => {
    for (const screen of SCREENS) {
      test(`@journey ${screen.name} is eight columns of the design's grid`, async ({ page }) => {
        await page.setViewportSize({ width: viewport, height: 900 });
        await page.goto(screen.path);

        const column = page.locator('[data-testid="content-columns"] > div').first();
        await expect(column).toBeVisible();

        const container = await page.getByTestId('content-container').boundingBox();
        const box = await column.boundingBox();
        // ⚡ **±2px for sub-pixel track rounding**, which the browser does and
        // the arithmetic above does not.
        expect(Math.abs(box!.width - expectedWidth(container!.width))).toBeLessThanOrEqual(2);
      });
    }

    /**
     * ⛔ **And the container above it never exceeds the design's maximum.**
     * ⚡ **At 2400 this is the assertion that matters** — 📁 *"1600px content
     * maximum"*, and a screen with no cap would report 2400 here.
     */
    test(`@journey the content region stops at 1600 at ${viewport}`, async ({ page }) => {
      await page.setViewportSize({ width: viewport, height: 900 });
      await page.goto('/settings');

      const box = await page.getByTestId('content-container').boundingBox();
      expect(box!.width).toBeLessThanOrEqual(1600);
    });
  });
}
