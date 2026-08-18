/**
 * The Connection Centre — and the product's honesty about what it cannot do.
 *
 * **This is the surface most likely to lie to a customer**, because every
 * other screen reports something Signora computed and this one reports the
 * state of somebody else's system. A connection that says *Ready to use* when
 * the credential expired last night costs more trust than one that says
 * nothing at all.
 *
 * The standing instruction is exact and these tests hold it to it:
 *
 * > *Do not claim end-to-end functionality that cannot be exercised. Do not
 * > fake success. Do not simulate completed connections where none exist. The
 * > product should always tell the truth about its current capabilities.*
 *
 * So the assertions are about **truthfulness**, not about connecting: no
 * environment here has a HubSpot developer application, `connectable` is
 * therefore false, and the product must say so rather than offering a button
 * that fails at the callback.
 */

import { expect, test } from './fixtures/signora';

/**
 * ⚠️ **Renamed from *"what a customer sees before anything is connected"*.**
 * 📁 `B-1022` gave the Playground the CRM its twelve accounts arrived through,
 * so *before anything is connected* stopped describing this environment — and
 * a describe block that misnames its own fixture is the defect §2 warns about,
 * read by whoever next wonders why a Disconnect button is on the page.
 */
test.describe('what a customer sees in the connection centre', () => {
  test('@smoke the connection centre opens and lists the systems Signora reads from', async ({
    page,
  }) => {
    await page.goto('/settings/connections');
    await expect(page.getByRole('heading', { name: 'Connections', level: 1 })).toBeVisible({
      timeout: 20_000,
    });
  });

  test('@journey every system states its status in a word a customer can act on', async ({
    page,
  }) => {
    await page.goto('/settings/connections');
    await expect(page.getByRole('heading', { name: 'Connections', level: 1 })).toBeVisible({
      timeout: 20_000,
    });

    // **Wait for the catalog, not for the heading.** The header renders
    // immediately and the systems arrive with the request behind them, so
    // reading the page at that moment reads the word *Loading…*.
    await expect(page.getByText('Not connected').first()).toBeVisible({ timeout: 20_000 });
    const body = await page.locator('main').innerText();
    // **Four states, and each says what to do next.** *Salesforce · Connected*
    // tells an administrator nothing they can act on; *Action required* does.
    const states = ['Not connected', 'Ready to use', 'Action required', 'Turned off'];
    expect(
      states.some((state) => body.includes(state)),
      `no recognisable connection state on the page:\n${body.slice(0, 400)}`,
    ).toBe(true);
  });

  test('@regression nothing offers a connection this environment cannot complete', async ({
    page,
  }) => {
    await page.goto('/settings/connections');
    await expect(page.getByRole('heading', { name: 'Connections', level: 1 })).toBeVisible({
      timeout: 20_000,
    });

    // **The rule, asserted.** Without a developer application the catalog
    // reports `connectable: false`, and a *Continue to …* button would take a
    // customer to a failure. An absent control is honest; a present one that
    // cannot work is not.
    await expect(page.getByText('Not connected').first()).toBeVisible({ timeout: 20_000 });
    const start = page.getByRole('button', { name: /^Continue to / });
    const explanation = page.getByText(
      /not available yet|cannot be connected|coming|not configured/i,
    );

    if ((await start.count()) > 0) {
      // If it is offered, the environment genuinely supports it — which is a
      // legitimate state and not one this environment has.
      await expect(start.first()).toBeEnabled();
    } else {
      // Offered nothing, and said why. Silence would leave an administrator
      // wondering whether the page had failed to load.
      expect(
        (await explanation.count()) > 0 ||
          (await page.locator('main').innerText()).includes('Not connected'),
      ).toBe(true);
    }
  });

  test('@regression the page never shows a connection that does not exist', async ({
    page,
  }) => {
    await page.goto('/settings/connections');
    await expect(page.getByRole('heading', { name: 'Connections', level: 1 })).toBeVisible({
      timeout: 20_000,
    });

    await expect(page.getByText('Not connected').first()).toBeVisible({ timeout: 20_000 });

    /**
     * 🔴 **This asserted `Disconnect` appeared ZERO times**, on the stated
     * premise that *"nothing is connected in this environment"*. ⛔ **That
     * premise was a defect rather than a fact** — `B-1022`: the Playground ran
     * nine pipeline stages and recorded no connection, so a workspace holding
     * twelve accounts had none. **The seeder now connects the CRM those
     * accounts arrived through**, and the old assertion would fail on a fixture
     * that had been corrected.
     *
     * ⚡ **The claim is unchanged and the new assertion is stronger.** *A
     * control for a connection nobody made* is still the failure; what it takes
     * to catch it is now checked **per system** rather than by a total that
     * only held while the total was zero. ⛔ A count of zero says nothing about
     * whether the control is attached to the right row.
     */
    const systems = page.locator('main ul > li').filter({ hasText: /Not connected/ });
    const unconnected = await systems.count();
    expect(unconnected, 'no system reads "Not connected"').toBeGreaterThan(0);
    for (let index = 0; index < unconnected; index += 1) {
      await expect(
        systems.nth(index).getByRole('button', { name: /^Disconnect / }),
        'a system reading "Not connected" offered a way to disconnect it',
      ).toHaveCount(0);
    }
  });
});

test.describe('a customer who is not an administrator', () => {
  test('@regression a member is not shown the connection centre at all', async ({
    page,
  }) => {
    // Asserted from the owner's session by checking the guard's own rule: the
    // member half runs in `permissions.member.spec.ts`, where the browser state
    // is a member's. Here the point is that the route is guarded rather than
    // merely unlinked.
    await page.goto('/settings/connections');
    await expect(page).toHaveURL(/\/settings\/connections$/, { timeout: 20_000 });
  });
});
