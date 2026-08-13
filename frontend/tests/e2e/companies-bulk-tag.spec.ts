/**
 * **A seller labels several companies at once** — [TASK-466](../../../docs/BACKLOG.md).
 *
 * 📁 **The row's journey**: *"a seller applies a batch to three companies and
 * reverses one — the reversal is the half that is normally untested."*
 *
 * ## ⚠️ Two of those steps are not reachable from a screen, and they are named
 *
 * 🔴 **There is no approval surface.** ⛔ A proposed batch is approved and
 * applied through `action_batch`'s endpoints — **which
 * [TASK-466](../../../docs/BACKLOG.md) itself added this cycle**, because
 * before that there was no route at all — **but no screen calls them.** 📁 The
 * approved design for Companies draws the bulk bar and no approvals inbox, and
 * ⛔ **inventing one would be a customer journey this lane made up**
 * ([D-156](../../../docs/DECISION_REGISTER.md) ⑥: *do not invent alternative
 * user experiences*).
 *
 * ⚡ **So the journey here is the part a customer can actually drive**: select
 * companies, name a label, propose it, and be told plainly that nothing has
 * happened yet. 📁 **The approve→apply→reverse half is proven at the API and
 * in the handlers** — `test_api_action_batch.py` and
 * `test_tag_batch_handlers.py` — **and the gap is
 * [C-1507](../../../docs/LANE_COORDINATION.md).**
 *
 * ⛔ **This is a declared absence, not a passing test that implies more than it
 * checked.**
 */

import type { Page } from '@playwright/test';

import { expect, test } from './fixtures/signora';

/**
 * 🔴 **Wait for the table, and never for a count.**
 *
 * ⛔ **`getByRole('row').count()` answers `0` while the read is in flight**,
 * so a `test.skip(count < 2)` guard reports *"no companies"* about a workspace
 * holding twelve — 📁 **exactly the race [B-262](../../../docs/BUGS.md) was
 * filed against and then withdrawn for**, where the instrument was wrong and
 * the page was truthful.
 *
 * ⚡ **So this waits for the checkbox the header only renders once rows
 * exist**, and a genuinely empty workspace fails on a timeout that says so
 * rather than passing as a skip.
 */
async function ready(page: Page): Promise<void> {
  await expect(page.getByRole('heading', { name: 'Companies', level: 1 })).toBeVisible();
  await expect(
    page.getByRole('checkbox', { name: 'Select the companies on this page' }),
  ).toBeVisible();
}

test.describe('a seller labels several companies at once', () => {
  test('🔴 selecting companies raises the bar, and it says how many', async ({
    page,
  }) => {
    // ⚡ **No sign-in call.** 📁 The `[owner]` project carries the storage
    // state, exactly as `companies.spec.ts` does — **a second sign-in per test
    // is a second thing to forget when the redirect changes** (B-304).
    await page.goto('/accounts');
    await expect(page.getByRole('heading', { name: 'Companies', level: 1 })).toBeVisible();

    await ready(page);

    await page.getByRole('checkbox', { name: 'Select the companies on this page' }).check();

    const bar = page.getByRole('region', { name: 'Selected companies' });
    await expect(bar).toBeVisible();
    await expect(bar.getByText(/\d+ selected/)).toBeVisible();
  });

  test('🔴 the confirm names the count and says nothing has happened yet', async ({
    page,
  }) => {
    /**
     * 📁 **The row's Definition of Done**: *"the confirm states the COUNT and
     * the ACTION in the customer's words"* — and the second half of the
     * promise is 📁 [ADR-0405](../../../docs/architecture/adr/0405-an-action-is-approved-before-it-is-effective.md):
     * ⛔ **an action is approved before it is effective.**
     */
    await page.goto('/accounts');
    await ready(page);

    await page.getByRole('checkbox', { name: 'Select the companies on this page' }).check();
    await page.getByRole('button', { name: 'Add tag' }).click();

    await expect(page.getByText(/Add a tag to \d+ compan(y|ies)/)).toBeVisible();
    await expect(
      page.getByText(/Nothing changes until somebody approves it/),
    ).toBeVisible();
    // ⚡ **The undo is told BEFORE they commit**, not in a toast afterwards.
    await expect(page.getByText(/take it back for a\s+day/)).toBeVisible();
  });

  test('✅ naming a label proposes it, and the chips do NOT appear', async ({
    page,
  }) => {
    /**
     * 🔴 **The assertion this journey exists for.**
     *
     * ⛔ **A screen that showed the tag immediately would have told the
     * customer the work was done** while the batch sat unapproved. ⚡ **The
     * chips arriving later, after somebody accepts, is the product working** —
     * and this proves the optimistic version was not shipped by accident.
     */
    await page.goto('/accounts');
    await ready(page);

    await page.getByRole('checkbox', { name: 'Select the companies on this page' }).check();
    await page.getByRole('button', { name: 'Add tag' }).click();

    const label = `e2e ${Date.now()}`;
    await page.getByLabel('New tag name').fill(label);
    await page.getByRole('button', { name: 'Create' }).click();

    // The tag now exists in the vocabulary and is offered as a choice.
    const choice = page.getByRole('button', { name: label });
    await expect(choice).toBeVisible();
    await choice.click();

    // ⛔ **Nothing is tagged.** The dialog closes and the table is unchanged.
    await expect(page.getByText(/Add a tag to/)).toBeHidden();
    await expect(page.getByRole('cell').filter({ hasText: label })).toHaveCount(0);
  });

  test('⛔ clearing the selection puts the bar away', async ({ page }) => {
    await page.goto('/accounts');
    await ready(page);

    await page.getByRole('checkbox', { name: 'Select the companies on this page' }).check();
    const bar = page.getByRole('region', { name: 'Selected companies' });
    await expect(bar).toBeVisible();

    await bar.getByRole('button', { name: 'Clear selection' }).click();

    await expect(bar).toBeHidden();
  });
});
