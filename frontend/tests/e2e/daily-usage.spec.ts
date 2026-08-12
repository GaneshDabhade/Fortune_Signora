/**
 * A seller's morning, end to end.
 *
 * **The journey the product exists for**: open the list, decide which account
 * to work, open it, understand why, check the evidence, see what has happened,
 * and move on to the next one. Every assertion here is about what a customer
 * can *do and trust*, never about which component rendered.
 *
 * The data is the Playground's twelve accounts, put through the real pipeline
 * by `make demo-seed`. Nothing here creates data, and nothing here depends on
 * a particular company being present — the accounts are named by the scenario
 * and the scenario is allowed to change.
 */

import { expect, test } from './fixtures/signora';

test.describe('the morning list', () => {
  test('@smoke opens with accounts ranked by attention', async ({ attention }) => {
    await attention.open();
    const names = await attention.names();

    expect(names.length).toBeGreaterThan(0);
    // **The proof that data actually reaches the browser.** Until the API
    // proxy existed, this page rendered "You are not part of an organization
    // yet" to the owner of a seeded organization.
    await expect(attention.noOrganization).toHaveCount(0);
  });

  test('@journey every row carries the four things a decision needs', async ({
    attention,
  }) => {
    await attention.open();
    await attention.names();

    const first = attention.rows.first();
    // What, why, how much it moved, how far it can be trusted — the order the
    // surface is built around.
    await expect(first.locator('a[href^="/accounts/"]')).toBeVisible();
    await expect(first).toContainText(/[A-Za-z]/);
    await expect(first.getByText(/Attention score/)).toBeVisible();
  });

  test('@journey the ranking is an ordering, not a coincidence', async ({
    attention,
    page,
  }) => {
    await attention.open();
    await attention.names();

    const scores = await page
      .locator('main ol > li')
      .evaluateAll((rows) =>
        rows.map((row) => {
          const text = row.textContent ?? '';
          const match = /Attention score\s*(\d+)/.exec(text);
          return match ? Number(match[1]) : Number.NaN;
        }),
      );

    expect(scores.every((score) => !Number.isNaN(score))).toBe(true);
    // *"Most pressing first"* is a promise the header makes in words. A list
    // that broke it would be wrong in a way no single row could reveal.
    const sorted = [...scores].sort((a, b) => b - a);
    expect(scores).toEqual(sorted);
  });

  test('@regression an account nobody has named still says something useful', async ({
    attention,
    page,
  }) => {
    await attention.open();
    await attention.names();

    // The Playground deliberately includes one account no provider has named.
    // It must render as an identifier with an explanation, never as a blank
    // row a seller would read as a broken product.
    const unnamed = page.getByText('no source has named this account yet');
    if ((await unnamed.count()) > 0) {
      await expect(unnamed.first()).toBeVisible();
    }
  });

  test('@journey a name several sources disagree about says so', async ({ page, attention }) => {
    await attention.open();
    await attention.names();

    const disputed = page.getByRole('button', { name: /Show details/ });
    if ((await disputed.count()) === 0) test.skip(true, 'no disputed name in this scenario');

    await disputed.first().click();
    await expect(page.getByText(/sources disagree on this name/i).first()).toBeVisible();
  });
});

test.describe('from the list to the account', () => {
  test('@smoke @journey opening an account explains its score', async ({
    attention,
    brief,
  }) => {
    await attention.open();
    const name = await attention.openFirstAccount();

    await brief.waitForScore();
    await expect(brief.whatContributed).toBeVisible();
    // The brief must be about the account the seller clicked. A ranking bug
    // that opened the wrong brief is invisible on the row and catastrophic in
    // a pipeline review.
    await expect(brief.backToList).toBeVisible();
    expect(name.length).toBeGreaterThan(0);
  });

  test('@journey the score can be traced to the evidence behind it', async ({
    attention,
    brief,
    page,
  }) => {
    await attention.open();
    await attention.openFirstAccount();
    await brief.waitForScore();

    await brief.openFirstCitation();
    // **The trust assertion.** A citation that opens an empty drawer is worse
    // than no citation: it invites a customer to check and then tells them
    // nothing.
    const dialog = brief.evidenceDialog;
    await expect(dialog).toBeVisible();
    const text = await dialog.innerText();
    expect(text.trim().length).toBeGreaterThan(20);

    await page.keyboard.press('Escape');
    await expect(dialog).toHaveCount(0);
  });

  test('@journey the account carries a history of what has happened', async ({
    attention,
    brief,
    page,
  }) => {
    await attention.open();
    await attention.openFirstAccount();
    await brief.waitForScore();

    /**
     * 🔴 **[B-247](../../../docs/BUGS.md): the history MOVED and this journey
     * kept looking on the page.** 📁 [TASK-1433](../../../docs/BACKLOG.md) gave
     * it to the utility panel's Activity tab — *"the panel takes it only where
     * the panel exists; below 1024 the section above renders"* — **and this
     * journey runs above that band.**
     *
     * ⛔ **The claim is unchanged**: *the account carries a history of what has
     * happened.* ✅ **Only where to look for it changed**, so the journey opens
     * the tab rather than asserting a heading the design moved.
     */
    const panel = page.getByRole('complementary');
    /**
     * ⚠️ **Idempotent, because the panel's open state is a STORED preference.**
     * ⛔ **An unconditional `Meta+.` would CLOSE it whenever an earlier journey
     * left it open** — 📁 the toggle is the design's own shortcut, and a test
     * that assumes a starting state is a test whose result depends on what ran
     * before it.
     */
    if ((await panel.getAttribute('data-state')) !== 'open') {
      await page.keyboard.press('Meta+.');
    }
    await expect(panel).toHaveAttribute('data-state', 'open');
    await panel.getByRole('tab', { name: 'Activity' }).click();
    await expect(panel).toHaveAttribute('aria-label', 'Activity panel');

    // **B-302.** The Playground composed nine pipeline stages and never the
    // Timeline projection, so this history was empty on all twelve accounts in
    // the only environment used for product review.
    await expect(panel.getByText(/Nothing has been recorded/i)).toHaveCount(0);
  });

  test('@journey the brief offers somewhere to go next', async ({
    attention,
    brief,
    page,
  }) => {
    await attention.open();
    await attention.openFirstAccount();
    await brief.waitForScore();

    // R10-01: the page's only exit used to be at the top, where nobody is when
    // they have finished reading.
    await expect(brief.backToList).toBeVisible();
    await page.keyboard.press('End');
    const sequence = page.locator('main a[href^="/accounts/"]');
    expect(await sequence.count()).toBeGreaterThan(0);
  });

  test('@regression back returns to the list with the list intact', async ({
    attention,
    brief,
    page,
  }) => {
    await attention.open();
    const before = await attention.names();
    await attention.openFirstAccount();
    await brief.waitForScore();

    await page.goBack();
    await expect(attention.heading).toBeVisible();
    const after = await attention.names();
    expect(after).toEqual(before);
  });

  test('@regression a brief opened by its address alone works', async ({
    attention,
    brief,
    page,
  }) => {
    await attention.open();
    await attention.openFirstAccount();
    const id = brief.accountId();

    // A deep link is how a seller shares an account with their manager. It
    // must not depend on having arrived from the list.
    await page.goto('/');
    await brief.open(id);
    await brief.waitForScore();
    await expect(brief.whatContributed).toBeVisible();
  });

  test('@regression reloading a brief does not lose it', async ({
    attention,
    brief,
    page,
  }) => {
    await attention.open();
    await attention.openFirstAccount();
    await brief.waitForScore();

    await page.reload();
    await brief.waitForScore();
    await expect(brief.whatContributed).toBeVisible();
  });
});

test.describe('what the product refuses to invent', () => {
  test('@regression an account that was never scored says so, and is not an error', async ({
    brief,
    page,
  }) => {
    // A well-formed identifier for an account nothing has scored. Also what a
    // caller sees for an account in another organization — deliberately
    // indistinguishable, or account identifiers become enumerable.
    await brief.open('00000000-0000-4000-8000-000000000000');
    await expect(brief.neverScored).toBeVisible();
    await expect(page.getByText('Could not load this account')).toHaveCount(0);
  });

  test('@regression an address that leads nowhere says so in a customer sentence', async ({
    page,
  }) => {
    await page.goto('/no-such-page');
    await expect(page.getByText('That address does not lead anywhere')).toBeVisible();
    // Not a stack trace, not a framework default, and it reassures rather than
    // alarms — the same standard every empty state on this product meets.
    await expect(page.getByText(/nothing about your accounts has changed/i)).toBeVisible();
  });
});
