/**
 * **The rail at the 1280 boundary** — [TASK-1473](../../../docs/BACKLOG.md),
 * 📁 [D-233](../../../docs/DECISION_REGISTER.md) rule ⓐ.
 *
 * > ✅ ***At 1024–1279 the band forces the rail to 56px. At ≥1280 the user's
 * > stored per-device-class preference decides.***
 *
 * ## 🔴 Why this is a journey and not a unit test
 *
 * ⚡ **The rule is about GEOMETRY at a viewport width**, and the row asks for
 * it two-sided in exactly those terms: *"the assertion must fail at 232px@1279
 * **and** at 56px@1280."* ⛔ **jsdom has no layout** — `tests/unit/rail.test.ts`
 * proves the pure rule, and **only a browser can say what the rail actually
 * measures.** 📁 The same distinction [TASK-1475](../../../docs/BACKLOG.md)
 * recorded: *"what a browser proved and jsdom could not — compact density
 * makes rows shorter, measured as geometry."*
 *
 * ## ⚠️ One pixel apart, on purpose
 *
 * ⛔ **1279 and 1280 are the assertion.** ⚡ **A test at 1100 and 1400 would
 * pass against a boundary placed anywhere between them**, and the boundary is
 * the whole of what was ruled.
 */

import { expect, test } from './fixtures/signora';

/** 📁 `RAIL_WIDTH = { expanded: 232, collapsed: 56 }` — the design's pair. */
const EXPANDED = 232;
const COLLAPSED = 56;

async function railWidth(page: import('@playwright/test').Page): Promise<number> {
  const rail = page.getByRole('navigation', { name: 'Primary' });
  await expect(rail).toBeVisible();
  // ⚡ **The rail element itself carries the width**, and the box is measured
  // rather than the style read — a style that never took effect would still
  // read back correctly.
  const box = await rail.locator('xpath=ancestor-or-self::*[@data-collapsed][1]').boundingBox();
  return Math.round(box?.width ?? 0);
}

test.describe('the band decides the rail below 1280, and the person decides above it', () => {
  test('🔴 at 1279 the rail is collapsed however it was left', async ({ page }) => {
    /**
     * ⛔ **The forced side.** 📁 The evidence it is forced rather than default
     * is the utility panel: the same band entry carries `panelDisplay: 'none'`,
     * **overriding that component's own persisted preference.**
     */
    await page.setViewportSize({ width: 1279, height: 900 });
    await page.goto('/');

    expect(await railWidth(page)).toBe(COLLAPSED);
  });

  test('🔴 at 1280 the rail is the person’s to decide', async ({ page }) => {
    /**
     * ⚡ **The other side, and it is what stops the fix from over-reaching.**
     * ⛔ **A rail collapsed everywhere would pass the test above and be just as
     * wrong** — the preference does real work between Laptop and Desktop, and
     * a customer who has never collapsed it must see 232px.
     */
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('/');

    expect(await railWidth(page)).toBe(EXPANDED);
  });

  test('✅ the collapse control is absent where it would change nothing', async ({
    page,
  }) => {
    /**
     * ⛔ **Absent, never disabled.** ⚡ **At 1024–1279 a toggle would report
     * success for nothing**, and the repository's own rule is that a control
     * which goes nowhere costs more trust than an absent one.
     */
    await page.setViewportSize({ width: 1279, height: 900 });
    await page.goto('/');
    await expect(page.getByRole('navigation', { name: 'Primary' })).toBeVisible();

    await expect(page.getByRole('button', { name: /navigation$/ })).toHaveCount(0);
  });

  test('✅ and it is offered again at 1280', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('/');
    await expect(page.getByRole('navigation', { name: 'Primary' })).toBeVisible();

    await expect(page.getByRole('button', { name: 'Collapse navigation' })).toBeVisible();
  });
});
