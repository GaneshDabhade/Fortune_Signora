/**
 * The one thing Signora asks a seller to *do*.
 *
 * Everything else on the brief is an argument. This is where a person commits
 * to it, walks away from it, or says it was never real — and it is the only
 * place the product writes down a human decision rather than a computed one.
 *
 * ### Why these are the highest-trust assertions in the suite
 *
 * A decision is **permanent, attributed and dated**. If the product recorded
 * one it did not make, lost one it did, or attributed it to the wrong person,
 * a customer's account history becomes something they cannot cite — and the
 * whole product is a citation. So the assertions here are about the record,
 * not about the button.
 *
 * ### Deliberately gentle with the seeded data
 *
 * Taking an account on is reversible in practice and keeps it on the list; the
 * terminal moves remove it. **This suite performs one real `engaged`
 * transition and exercises the terminal ones up to the point of confirmation**
 * — enough to prove the dialog, the required reason and the refusal wording,
 * without spending a demonstration account per run. `make demo-seed` is the
 * reset if a run ever needs one.
 *
 * Runs last by filename, so a decision it records cannot change what an
 * earlier spec reads.
 */

import { expect, test } from './fixtures/signora';

/** Open the first account that still offers a given move. Returns its name, or
 * null when the seeded book has none left in that state. */
async function findAccountOffering(
  page: import('@playwright/test').Page,
  action: RegExp,
): Promise<string | null> {
  await page.goto('/');
  await expect(page.locator('main a[href^="/accounts/"]').first()).toBeVisible({
    timeout: 20_000,
  });
  const hrefs = await page
    .locator('main a[href^="/accounts/"]')
    .evaluateAll((links) => links.map((link) => link.getAttribute('href') ?? ''));

  for (const href of hrefs.slice(0, 6)) {
    await page.goto(href);
    await expect(page.getByText(/Account score \d+ out of 100/)).toBeVisible({
      timeout: 20_000,
    });
    if ((await page.getByRole('button', { name: action }).count()) > 0) return href;
  }
  return null;
}

test.describe('committing to an account', () => {
  test('@journey a seller takes an account on, and the product records who and why', async ({
    page,
  }) => {
    const href = await findAccountOffering(page, /^I'm working this$/);
    if (href === null) test.skip(true, 'every seeded account has already been decided');

    await page.getByRole('button', { name: "I'm working this" }).click();
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // **Ownership is stated, not applied quietly.** It is a fact about a
    // person, and one they should see being recorded.
    await expect(dialog).toContainText(/assigned to you/i);

    // The reason is required, and the control says so before the customer
    // submits rather than after.
    const confirm = dialog.getByRole('button', { name: 'Take it on' });
    await expect(confirm).toBeDisabled();

    const reason = `E2E: taking this on ${Date.now()}`;
    await dialog.getByRole('textbox').fill(reason);
    // **The permanence is disclosed at the moment of the decision**, not in a
    // help page somebody reads afterwards.
    await expect(dialog).toContainText(/permanently, with your name and the date/i);
    await expect(confirm).toBeEnabled();
    await confirm.click();

    // Not optimistic: the stage the page shows is the one the server accepted.
    await expect(page.getByText(/What has been decided/)).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText(reason)).toBeVisible();
  });

  test('@journey the decision survives a reload, because it is a record', async ({
    page,
  }) => {
    await page.goto('/');
    await expect(page.locator('main a[href^="/accounts/"]').first()).toBeVisible({
      timeout: 20_000,
    });
    // Any account that has been decided — including by the test above.
    const hrefs = await page
      .locator('main a[href^="/accounts/"]')
      .evaluateAll((links) => links.map((link) => link.getAttribute('href') ?? ''));

    for (const href of hrefs.slice(0, 6)) {
      await page.goto(href);
      await expect(page.getByText(/Account score \d+ out of 100/)).toBeVisible({
        timeout: 20_000,
      });
      const history = page.getByText('What has been decided');
      if ((await history.count()) === 0) continue;

      const before = await page
        .locator('section')
        .filter({ has: page.getByRole('heading', { name: 'What has been decided' }) })
        .innerText();
      await page.reload();
      await expect(page.getByText('What has been decided')).toBeVisible({ timeout: 20_000 });
      const after = await page
        .locator('section')
        .filter({ has: page.getByRole('heading', { name: 'What has been decided' }) })
        .innerText();
      expect(after).toBe(before);
      return;
    }
    test.skip(true, 'no account carries a decision yet');
  });
});

test.describe('walking away from an account', () => {
  test('@regression a terminal decision cannot be recorded without a reason', async ({
    page,
  }) => {
    const href = await findAccountOffering(page, /^Not a real opportunity$/);
    if (href === null) test.skip(true, 'no account offers this move');

    await page.getByRole('button', { name: 'Not a real opportunity' }).click();
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // **Deliberately not confirmed.** Proving the guard costs nothing;
    // confirming would spend a demonstration account to learn the same thing.
    await expect(dialog.getByRole('button', { name: 'Dismiss it' })).toBeDisabled();
    await dialog.getByRole('textbox').fill('a reason');
    await expect(dialog.getByRole('button', { name: 'Dismiss it' })).toBeEnabled();

    await page.keyboard.press('Escape');
    await expect(dialog).toHaveCount(0);
  });

  test('@regression cancelling a decision records nothing', async ({ page }) => {
    const href = await findAccountOffering(page, /^Not a real opportunity$/);
    if (href === null) test.skip(true, 'no account offers this move');

    const history = page
      .locator('section')
      .filter({ has: page.getByRole('heading', { name: 'What has been decided' }) });
    const read = async (): Promise<string> =>
      (await history.count()) > 0 ? history.innerText() : '';

    const before = await read();

    await page.getByRole('button', { name: 'Not a real opportunity' }).click();
    await page.getByRole('dialog').getByRole('textbox').fill('changed my mind');
    await page.getByRole('dialog').getByRole('button', { name: 'Cancel' }).click();
    await expect(page.getByRole('dialog')).toHaveCount(0);

    await page.reload();
    // **Wait for the page before reading it.** Comparing a loaded page with a
    // loading one reports a decision that was never recorded as a decision
    // that vanished.
    await expect(page.getByText(/Account score \d+ out of 100/)).toBeVisible({
      timeout: 20_000,
    });
    expect(await read()).toBe(before);
  });
});

test.describe('the decision is the end of a visit', () => {
  test('@journey a decided account offers somewhere to go, and staying is a real choice', async ({
    page,
  }) => {
    const href = await findAccountOffering(page, /^I'm working this$/);
    if (href === null) test.skip(true, 'every seeded account has already been decided');

    await page.getByRole('button', { name: "I'm working this" }).click();
    const dialog = page.getByRole('dialog');
    await dialog.getByRole('textbox').fill(`E2E: continuing the morning ${Date.now()}`);
    await dialog.getByRole('button', { name: 'Take it on' }).click();

    // **An offer, never a redirect.** R10-02: the decision is the one moment
    // the product can be certain the reader is done, and it used to close the
    // dialog and do nothing. *Stay here* is listed first and nothing moves
    // until the person says so.
    //
    // Two outcomes are correct — an offer, or a quiet close when there is
    // nowhere to go — so the wait is for either. **A refusal is reported in
    // the domain's own words rather than as a timeout**, because those
    // sentences were written to be read and they are the most useful thing on
    // the screen when a decision is rejected.
    const stay = dialog.getByRole('button', { name: 'Stay here' });
    await expect
      .poll(async () => (await stay.count()) > 0 || (await dialog.count()) === 0, {
        timeout: 20_000,
        message: async () =>
          `the decision neither closed nor offered a next step. The dialog said: ${
            (await dialog.count()) > 0 ? await dialog.innerText() : '(gone)'
          }`,
      })
      .toBe(true);

    if ((await dialog.count()) === 0) return; // nowhere to go: the last account
    const next = dialog.getByRole('button', { name: /^Next: / });

    await expect(stay).toBeVisible();
    await expect(next).toBeVisible();
    await stay.click();
    await expect(dialog).toHaveCount(0);
    // Still here, which is the whole point.
    await expect(page).toHaveURL(new RegExp(href.replace(/\//g, '\\/')));
  });
});
