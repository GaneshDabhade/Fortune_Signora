/**
 * **An administrator defines a role, sees what putting somebody on it would
 * cost, and does it** — [TASK-1479](../../../docs/BACKLOG.md) slice ⓸, against
 * [ADR-0410](../../../docs/architecture/adr/0410-authorization-capability-layer.md)
 * §6 and 📁 `Fortune Signora Team Management.dc.html` / `Fortune Signora
 * Settings.dc.html`.
 *
 * ## 🔴 The journey exists to prove the layer REACHES a customer
 *
 * ⛔ **Every backend test in this slice would pass against a capability layer
 * nobody could see.** ⚡ **The API test that proves the layer narrows a real
 * request is `test_api_capability_roles.py`; this proves an administrator can
 * drive it end to end** — 📁 the unreachable-primitive class, which slice ⓶
 * caught by running the journey and finding a column built and never rendered.
 *
 * ## ⚠️ What the journey deliberately does not assert
 *
 * ⛔ **That the assigned person then loses access.** 📁 That is asserted
 * against the enforcer, in `test_api_capability_roles.py` and in the Security
 * Invariants — ⚡ **and driving it here would need a second signed-in browser
 * for a colleague this environment does not have.** **A declared absence,
 * rather than a passing test implying more than it checked.**
 */

import type { Page } from '@playwright/test';

import { expect, test } from './fixtures/signora';

async function team(page: Page): Promise<void> {
  await page.goto('/settings/team');
  await expect(page.getByRole('heading', { name: 'Your team', level: 1 })).toBeVisible();
  // 🔴 **Wait for the section, never for a count** — 📁 the
  // [B-262](../../../docs/BUGS.md) race, the same rule every journey this lane
  // has written follows.
  await expect(page.getByRole('heading', { name: 'Roles & permissions' })).toBeVisible();
}

test.describe('an administrator can define what a colleague may do', () => {
  test('🔴 Roles & permissions is on the screen, and reachable', async ({ page }) => {
    /**
     * ⛔ **Reachability first, because it is what the class of defect is.**
     * 📁 CX-01: a settings page nobody can reach is a page that is not shipped
     * — and this section lives beside the people it applies to precisely so it
     * needs no door of its own.
     */
    await team(page);

    await expect(page.getByRole('heading', { name: 'Roles & permissions' })).toBeVisible();
  });

  /**
   * ⚠️ **The empty state is asserted in `tests/components/capability-roles.test.tsx`,
   * deliberately, and it used to be here.**
   *
   * 🔴 **It passed on a seeded run and failed on the next one**, because the
   * creation test below leaves a role behind and `e2e-quick` does not reseed.
   * ⛔ **A journey that only holds on a fresh database is a journey that will
   * fail for a reason nobody can act on** — and the state it needs is one a
   * component test can simply supply.
   *
   * ⚡ **[§19](../../../CLAUDE.md) already draws this line**: *"a journey, never
   * a control."* **The empty state is a rendering given a known answer; what
   * only a journey can prove is that an administrator can DRIVE this to
   * completion**, which is what the tests below do.
   */

  test('🔴 New role says the role it creates can do nothing at all', async ({ page }) => {
    /**
     * 🔴 **The sentence that stops this screen lying**, and the one a customer
     * has to read before they act. 📁 ADR-0410 §5: *"a capability that is not
     * yet granted denies, which is the safe direction."*
     *
     * ⛔ **Without it somebody defines `Analyst`, assigns it, and cuts a
     * colleague off believing they narrowed them.**
     */
    await team(page);

    await page.getByRole('button', { name: 'New role' }).first().click();

    const dialog = page.getByRole('dialog');
    await expect(dialog.getByText(/starts able to do nothing at all/)).toBeVisible();
    await expect(dialog.getByText(/takes their access away/)).toBeVisible();
  });

  test('✅ the role a customer names appears in the list, holding nobody', async ({
    page,
  }) => {
    /**
     * ⚡ **`holders` is the only honest thing a new role can report**, and it
     * is what a *remove* control would have to ask first — the database
     * refuses to delete a role somebody holds.
     */
    await team(page);
    await page.getByRole('button', { name: 'New role' }).first().click();

    const dialog = page.getByRole('dialog');
    await dialog.getByLabel('What to call it').fill('Analyst');
    await dialog.getByRole('button', { name: 'Create role' }).click();

    // ⚠️ **Scoped to the card, because `Analyst` is in seven places the moment
    // it exists** — every roster row's select carries it as an option. ⛔ An
    // unscoped `getByText` was a strict-mode violation, and **the defect was
    // this assertion's rather than the product's.**
    await expect(page.getByText('Nobody holds this')).toBeVisible();
    await expect(
      page.getByRole('heading', { name: 'Roles & permissions' }).locator('..').locator('..'),
    ).toContainText('Analyst');
  });

  test('🔴 changing somebody names both directions before it happens', async ({ page }) => {
    /**
     * 🔴 **The design's own requirement**: *"Both directions are shown, because
     * a role change is a trade rather than a promotion."*
     *
     * ⛔ **A dialog listing only what somebody gains would describe a
     * promotion**, and this layer exists precisely so a role can narrow. ⚡
     * **Today the role grants nothing, so *Gains* says so** — and it stops
     * saying so on its own the day somebody grants it something, because both
     * sides are asked of the enforcer rather than held.
     */
    await team(page);
    await page.getByRole('button', { name: 'New role' }).first().click();
    const naming = page.getByRole('dialog');
    await naming.getByLabel('What to call it').fill('Analyst');
    await naming.getByRole('button', { name: 'Create role' }).click();
    await expect(page.getByText('Nobody holds this')).toBeVisible();

    await page.getByRole('combobox', { name: /can be limited to/ }).first().selectOption({
      label: 'Analyst',
    });

    const trade = page.getByRole('dialog');
    await expect(trade.getByRole('heading', { name: 'Gains' })).toBeVisible();
    await expect(trade.getByRole('heading', { name: 'Loses' })).toBeVisible();
    await expect(trade.getByText(/has not been granted anything yet/)).toBeVisible();
    await expect(
      trade.getByText(/Changes take effect on their next request, not their next sign-in/),
    ).toBeVisible();
  });

  test('✅ what somebody can actually do is offered, and names where it comes from', async ({
    page,
  }) => {
    /**
     * 📁 **ADR-0410 §3 — computed, never stored.** ⚡ **Every line was asked of
     * the same enforcer that decides this person's requests**, which is what
     * makes *"Comes from being an owner"* a fact rather than a label.
     *
     * ⛔ **And none of the enforcer's own vocabulary reaches the screen** —
     * `workspace`, `target_account`, `commercial_focus` — which is the guard
     * `vocabulary.test.tsx` structurally cannot provide, because these arrive
     * at runtime.
     */
    await team(page);

    await page.getByRole('button', { name: 'See what they can do' }).first().click();

    const dialog = page.getByRole('dialog');
    // ⚠️ **The membership role is deliberately NOT pinned.** The seeded roster
    // holds owners and members, and which one `.first()` reaches is the
    // seeder's business rather than this journey's. ⚡ **The assertion is that
    // the panel NAMES where the answer came from**, which is the design's
    // requirement — *"every line names where it comes from"*.
    await expect(dialog.getByText(/Comes from being (an owner|a member)/)).toBeVisible();
    await expect(dialog.getByText('The companies you watch')).toBeVisible();
    await expect(dialog.getByText(/commercial_focus|target_account|workspace:/)).toHaveCount(0);
  });
});
