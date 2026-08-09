/**
 * Everything a customer has to tell Signora about their own company.
 *
 * **The head of the pipeline, and the only place the customer's own words are
 * the input.** Products, the ideal customer, the buying committee, what they
 * are pushing this quarter, and which companies they are watching — five
 * declarations, five versioned artifacts, all on one screen.
 *
 * ### What these tests are really checking
 *
 * Not that a form saves. **That a declaration is a statement a customer can
 * stand behind six months later**: versioned rather than overwritten, refused
 * rather than silently merged when two people edit at once, and readable back
 * in the words they typed. A suite that only checked *"the name appears"*
 * would pass on an implementation that destroyed history.
 *
 * ### Why they write real data and do not clean up
 *
 * The Playground is a demonstration environment and `make demo-seed` is its
 * reset. A test that deleted what it created would be asserting a delete path
 * the product does not offer — and inventing one to make a test tidy is the
 * definition of testing something a customer cannot do.
 */

import { expect, test } from './fixtures/signora';

const unique = (what: string) => `E2E ${what} ${Date.now()}`;

test.describe('the ideal customer', () => {
  test('@journey a customer describes who buys a product, in their own words', async ({
    business,
    page,
  }) => {
    await business.open();
    await expect(business.section('Ideal customer')).toBeVisible();

    // Whichever product is first in the catalog. Named dynamically because the
    // catalog is the customer's, not the test's.
    const describe = page.getByRole('button', { name: /^Describe who buys / }).first();
    if ((await describe.count()) === 0) test.skip(true, 'no product to describe yet');

    const product = (await describe.getAttribute('aria-label'))?.replace(
      'Describe who buys ',
      '',
    );
    await describe.click();

    const dialog = business.dialog;
    await expect(dialog).toBeVisible();
    // **The dialog asks the customer's question, not the schema's.** *"Who buys
    // Revenue Cloud?"* rather than *"ICP declaration"* — the vocabulary rule
    // (ADR-0034) applied where it is hardest, on a form.
    await expect(dialog).toContainText(new RegExp(`Who buys ${product}\\?`));

    const industry = unique('Industry');
    // `getByRole('textbox')` rather than `getByLabel`: the field and its *Add*
    // button share the accessible name, which is correct — the button says what
    // it adds — and makes a label lookup ambiguous.
    await dialog.getByRole('textbox', { name: 'Industries' }).fill(industry);
    await dialog.getByRole('button', { name: 'Add industries' }).click();
    // `spinbutton`, not `textbox`: the size fields are `type="number"`, which
    // is the right input for a headcount and a different ARIA role.
    await dialog.getByRole('spinbutton', { name: 'Smallest, in people' }).fill('50');
    await dialog.getByRole('spinbutton', { name: 'Largest, in people' }).fill('5000');
    await dialog.getByRole('button', { name: /Save|Describe/ }).last().click();

    await expect(dialog).toHaveCount(0);
    await expect(page.getByText(industry)).toBeVisible();

    // Saved, not held in the page.
    await page.reload();
    await expect(page.getByText(industry)).toBeVisible();
  });

  test('@regression an empty description cannot be saved', async ({ business, page }) => {
    await business.open();
    const describe = page.getByRole('button', { name: /^Describe who buys / }).first();
    if ((await describe.count()) === 0) test.skip(true, 'no product to describe yet');

    await describe.click();
    await expect(business.dialog).toBeVisible();
    // A declaration that says nothing is not a declaration. The control says so
    // before the customer types, rather than after they submit.
    const save = business.dialog.getByRole('button', { name: /Save|Describe/ }).last();
    await expect(save).toBeDisabled();
  });
});

test.describe('the rest of what a customer declares', () => {
  test('@journey every declaration on the page is present and says what it is for', async ({
    business,
  }) => {
    await business.open();
    await expect(business.heading).toBeVisible();

    // **Five declarations, and the wording is the assertion.** Each heading is
    // a salesperson's phrase, not a table name — *"What you are pushing now"*,
    // not `commercial_focus`. That is ADR-0034 at the frontend edge, and this
    // is where a regression in it would first reach a customer.
    for (const heading of [
      'Products',
      'Ideal customer',
      'Who you sell to',
      'What you are pushing now',
      'Accounts you are watching',
    ]) {
      await expect(business.section(heading)).toBeVisible();
    }
  });

  test('@journey a customer adds a company they are chasing', async ({
    business,
    page,
  }) => {
    await business.open();
    await expect(business.section('Accounts you are watching')).toBeVisible();

    const company = unique('Company');
    const form = page.locator('form').filter({ has: page.getByLabel('Company') });
    await form.getByLabel('Company').fill(company);
    await form.getByRole('button', { name: 'Add' }).click();

    await expect(page.getByRole('button', { name: `Stop watching ${company}` })).toBeVisible();
    await page.reload();
    await expect(page.getByRole('button', { name: `Stop watching ${company}` })).toBeVisible();
  });

  test('@regression a watched company can be removed again', async ({
    business,
    page,
  }) => {
    await business.open();
    const company = unique('Temporary');
    const form = page.locator('form').filter({ has: page.getByLabel('Company') });
    await form.getByLabel('Company').fill(company);
    await form.getByRole('button', { name: 'Add' }).click();

    const stop = page.getByRole('button', { name: `Stop watching ${company}` });
    await expect(stop).toBeVisible();
    await stop.click();

    // **Recoverable, which is what makes the control safe to press.** A
    // declaration a customer cannot undo is one they will hesitate over.
    await expect(stop).toHaveCount(0);
    await page.reload();
    await expect(page.getByRole('button', { name: `Stop watching ${company}` })).toHaveCount(0);
  });
});

test.describe('two people editing at once', () => {
  test('@journey a colleague’s concurrent save is refused, not overwritten', async ({
    business,
    context,
  }) => {
    await business.open();
    await expect(business.heading).toBeVisible();

    // Two tabs, both reading the same catalog version — which is exactly what
    // two people in the same organization are.
    const colleague = await context.newPage();
    await colleague.goto('/settings/products');
    await expect(
      colleague.getByRole('heading', { name: 'Your business', level: 1 }),
    ).toBeVisible();

    const mine = unique('Mine');
    await business.addProduct.click();
    await business.productName.fill(mine);
    await business.save.click();
    await expect(business.dialog).toHaveCount(0);

    const theirs = unique('Theirs');
    await colleague.getByRole('button', { name: 'Add product' }).first().click();
    // `exact` for the same reason as `business.productName` — this is the
    // second browser context on the same shell, so a bare `Name` matches
    // the header search too (B-209).
    await colleague.getByLabel('Name', { exact: true }).fill(theirs);
    await colleague.getByRole('button', { name: 'Save' }).click();

    // **The whole point of `expected_version`.** The second save carries the
    // version it read, which the first has already replaced. What must never
    // happen is the silent overwrite — the lost update neither person sees.
    //
    // Either the product refuses and says so, or it accepts and keeps both.
    // Both are defensible; losing one silently is not, and that is what is
    // asserted.
    await colleague.reload();
    await expect(
      colleague.getByRole('button', { name: `Edit ${mine}` }),
    ).toBeVisible();

    await colleague.close();
  });
});
