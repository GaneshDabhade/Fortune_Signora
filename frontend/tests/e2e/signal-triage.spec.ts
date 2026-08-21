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
    // 🔴 **CORRECTED — this said *"the three the union cannot construct
    // honestly in bulk"*, and that is no longer the reason for two of them.**
    // 📁 The design's `bulkActions` are *Assign · Snooze · Dismiss · Bookmark*,
    // and **the per-signal snooze and assign now exist**, so bulk versions are
    // constructible. ⛔ **They are out of this slice's scope, not out of the
    // contract's reach** — 📁 bulk dismissal's refusal still stands on its own
    // product argument, and `Bookmark` still has no producer. **The gap is
    // [C-292](../../../docs/LANE_COORDINATION.md).**
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


/**
 * 🔴 **The four exits the screen's own description promises** —
 * 📁 *"Every one leaves the queue by being actioned, **assigned**, **snoozed**
 * or dismissed with a reason."*
 *
 * ⚡ **What only a browser can say here**: that a snooze **produces a state the
 * Snoozed view can surface.** ⛔ **A component test can prove the dialog sends
 * `{kind:'snoozed'}`; it cannot prove the signal actually arrives in the other
 * tab with its return date** — and a navigation destination whose state nothing
 * can produce is the dead end this slice exists to close.
 */
test.describe('a triager routes and defers, not only closes', () => {
  test('🔴 every exit the description promises has a control', async ({ page }) => {
    await page.goto('/signals');
    await expect(page.getByRole('heading', { name: 'Signals', level: 1 })).toBeVisible();
    await settled(page);

    const rows = page.getByRole('listitem');
    test.skip((await rows.count()) === 0, 'this queue is empty');

    const row = rows.first();
    for (const name of ['Act on it', 'Assign', 'Snooze', 'Dismiss']) {
      await expect(row.getByRole('button', { name, exact: true })).toBeVisible();
    }
  });

  /**
   * ⚡ **The whole loop, end to end**: defer a signal with a date, then find it
   * in the view that exists to show deferred signals — **saying when it comes
   * back**, which is 📁 `Resolution.snoozed_until` and not a guess.
   */
  test('🔴 a snoozed signal leaves the queue and returns a date in the Snoozed view', async ({
    page,
  }) => {
    await page.goto('/signals');
    await expect(page.getByRole('heading', { name: 'Signals', level: 1 })).toBeVisible();
    await settled(page);

    const rows = page.getByRole('listitem');
    test.skip((await rows.count()) === 0, 'this queue is empty');

    const before = await rows.count();
    await rows.first().getByRole('button', { name: 'Snooze', exact: true }).click();

    const confirm = page.getByRole('button', { name: 'Snooze signal' });
    // ⛔ **Nothing is submittable until a date is named.**
    await expect(confirm).toBeDisabled();

    const soon = new Date();
    soon.setDate(soon.getDate() + 7);
    const day = soon.toISOString().slice(0, 10);
    await page.getByLabel('Comes back on').fill(day);
    await expect(confirm).toBeEnabled();
    await confirm.click();

    // ⚡ **The dialog closes on SUCCESS, never on the click** — so its
    // disappearance is evidence the write landed.
    await expect(confirm).toHaveCount(0);
    await expect(rows).toHaveCount(before - 1);

    await page.getByRole('tab', { name: 'Snoozed' }).click();
    await expect(page.getByText(/^Returns /).first()).toBeVisible();
  });

  /**
   * 🔴 **📁 `resolution.py`: *"Still open. Assigning is routing, not
   * resolving."*** ⛔ **So the row stays** — and the chip is the only evidence
   * the reader has that the control did anything at all.
   */
  test('🔴 an assigned signal stays in the queue, under a name', async ({ page }) => {
    await page.goto('/signals');
    await expect(page.getByRole('heading', { name: 'Signals', level: 1 })).toBeVisible();
    await settled(page);

    const rows = page.getByRole('listitem');
    test.skip((await rows.count()) === 0, 'this queue is empty');

    await rows.first().getByRole('button', { name: 'Assign', exact: true }).click();

    const confirm = page.getByRole('button', { name: 'Assign signal' });
    const picker = page.getByLabel('Colleague');

    // ⚠️ **A workspace of one is a designed state, not a broken dialog** — 📁
    // `colleaguesFrom` offers only members whose membership carries an address.
    if ((await picker.count()) === 0) {
      await expect(page.getByText(/nobody else here to assign this to/i)).toBeVisible();
      return;
    }

    await expect(confirm).toBeDisabled();
    await picker.selectOption({ index: 1 });
    await expect(confirm).toBeEnabled();
    await confirm.click();

    await expect(confirm).toHaveCount(0);
    // ⚡ **Still here, and now it says who owns the decision.**
    await expect(page.getByText(/^Assigned to /).first()).toBeVisible();
  });
});
