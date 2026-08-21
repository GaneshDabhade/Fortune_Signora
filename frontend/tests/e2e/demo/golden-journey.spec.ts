/**
 * The Product Demonstration Suite — Signora, used rather than verified.
 *
 *     make product-demo          watch it, at a human pace
 *     make product-demo-record   record it, and keep the video
 *
 * ## Why this is not a test
 *
 * It shares a runner with the regression suite and shares almost nothing else,
 * because the two goals genuinely conflict:
 *
 * | | Regression | Demonstration |
 * |---|---|---|
 * | **Wants** | to be fast, headless, independent | to be **watched** |
 * | **Shape** | many small isolated cases | **one continuous story** |
 * | **On failure** | a precise assertion | *"the demonstration stopped here"* |
 * | **Artifact** | a pass | a **video somebody can replay** |
 *
 * Folding a demonstration into the regression suite would make the regression
 * suite slow and the demonstration invisible. They are separate projects.
 *
 * ## What it demonstrates
 *
 * A single working morning, in the order a seller lives it, narrated as it
 * goes. **Every step is the real product** — real authentication, real API,
 * real pipeline output. Nothing here is staged, and the narration says what is
 * happening rather than what is supposed to happen.
 *
 * ## What it deliberately does not do
 *
 * **It does not assert its way through the product.** A demonstration that
 * failed on a changed sentence would be re-baselined until it demonstrated
 * nothing, which is the same failure mode as a re-baselined screenshot. It
 * asserts only what would make the demonstration *meaningless* if absent — a
 * page that never loaded, a list with nothing in it — and narrates the rest.
 */

import { expect, test } from '../fixtures/signora';
import { OWNER } from '../fixtures/personas';

/** Narration, so a person watching knows what they are looking at, and so the
 * terminal output reads as a story rather than as a test log. */
function say(step: string, detail?: string): void {
  process.stdout.write(`\n  ${step}${detail ? `\n     ${detail}` : ''}\n`);
}

/** A beat, so a human eye can follow. Only in the demonstration — a regression
 * test that slept would be a regression test nobody ran. */
async function beat(page: import('@playwright/test').Page, ms = 1200): Promise<void> {
  await page.waitForTimeout(ms);
}

test('a working morning at Signora', async ({ page, accounts, brief }) => {
  say(
    'Signora — a working morning',
    `signed in as ${OWNER.name}, ${OWNER.persona}`,
  );

  // ── 1 ─────────────────────────────────────────────────────────────────────
  say(
    '1 · "Which accounts should I work on today?"',
    'The first screen is the morning\'s work, not a dashboard about it.',
  );
  await accounts.open();
  const names = await accounts.names();
  expect(names.length).toBeGreaterThan(0);
  say(
    `   ${names.length} accounts, most pressing first`,
    names.slice(0, 4).map((name) => `· ${name}`).join('   '),
  );
  await beat(page, 2500);

  // ── 2 ─────────────────────────────────────────────────────────────────────
  say(
    '2 · Every row says what changed, and how far it can be trusted',
    'Nothing on this screen was written by a model. All of it is computed.',
  );
  const firstRow = await accounts.rows.first().innerText();
  say('   the top row reads:', firstRow.replace(/\n+/g, ' · '));
  await beat(page);

  // ── 3 ─────────────────────────────────────────────────────────────────────
  say('3 · "Why this account?"', 'The question the list cannot answer.');
  const opened = await accounts.openFirstAccount();
  await brief.waitForScore();
  say(`   opened ${opened}`);
  await beat(page, 2000);

  // ── 4 ─────────────────────────────────────────────────────────────────────
  say(
    '4 · The score decomposes into an arithmetic',
    'A number a customer cannot take apart is a number they have to believe.',
  );
  const arithmetic = await page.getByText(/\d+ of \d+ points/).first().innerText();
  say(`   ${arithmetic}`);
  await page.getByRole('heading', { name: 'Account score' }).scrollIntoViewIfNeeded();
  await beat(page, 2000);

  // ── 5 ─────────────────────────────────────────────────────────────────────
  say(
    '5 · "Prove it."',
    'Every contributing line opens the provider readings underneath it.',
  );
  await brief.openFirstCitation();
  // **Wait for the readings, not for the dialog.** The drawer opens with a
  // placeholder title — *"The evidence behind this"* — while the evidence is in
  // flight, and narrating that would demonstrate the loading state rather than
  // the evidence.
  await expect
    .poll(async () => (await brief.evidenceDialog.innerText()).length, { timeout: 20_000 })
    .toBeGreaterThan(60);
  const evidence = await brief.evidenceDialog.innerText();
  say('   the evidence says:', evidence.replace(/\n+/g, ' · ').slice(0, 160));
  await beat(page, 2500);

  // ── 5a ────────────────────────────────────────────────────────────────────
  // **A small thing, demonstrated because small things are what "premium"
  // means.** Scrolling while reading a citation used to move the argument
  // underneath it, so a reader came back to a page that had shifted and lost
  // their place ([B-307](../../../../docs/BUGS.md)).
  say(
    '5a · The argument holds still while you check it',
    'The page behind does not move, and returns you where you were.',
  );
  await page.mouse.wheel(0, 600);
  await beat(page, 1500);
  await page.keyboard.press('Escape');

  // ── 6 ─────────────────────────────────────────────────────────────────────
  say(
    '6 · "What has actually happened here?"',
    'The record of events, underneath what Signora thinks about them.',
  );
  /**
   * ⚠️ **Bounded at 20s, and it was unbounded.** ⛔ **`scrollIntoViewIfNeeded`
   * with no timeout inherits the `demo` project's 180 seconds**, so on
   * 2026-08-19 a heading that never appeared cost **the entire budget — 180s,
   * 14% of the whole browser gate — to report one missing element.**
   *
   * ⚡ **Every other wait in this file already uses `{ timeout: 20_000 }`.**
   * ⛔ **Nothing is weakened: the heading is still required, and a heading that
   * is absent is absent at 20 seconds exactly as it is at 180.** ✅ **What
   * changes is only how long the demonstration is willing to stare at it.**
   *
   * 📁 **And the assertion is separated from the scroll deliberately**, so the
   * failure says *the record of events was not on this screen* rather than
   * `locator.scrollIntoViewIfNeeded: Test timeout exceeded`.
   */
  /**
   * 🔴 **[B-247](../../../../docs/BUGS.md) — the history MOVED and this journey
   * kept looking for it on the page.**
   *
   * 📁 **[TASK-1433](../../../../docs/BACKLOG.md) gave it to the utility
   * panel's Activity tab** — *"the panel takes it only where the panel exists;
   * below 1024 the section above renders"* — **and this demonstration runs
   * above that band.** ⛔ **`daily-usage` was corrected for exactly this and
   * this file was not**, which is why it has been failing on `main`.
   *
   * ⚠️ **The failure was NOT the heading rename**, and that is worth stating:
   * this looked for *"What has happened"*, the rename made it look for
   * *"Recent activity"*, and it failed identically both times. **Same defect,
   * new name** — the rename neither caused it nor hid it.
   *
   * ✅ **The claim is unchanged — the account carries a record of what has
   * happened.** ⚡ **Only where a viewer looks for it changed**, so the
   * demonstration opens the tab rather than asserting a heading the design
   * moved.
   */
  const panel = page.getByRole('complementary');
  // ⚠️ **Idempotent, because the panel's open state is a STORED preference** —
  // ⛔ an unconditional `⌘.` would CLOSE it whenever an earlier step left it
  // open, which makes the result depend on what ran before.
  if ((await panel.getAttribute('data-state')) !== 'open') {
    await page.keyboard.press('Meta+.');
  }
  await expect(
    panel,
    'the utility panel never docked — the record of events lives in its ' +
      'Activity tab above 1024 (see utility-panel.spec.ts, which asserts it BOTH ways)',
  ).toHaveAttribute('data-state', 'open', { timeout: 20_000 });

  await panel.getByRole('tab', { name: 'Activity' }).click();
  await expect(panel).toHaveAttribute('aria-label', 'Activity panel');
  // 📁 **[B-302](../../../../docs/BUGS.md)** — the Playground composed nine
  // pipeline stages and never the Timeline projection, so this history was
  // empty on every account in the one environment used for product review.
  await expect(panel.getByText(/Nothing has been recorded/i)).toHaveCount(0);
  await beat(page, 2000);

  // ── 7 ─────────────────────────────────────────────────────────────────────
  say(
    '7 · "Where does my morning continue?"',
    'The list is ranked, so next means next most pressing.',
  );
  await page.keyboard.press('End');
  await beat(page, 1500);

  // ── 8 ─────────────────────────────────────────────────────────────────────
  say(
    '8 · What Signora needed to know first',
    'Every judgement above is relative to what this company says it sells.',
  );
  await page.goto('/settings/products');
  await expect(page.getByRole('heading', { name: 'Your business', level: 1 })).toBeVisible({
    timeout: 20_000,
  });
  await beat(page, 2500);

  // ── 9 ─────────────────────────────────────────────────────────────────────
  say(
    '9 · What Signora refuses to claim',
    'No developer application is configured here, so no button is offered.',
  );
  await page.goto('/settings/connections');
  await expect(page.getByText('Not connected').first()).toBeVisible({ timeout: 20_000 });
  await beat(page, 2000);

  say(
    'End of the demonstration.',
    'Every screen was the real product, against real pipeline output.',
  );
});
