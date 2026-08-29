/**
 * **§16 tier one — the frame paints complete and does not change shape** —
 * [TASK-1471](../../../docs/BACKLOG.md).
 *
 * 🔴 **Only a browser can answer this.** ⚡ **The property is about what a
 * customer sees BETWEEN two reads landing**, and jsdom has no paint and no
 * network. ⛔ **The defect this guards was measured here and nowhere else:
 * 6 → 7 → 8 destinations across one cold boot.**
 */
import { expect, test } from './fixtures/signora';

const RAIL = 'nav[aria-label="Primary"]';
const DESTINATIONS = `${RAIL} a[href^="/"], ${RAIL} [data-pending="true"]`;

test.use({ viewport: { width: 1280, height: 900 } });

test('🔴 the rail keeps its destination count while the workspace resolves', async ({ page }) => {
  const counts = new Set<number>();

  await page.goto('/', { waitUntil: 'commit' });

  // ⚡ **Sampled from the first frame that has a rail at all**, through to a
  // settled screen — ⛔ **not once at the end**, which is what let the shape
  // change go unnoticed.
  for (let i = 0; i < 25; i += 1) {
    const n = await page.locator(DESTINATIONS).count().catch(() => -1);
    if (n > 0) counts.add(n);
    await page.waitForTimeout(60);
  }

  await expect(page.getByRole('main')).toBeVisible();

  /**
   * 🔴 **`Home` is the rail's FIRST entry**, so a count that grows moves every
   * row beneath it. 📁 *"the frame is never blank, because the frame is the
   * same on every route."*
   *
   * ⚠️ **The set may still hold TWO values and that is [B-253](../../../docs/BUGS.md)**,
   * a separate defect with a product decision under it: a guarded destination
   * renders as a locked button until the ROLE resolves. ⛔ **This assertion is
   * about the workspace half and says so** — it allows the role transition and
   * would fail on a third value, which is what this row removed.
   */
  /**
   * ⛔ **The floor, and without it the ceiling is satisfied BEST by a rail
   * that never renders**, which is the ceiling-with-no-floor shape QE is filing.
   * ⚠️ **Their row id is not cited: it is on their branch and
   * `row-citations.test.tsx` refuses a row this tree cannot resolve.**
   *
   * ⚡ **`if (n > 0)` above is what makes that reachable**: zero is filtered
   * out of the population, so **a cold boot that painted no rail at all
   * contributes nothing, `counts` is empty, and `0 <= 2` passes.** ⚠️ **Fewer
   * distinct shapes is *better* by this measure and none is best of all** —
   * which is precisely the ordering that turns a budget into a guard that
   * cannot fail.
   *
   * ✅ **`toBeVisible()` on `main` above does not cover it**: the content
   * region and the rail are different elements, and 📁 *"the frame is never
   * blank"* is a claim about the frame.
   */
  expect(
    [...counts].length,
    'no frame ever carried a rail, so nothing was sampled — the assertion below ' +
      'would pass on a cold boot that never painted the frame',
  ).toBeGreaterThan(0);

  expect([...counts].length, `rail destination counts seen: ${[...counts]}`).toBeLessThanOrEqual(2);
});

test('✅ Home holds its place, and never as a broken link', async ({ page }) => {
  await page.goto('/', { waitUntil: 'commit' });

  // ⛔ **A `[workspace]` literal must never reach a link** — B-233 took the
  // whole navigation region down with exactly that.
  await expect(page.locator(`${RAIL} a[href*="[workspace]"]`)).toHaveCount(0);

  await expect(page.getByRole('main')).toBeVisible();
  await expect(page.locator(RAIL).getByRole('link', { name: 'Home' })).toHaveAttribute(
    'href',
    /^\/w\/[0-9a-f-]+\/home$/,
  );
});
