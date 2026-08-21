/**
 * **Account 360's section states, in a browser** —
 * [TASK-1476](../../../docs/BACKLOG.md), against 📁
 * `Fortune Signora Account 360.dc.html` §*States*.
 *
 * 🔴 **What a browser proves and jsdom cannot.** ⚡ Three of the design's rules
 * are about **what a reader can still see and still reach** after a section
 * changes state, and each one is geometry or navigation rather than markup:
 *
 * - *"Header keeps the count and the worst status, so collapsing cannot hide a
 *   risk"* — **the header must still be ON SCREEN**, not merely in the DOM.
 * - *"Anchor links from the page nav auto-expand the target section"* — **a
 *   real click on a real `href="#…"`**, which is a navigation jsdom does not
 *   perform.
 * - *"Every section is a labelled region with a heading, reachable by landmark
 *   navigation"* — **and it must survive the collapse.**
 */
import { expect, test } from '@playwright/test';

import { openScoredAccount } from './fixtures/accounts';

/**
 * ⚡ **Open an account that HAS something to have a state about.**
 *
 * ⛔ **Not simply the first row.** ⚠️ **The first account in the list is
 * routinely one nothing has scored** — the page then renders *"Nothing has
 * scored this account yet"* and **no section exists at all**, which is a
 * correct screen and the wrong subject for this journey. 📁 **This is
 * [B-245](../../../docs/BUGS.md)'s shape**: a journey that assumed the first
 * row was representative.
 *
 * ✅ **So it walks the list until a record page renders its sections**, and
 * **fails loudly if none does** rather than skipping — ⛔ a silent skip is a
 * journey that reports green having asserted nothing.
 */

test.describe('Account 360 — a section changes state and stays honest', () => {
  /**
   * 🔴 **The design's safety rule, and the reason it is a journey rather than a
   * unit test.** ⛔ A header that is in the DOM behind a collapsed body is not
   * a header a rep can read — **`toBeVisible` is the assertion that means what
   * the rule means.**
   */
  test('@journey collapsing a section never hides its count', async ({ page }) => {
    await openScoredAccount(page);

    const heading = page.getByRole('heading', { name: 'Account score' });
    await expect(heading).toBeVisible();

    const toggle = page.getByRole('button', { name: 'Account score' });
    await expect(toggle).toHaveAttribute('aria-expanded', 'true');

    // ⚡ **The count beside the heading, read BEFORE the collapse** so the
    // assertion compares the same number rather than trusting it re-renders.
    const summary = page.locator('#score').locator('span').filter({ hasText: /^\d+$/ }).first();
    const before = (await summary.innerText()).trim();

    await toggle.click();
    await expect(toggle).toHaveAttribute('aria-expanded', 'false');

    // ⛔ **Still on screen with the body shut.** 📁 *"Collapsing cannot hide a
    // risk."*
    await expect(heading).toBeVisible();
    await expect(summary).toBeVisible();
    await expect(summary).toHaveText(before);
  });

  /**
   * 📁 ***"Anchor links from the page nav auto-expand the target section."***
   *
   * ⚡ **A real click on a real anchor**, which is the whole point: the rail
   * does not know about expansion and must not have to.
   */
  test('@journey a rail link opens the section it points at', async ({ page }) => {
    await openScoredAccount(page);

    const toggle = page.getByRole('button', { name: 'Account score' });
    await toggle.click();
    await expect(toggle).toHaveAttribute('aria-expanded', 'false');

    // ⚡ **The rail's own link**, not a synthesised hash change.
    await page.getByRole('navigation', { name: 'On this page' })
      .getByRole('link', { name: 'Account score' })
      .click();

    await expect(toggle).toHaveAttribute('aria-expanded', 'true');
  });

  /**
   * 📁 ***"Every section is a labelled region with a heading, reachable by
   * landmark navigation"*** — ⛔ **and *in every state* is part of the
   * sentence.**
   *
   * 🔴 **This is the regression that shipped and was caught**: the first
   * version made the heading a `span` inside the toggle, and every section
   * left the document outline.
   */
  test('@journey the section outline survives a collapse', async ({ page }) => {
    await openScoredAccount(page);

    // ⚠️ **The assertion is about SECTION headings, and the first version was
    // not.** ⛔ It counted every `h2` on the page and expected the total to be
    // unchanged — **and one of the collapsible bodies contains an `h2` of its
    // own**, which correctly leaves the accessibility tree when the body is
    // hidden. 📁 The design's rule is *"every SECTION is a labelled region with
    // a heading"*, so a content heading inside a shut body disappearing is the
    // feature rather than the defect. ✅ **Scoped to the rule it is enforcing.**
    // 🔴 **The design's names.** ⛔ **These read `['What contributed', 'What
    // changed']`** — 📁 both **invented**: *"What contributed"* appears **0
    // times in the 35-document snapshot** and *"What changed"* **0 times in
    // Account 360**, while the design titles the two sections ***"Account
    // score"*** and ***"Signals timeline"***.
    //
    // ⚠️ **This spec was already HALF-migrated and that is the useful part**:
    // line 83 expected the rail link *"Account score"* while the heading three
    // lines up expected *"What contributed"*, **so the rail and the section it
    // points at were asserted under two different names.** 🔴 **The rename made
    // that visible; it did not create it.**
    const sections = ['Account score', 'Signals timeline'];

    for (const name of sections) {
      // ⚡ **`exact`, and the reason has CHANGED with the rename.** ⛔ It used
      // to be that *"What changed"* is a prefix of the Signals body's own `h2`
      // *"What changed, and who says so"*, so a loose match resolved to both.
      // ✅ **That collision is gone** — the section is *"Signals timeline"*
      // now — ⚡ **and `exact` stays**: the body heading still leaves the
      // outline when the body is hidden, and an exact match is what keeps this
      // assertion about the SECTION rather than about whatever is inside it.
      await expect(page.getByRole('heading', { name, exact: true })).toBeVisible();
    }

    for (const name of sections) {
      await page.getByRole('button', { name }).click();
      await expect(page.getByRole('button', { name })).toHaveAttribute('aria-expanded', 'false');
    }

    // ⛔ **Two sections shut, and both are still in the outline.** ⚡ This is
    // the regression that shipped once: the heading was a `span` inside the
    // toggle, so collapsing removed the section from landmark navigation
    // entirely.
    for (const name of sections) {
      // ⚡ **`exact`, and the reason has CHANGED with the rename.** ⛔ It used
      // to be that *"What changed"* is a prefix of the Signals body's own `h2`
      // *"What changed, and who says so"*, so a loose match resolved to both.
      // ✅ **That collision is gone** — the section is *"Signals timeline"*
      // now — ⚡ **and `exact` stays**: the body heading still leaves the
      // outline when the body is hidden, and an exact match is what keeps this
      // assertion about the SECTION rather than about whatever is inside it.
      await expect(page.getByRole('heading', { name, exact: true })).toBeVisible();
    }
  });

  /**
   * 🔴 **Contacts & decision makers states what Signora cannot see** —
   * ⚠️ **and this is the section this lane wrongly called buildable.** ⛔ It
   * must render as an absence with a sentence, **never as an empty list and
   * never as the workspace's ICP committee.**
   */
  test('@journey Contacts says what is missing rather than showing the wrong people', async ({
    page,
  }) => {
    await openScoredAccount(page);

    const contacts = page.locator('#contacts');
    await expect(contacts).toBeVisible();
    await expect(contacts.getByRole('heading', { name: 'Contacts & decision makers' })).toBeVisible();

    // 📁 The absence sentence, not a roster and not "coming soon".
    await expect(contacts).toContainText('not who holds it');
    await expect(contacts).not.toContainText('coming soon');
  });
});
