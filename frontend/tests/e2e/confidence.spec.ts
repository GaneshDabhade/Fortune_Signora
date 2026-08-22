/**
 * The questions a customer never asks out loud, and judges the product by.
 *
 * *"What happens if my session expires while I'm typing?"* *"If the wifi drops
 * halfway through?"* *"If I have two tabs open?"* Nobody asks these. Everybody
 * notices the answer, once, and it decides whether they trust the product with
 * their week.
 *
 * **These are not edge cases and they are not error handling.** They are the
 * ordinary conditions of a laptop on a train, and they are where a mature SaaS
 * product distinguishes itself from a working one.
 *
 * ### The rule these tests hold the product to
 *
 * > **A customer must always be able to tell what happened, and always have a
 * > way forward.** Not *"nothing broke"* — a screen that silently shows less
 * > than it should is worse than an error, because the customer acts on it.
 */

import { expect, test } from './fixtures/signora';
import { OWNER } from './fixtures/personas';

test.describe('the session ends while somebody is working', () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test('@journey a session that ends mid-edit does not silently swallow the work', async ({
    page,
    context,
    signIn,
    business,
  }) => {
    await signIn(OWNER);
    await business.open();
    await expect(business.heading).toBeVisible();

    // Half-typed, exactly as somebody interrupted by a meeting leaves it.
    const halfTyped = `E2E Interrupted ${Date.now()}`;
    await business.addProduct.click();
    await business.productName.fill(halfTyped);

    // The session ends for real — server-side, the way an expiry does — while
    // the dialog is still open and the customer is still looking at it.
    await context.request.post('/api/auth/sign-out', {
      headers: { 'content-type': 'application/json' },
      data: {},
    });

    await business.save.click();

    // **Either outcome is defensible; disappearing is not.** The product may
    // refuse and say so, or it may bounce to sign-in. What it must never do is
    // close the dialog as though the work was saved.
    //
    // 🔴 **[B-246](../../../docs/BUGS.md): the loser of this race used to
    // REJECT.** ⛔ **`Promise.race` settles on the winner and leaves the other
    // promise running** — so the abandoned branch threw its timeout into
    // whichever test happened to be running twenty seconds later, **and the
    // failure was reported against a scenario that did nothing wrong.**
    //
    // ✅ **Both branches now resolve.** ⛔ **Not a wider timeout**, which only
    // moves the rejection further down the file.
    const signedOut = page
      .waitForURL(/\/signin/, { timeout: 20_000 })
      .then(() => 'sign-in' as const)
      .catch(() => 'never' as const);
    const stillHere = expect(business.dialog)
      .toBeVisible({ timeout: 20_000 })
      .then(() => 'dialog' as const)
      .catch(() => 'never' as const);
    const outcome = await Promise.race([signedOut, stillHere]);

    // ⚡ **`never` is not an outcome the product may produce** — it means the
    // dialog closed as though the work was saved, which is the one thing this
    // scenario exists to refuse.
    expect(outcome).not.toBe('never');

    test.info().annotations.push({
      type: 'session-expiry-outcome',
      description: outcome,
    });

    if (outcome === 'sign-in') {
      // Bounced. The one thing that must not have happened is a silent save.
      await signIn(OWNER);
      await business.open();
      await expect(business.productRow(halfTyped)).toHaveCount(0);
    }
  });
});

test.describe('the network is not what it was in development', () => {
  test('@journey a slow API shows something, rather than an empty screen', async ({
    page,
    accounts,
  }) => {
    // Three seconds is a bad hotel wifi, not a pathological case.
    await page.route('**/api/proxy/**/accounts*', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 3000));
      await route.continue();
    });

    await accounts.open();

    // **Once the page has painted, the content region must say something is
    // happening.** A blank region reads as a broken product and the reader
    // reloads, which starts the three seconds again.
    //
    // `innerText` cannot answer this and that is not a subtlety to skip over:
    // **a skeleton has no text**, so a check on the page's words reports a
    // blank screen for a screen that is correctly showing a loading state.
    // What a customer perceives is *something in the content region*, which is
    // text **or** a skeleton.
    await expect(accounts.heading).toBeVisible({ timeout: 20_000 });
    /**
     * ⚠️ **`rows` counted `ol > li` and the retired screen drew one.**
     * ⛔ Companies draws a table, and `ol > li` matched two unrelated elements
     * there — **so the guard below tripped on a correct loading state.**
     * ✅ **The row is what the page object says it is**, which is the same
     * definition every other assertion in these journeys uses.
     */
    const inFlight = await page.locator('main').evaluate((main) => ({
      skeletons: main.querySelectorAll('[data-skeleton]').length,
      rows: main.querySelectorAll('a[href^="/accounts/"]').length,
      words: (main.textContent ?? '').trim().length,
    }));

    // Still loading — otherwise this test is asserting nothing about loading.
    expect(inFlight.rows, 'the data arrived before the assertion could run').toBe(0);
    expect(
      inFlight.skeletons > 0 || inFlight.words > 20,
      'the content region was empty while a request was in flight',
    ).toBe(true);

    await expect(accounts.accountLinks.first()).toBeVisible({ timeout: 30_000 });
  });

  test('@journey losing the connection mid-visit is recoverable without a reload', async ({
    page,
    accounts,
    context,
  }) => {
    await accounts.open();
    await accounts.names();

    await context.setOffline(true);
    await page.goto('/settings/products').catch(() => undefined);
    await context.setOffline(false);

    // **The recovery is what is asserted, not the failure.** A customer who
    // reconnects should be able to carry on; needing to reload is the product
    // asking them to fix it.
    await page.goto('/');
    await expect(accounts.accountLinks.first()).toBeVisible({ timeout: 30_000 });
  });
});

test.describe('two tabs, one customer', () => {
  test('@journey a change in one tab is visible in the other after a refresh', async ({
    business,
    context,
  }) => {
    await business.open();
    await expect(business.heading).toBeVisible();

    const second = await context.newPage();
    await second.goto('/settings/products');
    await expect(
      second.getByRole('heading', { name: 'Your business', level: 1 }),
    ).toBeVisible({ timeout: 20_000 });

    const name = `E2E Two Tabs ${Date.now()}`;
    await business.addProduct.click();
    await business.productName.fill(name);
    await business.save.click();
    await expect(business.dialog).toHaveCount(0);

    // **Not asserted live.** Nothing in this product pushes, and pretending
    // otherwise would be a test asserting a capability that does not exist.
    // What must hold is that the second tab is not *stuck* on a stale view it
    // will never leave.
    await second.reload();
    await expect(second.getByRole('button', { name: `Edit ${name}` })).toBeVisible({
      timeout: 20_000,
    });
    await second.close();
  });

  test('@regression two tabs never disagree about who is signed in', async ({
    page,
    context,
  }) => {
    await page.goto('/');
    const second = await context.newPage();
    await second.goto('/settings');

    // 🔴 **`getByText` was matching a HIDDEN password label**, not the shell.
    // 📁 `B-429` moved the address into `AccountMenu`'s accessible name, so
    // the address is no longer bare text anywhere on a signed-in page — and
    // the loosest locator in the file then resolved to
    // *"Password for dana.reyes@…"* on a form that was not visible.
    // ⛔ **A test that passes by finding the wrong element is worse than one
    // that fails**: this one would have gone green again the moment any
    // hidden form mentioned the address.
    const identity = (target: typeof page) =>
      target.getByRole('button', { name: `Account menu for ${OWNER.email}` });
    await expect(identity(page)).toBeVisible();
    await expect(identity(second)).toBeVisible();
    await second.close();
  });
});

test.describe('the token behind every request', () => {
  test('@regression a rejected token is refreshed once, and the customer never sees it', async ({
    page,
    accounts,
  }) => {
    // The first proxied call is refused as though the token had just expired.
    // The client's documented behaviour is to mint a new one and retry **once**
    // — more would mask a real configuration fault as intermittent slowness.
    let refused = false;
    await page.route('**/api/proxy/**/accounts*', async (route) => {
      if (!refused) {
        refused = true;
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({
            error: { code: 'unauthenticated', message: 'expired', correlation_id: 'e2e' },
          }),
        });
        return;
      }
      await route.continue();
    });

    await accounts.open();
    // The list arrives anyway. A customer whose token expired mid-morning
    // should never learn that it did.
    await expect(accounts.accountLinks.first()).toBeVisible({ timeout: 30_000 });
    expect(refused, 'the 401 was never exercised').toBe(true);
  });
});

/**
 * **A permission change mid-session cannot be tested, because a customer
 * cannot make one.**
 *
 * `GET` and `POST /workspaces/{id}/members` exist; there is **no `PATCH` and no
 * `DELETE`**. A role cannot be changed and a member cannot be removed, by
 * anybody, through any surface. So the journey *"my manager demotes me while I
 * have Settings open"* has no customer path to exercise.
 *
 * **Recorded here rather than skipped silently**, because the absence is the
 * finding: it is the same shape as the two-roles-where-reviewers-asked-for-five
 * observation, and it is an enterprise-readiness gap rather than a defect.
 *
 * ⚠️ **This carried an empty `test.skip('…', () => {})` until 2026-08-19.**
 * ⛔ **A test with no body that is always skipped is a comment wearing a test's
 * clothes** — it can never fail, so it protects nothing, and it inflated the
 * suite's count with a case that was never a case (`CLAUDE.md` §2: *a guard
 * that cannot fail is not protection*). ✅ **The note is kept because the
 * observation is real; the fake test is gone because it was not.**
 */

