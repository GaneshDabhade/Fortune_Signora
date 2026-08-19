/**
 * **Search → Open Result** — [TASK-484](../../../docs/BACKLOG.md), the first of
 * the two journeys that work and nothing verifies.
 *
 * ⚠️ **In its own file, and that is a finding rather than a preference.**
 * The first draft appended it to `auth-journey.spec.ts` — **and the `owner`
 * project `testIgnore`s that file by name**, because it is the anonymous
 * suite. **A `test.use({ storageState })` inside it cannot override a project
 * that never collects the file.** ⛔ **So an authenticated journey placed
 * there runs anonymously, fails on the sign-in redirect, and looks like a
 * product defect.**
 */
import { expect, test } from '@playwright/test';

test.describe('Search → Open Result', () => {
  

  test('@journey a seller finds an account by name and opens it', async ({ page }) => {
    /**
     * 🔴 **The name is taken from the workspace, not written into the spec.**
     *
     * ⚠️ **This searched for `Databricks` and the Playground has no such
     * account** — its accounts are `Tessellate Security`, `Sandgate Retail
     * Systems`, `Northfield Data Systems` and so on. ⛔ **So the journey could
     * only ever fail**, and it failed in a way that read as a broken search
     * rather than as a query for something that is not there.
     *
     * ⚡ **A seller searches for an account they have.** Reading one from the
     * list first is both what a person does and what makes this survive the
     * next change to the seed — ⛔ swapping one hard-coded name for another
     * would leave the same trap for whoever reseeds next.
     */
    await page.goto('/accounts');
    const rows = page.locator('main a[href^="/accounts/"]');
    await expect(rows.first()).toBeVisible({ timeout: 20_000 });

    /**
     * ⚠️ **Not `rows.first()` — some rows have no name.** The Playground holds
     * accounts whose first line is a hex fragment of their id (`1b3880c3`),
     * because 📁 the list falls back to an identifier when a source supplied no
     * legal name. ⛔ **Searching for one of those finds nothing**, and which row
     * comes first varies under load — **which is exactly the flake this journey
     * had**: green alone, red beside two other spec files.
     *
     * ⚡ **The journey is *"finds an account BY NAME"***, so it needs an account
     * that has one.
     */
    const named = (await rows.allInnerTexts())
      .map((text) => (text.split('\n')[0] ?? '').trim())
      .find((text) => /^[A-Za-z][A-Za-z' ]{4,}$/.test(text));
    expect(named, 'no account in this workspace has a legal name to search for').toBeTruthy();
    const existing = named!;

    await page.goto('/');
    const search = page.getByRole('combobox', { name: 'Find an account by name' });
    await expect(search).toBeVisible();

    // ⚠️ **B-226 — this typed a single character and could never pass.**
    // `MINIMUM_QUERY = 2` has been the search's threshold since 2026-08-03
    // and the spec was written against it on 2026-08-08, so the listbox was
    // being waited for through a designed refusal.
    await search.fill(existing);
    // The listbox is the affordance the component's own comment defends:
    // *"a listbox rather than a menu — the results are a set of things to
    // choose"*. Waiting on it rather than on a timeout.
    const results = page.getByRole('listbox', { name: 'Accounts' });
    await expect(results).toBeVisible({ timeout: 15_000 });

    const first = results.getByRole('option').first();
    await expect(first).toBeVisible();
    const name = ((await first.textContent()) ?? '').trim();

    await first.click();

    // The destination is the assertion — the same lesson B-304 taught the
    // sign-in setup, where every session landed on a route nobody had.
    await page.waitForURL(/\/accounts\/[0-9a-f-]{36}/, { timeout: 20_000 });
    expect(name.length).toBeGreaterThan(0);
  });

  /**
   * 🔴 **[B-288](../../../docs/BUGS.md) — the whole region used to crash here.**
   *
   * ⚡ **A search that matches nothing is a normal thing to do**, and the
   * component has three designed sentences for it. ⛔ **What it actually did was
   * throw**: the endpoint returns one group per `EntityKind`, `person` was added
   * to that enum and never to the frontend's union, and
   * `KIND_LABEL['person'].toLowerCase()` took down the search region — **so the
   * seller lost the search box itself and got *"Signora could not load account
   * search"* until they reloaded.**
   */
  test('@journey a search that matches nothing says so, and the box survives', async ({
    page,
  }) => {
    await page.goto('/');
    const search = page.getByRole('combobox', { name: 'Find an account by name' });
    await expect(search).toBeVisible();

    await search.fill('Zzqqxx');

    // 📁 *"Nothing in accounts matches …"* — one of the three coverage
    // sentences, and ⛔ never the region's failure state.
    await expect(page.getByText(/Nothing in accounts matches/i)).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.getByText(/could not load account search/i)).toHaveCount(0);
    // ⛔ **The control is still there**, which is what a crash took away.
    await expect(search).toBeVisible();
  });

  test('search is reachable from the shell, not only by URL', async ({ page }) => {
    // Reachability, one level up from `infra/reachability.py`: a control that
    // exists only if you already know it is there is the Connection Center's
    // defect in a different costume.
    await page.goto('/');
    await expect(
      page.getByRole('combobox', { name: 'Find an account by name' }),
    ).toBeVisible();
  });
});

