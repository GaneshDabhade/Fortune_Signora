/**
 * What happens when a customer does something the happy path did not expect.
 *
 * **Not edge cases — the ordinary week.** People refresh, they press back,
 * they leave a tab open over lunch, they double-click a button that felt slow,
 * and they paste a link to a colleague. Each of these has broken a SaaS
 * product I have used this year, and none of them appears in a golden-path
 * suite.
 */

import { expect, test } from './fixtures/signora';
import { OWNER } from './fixtures/personas';

test.describe('the browser, used the way people use it', () => {
  test('@regression refreshing the list keeps the same accounts in the same order', async ({
    accounts,
    page,
  }) => {
    await accounts.open();
    const before = await accounts.names();
    await page.reload();
    const after = await accounts.names();

    // The ranking is computed by the pipeline, not by the browser. Two reads
    // of an unchanged workspace that disagreed would mean the order is not a
    // property of the data — which is the whole promise of the surface.
    expect(after).toEqual(before);
  });

  test('@regression forward after back returns to the account', async ({
    accounts,
    brief,
    page,
  }) => {
    await accounts.open();
    await accounts.openFirstAccount();
    const url = page.url();
    // ⚠️ **Not `waitForScore()`.** 📁 Companies is the whole book in the book's
    // own order, and *"a Signora score is not on this list yet"* — so its first
    // row is whichever account sorts first, and the Playground's is one no
    // provider has scored. ⛔ That is a designed state, not a failure. 📁 The
    // claim here is *forward after back returns to the account*, so what must
    // be on screen either side of the journey is the brief.
    await expect(brief.backToList).toBeVisible({ timeout: 20_000 });

    await page.goBack();
    await expect(accounts.heading).toBeVisible();
    await page.goForward();

    await expect(page).toHaveURL(url);
    await expect(brief.backToList).toBeVisible({ timeout: 20_000 });
  });

  test('@regression the active organization survives a reload', async ({
    settings,
    page,
  }) => {
    await settings.open();
    await expect(settings.organizationsTable).toBeVisible();
    const active = await page.getByText('Active').first().locator('..').innerText();

    await page.reload();
    await expect(settings.organizationsTable).toBeVisible();
    const afterReload = await page.getByText('Active').first().locator('..').innerText();

    expect(afterReload).toBe(active);
  });

  test('@regression a second tab sees the same signed-in product', async ({
    page,
    context,
  }) => {
    await page.goto('/');
    const second = await context.newPage();
    await second.goto('/');

    // A session that only worked in the tab that created it would strand
    // anybody who opens an account in a new tab — which is how a seller reads
    // two accounts side by side.
    await expect(second.getByTestId('home')).toBeVisible();
    await second.close();
  });

});

/**
 * **Signing out is destructive to the suite, and that is correct behaviour.**
 *
 * The shared browser state every other test reuses is a session cookie, and
 * signing out revokes the session it names — server-side, for everybody
 * holding it. Run inside the shared state, this test would leave every
 * subsequent test signed out, which is exactly what it did on its first run:
 * four unrelated failures, all of them reading as broken screens.
 *
 * So it gets its own session, signs in itself, and destroys only its own.
 */
test.describe('signing out', () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test('@regression closes the product in every tab, not only the one that clicked', async ({
    page,
    context,
    signIn,
  }) => {
    await signIn(OWNER);

    const second = await context.newPage();
    await second.goto('/');
    await expect(second.getByTestId('home')).toBeVisible();

    /**
     * 🔴 **[B-249](../../../docs/BUGS.md), third and fourth instances.** ⛔ **The
     * row named two journeys and there were four**: `Sign out` moved into the
     * account menu with the address, in the same change
     * ([TASK-1440](../../../docs/BACKLOG.md)), and
     * [`account-menu.tsx`](../../components/shell/account-menu.tsx) gates its
     * contents on `open`.
     *
     * ⚡ **Recorded rather than quietly fixed**: the row's own point is that the
     * cause is a CLASS, not an accident — **and a class whose census was short
     * by two is worth saying out loud.**
     */
    await page.getByRole('button', { name: /^Account menu for / }).click();
    await page.getByRole('button', { name: 'Sign out' }).click();
    await page.waitForURL(/\/signin/, { timeout: 20_000 });

    // The second tab holds a rendered page; the session behind it is gone.
    // What must not happen is that it keeps working — a signed-out session
    // still serving data is the defect a shared machine turns into an
    // incident.
    await second.reload();
    await expect(second).toHaveURL(/\/signin/, { timeout: 20_000 });
    await second.close();
  });
});

test.describe('controls that are pressed twice', () => {
  test('@regression saving a product twice does not create two', async ({
    business,
    page,
  }) => {
    await business.open();
    await expect(business.heading).toBeVisible();

    const name = `E2E Double ${Date.now()}`;
    await business.addProduct.click();
    await business.productName.fill(name);

    // Two clicks as fast as a person who thought the first did not register.
    // The catalog is published as a whole with an `expected_version`, so a
    // second submission is either applied once or refused with a 409 — never a
    // duplicate row.
    //
    // **The dialog's fate is deliberately not asserted.** Closing on the first
    // success and staying open on a refusal are both defensible, and which one
    // happens depends on which click the server sees first. What must hold
    // either way is the outcome below: one product, not two.
    // The second click gets a short deadline of its own. Playwright waits for
    // actionability, and once the first save closes the dialog the button is
    // gone — so an unbounded second click waits out the whole test rather
    // than doing what a hurried person's second click does, which is nothing.
    await Promise.all([
      business.save.click(),
      business.save.click({ timeout: 2_000 }).catch(() => {}),
    ]);

    await page.reload();
    // One product, not two. Located by its edit control: the name legitimately
    // appears several times once saved, because three other declarations offer
    // it as a choice.
    await expect(page.getByRole('button', { name: `Edit ${name}` })).toHaveCount(1);
  });
});

test.describe('when the network is not cooperating', () => {
  test('@regression a failed list says so rather than showing nothing', async ({
    page,
    accounts,
  }) => {
    // The API is made to fail for this page only. Not a mock of the product's
    // own data — the request still goes to the real endpoint and the real
    // client handles the failure. What is simulated is the network, which is
    // the one thing a customer's environment genuinely does to us.
    await page.route('**/api/proxy/**/accounts*', (route) => route.abort('failed'));
    await accounts.open();

    /**
     * ⚠️ **The copy is Companies', and it used to be the retired screen's.**
     * ⛔ *"Could not load your accounts / Nothing has changed about your
     * accounts"* was the Attention list's wording; **Companies answers the
     * same fear in its own words**, and asserting the old strings against the
     * new screen would have failed for the right reason and read as a defect.
     *
     * ⚡ **`.first()` is required, not defensive**: 📁 `companies-failed-read.test.tsx`
     * records it — *"the page variant states it in a heading AND in a
     * sentence, and a single-match query would fail on a correct render."*
     */
    await expect(page.getByText(/could not load/i).first()).toBeVisible();
    // The wording is the point: it must reassure that nothing has been *lost*,
    // because a seller's first thought on an error is that they lost work.
    await expect(page.getByText(/no account has been removed/i)).toBeVisible();
  });

  test('@regression a failed brief does not look like an empty account', async ({
    page,
    brief,
    accounts,
  }) => {
    await accounts.open();
    const links = await accounts.accountLinks.first().getAttribute('href');
    const id = links?.split('/').pop() ?? '';

    await page.route('**/api/proxy/**/score', (route) => route.abort('failed'));
    await brief.open(id);

    // *"Could not load"* and *"nothing has scored this"* are different
    // sentences for different situations, and rendering the second for the
    // first would tell a customer a falsehood about their own data.
    // ⚡ **`.first()` for the reason above** — the brief states it in a heading
    // and again in the sentence beneath it.
    await expect(page.getByText('Could not load this account').first()).toBeVisible();
    await expect(brief.neverScored).toHaveCount(0);
  });
});
