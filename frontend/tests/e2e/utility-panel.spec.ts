import { expect, test } from '@playwright/test';

/**
 * **The utility panel** — [TASK-1433](../../../docs/BACKLOG.md).
 *
 * ## 🔴 What this journey is for, and it is the row's own risk
 *
 * > ⚠️ ***"Building the chrome because it is the easy half. The chrome is not
 * > the deliverable."***
 *
 * ⛔ **So this does not assert that a panel slides.** ✅ **It walks the row's
 * Definition of Done**: *"the panel docks at both widths, pushes content
 * rather than covering it, `⌘.` toggles it, and the Activity tab renders
 * `AccountHistory` on the account record."*
 *
 * ⚡ **A browser is the only place three of those four can be checked at all** —
 * jsdom has no layout, so *pushes rather than covers* and *both widths* have no
 * answer there.
 */
/**
 * ⚡ **Opens an account by DEEP LINK, and that is not a shortcut.**
 *
 * ⚠️ **Clicking through from the attention list raced the panel's own rule.**
 * 📁 The panel *"remembers its open state per module"* — ⛔ **so `⌘.` pressed in
 * the moments after a route change toggles the module being LEFT, and the
 * arriving module then applies its own memory and closes it again.** ✅ **That
 * is the feature working**; the test was pressing a key while the screen was
 * still changing, which nobody does.
 *
 * 📁 **And a deep link is the realistic entry anyway** — the design's own
 * reason for mandatory breadcrumbs: *"most sessions start from a deep link in
 * Slack or email."*
 */
async function openAnAccount(page: import('@playwright/test').Page): Promise<void> {
  await page.goto('/');
  const href = await page.locator('main a[href^="/accounts/"]').first().getAttribute('href');
  await page.goto(href!);
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
}

test('@journey the panel docks on an account, and its Activity tab is the real history', async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await openAnAccount(page);

  const panel = page.getByRole('complementary');

  /**
   * 🔴 **Exactly one complementary landmark** — [B-234](../../../docs/BUGS.md).
   * ⚠️ **There were two**: the rail's wrapper was an `<aside>`, and the design
   * gives that role to the panel alone. ⛔ **Playwright found it as *"intercepts
   * pointer events"***, which is the least likely message to lead anybody to an
   * accessibility defect.
   */
  await expect(panel).toHaveCount(1);

  // 📁 *"1024–1279 — utility panel closes to a 28px tab rail"*, and the stored
  // preference starts closed, so the reference width opens as a tab rail too.
  await expect(panel).toHaveAttribute('data-state', 'tab-rail');

  // 📁 **`⌘.` — *"Toggle utility panel"***, from the design's own shortcut map.
  await page.keyboard.press('Meta+.');
  await expect(panel).toHaveAttribute('data-state', 'open');

  await panel.getByRole('tab', { name: 'Activity' }).click();

  // 📁 *"`aside[complementary]` — labelled with its active tab."*
  await expect(panel).toHaveAttribute('aria-label', 'Activity panel');

  /**
   * 🔴 **The deliverable.** ⛔ **Not that a tab is selected — that a MODULE
   * published into it**, which is the only assertion the row would accept.
   *
   * ⚡ **Asserted as *the panel's own empty state is absent*** rather than by
   * matching a month name: ⛔ **the seeded history's dates move with the seed**,
   * and a test that hunts for `AUGUST` fails in September for no reason.
   * ✅ **`AccountHistory` owns every one of its states — history, empty,
   * loading and error — so if the panel is not showing ITS placeholder, the
   * account's component is what is in there.**
   */
  await expect(panel.getByText(/Nothing on this screen keeps a history yet/i)).toHaveCount(0);
  await expect(panel.getByRole('tabpanel')).toContainText(/./);

  /**
   * ⛔ **And it is not ALSO in the page body.** ⚡ **One component, one data
   * source, one placement** — the section that used to render it stands down
   * when the panel is carrying it.
   */
  await expect(page.getByRole('heading', { name: 'What has happened' })).toHaveCount(0);
});

test('@journey the panel PUSHES the content rather than covering it', async ({ page }) => {
  /**
   * 📁 **The design's word is *"pushes content"***, and ⚠️ **the first
   * implementation did not**: the provider rendered the panel outside the
   * frame's flex row, so it floated after the page and the rail's `Settings`
   * link sat on top of its tabs.
   *
   * ⛔ **A component test cannot see this.** ✅ **Two boxes and one comparison
   * can**: the content region must end where the panel begins, and must be
   * narrower with the panel open than with it closed.
   */
  await page.setViewportSize({ width: 1440, height: 1000 });
  await openAnAccount(page);

  const main = page.getByRole('main');
  const closed = (await main.boundingBox())?.width ?? 0;

  await page.keyboard.press('Meta+.');
  const panel = page.getByRole('complementary');
  await expect(panel).toHaveAttribute('data-state', 'open');

  /**
   * ⚠️ **Wait for the WIDTH, not for the state.** ⛔ **`data-state` flips a
   * frame before the 150ms width transition finishes**, and a box read in
   * between reports a panel that is neither 28 nor 300 — **which produced a
   * failure that looked like an overlap and was a stopwatch.**
   */
  await expect
    .poll(async () => Math.round((await panel.boundingBox())?.width ?? 0))
    .toBeGreaterThanOrEqual(300);

  const opened = (await main.boundingBox())?.width ?? 0;
  const panelBox = await panel.boundingBox();
  const mainBox = await main.boundingBox();

  expect(opened, 'the content did not narrow, so the panel is covering it').toBeLessThan(closed);
  // ⚡ **No overlap**: the panel starts at or after the content's right edge.
  expect(panelBox!.x).toBeGreaterThanOrEqual(mainBox!.x + mainBox!.width - 1);
});

test('@journey the panel is ABSENT on a phone, and the history is still on the page', async ({
  page,
}) => {
  /**
   * 🔴 **The rule that makes the panel safe to dock into.** 📁 The design gives
   * the panel no width below 1024 — ⛔ **and it never says the CONTENT
   * disappears, only the panel.** ⚠️ **A module that put its only copy of
   * something in the panel would lose it entirely on a phone**, which is the
   * defect this asserts cannot happen.
   */
  await page.setViewportSize({ width: 390, height: 900 });
  await openAnAccount(page);

  await expect(page.getByRole('complementary')).toHaveCount(0);
  await expect(page.getByRole('heading', { name: 'What has happened' })).toBeVisible();
});
