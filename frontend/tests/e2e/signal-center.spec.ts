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
  await page.waitForURL(/\/w\/[0-9a-f-]{36}\/home$/, { timeout: 30_000 });

  /**
   * 🔴 **The rail, and it is the door the product GUARANTEES.**
   *
   * ⚠️ **This asserted a Home link reading *"Review every signal"* and that copy
   * no longer exists.** 📁 Home's rebuild against the finalized design replaced
   * that entrance with the attention card's own rule — *"a sixth becomes 'See
   * all 8 in Signals'"* — ⛔ **which renders only when there are more than three
   * items**, so on a quiet workspace it is not there at all.
   *
   * ⚡ **That is not a regression, it is where the guarantee moved.** 📁 `Signals`
   * is one of the App Shell's nine destinations and is always in the rail, so
   * **the rail is what makes the screen reachable from anywhere** — and the card
   * link below is an additional convenience rather than the only way in.
   *
   * ⛔ **The original point survives intact**: 📁 *"`reachability.py` reads source
   * and sees a `Link`; it cannot see which branch renders it"* — **and a rail
   * item is exactly the case a static scan cannot distinguish from one buried in
   * a populated branch.** This still walks it.
   */
  const door = page.getByRole('navigation').getByRole('link', { name: 'Signals' });
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
 * 📁 **Home's own door, and the rule that governs it** — *"a sixth becomes 'See
 * all 8 in Signals'"*, and `P-07`: *"Home is a starting point, not a queue. **A
 * sixth item becomes a link to Signals, which is the surface designed for
 * triage**."*
 *
 * ⚡ **Kept as a separate test from the reachability walk above**, because they
 * are different claims: **the rail's door is unconditional, this one is the
 * design's overflow rule** — and conflating them is what made the old spec read
 * as a reachability guarantee when it was asserting a conditional link.
 */
test('@journey Home offers the overflow link when the queue outruns the card', async ({
  page,
}) => {
  await page.goto('/');
  await page.waitForURL(/\/w\/[0-9a-f-]{36}\/home$/, { timeout: 30_000 });
  await expect(page.locator('[data-card]').first()).toBeVisible({ timeout: 30_000 });

  const card = page.locator('[data-card="needs-you-today"]');
  // ⛔ **The precondition, stated rather than assumed** — 📁 the rule is about a
  // queue with more items than the card shows, so a spec that did not say so
  // would pass silently on a workspace with three.
  await expect(
    card,
    'the seller composition\'s attention card — this rule is that card\'s',
  ).toBeVisible();

  const overflow = card.getByRole('link', { name: /See all \d+ in Signals/ });
  await expect(overflow).toBeVisible();
  await overflow.click();

  await expect(page).toHaveURL(/\/signals$/);
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

    /**
     * 🔴 **The panel is COUNTED, so it has to have settled first.**
     *
     * ⚠️ **This walked the DOM the moment the tab reported selected**, which is
     * before the tab's own read has landed — so under load it counted a
     * half-rendered list, `n > 1` was never observed, and the run ended on
     * `sawTwoOfOneType` being false. ⛔ **It passed alone and failed in a full
     * file**, which reads exactly like contamination and is not: **the same
     * page, sampled earlier.**
     *
     * ⚡ **Found by adding a third test to this file** — three concurrent pages
     * against one API was enough, and two was not.
     *
     * ⛔ **`networkidle` was the first fix and it was not enough** — it still
     * failed two runs in five. ⚡ **The queue's OWN skeleton is the settled
     * signal**: 📁 `signal-queue.tsx` renders three `h-16` skeletons while
     * `queue.isPending`, so their absence is the tab's read having landed,
     * which is the thing being waited for rather than a proxy for it.
     */
    await expect(page.locator('[data-skeleton].h-16')).toHaveCount(0, { timeout: 20_000 });

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
