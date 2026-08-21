/**
 * A seller's morning, end to end.
 *
 * **The journey the product exists for**: see what needs you, decide which
 * account to work, open it, understand why, check the evidence, see what has
 * happened, and move on to the next one. Every assertion here is about what a
 * customer can *do and trust*, never about which component rendered.
 *
 * 🔴 **The morning used to start on `/attention` and that screen is retired.**
 * 📁 The App Shell's nine destinations do not include it, and no design
 * document defines it. ⚡ **The morning now starts on Home** — 📁 *"Home tells
 * a person what to do next, using the workspace's own data, with a reason
 * attached to every item"* — **and the book of accounts is Companies.**
 * ⛔ **The tests below were re-aimed rather than deleted**: the promises they
 * assert are the design's, and only the surface carrying them changed.
 *
 * The data is the Playground's twelve accounts, put through the real pipeline
 * by `make demo-seed`. Nothing here creates data, and nothing here depends on
 * a particular company being present — the accounts are named by the scenario
 * and the scenario is allowed to change.
 */

import { expect, test } from './fixtures/signora';

test.describe('the morning list', () => {
  test('@smoke the book of accounts opens and is populated', async ({ accounts }) => {
    await accounts.open();
    const names = await accounts.names();

    expect(names.length).toBeGreaterThan(0);
    // **The proof that data actually reaches the browser.** Until the API
    // proxy existed, this page rendered "You are not part of an organization
    // yet" to the owner of a seeded organization.
    await expect(accounts.noOrganization).toHaveCount(0);
  });

  test('@journey every item Home raises carries a reason and a way in', async ({
    page,
  }) => {
    /**
     * 📁 **Home's registry, `card.attention`**: *"Up to five ordered items,
     * **each with a reason and a cost of ignoring it**"* — and 📁 P-08,
     * *"every attention item carries a reason."*
     *
     * ⚠️ **This asserted the retired screen's row anatomy** — an `Attention
     * score` per row in an ordered list. ⛔ **Companies is not that screen**:
     * it is the whole book, with its own columns, and re-pointing the old
     * assertion at it would have tested a promise nothing makes.
     */
    await page.goto('/');
    await page.waitForURL(/\/w\/[0-9a-f-]+\/home$/, { timeout: 30_000 });
    const card = page.locator('[data-card="needs-you-today"]');
    await expect(card).toBeVisible({ timeout: 20_000 });

    const first = card.locator('a[href^="/accounts/"]').first();
    await expect(first).toBeVisible({ timeout: 20_000 });
    // The account is named, the reason is written, and there is a way in.
    await expect(card).toContainText(/[A-Za-z]{3,}/);
    await expect(first).toHaveText('Open the account');
  });

  test('@journey Home ranks what needs you, and says by what', async ({ page }) => {
    /**
     * 📁 **`card.attention`, in the design's own words**: *"Up to five ordered
     * items"*, ranked — and the card states the basis in the header, because
     * *"most pressing first"* is a promise a reader cannot verify from one row.
     *
     * ⚠️ **The retired screen proved this by reading an `Attention score` off
     * every row and checking the sequence descended.** ⛔ **Home does not draw
     * a score per item** — 📁 its rows carry *"a reason and a cost of ignoring
     * it"* instead — **so the assertion is now the design's cap and its stated
     * basis**, which are the two claims Home actually makes.
     */
    await page.goto('/');
    await page.waitForURL(/\/w\/[0-9a-f-]+\/home$/, { timeout: 30_000 });
    const card = page.locator('[data-card="needs-you-today"]');
    await expect(card).toBeVisible({ timeout: 20_000 });
    await expect(card.locator('a[href^="/accounts/"]').first()).toBeVisible({ timeout: 20_000 });

    // 📁 *"Up to five ordered items"* — a sixth becomes *"See all N in Signals"*.
    const items = await card.locator('a[href^="/accounts/"]').count();
    expect(items).toBeGreaterThan(0);
    expect(items).toBeLessThanOrEqual(5);

    // ⛔ **The basis is stated rather than implied.** A ranked list that does
    // not say what it ranked by asks a reader to trust an order they cannot see.
    await expect(card.getByText(/Ranked by what it costs to ignore/i)).toBeVisible();
  });

  test('@regression an account nobody has named still says something useful', async ({
    accounts,
    page,
  }) => {
    await accounts.open();
    await accounts.names();

    // The Playground deliberately includes one account no provider has named.
    // It must render as an identifier with an explanation, never as a blank
    // row a seller would read as a broken product.
    const unnamed = page.getByText('no source has named this account yet');
    if ((await unnamed.count()) > 0) {
      await expect(unnamed.first()).toBeVisible();
    }
  });

  test('@journey a name several sources disagree about says so', async ({ page, accounts }) => {
    await accounts.open();
    await accounts.names();

    const disputed = page.getByRole('button', { name: /Show details/ });
    if ((await disputed.count()) === 0) test.skip(true, 'no disputed name in this scenario');

    await disputed.first().click();
    await expect(page.getByText(/sources disagree on this name/i).first()).toBeVisible();
  });
});

test.describe('from the list to the account', () => {
  test('@smoke @journey opening an account explains its score', async ({
    home,
    brief,
  }) => {
    await home.open();
    const opened = await home.openFirstRankedAccount();

    await brief.waitForScore();
    await expect(brief.whatContributed).toBeVisible();
    // The brief must be about the account the seller clicked. A ranking bug
    // that opened the wrong brief is invisible on the row and catastrophic in
    // a pipeline review.
    await expect(brief.title).toBeVisible();
    expect(brief.accountId()).toBe(opened);
  });

  test('@journey the score can be traced to the evidence behind it', async ({
    home,
    brief,
    page,
  }) => {
    await home.open();
    await home.openFirstRankedAccount();
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
    home,
    brief,
    page,
  }) => {
    await home.open();
    await home.openFirstRankedAccount();
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

  test('@journey the brief offers somewhere to go next', async ({ brief, page }) => {
    /**
     * ⚠️ **Entered from HOME, and the entrance is load-bearing.**
     *
     * 🔴 **Measured when the retired screen went**: entering from Companies
     * made this fail, and the product was right. 📁 The brief's *next in
     * sequence* is derived from `opportunity_engine`'s attention list — **open
     * opportunities, ranked** — and **Companies is the whole book**, so an
     * account with no open opportunity has no neighbours to offer. ⛔ **A page
     * object that quietly picked a scored row would have hidden that.**
     *
     * ⚠️ **Home's card is NOT the same list, and the earlier note here said it
     * was.** 📁 `card.attention` reads the **triage queue** — open signals,
     * ranked by what ignoring them costs — and one account may hold three of
     * them, so five items can be three accounts. 📁 The sequence reads
     * `opportunity_engine`'s attention list, which is **accounts with an open
     * opportunity**. ✅ **They overlap because an account earns an opportunity
     * from the same evidence that raises its signals**, which is why entering
     * from Home works — but *"by construction"* overstated it, and the
     * assertion below is what actually holds it.
     */
    await page.goto('/');
    await page.waitForURL(/\/w\/[0-9a-f-]+\/home$/, { timeout: 30_000 });
    const card = page.locator('[data-card="needs-you-today"]');
    await expect(card).toBeVisible({ timeout: 20_000 });
    await card.locator('a[href^="/accounts/"]').first().click();
    await page.waitForURL(/\/accounts\/[0-9a-f-]{36}/, { timeout: 20_000 });
    await brief.waitForScore();

    // R10-01: the page's only exit used to be at the top, where nobody is when
    // they have finished reading.
    await expect(brief.title).toBeVisible();
    await page.keyboard.press('End');
    // ⚠️ **`count()` does not auto-wait**, and the sequence renders on a query
    // that is still in flight when the score lands — 📁 *"it costs no request"*
    // only once `useAccounts` has resolved. ⛔ Counting immediately reported
    // *the brief offers nowhere to go* on a page that was about to offer two,
    // which is a flake that reads as a product defect.
    const sequence = page.locator('main a[href^="/accounts/"]');
    await expect(sequence.first()).toBeVisible({ timeout: 20_000 });
    expect(await sequence.count()).toBeGreaterThan(0);
  });

  test('@regression back returns to the list with the list intact', async ({
    accounts,
    brief,
    page,
  }) => {
    await accounts.open();
    const before = await accounts.names();
    await accounts.openFirstAccount();
    // ⚠️ **Not `waitForScore()`.** ⛔ Companies is the whole book in the book's
    // own order, so its first row is whichever account sorts first — and the
    // Playground's is one no provider has scored, which is a designed state
    // and not a failure. 📁 The claim under test is *back returns to the list
    // with the list intact*, so what this must wait for is a brief on screen.
    await expect(brief.title).toBeVisible({ timeout: 20_000 });

    await page.goBack();
    await expect(accounts.heading).toBeVisible();
    const after = await accounts.names();
    expect(after).toEqual(before);
  });

  test('@regression a brief opened by its address alone works', async ({
    home,
    brief,
    page,
  }) => {
    await home.open();
    const id = await home.openFirstRankedAccount();

    // A deep link is how a seller shares an account with their manager. It
    // must not depend on having arrived from the list.
    await page.goto('/');
    await brief.open(id);
    await brief.waitForScore();
    await expect(brief.whatContributed).toBeVisible();
  });

  test('@regression reloading a brief does not lose it', async ({
    home,
    brief,
    page,
  }) => {
    await home.open();
    await home.openFirstRankedAccount();
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
