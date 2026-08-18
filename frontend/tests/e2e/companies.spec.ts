/**
 * **A seller finds their book and opens a company** —
 * [TASK-440](../../../docs/BACKLOG.md).
 *
 * 📁 **The row's journey**: *"a seller opens Companies, filters to their own
 * book, searches a company by name, and opens it."*
 *
 * ⚠️ **Two of those four steps are not in this slice, and they are named rather
 * than quietly dropped.** 🔴 **`ListedAccount` publishes `account` and `kind`.
 * That is the whole contract** — **the browse read has no notion of who owns an
 * account**, so *filter to my book* has nothing to filter on, and search is a
 * different read that already ships in the top bar. ⛔ **Building either here
 * would mean inventing a field the platform does not publish**
 * ([§20c](../../../CLAUDE.md)), and the gap is
 * [C-289](../../../docs/LANE_COORDINATION.md).
 *
 * ✅ **So the journey is the part that exists end to end: reach it, read it,
 * open one.**
 */

import { expect, test } from './fixtures/signora';

test.describe('a seller reaches their whole book', () => {
  /**
   * 🔴 **The entrance, and it is the reason this screen could not ship before.**
   *
   * ⛔ **[C-229](../../../docs/LANE_COORDINATION.md) held it**: `/accounts` was
   * built, green on every other gate, and `make reachability` reported
   * *"NO ENTRANCE — built, and no screen leads here."* ✅ **The finalized design
   * settles it** — the App Shell's rail reads `… Accounts (8,412) …`, **the
   * exact row count this row cites** — and 📁
   * [D-141](../../../docs/DECISION_REGISTER.md) ① closed the item on that
   * evidence.
   *
   * ⚡ **This test is what keeps the entrance from being deleted by a later
   * navigation change without somebody noticing.**
   */
  test('🔴 the rail leads there, which is what C-229 was about', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('home')).toBeVisible();

    await page
      .getByRole('navigation', { name: 'Primary' })
      .getByRole('link', { name: 'Accounts' })
      .click();

    await expect(page).toHaveURL(/\/accounts$/);
    await expect(page.getByRole('heading', { name: 'Companies', level: 1 })).toBeVisible();
  });

  test('✅ the screen says what it is, in the customer’s words', async ({ page }) => {
    await page.goto('/accounts');

    // 📁 The design's own sentence, and ⛔ **`Organization` vocabulary rather
    // than `workspace`** ([ADR-0034](../../../docs/architecture/adr/0034-ubiquitous-language.md)).
    await expect(page.getByText(/every account you can see, in one surface/i)).toBeVisible();
  });

  /**
   * ⛔ **The screen must never claim a total it was not told.** 📁 The design
   * prints *"8,412 total · 312 in view"* and **the read publishes no total** —
   * ⚠️ **inventing one would fabricate the number a seller trusts most.**
   */
  test('⛔ it never prints a total the read did not publish', async ({ page }) => {
    await page.goto('/accounts');
    await expect(page.getByRole('heading', { name: 'Companies', level: 1 })).toBeVisible();

    await expect(page.getByText('8,412')).toHaveCount(0);
  });

  /**
   * 🔴 **Either state is correct, and the journey asserts that ONE of them is
   * reached** — never that the environment has rows.
   *
   * ⚠️ **A journey asserting *"the table has rows"* fails on a clean database
   * and passes on a seeded one, which makes it a test of the seeder.** ⛔ **What
   * must never happen is a THIRD outcome**: a blank screen, or an empty state
   * standing in for a failure.
   */
  test('✅ it reaches a designed state — rows or a stated empty book', async ({ page }) => {
    await page.goto('/accounts');
    await expect(page.getByRole('heading', { name: 'Companies', level: 1 })).toBeVisible();

    const table = page.getByRole('table');
    const empty = page.getByText('No companies yet');

    await expect(async () => {
      const reached = (await table.count()) + (await empty.count());
      expect(reached).toBeGreaterThan(0);
    }).toPass();

    // ⛔ **And never the failure state on a healthy stack** — 📁
    // [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md) works in both
    // directions: a stated absence rendered when nothing failed is its own lie.
    await expect(page.getByText(/could not load/i)).toHaveCount(0);
  });

  test('✅ a company opens from the list', async ({ page }) => {
    await page.goto('/accounts');
    await expect(page.getByRole('heading', { name: 'Companies', level: 1 })).toBeVisible();

    // ⚠️ **Wait for a designed state BEFORE counting, and this was a real
    // defect in the first version of this test.** ⛔ **It counted links
    // immediately, got `0` on a table that had not rendered yet, and skipped
    // itself** — **reporting a pass on the one step the journey exists to
    // prove.** ⚡ **A skip that fires on a timing race is indistinguishable
    // from a skip that fires on an empty environment**, which is exactly the
    // shape of guard [§2](../../../CLAUDE.md) calls documentation pretending
    // to be code.
    const table = page.getByRole('table');
    const empty = page.getByText('No companies yet');
    await expect(table.or(empty).first()).toBeVisible();

    const rows = table.getByRole('link');
    // ⚡ **Skipped rather than failed on a genuinely empty book** — ⛔ **a
    // journey that requires seeded rows is a test of the seeder**
    // ([§20e](../../../CLAUDE.md), *test data enters the way a customer's data
    // enters*).
    test.skip((await rows.count()) === 0, 'this environment has no resolved accounts');

    await rows.first().click();

    await expect(page).toHaveURL(/\/accounts\/[0-9a-f-]+$/);
  });
});
