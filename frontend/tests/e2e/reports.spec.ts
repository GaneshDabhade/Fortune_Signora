import { expect, test } from '@playwright/test';

/**
 * **Reports** — [TASK-1417](../../../docs/BACKLOG.md).
 *
 * > 📁 ***"Built once, read three ways — screen, presentation and board
 * > pack."***
 *
 * ## 🔴 What this journey is actually for
 *
 * ⛔ **A component test proves the screen renders what it was given.** ⚡ **It
 * cannot prove the route RESOLVES**, and this repository has measured that
 * distinction twice: 📁 **eighteen of the entry engine's twenty-four
 * destinations returned `404`** while every unit test was green
 * ([500](../../../docs/architecture/500-authenticated-entry-reconciliation.md) §3).
 *
 * ⚠️ **So the first assertion is the one that matters: the door opens.**
 *
 * ## ⛔ And the second is that it opens onto something honest
 *
 * 📁 **The design's screen is a Q3 board pack full of figures a query engine
 * would produce, and there is no query engine.**
 * 🔴 **[§20c](../../../CLAUDE.md): *"Never introduce mock business data.
 * Screens without a shipped module behind them ship a designed empty
 * state."*** ⚡ **A browser is where that is worth re-checking**, because a
 * figure could arrive from a layout, a cached fixture or a stray import that
 * a component test rendering one component in isolation would never see.
 */
test('@journey Reports opens, and shows a designed empty state rather than invented figures', async ({
  page,
}) => {
  /**
   * 🔴 **Entered through the rail, not by typing the URL.**
   *
   * ⚠️ **This lane first shipped the route with NO rail entry**, reasoning that
   * an entry leading to an empty state repeats M12.3's *"coming soon"*.
   * ⛔ **`reachability.py` refused it** — *"no entrance at all: 1 ← every one
   * is a defect"* — **and it was right: a route a customer cannot reach is a
   * route that does not exist.** ⚡ **So the door is walked here rather than
   * assumed**, the way [`signal-center.spec.ts`](signal-center.spec.ts) walks
   * its own.
   */
  await page.goto('/');
  await page.getByRole('navigation', { name: 'Primary' }).getByRole('link', { name: 'Reports' }).click();
  await expect(page).toHaveURL(/\/reports$/);

  // 🔴 **The route resolves.** A `404` here is the failure eighteen entry
  // destinations had while their unit tests passed.
  await expect(page.getByRole('heading', { name: 'Reports', level: 1 })).toBeVisible();
  await expect(page.getByText(/built once, read three ways/i)).toBeVisible();

  // ⚡ **The designed empty state**, and its description — §20c's requirement
  // is a *designed* one, so a title alone would not satisfy it.
  await expect(page.getByText('No reports yet')).toBeVisible();
  await expect(page.getByText(/every block on it inherits that question/i)).toBeVisible();

  /**
   * ⛔ **None of the design's illustrative figures reaches a customer.**
   * 📁 Each is from `Fortune Signora Reports.dc.html`, named literally so a
   * reader can check the list against the file rather than trusting a regex.
   */
  const body = page.locator('body');
  for (const invented of ['$42.8M', '3,104', 'Vantage renewal', 'Q3 board pack']) {
    await expect(body, invented).not.toContainText(invented);
  }
});

/**
 * ✅ **The half of this screen that is true today.**
 *
 * 📁 **The chart library is finalized product copy about what Signora draws**,
 * and ⛔ **it contains no customer data at all** — which is precisely why it
 * can ship while the board pack cannot.
 */
test('@journey the chart library names the eight, and the three the product refuses', async ({
  page,
}) => {
  await page.goto('/reports');

  await expect(page.getByRole('heading', { name: 'Chart library', level: 2 })).toBeVisible();

  // 📁 The design's eight, each paired with the shape it suits — the pairing
  // is the content, so both halves are asserted.
  await expect(page.getByText('Signed contributions to one total')).toBeVisible();
  await expect(page.getByText('Actual against required, same axes')).toBeVisible();

  // 📁 *"No doughnuts, no dual axes, no 3D"* — the design says it out loud, so
  // the screen does too rather than leaving it as an absence.
  await expect(page.getByText(/no doughnuts, no dual axes, no 3d/i)).toBeVisible();
});
