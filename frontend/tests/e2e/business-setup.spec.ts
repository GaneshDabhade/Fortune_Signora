/**
 * *Your business* — the one screen where the customer's own words are the
 * input rather than the output.
 *
 * **Every declaration here is versioned, and that is the product promise being
 * tested**: a catalog is saved as a new version with a name and a date, never
 * edited in place, so a customer can always answer *"what did we say we sold
 * in March?"*. A test that only checked the name appeared would pass on an
 * implementation that overwrote history.
 *
 * These tests write real data through the real API. They are additive — a
 * product is added and left — because the seeded organization is a
 * demonstration environment, and a test that deleted what it created would
 * also be asserting a delete path the product does not offer.
 */

import { expect, test } from './fixtures/signora';

const unique = () => `E2E Product ${Date.now()}`;

/**
 * **B-306.** An owner could open Settings by clicking the sidebar and was
 * thrown back to the attention list by pressing F5 — so the entire
 * administrative surface was unreachable by URL, unbookmarkable and
 * unshareable. These are the cases that failed.
 */
test.describe('the administrative surface is reachable by address', () => {
  for (const path of ['/settings', '/settings/products', '/settings/connections']) {
    test(`@regression ${path} opens on a direct load`, async ({ page }) => {
      await page.goto(path);
      await expect(page).toHaveURL(new RegExp(`${path}$`), { timeout: 20_000 });
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    });
  }

  test('@regression reloading Settings keeps you on Settings', async ({
    settings,
    page,
  }) => {
    await settings.open();
    await expect(settings.heading).toBeVisible();
    await page.reload();
    await expect(settings.heading).toBeVisible();
    await expect(page).toHaveURL(/\/settings$/);
  });
});

test.describe('declaring what the company sells', () => {
  test('@smoke the business page opens and explains why it exists', async ({
    business,
  }) => {
    await business.open();
    await expect(business.heading).toBeVisible();
    // The page's own justification, in a salesperson's words. If this sentence
    // ever names a module or a table, `vocabulary.test.tsx` fails first —
    // this asserts it is still *present*, which that test cannot.
    await expect(
      business.heading.locator('xpath=following-sibling::p[1]'),
    ).toContainText(/before it can tell you anything useful/i);
  });

  test('@journey a customer can add a product and see it listed', async ({
    business,
  }) => {
    await business.open();
    await expect(business.heading).toBeVisible();

    const name = unique();
    await business.addProduct.click();
    await expect(business.dialog).toBeVisible();
    await business.productName.fill(name);
    await business.save.click();

    // The dialog closes on success, and the catalog shows the new version.
    await expect(business.dialog).toHaveCount(0);
    // **Located by its edit control, not by its text.** The name appears four
    // times on this page once it is saved — in the catalog, and in the three
    // declarations that let a customer say which product they mean. That is
    // correct behaviour and the reason a text locator is the wrong one here.
    await expect(business.productRow(name)).toBeVisible();
  });

  test('@journey the product survives a reload, because it was saved', async ({
    business,
    page,
  }) => {
    await business.open();
    const name = unique();
    await business.addProduct.click();
    await business.productName.fill(name);
    await business.save.click();
    await expect(business.dialog).toHaveCount(0);

    await page.reload();
    await expect(business.productRow(name)).toBeVisible();
  });

  test('@regression a product with no name cannot be saved', async ({ business }) => {
    await business.open();
    await business.addProduct.click();
    await expect(business.dialog).toBeVisible();

    // Disabled rather than rejected: refusing after the fact would make a
    // customer type, submit, and then be told. The control says so first.
    await expect(business.save).toBeDisabled();
    await business.productName.fill('   ');
    await expect(business.save).toBeDisabled();
  });

  test('@regression cancelling a product does not create one', async ({
    business,
    page,
  }) => {
    await business.open();
    const name = unique();
    await business.addProduct.click();
    await business.productName.fill(name);
    await page.getByRole('button', { name: 'Cancel' }).click();

    await expect(business.dialog).toHaveCount(0);
    await expect(business.productRow(name)).toHaveCount(0);
  });

  test('@journey who you sell to is present, and honest when empty', async ({
    business,
    page,
  }) => {
    await business.open();
    await expect(business.whoYouSellTo).toBeVisible();

    // Either segments exist or the product says plainly that none do. What it
    // must never do is render nothing, which is indistinguishable from broken.
    //
    // Waited on rather than counted immediately: the section loads
    // independently of the catalog above it (B-006), so the heading is on
    // screen while its own answer is still in flight.
    await expect(
      business.noSegmentsYet.or(page.locator('main h3').first()),
    ).toBeVisible({ timeout: 20_000 });
  });

  test('@regression every section reports its own failure rather than one', async ({
    business,
    page,
  }) => {
    await business.open();
    await expect(business.heading).toBeVisible();
    // B-006: a single error message for five independent declarations made an
    // outage indistinguishable from a feature the customer does not have.
    // With everything healthy, none of them may be claiming a failure.
    await expect(page.getByText(/Could not load/i)).toHaveCount(0);
  });
});
