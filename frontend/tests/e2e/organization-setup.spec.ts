/**
 * *Organization setup* — the administrative landing page, and the one screen
 * that has to be honest about what the product cannot do yet.
 *
 * **TASK-468**, against `docs/design-snapshot/screens/Workspace Setup.dc.html`.
 *
 * **What this journey exists to prove is the design's own rationale**:
 * *"Locked is shown, not hidden — removing them from the page makes
 * administrators think the product lost a feature."* A journey that only
 * created an organization would pass on a screen that silently dropped
 * region, URL, branding, domains and deletion — which is the failure the
 * rationale names.
 *
 * These write real data through the real API and are additive: an
 * organization is created and left, because the product offers no delete and
 * a test asserting one would be asserting a path that does not exist.
 */

import { expect, test } from './fixtures/signora';

const unique = () => `E2E Org ${Date.now()}`;

test.describe('a customer sets up an organization', () => {
  test('@regression /settings/organization opens on a direct load', async ({ page }) => {
    await page.goto('/settings/organization');
    await expect(page).toHaveURL(/\/settings\/organization$/, { timeout: 20_000 });
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });

  test('@regression Settings offers a way in', async ({ page }) => {
    // B-306's lesson: a screen reachable only by typing its URL is a screen
    // nobody finds. The reachability test asserts the link exists; this
    // asserts a person can actually follow it.
    await page.goto('/settings');
    await page.getByRole('link', { name: 'Organization setup' }).click();
    await expect(page).toHaveURL(/\/settings\/organization$/);
  });

  test('creates an organization and lands inside it', async ({ page }) => {
    const name = unique();
    await page.goto('/settings/organization');

    await page.getByLabel('Organization name').fill(name);
    await page.getByRole('button', { name: 'Create organization' }).click();

    // The organization the customer just made is the one they are now in —
    // the row's stated journey, and the half a creation form usually forgets.
    await expect(page.getByText(name).first()).toBeVisible({ timeout: 20_000 });
  });

  test('every capability is named, including the ones not built', async ({ page }) => {
    await page.goto('/settings/organization');

    for (const label of [
      'Organization URL',
      'Data region',
      'Logo',
      'Brand colour',
      'Delete this organization',
    ]) {
      await expect(page.getByText(label, { exact: true })).toBeVisible();
    }
  });

  test('offers no control for a capability the platform cannot answer', async ({
    page,
  }) => {
    await page.goto('/settings/organization');
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();

    // A region selector or a colour picker here would be mock business data
    // (§20c) — and worse than absent, because an administrator would use it
    // and believe the choice took effect.
    //
    // 🔴 **[B-249](../../../docs/BUGS.md): scoped to `main`, because the page
    // is not the screen.** 📁
    // [`AccountSearch`](../../components/intelligence/account-search.tsx)
    // carries `role="combobox"` and lives in the TOP BAR, **so a page-wide
    // query catches the shell's own search on every screen.** ⚡ **The assertion
    // means *this SCREEN offers no control the platform cannot answer*, and the
    // shell's search is neither this screen's nor unanswerable.**
    await expect(page.getByRole('main').getByRole('combobox')).toHaveCount(0);
  });

  /**
   * 🔴 **[B-245](../../../docs/BUGS.md) — which organization a person lands in
   * when they have several and have chosen none.**
   *
   * ⚡ **It belongs in THIS file and nowhere else**: the test above has just
   * created a second organization, which is B-245's precondition and is exactly
   * the state the row describes — *"a salesperson who creates a second
   * organization to try something out."* ⛔ **A spec of its own would have to
   * manufacture the same state a second time**, and this project already runs
   * as `MUTATOR` for the reason [B-1017](../../../docs/BUGS.md) gives.
   *
   * ⚠️ **The regression this catches is one no component test found.** The walk
   * used to run in an effect, so a render carried *"settled, and nothing
   * selected"* — **and the shell read it as rule 7 and navigated.** ⚡ **Measured
   * here first**: choose an organization, open `/accounts`, land back on
   * `/workspaces`, with a perfectly good last-used in `localStorage`.
   */
  test('@regression the chooser is offered once, and the choice sticks', async ({ page }) => {
    /**
     * ⛔ **This test establishes its own precondition rather than inheriting
     * one.** ⚠️ **It did not, and the run said so**: the test above creates one
     * organization, and this persona holds no seeded membership — 📁
     * [B-1017](../../../docs/BUGS.md) is why the mutating journeys run as a
     * persona of their own — **so the count was exactly one and rule 6
     * correctly declined to offer a chooser.**
     *
     * ⚡ **Two creations here, so the state holds under `-g` and under
     * `--repeat-each`**, where the test above may not have run at all. ⛔ **A
     * precondition that depends on another test's side effect is a
     * precondition nobody can see.**
     */
    for (const name of [unique(), unique()]) {
      await page.goto('/settings/organization');
      await page.getByLabel('Organization name').fill(name);
      await page.getByRole('button', { name: 'Create organization' }).click();
      await expect(page.getByText(name).first()).toBeVisible({ timeout: 20_000 });
    }

    // 📁 **Rule 7** — *"two or more active memberships and no pin, no
    // last-used… the chooser is mandatory here and only here."*
    await page.evaluate(() => window.localStorage.removeItem('signora.activeWorkspaceId'));
    await page.goto('/accounts');
    await expect(page).toHaveURL(/\/workspaces$/, { timeout: 20_000 });
    await expect(page.getByRole('heading', { name: 'Choose an organization' })).toBeVisible();

    /**
     * ⛔ **Rule 7's precondition, established from the SCREEN rather than from
     * a side channel.** ⚠️ **A `fetch('/api/proxy/workspaces')` from the page
     * carries no Authorization header** — the proxy mints one from the session
     * — **so it answered `0` and the precondition assertion refused the run**,
     * which is the guard behaving correctly about the wrong measurement.
     *
     * ⚡ **The rows the chooser draws ARE the membership count**, and asserting
     * on them means the precondition and the subject are the same fact.
     */
    const rows = page.getByRole('main').getByRole('button');
    await expect(
      rows,
      'rule 7 needs two or more memberships, and the chooser is offering fewer — ' +
        'the assertions below would pass for the wrong reason',
    ).not.toHaveCount(1);
    expect(await rows.count()).toBeGreaterThan(1);

    // ♿ 📁 `2.4.3` — *"WS-B places focus on the h1 on load, **not the search
    // field**, so the list is announced before the control."*
    await expect(page.locator('h1')).toBeFocused();

    // 📁 **Rule 4** — the choice is recorded and the next visit does not ask.
    await page.getByRole('main').getByRole('button').first().click();
    await expect(page).not.toHaveURL(/\/workspaces$/, { timeout: 20_000 });

    await page.goto('/accounts');
    // 🔴 **The regression.** ⛔ **Not `toHaveURL(/accounts/)` alone** — that
    // would pass on a redirect that happened to return here. ⚡ **The claim is
    // that the chooser is NOT offered again**, so the chooser is what is
    // asserted against.
    await expect(page).toHaveURL(/\/accounts$/, { timeout: 20_000 });
    await expect(
      page.getByRole('heading', { name: 'Choose an organization' }),
    ).toHaveCount(0);
  });

  test('never shows the customer the platform word', async ({ page }) => {
    await page.goto('/settings/organization');
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();

    // ADR-0034, and C-239: the approved design says "workspace" throughout
    // and a customer may not be shown it.
    const body = await page.locator('main').innerText();
    expect(body.toLowerCase()).not.toContain('workspace');
  });
});
