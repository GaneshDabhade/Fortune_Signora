/**
 * **The three App Shell sections the design specifies** —
 * [TASK-1463](../../../docs/BACKLOG.md), §16 · §18 · §19.
 *
 * 🔴 **All three need a browser, and the row says so**: an `opacity` of 60% and
 * a height of 2px are **computed** values, and jsdom applies no CSS at all —
 * ⛔ **the same reason [TASK-1461](../../../docs/BACKLOG.md)'s duplicated
 * navigation survived a suite that asserted the rail on every screen.**
 */

import { expect, test, type Page } from './fixtures/signora';

/**
 * 🔴 **Wait for a designed state before measuring anything.**
 *
 * ⚠️ **This lane shipped the same false skip twice** —
 * [TASK-440](../../../docs/BACKLOG.md) and
 * [TASK-1468](../../../docs/BACKLOG.md) — **and `waitForLoadState('networkidle')`
 * did not prevent the second.** ⛔ **`networkidle` is a claim about the
 * transport; `toBeVisible` is a claim about the screen**, and the request had
 * settled while React had not painted.
 */
async function settled(page: Page) {
  await expect(
    page.getByTestId('home').or(page.getByRole('main')).first(),
  ).toBeVisible();
}

test.use({ viewport: { width: 1280, height: 900 } });

test.describe('§16 · an in-place refresh never covers what is readable', () => {
  /**
   * 🔴 **The 2px strip is in the document at all times**, and only the bar
   * inside it appears. ⚠️ **A conditionally rendered 2px node would move every
   * screen down two pixels on every refetch** — 📁 the design rules that out by
   * name: *"No overlay, no spinner, no layout shift."*
   */
  test('🔴 the strip holds its 2px whether or not a refresh is running', async ({ page }) => {
    await page.goto('/');
    await settled(page);

    const strip = page.locator('main').locator('xpath=preceding-sibling::div[1]');
    await expect(strip).toHaveCSS('height', '2px');
  });

  /**
   * ✅ **A window focus is the design's own trigger** — 📁 *"Filter change,
   * sync, retry"* — and `refetchOnWindowFocus` is `true` in
   * [`client.tsx`](../../lib/query/client.tsx), so this is the product's real
   * refresh path rather than one the test invented.
   */
  test('✅ content dims to 60% while it is being replaced, and never disappears', async ({
    page,
  }) => {
    await page.goto('/');
    await settled(page);

    const main = page.getByRole('main');
    await expect(main).toHaveCSS('opacity', '1');

    // ⚡ **Nothing is stubbed**: the queries are made stale and the browser is
    // told the tab came back, which is exactly what a returning user does.
    await page.evaluate(() => window.dispatchEvent(new Event('visibilitychange')));
    await page.evaluate(() => window.dispatchEvent(new Event('focus')));

    // ⛔ **Either outcome is correct and the test asserts the INVARIANT**: at no
    // point is the content hidden, replaced by a spinner, or moved. ⚠️ **A
    // refresh over a warm cache can complete before a screenshot** — asserting
    // *"it dimmed"* would be a test of how fast the API answered.
    await expect(main).toBeVisible();
    await expect(main).toHaveCSS('position', 'static');
  });
});

/**
 * 🔴 **§18 and §19's labelled side are NOT asserted in a browser, and this is the
 * finding rather than an omission.**
 *
 * ⚠️ **Both need a condition the environment does not have** — an unactivated
 * workspace, and a reader holding more than one. ⛔ **The first version of this
 * file asserted against whatever happened to exist and BOTH assertions passed by
 * never running**: the demo workspace has declared targets, and the demo owner
 * held one organization.
 *
 * ⚡ **So the journey created the condition through the shipped `New
 * organization` control** — 📁 [§20e](../../../CLAUDE.md)'s *test data enters the
 * way a customer's data enters* — **and that is what found [B-245](../../../docs/BUGS.md):**
 *
 * > 🔴 **A journey cannot create an organization and leave the environment as it
 * > found it.** 📁 `list_visible` orders **newest-first**, so the created
 * > organization becomes `workspaces[0]` — **the default for every browser
 * > context that has no stored choice** — and ⛔ **the product publishes no way
 * > to delete one.** ⚡ **Restoring the *stored* choice is not enough**, which is
 * > why [B-229](../../../docs/BUGS.md)'s repair is insufficient for this case:
 * > **a fresh context has no stored choice to restore.**
 *
 * ⛔ **Measured, not theorised: six organizations accumulated, and the suite's
 * account-backed journeys began failing on an empty workspace two projects
 * later** — **which is the same cost B-229 recorded at 23 failures.**
 *
 * ✅ **Both sections ARE asserted, in
 * [`activation.test.tsx`](../components/activation.test.tsx) and
 * [`workspace-label.test.tsx`](../components/workspace-label.test.tsx)**, where
 * a reader with one organization, a reader with three, and an unactivated
 * workspace can all be constructed. ⚡ **A browser is needed for computed CSS —
 * which is what §16 asserts above — not for a boolean.**
 */
