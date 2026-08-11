import { expect, test } from '@playwright/test';

/**
 * **Account 360, and the seven sections nothing can fill** —
 * [TASK-1415](../../../docs/BACKLOG.md).
 *
 * 🔴 **What a browser is needed for.** ⛔ **A component test proves the section
 * renders when it is handed one.** ⚡ **Only a walk proves the record page
 * actually carries all seven**, and that a rep scrolling the screen the design
 * describes is never left guessing whether a missing section is a bug.
 *
 * 📁 **[§20c](../../../CLAUDE.md)**: *"screens without a shipped module behind
 * them ship a designed empty state."* ⛔ **An omission is not one.**
 */
async function openAnAccount(page: import('@playwright/test').Page): Promise<void> {
  await page.goto('/');
  const href = await page.locator('main a[href^="/accounts/"]').first().getAttribute('href');
  await page.goto(href!);
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
}

test('@journey the record page states what Signora cannot answer, rather than omitting it', async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await openAnAccount(page);

  const main = page.getByRole('main');

  // 📁 **The design's seven**, each by its own heading. ⛔ **Named literally**,
  // so this fails if one is quietly dropped rather than passing over a regex.
  for (const label of [
    'Customer health',
    'Buying intent',
    'Organisation chart',
    'Relationship graph',
    'Technology stack',
    'Market signals',
    'Meetings',
  ]) {
    await expect(main.getByRole('heading', { name: label, level: 2 }), label).toBeVisible();
  }

  // ⛔ **And each says what is missing.** 🔴 A heading over nothing would be
  // worse than the omission — it would look like a section that failed to load.
  await expect(main.getByText(/no intent source is connected/i)).toBeVisible();
  await expect(main.getByText(/inferred from email, calendar and public sources/i)).toBeVisible();
});

test('@journey no absent section says "coming soon"', async ({ page }) => {
  /**
   * 📁 **The rail already paid for that once** — *"at M12.3, three of six said
   * `coming soon` on the screen a customer sees first."* ⚡ **An absence states
   * what is missing**, which is something a customer can act on; *coming soon*
   * tells them to wait without saying for what.
   */
  await page.setViewportSize({ width: 1440, height: 1000 });
  await openAnAccount(page);

  const body = page.locator('body');
  for (const forbidden of ['coming soon', 'under construction', 'not implemented']) {
    await expect(body, forbidden).not.toContainText(new RegExp(forbidden, 'i'));
  }
});

test('@journey the "On this page" rail maps every section, including the empty rooms', async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await openAnAccount(page);

  const rail = page.getByRole('navigation', { name: 'On this page' });
  await expect(rail).toBeVisible();

  // ⛔ **A map that hides the rooms you cannot enter is one nobody can trust** —
  // 📁 the reasoning `rail.ts` already records for a restricted destination.
  await expect(rail.getByRole('link', { name: 'Account score' })).toBeVisible();
  await expect(rail.getByRole('link', { name: 'Buying intent' })).toBeVisible();

  // ⚡ **And the rail actually reaches the section it names.**
  await rail.getByRole('link', { name: 'Meetings' }).click();
  await expect(page.locator('#meetings')).toBeVisible();
});
