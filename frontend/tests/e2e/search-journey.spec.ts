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
    await page.goto('/');
    const search = page.getByRole('combobox', { name: 'Find an account by name' });
    await expect(search).toBeVisible();

    await search.fill('a');
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

