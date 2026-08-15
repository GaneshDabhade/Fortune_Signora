/**
 * **A seller sees which of their groupings each company is in** —
 * [TASK-1479](../../../docs/BACKLOG.md) slice ⓶b, against
 * [ADR-0411](../../../docs/architecture/adr/0411-customer-organized-account-metadata.md)
 * and 📁 `Fortune Signora Companies.dc.html`.
 *
 * ## ⚠️ *Segment* means the enumerated grouping, and it is ruled
 *
 * 📁 **[D-235](../../../docs/DECISION_REGISTER.md) ②** closed
 * [C-1503](../../../docs/LANE_COORDINATION.md): a customer says *ICP* for the
 * stored predicate and **Segment for the customer-organized grouping this
 * column renders.** ⛔ Nothing is renamed.
 *
 * ## ⛔ What this journey can and cannot reach
 *
 * **There is no *New segment* control on the approved Companies design that a
 * customer can drive to completion**, exactly as there is no owner-assignment
 * control and no approvals inbox — 📁 the same finding
 * [C-1507](../../../docs/LANE_COORDINATION.md) records, and
 * [D-156](../../../docs/DECISION_REGISTER.md) ⑥ forbids inventing one.
 *
 * ⚡ **So the journey is the part a customer can drive**: the column exists, it
 * is theirs to turn on, and **a company in no grouping says so rather than
 * showing a blank a seller would read as a missing value.**
 *
 * **The write path is proven at the API** — `test_api_account_segments.py` —
 * **and in the handlers**. ⛔ **A declared absence, rather than a passing test
 * implying more than it checked.**
 */

import type { Page } from '@playwright/test';

import { expect, test } from './fixtures/signora';

/**
 * 🔴 **Wait for the table, and never for a count** — 📁 the
 * [B-262](../../../docs/BUGS.md) race, and the same helper the owner and
 * bulk-tag journeys use for the same reason.
 */
async function ready(page: Page): Promise<void> {
  await expect(page.getByRole('heading', { name: 'Companies', level: 1 })).toBeVisible();
  await expect(
    page.getByRole('checkbox', { name: 'Select the companies on this page' }),
  ).toBeVisible();
}

test.describe('a seller sees which groupings each company is in', () => {
  test('🔴 Segment is a column they can turn on', async ({ page }) => {
    /**
     * ⛔ **Off by default and offered**, like Tags and Owner. 📁
     * `DEFAULT_COLUMNS` excludes it, and **a column that could not be turned
     * on would be a capability nobody could reach** — which is exactly what
     * slice ⓶'s journey caught: the Owner column was registered, built and
     * unit-tested, and the page never rendered it.
     *
     * ⚠️ **A `<summary>`, not a button** — carried from ⓶a, where the first
     * version of that journey was written from what the screen ought to have
     * rather than from what it has.
     */
    await page.goto('/accounts');
    await ready(page);

    await page.getByText(/Columns · \d+ of \d+/).click();

    await expect(page.getByRole('checkbox', { name: 'Segment' })).toBeVisible();
  });

  test('✅ a company in no grouping says so rather than showing a blank', async ({
    page,
  }) => {
    /**
     * ⚡ **The assertion this journey exists for**, and it is the state every
     * workspace starts in. 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md)'s
     * loading cousin: **an unresolved read must not render as an empty
     * result**, and an empty cell is what a seller reads as *"Signora looked
     * and found nothing."*
     *
     * 🔴 **The distinction the cell has to keep is invisible to a unit test
     * against a fixture**: *the answer has not arrived* and *this company is
     * in nothing* are one pixel apart on screen and two different facts, and
     * **only a real read against a real API passes through both.**
     */
    await page.goto('/accounts');
    await ready(page);

    // The column is opt-in; turn it on the way a customer would.
    await page.getByText(/Columns · \d+ of \d+/).click();
    await page.getByRole('checkbox', { name: 'Segment' }).check();

    await expect(page.getByText('No segment').first()).toBeVisible();
  });
});
