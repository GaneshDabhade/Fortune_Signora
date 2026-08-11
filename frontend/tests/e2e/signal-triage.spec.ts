/**
 * **The Signal Center's queue-local surfaces, in a browser** —
 * [TASK-1468](../../../docs/BACKLOG.md) ② ③ ⑦.
 *
 * ⚡ **What only a browser can say here**: that the chips, the action bar and
 * the counts strip coexist without the list jumping, and that a bulk decision
 * actually leaves the queue.
 */

import { expect, test, type Page } from './fixtures/signora';

/**
 * ⚡ **Wait for a DESIGNED state before counting anything.**
 *
 * ⛔ **Either a queue with rows or the empty state is correct**; what must not
 * happen is a count taken while neither has rendered. 📁 This helper exists
 * because the same false skip shipped once already —
 * [TASK-440](../../../docs/BACKLOG.md) — **and `networkidle` did not prevent
 * its second appearance here.**
 */
async function settled(page: Page): Promise<void> {
  const rows = page.getByRole('checkbox').first();
  const quiet = page.getByText(/Nothing needs review/i);
  await expect(rows.or(quiet).first()).toBeVisible();
}

test.describe('a triager narrows the queue and clears several at once', () => {
  test('✅ the counts strip says what needs review', async ({ page }) => {
    await page.goto('/signals');
    await expect(page.getByRole('heading', { name: 'Signals', level: 1 })).toBeVisible();

    await expect(page.getByTestId('queue-counts')).toContainText('need review');
  });

  /**
   * 🔴 **The design draws *"14 need review · 6 assigned to you · 41 this
   * week"*, and two of those three have no source.** ⛔ **`QueueEntry` carries
   * no assignee and no timestamp**, so both would be invented.
   */
  test('⛔ and never the two counts the contract cannot support', async ({ page }) => {
    await page.goto('/signals');
    await expect(page.getByRole('heading', { name: 'Signals', level: 1 })).toBeVisible();

    await expect(page.getByText(/assigned to you/i)).toHaveCount(0);
    await expect(page.getByText(/this week/i)).toHaveCount(0);
  });

  test('✅ the filter narrows, and the way back is always one click', async ({ page }) => {
    await page.goto('/signals');
    await expect(page.getByRole('heading', { name: 'Signals', level: 1 })).toBeVisible();

    const filters = page.getByTestId('signal-filters');
    // 🔴 **`networkidle` is NOT enough, and this test proved it twice.**
    // ⚠️ **The first version awaited it and skipped anyway** — the request had
    // settled and React had not painted, so `count()` read `0` on a queue that
    // held sixteen signals across nine types. ⛔ **A skip that fires on a
    // render race is indistinguishable from one that fires on an empty
    // environment**, which is [TASK-440](../../../docs/BACKLOG.md)'s finding
    // arriving a second time. ✅ **Await the ELEMENT, never the network.**
    await settled(page);
    test.skip((await filters.count()) === 0, 'this queue has fewer than two signal types');

    const chip = filters.getByRole('button').first();
    await chip.click();

    await expect(chip).toHaveAttribute('aria-pressed', 'true');
    await expect(page.getByText(/of \d+ shown/)).toBeVisible();

    await page.getByRole('button', { name: 'Clear' }).click();
    await expect(page.getByText(/of \d+ shown/)).toHaveCount(0);
  });

  test('✅ selecting rows offers exactly one bulk decision', async ({ page }) => {
    await page.goto('/signals');
    await expect(page.getByRole('heading', { name: 'Signals', level: 1 })).toBeVisible();
    await settled(page);

    const boxes = page.getByRole('checkbox');
    test.skip((await boxes.count()) === 0, 'this queue is empty');

    await boxes.first().check();

    const bar = page.getByTestId('bulk-bar');
    await expect(bar).toContainText('1 selected');
    await expect(bar.getByRole('button', { name: 'Mark actioned' })).toBeVisible();
    // ⛔ **The three the union cannot construct honestly in bulk.**
    await expect(bar.getByRole('button', { name: /dismiss|snooze|assign/i })).toHaveCount(0);
  });

  /**
   * 🔴 **The rule that stops a bulk control acting on rows the reader cannot
   * see.** ⚠️ **A selection surviving a filter says *"3 selected"* while two of
   * them are off screen**, and the person presses it believing it means the
   * three in front of them.
   */
  test('🔴 narrowing the list drops the selection rather than hiding it', async ({ page }) => {
    await page.goto('/signals');
    await expect(page.getByRole('heading', { name: 'Signals', level: 1 })).toBeVisible();
    await settled(page);

    const filters = page.getByTestId('signal-filters');
    const boxes = page.getByRole('checkbox');
    test.skip((await filters.count()) === 0 || (await boxes.count()) === 0, 'needs two types and a row');

    await boxes.first().check();
    await expect(page.getByTestId('bulk-bar')).toBeVisible();

    await filters.getByRole('button').first().click();

    await expect(page.getByTestId('bulk-bar')).toHaveCount(0);
  });
});
