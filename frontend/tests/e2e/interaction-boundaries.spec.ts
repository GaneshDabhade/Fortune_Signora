/**
 * **Interaction boundaries** — B-307, generalised into the category it belongs to.
 *
 * The page scrolling behind an open dialog was reported and fixed as one bug.
 * It is not one bug. It is one answer to one of nine questions that every modal
 * in every product has to answer, and **the other eight had never been asked
 * here at all**:
 *
 * | | |
 * |---|---|
 * | Can the background **scroll**? | B-307 — it could. Fixed |
 * | Can the background receive **focus**? | Tab from inside must not walk out |
 * | Can the background receive **keyboard** events? | A shortcut behind a modal is a surprise |
 * | Can the background **update** unexpectedly? | Content moving behind a reader |
 * | Can background **navigation** occur? | A link behind the modal, still clickable |
 * | Can **browser history** change? | Does a dialog add an entry Back must undo? |
 * | Does **refresh** create inconsistent state? | Reload with a dialog open |
 * | Does **Escape** behave consistently? | Every dialog, every time |
 * | Does **focus return** correctly on close? | Or is the reader dropped at the top? |
 *
 * **A modal is a promise that the rest of the product has stopped.** Each
 * question is one way that promise gets broken, and a product that keeps eight
 * of them and breaks one still feels unfinished — which is why the useful unit
 * is the boundary rather than the defect.
 *
 * ## What is asserted, and what is deliberately observed
 *
 * Not everything below is a defect if it fails. **Where the product has made no
 * decision, this records what it does rather than inventing a requirement** —
 * a test that asserts a behaviour nobody chose is a test that will be deleted
 * the moment somebody chooses differently. Those cases annotate; the rest
 * assert.
 */

import { expect, test } from './fixtures/signora';

/** Open the first citation on the first account — the product's one modal that
 * a customer meets while reading rather than while editing. */
async function openReadingDialog(
  accounts: import('./pages/accounts').AccountsPage,
  brief: import('./pages/brief').BriefPage,
): Promise<void> {
  await accounts.open();
  await accounts.openFirstAccount();
  await brief.waitForScore();
  await brief.openFirstCitation();
}

/**
 * **What a focus trap actually promises, and what it does not.**
 *
 * The first version of this asserted *"focus is inside the dialog after every
 * Tab"*, and it failed — on a product whose trap is working correctly. Probing
 * where focus really goes settled it:
 *
 * ```
 *   INPUT [in dialog] → BUTTON "Cancel" [in dialog] → BODY → INPUT [in dialog] → …
 * ```
 *
 * **Chromium parks focus on `body` at the wrap point of every modal cycle.**
 * That is the platform behaving correctly, and an assertion that forbids it
 * would have to be deleted or weakened on the first browser upgrade.
 *
 * **The property that matters is the one a customer would notice**: *can the
 * keyboard reach the product behind the modal?* That survives the wrap, it
 * survives a browser upgrade, and it is what "modal" means.
 */
async function focusReachesNothingBehind(
  page: import('@playwright/test').Page,
  steps: number,
): Promise<string[]> {
  const escaped: string[] = [];
  for (let step = 0; step < steps; step += 1) {
    await page.keyboard.press('Tab');
    const landed = await page.evaluate(() => {
      const active = document.activeElement;
      if (!active || active === document.body) return null;
      // 🔴 **[B-248](../../../docs/BUGS.md): this asked whether focus was
      // inside `document.querySelector('dialog')` — THE FIRST dialog in the
      // document.** ⛔ **The shell now mounts a second**, so focus legitimately
      // held by the evidence dialog was reported as an escape.
      //
      // ✅ **`closest` asks the question the test actually means** — *is the
      // focused element inside **a** dialog?* — ⚠️ **and it cannot rot again
      // the next time the shell mounts one.**
      if (active.closest('dialog')) return null;
      return `${active.tagName} "${(active.textContent ?? '').trim().slice(0, 30)}"`;
    });
    if (landed) escaped.push(`after ${step + 1} tabs: ${landed}`);
  }
  return escaped;
}

test.describe('a dialog stops the rest of the product', () => {
  test('@a11y the keyboard cannot walk out of a dialog and into the page behind it', async ({
    page,
    accounts,
    brief,
  }) => {
    await openReadingDialog(accounts, brief);
    await expect(page.getByRole('dialog')).toBeVisible();

    // Twenty tabs is several times round any dialog here, so a leak would have
    // leaked repeatedly by the end.
    expect(await focusReachesNothingBehind(page, 20)).toEqual([]);
  });

  test('@a11y a control behind the dialog cannot be reached or activated', async ({
    page,
    accounts,
    brief,
  }) => {
    await openReadingDialog(accounts, brief);

    // The shell's navigation is always present and always behind the modal.
    const behind = page.getByRole('link', { name: 'Settings' }).first();
    await expect(behind).toBeVisible();

    // **Clicked through the backdrop on purpose.** `force` skips Playwright's
    // actionability wait, which would otherwise mask the question: the point
    // is not whether Playwright *would* click it, it is whether the browser
    // lets the click land on a control the modal claims to have disabled.
    const before = page.url();
    await behind.click({ force: true, timeout: 5_000 }).catch(() => undefined);
    expect(page.url(), 'a link behind the dialog navigated the page').toBe(before);
  });

  test('@regression Escape closes exactly one dialog and leaves the page where it was', async ({
    page,
    accounts,
    brief,
  }) => {
    await openReadingDialog(accounts, brief);
    const where = page.url();

    await page.keyboard.press('Escape');
    await expect(page.getByRole('dialog')).toHaveCount(0);
    expect(page.url(), 'closing a dialog navigated somewhere').toBe(where);

    // A second Escape on a page with nothing open must do nothing at all —
    // not go back, not clear the route, not close the shell.
    await page.keyboard.press('Escape');
    expect(page.url(), 'a stray Escape navigated the page').toBe(where);
  });

  test('@a11y closing returns focus to something, never to the bare page', async ({
    page,
    accounts,
    brief,
  }) => {
    await openReadingDialog(accounts, brief);
    await page.keyboard.press('Escape');
    await expect(page.getByRole('dialog')).toHaveCount(0);

    // **Focus on `<body>` is the reader being dropped.** The next Tab starts
    // from the top of the page rather than from the citation they were
    // reading, which on a long brief means scrolling back to find their place.
    const landed = await page.evaluate(() => ({
      tag: document.activeElement?.tagName ?? 'NONE',
      label: document.activeElement?.textContent?.trim().slice(0, 40) ?? '',
    }));
    test.info().annotations.push({
      type: 'focus-after-close',
      description: `${landed.tag} ${landed.label}`,
    });
    expect(landed.tag, 'focus was dropped to the page after closing a dialog').not.toBe('BODY');
  });
});

test.describe('a dialog and the browser', () => {
  test('@regression Back does not have to be pressed twice to leave a page with a dialog', async ({
    page,
    accounts,
    brief,
  }) => {
    await accounts.open();
    const listUrl = page.url();
    await accounts.openFirstAccount();
    await brief.waitForScore();
    await brief.openFirstCitation();
    await expect(page.getByRole('dialog')).toBeVisible();

    // **The question a customer asks with their thumb.** If opening a dialog
    // pushes a history entry, Back closes the dialog and the customer presses
    // it again — twice to do one thing. If it does not, Back leaves the brief
    // with the dialog open, and returning shows it closed. Both are defensible;
    // silently doing one while the design assumed the other is not.
    await page.goBack();
    await page.waitForURL(listUrl, { timeout: 15_000 });
    await expect(accounts.heading).toBeVisible();
    // No orphan: whatever Back did, it must not leave a dialog over the list.
    await expect(page.getByRole('dialog')).toHaveCount(0);
  });

  test('@regression reloading with a dialog open lands on a usable page, not a stuck one', async ({
    page,
    accounts,
    brief,
  }) => {
    await openReadingDialog(accounts, brief);
    await page.reload();

    // A dialog is view state and a reload is entitled to drop it. **What must
    // not survive is the modal's side effects** — a locked scroller with no
    // dialog above it is a page a customer cannot use and cannot diagnose,
    // and it is the exact failure mode the B-307 fix could have introduced.
    //
    // **Waits on the score, not on a level-1 heading.** The first version
    // waited for an `<h1>` and timed out, which is how [B-313](../../../docs/BUGS.md)
    // was found: the account brief has no top-level heading at all, only two
    // orphaned `<h2>`s. The test was wrong about this page and right about the
    // product.
    await brief.waitForScore();
    const overflow = await page.evaluate(() => getComputedStyle(document.body).overflow);
    expect(overflow, 'the page was left unscrollable with no dialog open').not.toBe('hidden');

    const scrollable = await page.evaluate(
      () => document.documentElement.scrollHeight > window.innerHeight + 100,
    );
    if (scrollable) {
      // **Move the pointer onto the content first.** `mouse.wheel` dispatches
      // wherever the pointer happens to be, and after a reload it is at (0,0)
      // — over the sidebar, which does not scroll the page. The first version
      // wheeled there, measured no movement, and reported the product as stuck
      // when the only thing stuck was the cursor.
      await page.mouse.move(700, 400);
      await page.mouse.wheel(0, 400);
      // **Polled, not read once.** A wheel gesture is not instantaneous —
      // reading `scrollY` on the next line reports the position before the
      // scroll has happened, which is indistinguishable from a page that
      // cannot scroll at all. The first version did exactly that and accused
      // the product of being stuck.
      await expect
        .poll(() => page.evaluate(() => window.scrollY), { timeout: 5_000 })
        .toBeGreaterThan(0);
    }
  });
});

test.describe('the page behind holds still', () => {
  test('@regression the content behind a dialog does not move while it is open', async ({
    page,
    accounts,
    brief,
  }) => {
    await accounts.open();
    await accounts.openFirstAccount();
    await brief.waitForScore();

    await brief.openFirstCitation();
    await expect(page.getByRole('dialog')).toBeVisible();
    // **Both readings are taken with the dialog already open and settled.**
    // Two reasons, and the second cost a red run: the `<dialog>` renders inside
    // `main`, so a baseline taken before it opened differs by the dialog's own
    // text — and the drawer opens on a placeholder title, *"The evidence behind
    // this"*, while the evidence is still in flight. A baseline taken then
    // changes a second later because **the dialog** loaded, and the test
    // reports the page moving when nothing on the page did.
    await expect
      .poll(async () => (await brief.evidenceDialog.innerText()).length, { timeout: 20_000 })
      .toBeGreaterThan(60);
    await page.waitForLoadState('networkidle');
    const before = await page.locator('main').innerText();

    // Long enough for a poll or a refetch to land if one exists. **A brief
    // that re-renders underneath a citation means the reader closes the modal
    // onto a different argument than the one they opened it from** — the score
    // they were checking has moved, and nothing told them.
    await page.waitForTimeout(6_000);
    const after = await page.locator('main').innerText();

    expect(after, 'the page behind the dialog changed while it was open').toBe(before);
    await page.keyboard.press('Escape');
  });
});

test.describe('the editing dialog answers the same questions', () => {
  test('@regression an edit dialog abandoned with Escape changes nothing', async ({
    page,
    business,
  }) => {
    await business.open();
    await expect(business.heading).toBeVisible();

    const abandoned = `E2E Abandoned ${Date.now()}`;
    await business.addProduct.click();
    await expect(business.dialog).toBeVisible();
    await business.productName.fill(abandoned);

    // **Escape on a half-typed form is the commonest thing a customer does**,
    // and the one place a modal must be sure it saves nothing. A dialog that
    // persists on dismiss is worse than one that loses work: the customer does
    // not know it happened.
    await page.keyboard.press('Escape');
    await expect(business.dialog).toHaveCount(0);

    // **Named, not compared.** The first version diffed the whole of `main`
    // before and after, and failed on a page that had merely finished loading
    // its remaining sections in between — a test reporting *"Escape saved the
    // form"* about a product that had done nothing of the kind. The precise
    // question is whether this product exists, and it survives the page
    // arriving in any order.
    await expect(business.productRow(abandoned)).toHaveCount(0);
    await page.reload();
    await expect(business.heading).toBeVisible();
    await expect(business.productRow(abandoned)).toHaveCount(0);
  });

  test('@a11y an edit dialog traps the keyboard too, not only the reading one', async ({
    page,
    business,
  }) => {
    await business.open();
    await business.addProduct.click();
    await expect(business.dialog).toBeVisible();

    // Asserted separately from the reading dialog on purpose. They share a
    // component today; a shared component is a reason to expect the same
    // answer, never a reason to stop asking the question.
    expect(await focusReachesNothingBehind(page, 15)).toEqual([]);
    await page.keyboard.press('Escape');
  });

  test('@a11y a dialog offers the keyboard something to land on', async ({
    page,
    accounts,
    brief,
  }) => {
    // ✅ **`test.fail()` REMOVED — [B-312](../../../docs/BUGS.md) is fixed**, and
    // removing this line is what its author asked for: *"turns red the moment
    // somebody fixes it, which is the prompt to delete this line."*
    //
    // ⚡ **The device worked exactly as designed.** A `test.skip()` would have
    // asserted nothing and been forgotten; this stayed red-when-correct until
    // the defect was gone, and then told the lane fixing it that it was done.
    // ⛔ **Both reasons it was not Lane B's are inside this lane's assignment**:
    // `components/ui` and the `product_surface` component test it breaks.
    await openReadingDialog(accounts, brief);

    // **The other half of a focus trap, and the half nobody checks.** Trapping
    // focus inside a dialog that contains nothing focusable does not protect a
    // keyboard user — it strands them: every Tab lands on `body`, there is
    // nothing to press, and the only way out is a key nothing on screen
    // mentions. [B-312](../../../docs/BUGS.md).
    const focusable = await page
      .getByRole('dialog')
      .locator('a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])')
      .count();
    expect(
      focusable,
      'the dialog contains nothing a keyboard can reach — Escape is the only way out, and nothing says so',
    ).toBeGreaterThan(0);

    await page.keyboard.press('Escape');
  });
});
