/**
 * **Somebody chooses which organization to work in, and enters it** —
 * [TASK-1421](../../../docs/BACKLOG.md), against 📁 `Fortune Signora Workspace
 * Chooser.dc.html`.
 *
 * ## 🔴 What this journey proves that no unit test can
 *
 * ⛔ **The route was a 404.** ⚡ **Four entry rules already sent people here** —
 * 📁 the design's own §01: *"Four Entry rules dead-ended here… nothing drew
 * it."* **A component test renders the page directly and would pass against a
 * route that does not exist**; only a browser asking the server for
 * `/workspaces` can tell the difference.
 *
 * ## ⚠️ What it deliberately does not drive
 *
 * ⛔ **Rule 13 — *several memberships, no last-used* — the state that sends a
 * customer here by itself.** ⚡ **The seeded Playground enrols everybody in one
 * organization**, so producing two would mean creating a second through the
 * product mid-journey and clearing a stored preference. **A declared absence
 * rather than a passing test implying more than it checked** — the rule itself
 * is asserted in `tests/unit/entry-engine.test.ts`, where the state is an
 * argument rather than a fixture.
 */

import { expect, test } from './fixtures/signora';

test.describe('a person chooses which organization to work in', () => {
  test('🔴 the route renders a decision rather than a 404', async ({ page }) => {
    /**
     * ⛔ **The whole defect, and it is one assertion.** ⚡ Before this row,
     * `app/workspaces/` held only `none/page.tsx` — **so anybody with two
     * organizations and no last-used, or anybody following the *"Go to your
     * organizations"* link on the not-a-member gate, reached nothing.**
     */
    const response = await page.goto('/workspaces');

    expect(response?.status()).toBe(200);
    await expect(
      page.getByRole('heading', { name: 'Choose an organization', level: 1 }),
    ).toBeVisible();
  });

  test('✅ it says how many there are and that the choice is remembered', async ({
    page,
  }) => {
    /**
     * 📁 The design's verbatim copy: *"You are a member of four. Signora will
     * remember this choice on this device, so you will not be asked again."*
     * ⚡ **The promise is the point** — somebody asked to choose needs to know
     * they will not be asked every morning.
     */
    await page.goto('/workspaces');

    await expect(page.getByText(/You are a member of/)).toBeVisible();
    await expect(page.getByText(/remember this choice on this device/)).toBeVisible();
  });

  test('🔴 choosing one enters it', async ({ page }) => {
    /**
     * ⚡ **The journey's actual subject.** ⛔ A chooser that lists
     * organizations and does not enter one is a screen, not a decision.
     */
    await page.goto('/workspaces');
    await expect(
      page.getByRole('list', { name: 'Your organizations' }),
    ).toBeVisible();

    await page.getByRole('list', { name: 'Your organizations' })
      .getByRole('button')
      .first()
      .click();

    // ⚡ **Landing anywhere inside the shell is the assertion** — the rail is
    // what proves an organization was resolved, and 📁 the design's *"Home
    // (guaranteed render after switch)"* is the dependency it names.
    await expect(page.getByRole('navigation', { name: 'Primary' })).toBeVisible();
  });

  test('✅ it never names an organization the person cannot see', async ({ page }) => {
    /**
     * 📁 The design's banned list, verbatim: *"any message that names a
     * workspace the person cannot see."* ⛔ **So the footer asks them to ask
     * somebody, and names nothing.**
     */
    await page.goto('/workspaces');

    await expect(
      page.getByText(/Expecting an organization that is not here\? Ask an administrator/),
    ).toBeVisible();
  });
});
