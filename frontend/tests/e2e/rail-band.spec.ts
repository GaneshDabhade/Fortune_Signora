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

/**
 * 🔴 **A single `boundingBox()` here samples a FRAME, not a width** —
 * [B-1032](../../../docs/BUGS.md).
 *
 * 📁 `app-shell.tsx` carries `smalllaptop:transition-[width]
 * smalllaptop:duration-150`, and the rail's width genuinely changes after
 * hydration: **the server renders it expanded** — its own comment says so —
 * **and the band collapses it on the client.** ⛔ So a read taken on arrival
 * races a 150ms clock, and **a loaded machine loses more often.** QE measured
 * `232 · 109 · 85 · 61` against an expected `56` and reported it to Lane A as
 * a possible product defect; **those were four frames of one animation, and
 * the product was right every time.**
 *
 * ## ⛔ Not a `waitForTimeout`, and not `reducedMotion` either
 *
 * ⚡ **This waits for the thing.** Two waits, and they answer different
 * questions:
 *
 * ① **`data-collapsed` is the STATE the width follows** — React's, applied
 *    once the band has been evaluated on the client. Waiting for it is what
 *    distinguishes *"the rail is 232 because the band has not run yet"* from
 *    *"the rail is 232 because the band decided so"*, ⛔ **which is exactly
 *    what the old read could not tell apart.**
 * ② **Then the width has to STOP MOVING** — two consecutive animation frames
 *    agreeing. ⛔ **It is never assumed settled after an interval;** a rail
 *    that never settles hangs the test, which is the honest outcome.
 *
 * ⚠️ **`reducedMotion: 'reduce'` would also work** — 📁 `globals.css` forces
 * `transition-duration: 0.01ms` globally under it, so the animation would not
 * exist to be sampled. ⛔ **Rejected deliberately: it measures the geometry in
 * a mode most customers are not in**, and the claim under test is what the
 * rail is for everybody.
 *
 * ✅ **The assertion it feeds stays an exact `toBe`.** Settling does not make
 * this pass more easily — a rail that comes to rest at the wrong width fails,
 * and reports the width it came to rest at rather than a frame of the way
 * there.
 */
async function settledRailWidth(
  page: import('@playwright/test').Page,
  { collapsed }: { collapsed: boolean },
): Promise<number> {
  const rail = page.getByRole('navigation', { name: 'Primary' });
  await expect(rail).toBeVisible();
  // ⚡ **The rail element itself carries the width**, and the box is measured
  // rather than the style read — a style that never took effect would still
  // read back correctly.
  const element = rail.locator('xpath=ancestor-or-self::*[@data-collapsed][1]');

  await expect(
    element,
    `the rail never reached data-collapsed=${collapsed}`,
  ).toHaveAttribute('data-collapsed', String(collapsed));

  return element.evaluate(
    (node) =>
      new Promise<number>((resolve) => {
        let previous = Number.NaN;
        const sample = () => {
          const width = node.getBoundingClientRect().width;
          if (width === previous) {
            resolve(Math.round(width));
            return;
          }
          previous = width;
          requestAnimationFrame(sample);
        };
        requestAnimationFrame(sample);
      }),
  );
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

    expect(await settledRailWidth(page, { collapsed: true })).toBe(COLLAPSED);
  });

  /**
   * 🔴 **"However it was left" — and until now nothing had left it anything.**
   *
   * ⚠️ **The test above runs on a profile with no stored preference**, so it
   * asserted that a rail nobody had touched was collapsed. ⛔ **That is the
   * default, not the override**, and the override is the whole claim: 📁 the
   * band decides *below* 1280 regardless of what the person chose above it.
   *
   * ⚡ **So this leaves it expanded the way a person does** — the control at
   * 1280, which the last test in this file proves is there — **and then crosses
   * the band.** ⛔ No `localStorage` poke: the preference is written by the
   * product, under whatever key the product uses, which is the only version of
   * this that cannot drift from it.
   *
   * ⚠️ **Where this came from, and it is worth keeping.** On 2026-08-19 QE
   * measured `232` here on `main`, three isolated runs on a rebuilt
   * environment; Lane A measured `56`, three runs, on a tree whose only shell
   * change is a shortcut-registry entry. ⛔ **Both were reading a test that
   * never stored a preference** — so both were measuring the default and
   * neither was measuring the override, and **nothing in the assertion could
   * have told them apart.** ✅ This one can.
   */
  test('🔴 and it is collapsed even when the person left it OPEN above the band', async ({
    page,
  }) => {
    // Above the band, where the choice is the person's.
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('/');
    await expect(page.getByRole('navigation', { name: 'Primary' })).toBeVisible();

    // ⚡ **Make sure it is genuinely OPEN before crossing** — the control is a
    // toggle, so acting without checking could close it and prove nothing.
    if (await page.getByRole('button', { name: 'Expand navigation' }).isVisible()) {
      await page.getByRole('button', { name: 'Expand navigation' }).click();
    }
    await expect(page.getByRole('button', { name: 'Collapse navigation' })).toBeVisible();
    expect(
      await settledRailWidth(page, { collapsed: false }),
      'the rail was not left open above the band',
    ).toBe(EXPANDED);

    // Cross the band. Same session, same stored preference.
    await page.setViewportSize({ width: 1279, height: 900 });
    await page.goto('/');

    expect(await settledRailWidth(page, { collapsed: true })).toBe(COLLAPSED);
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

    expect(await settledRailWidth(page, { collapsed: false })).toBe(EXPANDED);
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
