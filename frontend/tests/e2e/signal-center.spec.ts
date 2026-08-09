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

/**
 * **The queue's summary is the signal's own** — [TASK-1427](../../../docs/BACKLOG.md).
 *
 * 🔴 **The row states its own Playwright line and it is the whole defect**:
 * *"two rows of the same `signal_type` render DIFFERENT summaries"*. ⛔ **The
 * failure this catches passes every other check** — rendering the catalog's
 * `why_it_matters` puts one sentence under every row of a type, and **each row
 * reads as though Signora had examined that account.**
 *
 * ⚡ **Asserted here rather than only in the component test** because the
 * component test supplies its own fixtures: it proves the screen renders what
 * it is handed. **This proves the platform actually publishes a per-signal
 * sentence end to end** — domain → `QueueEntryResponse` → the row.
 */
test('@journey a queue row carries its own summary, not its type’s', async ({ page }) => {
  await page.goto('/signals');
  await expect(page.getByRole('heading', { name: 'Signals', level: 1 })).toBeVisible();

  let sawASummary = false;
  let sawTwoOfOneType = false;

  /**
   * ⚠️ **All three tabs, and that is a correctness fix rather than thoroughness.**
   * The first draft walked only *Needs review* and passed alone but failed in the
   * full suite: **earlier journeys action and dismiss signals**, so by the time
   * this runs the open tab can hold fewer than two rows of any one type and the
   * assertion had nothing to check. ⚡ **A resolved signal keeps its rationale and
   * moves to *Closed*** — the population is conserved across the three tabs, so
   * walking all of them is order-independent. — [B-218](../../../docs/BUGS.md)'s class.
   */
  for (const tab of ['Needs review', 'Snoozed', 'Closed']) {
    await page.getByRole('tab', { name: tab }).click();
    await expect(page.getByRole('tab', { name: tab })).toHaveAttribute('aria-selected', 'true');

    const groups = page.locator('h2').locator('..');
    for (let i = 0; i < (await groups.count()); i += 1) {
      // ⛔ The rationale is the only paragraph carrying its own full text as
      // `title` — the clamp is visual and the complete sentence stays readable.
      const summaries = groups.nth(i).locator('li p[title]');
      const n = await summaries.count();
      if (n === 0) continue;

      const texts = (await summaries.allInnerTexts()).map((t) => t.trim());
      for (const text of texts) expect(text.length).toBeGreaterThan(0);
      sawASummary = true;

      if (n > 1) {
        // 🔴 Same type, same group — a per-TYPE sentence would make these equal.
        expect(new Set(texts).size).toBeGreaterThan(1);
        sawTwoOfOneType = true;
      }
    }
  }

  // ⚡ Both assertions above are vacuous on an empty queue, so the walk states
  // what it actually found (§2 — a guard that cannot fail is documentation
  // pretending to be code).
  expect(sawASummary).toBe(true);
  expect(sawTwoOfOneType).toBe(true);
});
