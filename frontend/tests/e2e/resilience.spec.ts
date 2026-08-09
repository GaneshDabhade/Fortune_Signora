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
    attention,
    page,
  }) => {
    await attention.open();
    const before = await attention.names();
    await page.reload();
    const after = await attention.names();

    // The ranking is computed by the pipeline, not by the browser. Two reads
    // of an unchanged workspace that disagreed would mean the order is not a
    // property of the data — which is the whole promise of the surface.
    expect(after).toEqual(before);
  });

  test('@regression forward after back returns to the account', async ({
    attention,
    brief,
    page,
  }) => {
    await attention.open();
    await attention.openFirstAccount();
    const url = page.url();
    await brief.waitForScore();

    await page.goBack();
    await expect(attention.heading).toBeVisible();
    await page.goForward();

    await expect(page).toHaveURL(url);
    await brief.waitForScore();
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
    await expect(second.getByRole('heading', { name: 'Attention', level: 1 })).toBeVisible();
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
    await expect(second.getByRole('heading', { name: 'Attention', level: 1 })).toBeVisible();

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
    attention,
  }) => {
    // The API is made to fail for this page only. Not a mock of the product's
    // own data — the request still goes to the real endpoint and the real
    // client handles the failure. What is simulated is the network, which is
    // the one thing a customer's environment genuinely does to us.
    await page.route('**/api/proxy/**/accounts*', (route) => route.abort('failed'));
    await attention.open();

    await expect(page.getByText('Could not load your accounts')).toBeVisible();
    // The wording is the point: it must reassure that nothing has *changed*,
    // because a seller's first thought on an error is that they lost work.
    await expect(page.getByText(/Nothing has changed about your accounts/i)).toBeVisible();
  });

  test('@regression a failed brief does not look like an empty account', async ({
    page,
    brief,
    attention,
  }) => {
    await attention.open();
    const links = await attention.accountLinks.first().getAttribute('href');
    const id = links?.split('/').pop() ?? '';

    await page.route('**/api/proxy/**/score', (route) => route.abort('failed'));
    await brief.open(id);

    // *"Could not load"* and *"nothing has scored this"* are different
    // sentences for different situations, and rendering the second for the
    // first would tell a customer a falsehood about their own data.
    await expect(page.getByText('Could not load this account')).toBeVisible();
    await expect(brief.neverScored).toHaveCount(0);
  });
});
