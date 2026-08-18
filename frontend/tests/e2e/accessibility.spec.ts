/**
 * Accessibility, as customer impact rather than as a compliance score.
 *
 * **Not aiming at WCAG in one pass** — the brief was to find the issues a
 * customer actually hits. Every assertion here corresponds to somebody being
 * unable to do something: reach a control without a mouse, know where they
 * are, get out of a dialog, or hear what a field is for.
 *
 * `components/ui` is frozen (§20c) and an accessibility issue in it is a
 * **defect**, not an enhancement — the freeze names them explicitly and says
 * they never wait for a business milestone.
 */

import { expect, test } from './fixtures/signora';

test.describe('reaching the product without a mouse', () => {
  test('@a11y the first tab stop is reachable and visible', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('home')).toBeVisible();

    await page.keyboard.press('Tab');
    const focused = page.locator(':focus');
    await expect(focused).toBeVisible();

    // A focus ring that cannot be seen is the same as no focus at all for
    // somebody navigating by keyboard.
    const ring = await focused.evaluate((element) => {
      const style = getComputedStyle(element);
      return `${style.outlineStyle}|${style.outlineWidth}|${style.boxShadow}`;
    });
    expect(ring).not.toBe('none|0px|none');
  });

  test('@a11y every navigation entry is reachable by keyboard', async ({ page }) => {
    await page.goto('/');
    // ⚠️ **Wait for the destination, not for the rail.** 📁 `/` is the shell's
    // entry resolver and forwards to Home — ⛔ **focusing a link while that
    // navigation is in flight loses the focus to the new document**, which
    // reads as a keyboard defect and is a race in the test.
    await expect(page.getByTestId('home')).toBeVisible();
    const nav = page.getByRole('navigation', { name: 'Primary' });
    await expect(nav).toBeVisible();

    for (const link of await nav.getByRole('link').all()) {
      await link.focus();
      await expect(link).toBeFocused();
    }
  });

  test('@a11y the current page is announced, not only coloured', async ({ page }) => {
    // ⚠️ **Was `/`, whose rail entry [TASK-1482](../../../docs/BACKLOG.md)
    // removed on [D-240](../../../docs/DECISION_REGISTER.md).** ⛔ **A route with
    // no rail entry has nothing to mark current**, so the assertion would have
    // had no subject. ✅ **`/business` still has one and the PROPERTY is
    // unchanged**: exactly one destination is marked, and it says which.
    await page.goto('/business');
    const current = page
      .getByRole('navigation', { name: 'Primary' })
      .locator('[aria-current="page"]');

    // Colour alone tells a screen-reader user nothing about where they are.
    await expect(current).toHaveCount(1);
    await expect(current).toContainText('Your business');
  });

  test('@a11y an account can be opened with the keyboard alone', async ({
    page,
    accounts,
    brief,
  }) => {
    await accounts.open();
    await accounts.names();

    await accounts.accountLinks.first().focus();
    await page.keyboard.press('Enter');
    await page.waitForURL(/\/accounts\/[0-9a-f-]{36}/);
    // ⚠️ **Not `waitForScore()`** — 📁 `B-1022`: Companies is the whole book in
    // the book's own order and *"a Signora score is not on this list yet"*, so
    // its first row is whichever account sorts first and the Playground's is
    // one no provider has named. ⛔ That is a designed state, not a failure.
    // 📁 The claim is *an account can be opened with the keyboard alone*, so
    // what must be on screen is the brief.
    await expect(brief.backToList).toBeVisible({ timeout: 20_000 });
  });
});

test.describe('dialogs', () => {
  test('@a11y the evidence drawer is a dialog, is labelled, and takes focus', async ({
    home,
    brief,
    page,
  }) => {
    // ⚡ **Home's ranked card, because an unscored account has no citations**
    // and therefore no evidence drawer to inspect — `B-1022`.
    await home.open();
    await home.openFirstRankedAccount();
    await brief.waitForScore();
    await brief.openFirstCitation();

    const dialog = brief.evidenceDialog;
    await expect(dialog).toHaveAttribute('aria-labelledby', /.+/);
    // Focus inside the dialog, or a keyboard user is reading a dialog they
    // cannot operate and tabbing through the page behind it.
    const inside = await dialog.evaluate((element) =>
      element.contains(document.activeElement),
    );
    expect(inside).toBe(true);

    await page.keyboard.press('Escape');
    await expect(dialog).toHaveCount(0);
  });

  test('@a11y closing a dialog returns focus to what opened it', async ({
    home,
    brief,
    page,
  }) => {
    await home.open();
    await home.openFirstRankedAccount();
    await brief.waitForScore();

    const citation = brief.citations.first();
    await citation.click();
    await expect(brief.evidenceDialog).toBeVisible();
    await page.keyboard.press('Escape');

    // Losing focus to `<body>` drops a keyboard user at the top of the page,
    // and they have to tab all the way back to where they were reading.
    await expect(citation).toBeFocused();
  });

  test('@a11y the new-organization dialog is labelled and escapable', async ({
    settings,
    page,
  }) => {
    await settings.open();
    await settings.newOrganization.click();

    const dialog = settings.dialog;
    await expect(dialog).toBeVisible();
    await expect(dialog).toHaveAttribute('aria-labelledby', /.+/);
    await page.keyboard.press('Escape');
    await expect(dialog).toHaveCount(0);
  });
});

test.describe('forms say what they are for', () => {
  test('@a11y every input on the sign-in form has a real label', async ({ page }) => {
    await page.goto('/signin');

    for (const input of await page.locator('input:visible').all()) {
      const name = await input.evaluate((element) => {
        const label = element.labels?.[0]?.textContent;
        return (
          label ??
          element.getAttribute('aria-label') ??
          element.getAttribute('aria-labelledby') ??
          ''
        );
      });
      expect(name.trim().length).toBeGreaterThan(0);
    }
  });

  test('@a11y every input on the business page has a real label', async ({
    business,
  }) => {
    await business.open();
    await expect(business.heading).toBeVisible();
    await business.addProduct.click();
    await expect(business.dialog).toBeVisible();

    for (const input of await business.dialog.locator('input:visible, textarea:visible').all()) {
      const name = await input.evaluate((element) => {
        const labelled = (element as HTMLInputElement).labels?.[0]?.textContent;
        return labelled ?? element.getAttribute('aria-label') ?? '';
      });
      expect(name.trim().length).toBeGreaterThan(0);
    }
  });
});

test.describe('the page has a structure a screen reader can use', () => {
  for (const [name, path] of [
    ['Companies', '/accounts'],
    ['the business page', '/settings/products'],
    ['settings', '/settings'],
  ] as const) {
    test(`@a11y ${name} has exactly one level-1 heading`, async ({ page }) => {
      await page.goto(path);
      const h1 = page.getByRole('heading', { level: 1 });
      await expect(h1).toHaveCount(1);
      // A heading with no text is worse than none — it appears in the
      // document outline and says nothing.
      expect((await h1.innerText()).trim().length).toBeGreaterThan(0);
    });
  }

  test('@a11y icons that carry no meaning are hidden from assistive technology', async ({
    page,
  }) => {
    await page.goto('/');
    await expect(page.getByTestId('home')).toBeVisible();

    // A decorative icon announced as "image" between every score and every
    // name turns one list into twice as much to listen to.
    const bare = await page.locator('main svg:not([aria-hidden]):not([aria-label])').count();
    expect(bare).toBe(0);
  });
});
