/**
 * **A seller sees who owns each company** — [TASK-1479](../../../docs/BACKLOG.md)
 * slice ⓶, against [ADR-0411](../../../docs/architecture/adr/0411-customer-organized-account-metadata.md).
 *
 * 📁 **The row's journey**: *"Owner is a reference to a member, so the column
 * shows a person and never a stored name."*
 *
 * ## ⚠️ What this journey can and cannot reach
 *
 * ⛔ **There is no owner-assignment control on the approved Companies design**,
 * exactly as there is no approvals inbox — 📁 the same finding
 * [C-1507](../../../docs/LANE_COORDINATION.md) records for tags, and
 * [D-156](../../../docs/DECISION_REGISTER.md) ⑥ forbids inventing one.
 *
 * ⚡ **So the journey here is the part a customer can drive**: the column
 * exists, it is theirs to turn on, and **an account nobody owns says so rather
 * than showing a blank a seller would read as a missing value.**
 *
 * **The write path is proven at the API** — `test_api_account_assignments.py`
 * — **and in the handlers**, and this is a declared absence rather than a
 * passing test implying more than it checked.
 */

import type { Page } from '@playwright/test';

import { expect, test } from './fixtures/signora';

/**
 * 🔴 **Wait for the table, and never for a count** — 📁 the
 * [B-262](../../../docs/BUGS.md) race, and the same helper the bulk-tag
 * journey uses for the same reason.
 */
async function ready(page: Page): Promise<void> {
  await expect(page.getByRole('heading', { name: 'Companies', level: 1 })).toBeVisible();
  await expect(
    page.getByRole('checkbox', { name: 'Select the companies on this page' }),
  ).toBeVisible();
}

test.describe('a seller sees who owns each company', () => {
  test('🔴 Owner is a column they can turn on', async ({ page }) => {
    /**
     * ⛔ **Off by default and offered**, like Tags. 📁 `DEFAULT_COLUMNS`
     * excludes it, and **a column that could not be turned on would be a
     * capability nobody could reach** — which is how the Tags vocabulary came
     * to be fetched only when its own column was already visible.
     *
     * ⚠️ **A `<summary>`, not a button** — measured rather than assumed. The
     * first version of this journey looked for a *Columns* button and found
     * nothing, **because it was written from what the screen ought to have
     * rather than from what it has.**
     */
    await page.goto('/accounts');
    await ready(page);

    await page.getByText(/Columns · \d+ of \d+/).click();

    await expect(page.getByRole('checkbox', { name: 'Owner' })).toBeVisible();
  });

  test('✅ an account nobody owns says so rather than showing a blank', async ({
    page,
  }) => {
    /**
     * ⚡ **The assertion this journey exists for.** 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md)'s
     * loading cousin: **an unresolved read must not render as an empty
     * result**, and an empty cell is exactly what a seller reads as *"Signora
     * looked and found nothing."*
     *
     * ⛔ **The seeded workspace assigns nobody**, so every row is genuinely
     * unassigned — which is the state that must be *stated* rather than left
     * blank.
     */
    await page.goto('/accounts');
    await ready(page);

    // The column is opt-in; turn it on the way a customer would.
    await page.getByText(/Columns · \d+ of \d+/).click();
    await page.getByRole('checkbox', { name: 'Owner' }).check();

    await expect(page.getByText('Unassigned').first()).toBeVisible();
  });
});
