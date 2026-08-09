import { expect, test } from '@playwright/test';

/**
 * **The Signal Center** — [TASK-439](../../../docs/BACKLOG.md).
 *
 * > 📁 ***"A triage queue, not a notification list · every signal ends in a
 * > decision."***
 *
 * ⚡ **The door is the half a unit test cannot check.** `reachability.py` reads
 * source and sees a `Link`; it cannot see which branch renders it. **The first
 * draft of this screen put the entrance inside the populated branch of the
 * attention list**, so a workspace with an empty list had no way in at all —
 * **the static scan passed and this walk failed.** ⛔ That is why the entrance
 * is asserted here rather than trusted.
 */
test('@journey the Signal Center is reachable, and offers the three states', async ({ page }) => {
  await page.goto('/');

  const door = page.getByRole('link', { name: /Review every signal/i });
  await expect(door).toBeVisible();
  await door.click();

  await expect(page).toHaveURL(/\/signals$/);
  await expect(page.getByRole('heading', { name: 'Signals', level: 1 })).toBeVisible();

  // 📁 The design's three: *Needs review* · *Snoozed* · *Closed*.
  for (const label of ['Needs review', 'Snoozed', 'Closed']) {
    await expect(page.getByRole('tab', { name: label })).toBeVisible();
  }

  await page.getByRole('tab', { name: 'Snoozed' }).click();
  await expect(page.getByRole('tab', { name: 'Snoozed' })).toHaveAttribute(
    'aria-selected',
    'true',
  );
});
