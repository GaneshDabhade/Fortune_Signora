/**
 * The same product, seen by somebody who administers nothing.
 *
 * **Two independent guarantees, and the suite asserts both separately**
 * because they fail in opposite directions and a customer cannot tell them
 * apart until the day one is missing:
 *
 *   the **courtesy** — a member is not offered a control the server will
 *   refuse, because a control that goes nowhere costs more trust than an
 *   absent one;
 *
 *   the **enforcement** — Casbin refuses the request regardless, so hiding the
 *   link is never what protects anything (ADR-0010).
 *
 * A suite that only checked the first would pass on a product whose server had
 * stopped enforcing anything at all.
 */

import { expect, test } from './fixtures/signora';
import { MEMBER } from './fixtures/personas';

test.describe('a member of the organization', () => {
  test('@smoke sees their morning like everybody else', async ({ attention, page }) => {
    await attention.open();
    const names = await attention.names();

    expect(names.length).toBeGreaterThan(0);
    // The intelligence surface is not an administrative capability. A member
    // who could not see the list would have no product at all.
    //
    // ⚠️ **Scoped to the profile link — B-225.** This read
    // `getByText(MEMBER.email)` and had been failing since 2026-08-08:
    // the shell renders the address TWICE by design, a desktop link and a
    // mobile span, and Playwright's strict mode counts matches in the DOM
    // rather than visible ones. The duplicate render is correct; the query
    // was wrong. Same repair as the shell's second wordmark in
    // `app-shell-rail.test.tsx`, and it asserts something stronger than
    // before: not that the address appears somewhere, but that it is the
    // link to their own profile.
    await expect(page.getByRole('link', { name: MEMBER.email })).toBeVisible();
  });

  test('@journey sees Settings as restricted rather than absent', async ({ page }) => {
    /**
     * 🔴 **REVERSED by TASK-1439 under D-225.** This asserted Settings was
     * absent. 📁 The App Shell design says the opposite — *"restricted
     * destinations stay visible at 45% with a lock and explain on click"* —
     * and [D-154](../../../docs/DECISION_REGISTER.md) settles which wins:
     * *"if an existing visual implementation differs from the finalized
     * design, the design wins. Always."*
     *
     * ⛔ **Nothing about REACHABILITY changed**, and the next test still
     * proves it: there is no link to follow, and the server refuses the
     * request regardless. **What changed is that a member is told the room
     * exists and who holds the key.**
     */
    await page.goto('/');
    const rail = page.getByRole('navigation', { name: 'Primary' });
    await expect(rail).toBeVisible();

    // Visible, and not followable.
    await expect(rail.getByRole('link', { name: 'Settings' })).toHaveCount(0);
    await expect(rail.getByLabel(/Settings — restricted/)).toBeVisible();

    // 📁 *"explain on click"* — and it names who can grant it, because a
    // person who is only refused asks for the wrong thing or asks nobody.
    await rail.getByLabel(/Settings — restricted/).first().click();
    await expect(page.getByText(/available to an owner/i)).toBeVisible();

    // ⚠️ **Was `Attention`** — [TASK-1482](../../../docs/BACKLOG.md) removed
    // that entry on [D-240](../../../docs/DECISION_REGISTER.md). ⛔ **The
    // property is unchanged and is the point of the assertion**: a member who
    // was just refused Settings still sees the destinations they DO hold, so
    // the rail is not reduced to what they cannot reach.
    await expect(rail.getByRole('link', { name: 'Your business' })).toBeVisible();
  });

  test('@regression typing the settings address does not open it', async ({ page }) => {
    await page.goto('/settings');
    // The client guard redirects. This is a courtesy and the test says so —
    // the next test is the one that proves anything.
    await expect(page).toHaveURL((url) => url.pathname === '/', { timeout: 20_000 });
  });

  test('@regression the server refuses an administrative write regardless', async ({
    page,
  }) => {
    await page.goto('/');
    // The caller's own real token, from the real exchange the browser uses.
    const token = await (await page.request.post('/api/token')).json();
    const workspaces = await (
      await page.request.get('/api/proxy/workspaces', {
        headers: { authorization: `Bearer ${token.access_token}` },
      })
    ).json();
    const workspaceId = workspaces.items[0].id;

    const scoped = await (
      await page.request.post(`/api/token?workspace_id=${workspaceId}`)
    ).json();
    const response = await page.request.put(`/api/proxy/workspaces/${workspaceId}/products`, {
      headers: {
        authorization: `Bearer ${scoped.access_token}`,
        'content-type': 'application/json',
      },
      // The real publish shape, including the optimistic-concurrency version
      // the product sends — so a 403 here is a refusal of the *authorization*,
      // not of a malformed body.
      data: {
        expected_version: 0,
        products: [
          {
            // Client-chosen, as the API requires: a server-minted id would
            // make a retried save duplicate every product.
            id: '9f3b1c2d-0000-4000-8000-00000000e2e1',
            name: 'Written by a member',
            description: 'Should never be saved.',
          },
        ],
      },
    });

    // **403, not 404.** A member is a legitimate part of this organization and
    // may know it exists; what they may not do is administer it. The 404 rule
    // is for a caller who is not a member at all, where the existence of the
    // organization is itself the secret.
    expect(response.status()).toBe(403);
  });

  test('@regression a member cannot read another organization by naming it', async ({
    page,
  }) => {
    await page.goto('/');
    const token = await (
      await page.request.post('/api/token?workspace_id=11111111-1111-4111-8111-111111111111')
    ).json();

    const response = await page.request.get(
      '/api/proxy/workspaces/11111111-1111-4111-8111-111111111111/accounts',
      { headers: { authorization: `Bearer ${token.access_token}` } },
    );

    // **404, never 403.** Distinguishing *exists but forbidden* from *does not
    // exist* is how organization identifiers become enumerable — a security
    // property, not an inconsistency to tidy up (CLAUDE.md §7).
    expect(response.status()).toBe(404);
  });
});
