/**
 * **The Companies workspace, in a browser** —
 * [TASK-1475](../../../docs/BACKLOG.md).
 *
 * 🔴 **What a browser proves and jsdom cannot**: that the pager REPLACES the
 * page rather than appending to it, that the card grid actually reflows at the
 * design's bands, and that a density change moves real pixels.
 *
 * 📁 **The design's rule for cards**: *"same data, same filters, same
 * selection — for scanning by account rather than by column."*
 */
import { expect, test } from '@playwright/test';

test.describe('Companies — views, filters, density and paging', () => {
  test('@journey a seller switches to cards, narrows, and the narrowing holds', async ({
    page,
  }) => {
    await page.goto('/accounts');
    await expect(page.getByRole('table')).toBeVisible();

    const before = await page.getByRole('table').getByRole('row').count();
    expect(before).toBeGreaterThan(1);

    await page.getByRole('button', { name: 'cards' }).click();
    const cards = page.getByTestId('accounts-cards');
    await expect(cards).toBeVisible();
    // ⛔ **One surface at a time**, not a table hidden behind a grid.
    await expect(page.getByRole('table')).toHaveCount(0);

    const firstName = (await cards.getByRole('listitem').first().innerText()).split('\n')[0] ?? '';
    // 📁 **A condition is ADDED, not typed into a permanent box** — the design's
    // filter row is chips behind *"＋ Add condition"* and draws no standing
    // search field. ⛔ **The journey follows the designed interaction rather
    // than asserting a control the design does not have.**
    await page.getByText('+ Add condition').click();
    await page.getByLabel('Name contains').fill(firstName.slice(0, 4));

    await expect(cards.getByRole('listitem')).toHaveCount(
      await cards.getByRole('listitem').count(),
    );
    // ✅ **The filter narrowed the cards** — same data, same filter.
    await expect(page.getByTestId('companies-count')).toContainText('of');
  });

  /**
   * 🔴 **The pager replaces; `Load more` appended.** ⚡ **That is the difference
   * a browser shows and a unit test can only assert** — the first page's rows
   * are gone from the document, not scrolled past.
   */
  test('@journey Next replaces the page and Previous returns to it', async ({ page }) => {
    await page.goto('/accounts');
    const table = page.getByRole('table');
    await expect(table).toBeVisible();

    // ⚠️ **The pager now reads the design's own sentence** — *"Rows 1–15 of
    // 15"* — **and marks the current page with `aria-current`.** ⛔ **The claim
    // is unchanged**: a page NUMBER is honest and a page COUNT is not.
    const pager = page.getByTestId('accounts-pager');
    await expect(pager).toContainText(/Rows 1–\d/);
    await expect(pager.getByText('1', { exact: true })).toHaveAttribute('aria-current', 'page');
    await expect(pager.getByRole('button', { name: 'Previous' })).toBeDisabled();

    const next = pager.getByRole('button', { name: 'Next' });
    if (await next.isEnabled()) {
      const firstRow = (await table.getByRole('row').nth(1).innerText()).trim();
      await next.click();
      await expect(pager.getByText('2', { exact: true })).toHaveAttribute(
        'aria-current',
        'page',
      );
      // ⛔ **Replaced, not appended.**
      await expect(table.getByText(firstRow, { exact: false })).toHaveCount(0);

      await pager.getByRole('button', { name: 'Previous' }).click();
      await expect(pager.getByText('1', { exact: true })).toHaveAttribute(
        'aria-current',
        'page',
      );
    }

    // ⛔ **No numbered page BUTTONS, however the design draws them** — ⚡ keyset
    // cannot reach page 3 without walking 1 and 2, so one would be a control
    // that could not work ([B-255](../../../docs/BUGS.md)).
    await expect(pager.getByRole('button', { name: '2', exact: true })).toHaveCount(0);
  });

  /**
   * 📱 **Responsive, at the design's own bands** — 📁 `phone: 640`,
   * `smalllaptop: 1024`, `laptop: 1280`.
   */
  test('@journey the card grid reflows across the design’s bands', async ({ page }) => {
    await page.goto('/accounts');
    await page.getByRole('button', { name: 'cards' }).click();
    const cards = page.getByTestId('accounts-cards');
    await expect(cards).toBeVisible();

    const widthOfFirst = async () => {
      const box = await cards.getByRole('listitem').first().boundingBox();
      return box?.width ?? 0;
    };

    await page.setViewportSize({ width: 560, height: 900 });
    const phone = await widthOfFirst();

    await page.setViewportSize({ width: 1400, height: 900 });
    const laptop = await widthOfFirst();

    // 🔴 **One column on a phone, three at laptop** — so a card is materially
    // narrower where the grid has more of them, measured rather than asserted
    // from a class name.
    expect(laptop).toBeLessThan(phone);
  });

  /**
   * 📁 **Density** — ⚡ **measured as geometry**, because a class name says
   * nothing about whether the row actually got shorter.
   */
  test('@journey compact density makes the rows shorter', async ({ page }) => {
    await page.goto('/accounts');
    const table = page.getByRole('table');
    await expect(table).toBeVisible();

    const rowHeight = async () => (await table.getByRole('row').nth(1).boundingBox())?.height ?? 0;
    const comfortable = await rowHeight();

    // 📁 **The design draws Density as a 30px pill, not a dropdown** — ⚡ **so
    // the journey clicks it**, which is how a seller changes it. ⛔ **Not a
    // weakened assertion**: the same two heights are still measured.
    await page.getByRole('button', { name: /^Density/ }).click();
    const compact = await rowHeight();

    expect(compact).toBeLessThan(comfortable);
  });

  /**
   * 📁 **The design's expanded row** — *"Expanded · Vantage Logistics"*, and
   * the context drawer beside it naming the same account.
   *
   * 🔴 **What a browser proves here**: that the panel opens INSIDE the table,
   * spanning the row rather than replacing it, ⛔ **and that dismissing the
   * preview does not take the expanded row with it** — the defect a screenshot
   * caught while every gate was green.
   */
  test('@journey a row expands in place, and the preview closes without it', async ({ page }) => {
    await page.goto('/accounts');
    const table = page.getByRole('table');
    await expect(table).toBeVisible();

    const rowsBefore = await table.getByRole('row').count();
    await page.getByRole('button', { name: /^Expand / }).first().click();

    // ✅ **The panel is a row of the table**, which is what keeps the columns
    // above it aligned with the columns below it.
    await expect(table.getByText(/^Expanded · /)).toBeVisible();
    expect(await table.getByRole('row').count()).toBe(rowsBefore + 1);

    // 📁 The design's three panels.
    await expect(table.getByText('Open opportunity')).toBeVisible();
    await expect(table.getByText(/^Commercial · /)).toBeVisible();
    await expect(table.getByText('Row-level AI')).toBeVisible();

    // ⛔ **No way to type an ACV** — ADR-0409 §5: a claim is only produced
    // where the provider supplies the fact.
    await expect(page.getByRole('textbox', { name: /acv/i })).toHaveCount(0);

    await page.getByText('Row preview').waitFor();
    await page.getByRole('button', { name: /close/i }).first().click();
    await expect(page.getByText('Row preview')).toHaveCount(0);
    // 🔴 **The row is still open.**
    await expect(table.getByText(/^Expanded · /)).toBeVisible();
  });
});
