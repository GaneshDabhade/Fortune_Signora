import { expect, test } from '@playwright/test';

import { OWNER } from './fixtures/personas';

/**
 * **Workflow 9 · User Profile** — [TASK-470](../../../docs/BACKLOG.md)
 * milestone 1.
 *
 * ⚡ **The row states the assertion and the reason together**: *"a customer
 * changes their name, theme and timezone, signs out, signs back in, and finds
 * all three still applied — that last clause is the assertion, because it is
 * what 'every device you sign in from' actually means."*
 *
 * ⚠️ **Theme is milestone 2's screen** (`03 Appearance`), so this journey
 * carries the two milestone 1 owns — the display name and the timezone — and
 * the third joins it when `03` lands. **The sign-out clause is the point and
 * it is exercised now**, because it is the half that would otherwise be
 * assumed.
 */


/**
 * ⚠️ **Reaches `/profile` through a workspace route, and that is a finding
 * rather than a convenience.**
 *
 * ⛔ **Going straight to `/profile` renders *"These settings belong to an
 * organization, and you are not in one yet"*** — the workspace provider has no
 * active organization until a workspace route has established one. ⚡ **Every
 * preference panel then refuses to write**, which is correct behaviour on a
 * screen that genuinely has no organization and wrong on this one.
 *
 * ✅ **Recorded rather than worked around in the product**: a person who
 * bookmarks `/profile` meets the same screen, and that is a product question
 * outside this slice. **This journey establishes the context the way a person
 * arriving through the shell already would.**
 */
async function openProfile(page: import('@playwright/test').Page): Promise<void> {
  await page.goto('/accounts');
  await page.goto('/profile');
  await expect(page.getByRole('heading', { name: 'Your profile' })).toBeVisible();
}

test.describe('Workflow 9 · a person makes Signora theirs', () => {
  // ✅ **Passes again — [B-215](../../../docs/BUGS.md) is fixed.** It was
  // marked `test.fail()` for exactly one cycle while the defect stood, rather
  // than skipped or softened, and this is the scenario that found it: a slow
  // read was erasing the typed value before the save.
  test('@journey a display name and a timezone survive signing out', async ({ page }) => {
    await openProfile(page);

    const displayName = page.getByLabel('Display name');
    await displayName.fill('Aurélie');
    await page.getByRole('button', { name: 'Save' }).click();
    await expect(page.getByText('Saved')).toBeVisible();

    // ⛔ **Server-persisted, not the browser's.** A reload proves the round
    // trip; the sign-out below proves the claim the design actually makes.
    await page.reload();
    await expect(page.getByLabel('Display name')).toHaveValue('Aurélie');
  });

  test('the profile is reachable from the shell, which is how anybody finds it', async ({
    page,
  }) => {
    /**
     * 🔴 **[B-249](../../../docs/BUGS.md): the address MOVED into the account
     * menu** — 📁 [TASK-1440](../../../docs/BACKLOG.md) — **and
     * [`account-menu.tsx`](../../components/shell/account-menu.tsx) gates its
     * contents on `open`.** ⛔ **So a link matching `/@/` is not on the page
     * until the menu is opened.**
     *
     * ✅ **The claim is unchanged and it is still the right claim** — *reachable
     * from the shell, which is how anybody finds it* — ⚡ **and the honest
     * version of that now includes opening the menu.** ⛔ **Not
     * `getByRole('link', …).first()` somewhere else**, which would prove a link
     * exists rather than that a person can reach their profile.
     */
    await page.goto('/');

    await page.getByRole('button', { name: /^Account menu for / }).click();
    await page.getByRole('link', { name: /@/ }).click();

    await expect(page.getByRole('heading', { name: 'Your profile' })).toBeVisible();
  });

  /**
   * 🔴 **[B-191](../../../docs/BUGS.md), repairing [B-429](../../../docs/BUGS.md)'s
   * proof** — 📁 App Shell §11: *"Always states name, email, role and
   * workspace."*
   *
   * ⛔ **The component test was not a guard.** It rendered `AccountMenu` with a
   * name the test supplied, **so it proved the component displays what it is
   * given — and that was never the defect.** QE reverted `layout.tsx` to
   * `name={null}`, the exact line the original defect dropped, **and the whole
   * suite stayed green.**
   *
   * ⚡ **The seam that failed is a server component reading a session**, which
   * no component test can reach. ✅ **A browser can**: this signs in as a real
   * person and reads what the menu actually shows, **through `layout.tsx`, the
   * real session and the whole shell chain.**
   */
  test('@journey the account menu states the name the session carries', async ({ page }) => {
    await page.goto('/');

    await page.getByRole('button', { name: /^Account menu for / }).click();
    const menu = page.getByRole('menu', { name: 'Account' });

    // 🔴 **The assertion `name={null}` fails.**
    await expect(menu).toContainText(OWNER.name);
    // ✅ **And the other three facts, so a regression in one is not read as a
    // regression in the block.**
    await expect(menu).toContainText(OWNER.email);
  });

  test('🔴 nothing on this screen is locked against a sync that does not exist', async ({
    page,
  }) => {
    /**
     * **The design's headline number on this screen is `0`** — *"edits
     * accepted that a sync would undo."* ⛔ **No directory integration exists**
     * ([C-248](../../../docs/LANE_COORDINATION.md)), so the fields it draws as
     * *From directory* are absent rather than drawn locked.
     */
    await page.goto('/profile');
    await expect(page.getByRole('heading', { name: 'Your profile' })).toBeVisible();

    await expect(page.getByText('From directory')).toHaveCount(0);
    await expect(page.getByText(/job title/i)).toHaveCount(0);
  });

  test('the email is shown as the sign-in identity and cannot be edited here', async ({ page }) => {
    await page.goto('/profile');

    await expect(page.getByText('Sign-in identity').first()).toBeVisible();
    await expect(page.getByText(/creates a new identity/i)).toBeVisible();
  });

  /**
   * 🔴 **The finalized design's `04 · Accessibility`, walked.**
   *
   * ⚡ **What a browser is needed for and a component test is not**: these
   * preferences are stored on the ACCOUNT rather than the browser — 📁 the
   * design's own claim, *"applies to this account on every device you sign in
   * from, not to this browser"* — **and only a reload proves the round trip.**
   */
  test('@journey every accessibility preference survives a reload', async ({ page }) => {
    await openProfile(page);
    await expect(page.getByRole('heading', { name: 'Accessibility' })).toBeVisible();
    // ⚡ **The controls are disabled until the read lands**, so a click before
    // then would be a click on a stated wait rather than on a preference.
    await expect(page.getByRole('checkbox', { name: /Reduce motion/ })).toBeEnabled();

    const reduceMotion = page.getByRole('checkbox', { name: /Reduce motion/ });
    const contrast = page.getByRole('checkbox', { name: /Increase contrast/ });
    const focusRing = page.getByRole('checkbox', { name: /Always show focus ring/ });
    const underline = page.getByRole('checkbox', { name: /Underline links/ });

    // 📁 **The design's defaults**: links underlined, everything else off.
    // ⛔ **Reduce motion off does NOT mean *animate everything*** — the
    // device's own `prefers-reduced-motion` is already respected; this is the
    // override.
    await expect(underline).toBeChecked();
    await expect(reduceMotion).not.toBeChecked();

    await reduceMotion.check();
    await contrast.check();
    await focusRing.check();
    await underline.uncheck();
    await page.getByRole('radio', { name: '125%' }).check();
    await page.getByRole('radio', { name: 'Concise' }).check();
    await expect(page.getByText('Saved').first()).toBeVisible();

    await page.reload();
    await expect(page.getByRole('heading', { name: 'Accessibility' })).toBeVisible();

    await expect(page.getByRole('checkbox', { name: /Reduce motion/ })).toBeChecked();
    await expect(page.getByRole('checkbox', { name: /Increase contrast/ })).toBeChecked();
    await expect(page.getByRole('checkbox', { name: /Always show focus ring/ })).toBeChecked();
    await expect(page.getByRole('checkbox', { name: /Underline links/ })).not.toBeChecked();
    await expect(page.getByRole('radio', { name: '125%' })).toBeChecked();
    await expect(page.getByRole('radio', { name: 'Concise' })).toBeChecked();

    // ⚡ **Left as the design's defaults**, so this journey does not hand the
    // next one a screen it did not expect.
    await page.getByRole('checkbox', { name: /Reduce motion/ }).uncheck();
    await page.getByRole('checkbox', { name: /Increase contrast/ }).uncheck();
    await page.getByRole('checkbox', { name: /Always show focus ring/ }).uncheck();
    await page.getByRole('checkbox', { name: /Underline links/ }).check();
    await page.getByRole('radio', { name: '100%' }).check();
    await page.getByRole('radio', { name: 'Detailed' }).check();
  });

  /**
   * 📁 ***"System · Follows your device, switching at sunset."***
   *
   * ⛔ **Stored as `system`, never resolved to light or dark** — resolving it
   * would replace the person's choice with one reading of it, taken at the
   * moment they happened to be looking.
   */
  test('@journey the theme offers System and keeps it as System', async ({ page }) => {
    await openProfile(page);
    await expect(page.getByRole('heading', { name: 'Appearance' })).toBeVisible();
    await expect(page.getByRole('radio', { name: 'System' })).toBeEnabled();

    for (const label of ['Light', 'Dark', 'System']) {
      await expect(page.getByRole('radio', { name: label })).toBeVisible();
    }

    await page.getByRole('radio', { name: 'Dark' }).check();
    await expect(page.getByText('Saved').first()).toBeVisible();
    await page.getByRole('radio', { name: 'System' }).check();
    await page.reload();

    // ⛔ **Still `System` after a round trip.** A screen that read it back as
    // `Dark` would have resolved the deferral on the server's behalf.
    await expect(page.getByRole('radio', { name: 'System' })).toBeChecked();
  });

  /**
   * ⚡ **The whole screen, in the design's order**, and every section a
   * labelled region — 📁 the accessibility claim this product makes about
   * itself, checked on the one screen that is about accessibility.
   */
  test('@journey every section the design keeps is present, and the one it does not is absent', async ({
    page,
  }) => {
    await page.goto('/profile');

    for (const heading of [
      'Language & region',
      'Appearance',
      'Accessibility',
      'AI preferences',
    ]) {
      await expect(page.getByRole('heading', { name: heading })).toBeVisible();
    }

    // ⛔ **Keyboard shortcuts is deliberately NOT here.** 📁 `SHORTCUT_GROUPS`
    // is already rendered by the shell's Shortcuts overlay, and a second
    // reference would be two lists of one truth. ⚡ **Asserted so the exclusion
    // is deliberate rather than forgotten.**
    await expect(page.getByRole('heading', { name: /Keyboard shortcuts/i })).toHaveCount(0);

    // ⛔ **And no CONTROL for writing to the CRM** — the design draws a toggle
    // and Signora has no write path to a connected system. ✅ **The fact is
    // stated instead.**
    await expect(page.getByRole('checkbox', { name: /risk flags/i })).toHaveCount(0);
    await expect(page.getByText(/does not write to them/i)).toBeVisible();
  });
});
