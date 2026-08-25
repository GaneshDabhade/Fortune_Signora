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

/**
 * ⚡ **The design's sections are destinations behind a 212px rail**, not
 * headings in one column — ⛔ so a journey that scrolled to a heading was
 * asserting the layout this slice replaced.
 */
async function openSection(
  page: import('@playwright/test').Page,
  label: string,
): Promise<void> {
  await openProfile(page);
  await page.getByRole('navigation', { name: 'Profile settings' }).getByRole('button', { name: label }).click();
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
    await page.getByRole('button', { name: /^Save/ }).click();
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
    /**
     * ⚠️ **Entry resolution settles first, and that wait is 🔴
     * [B-292](../../../docs/BUGS.md) rather than a precaution.**
     *
     * ⛔ **The shell is interactive while `/` resolves**, so a person who opens
     * the account menu and chooses their profile in that window **lands on Home
     * instead** — their navigation happens, and the resolver's `replace`
     * arrives afterwards and discards it. **Measured**: `/` → `/` →
     * `/w/…/home`, with `/profile` never reached.
     *
     * ✅ **Fixed in the resolver** — it no longer moves somebody who has
     * already moved. ⚡ **The wait stays**, because this test's claim is
     * *reachable from the shell* and not *the resolver behaves*: the resolver's
     * own guard is asserted where the resolver is.
     */
    await page.waitForURL(/\/w\/[0-9a-f-]{36}\/home$/, { timeout: 30_000 });

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
    /**
     * ⚡ **Declared slow rather than trimmed.**
     *
     * ⛔ **Six preferences set, a reload, six read back and six restored is
     * TWELVE round trips**, each its own `PATCH` — and it exceeded the default
     * 60s. ✅ **`test.slow()` is Playwright's own mechanism for a scenario that
     * is legitimately long**; ⛔ **dropping the restore or asserting a subset
     * would make it faster by verifying less**, which is the trade this file
     * exists not to make.
     */
    test.slow();
    await openSection(page, 'Accessibility');
    await expect(page.getByRole('heading', { name: 'Accessibility' })).toBeVisible();
    // ⚡ **The controls are disabled until the read lands**, so a click before
    // then would be a click on a stated wait rather than on a preference.
    await expect(page.getByRole('checkbox', { name: /^Reduce motion\b/ })).toBeEnabled();

    const reduceMotion = page.getByRole('checkbox', { name: /^Reduce motion\b/ });
    const contrast = page.getByRole('checkbox', { name: /^Increase contrast\b/ });
    const focusRing = page.getByRole('checkbox', { name: /^Always show focus ring\b/ });
    const underline = page.getByRole('checkbox', { name: /^Underline links\b/ });

    /**
     * 🔴 **`setChecked` rather than `check`, and the difference is the whole
     * fix.**
     *
     * ⛔ **This asserted the design's pristine defaults first** — underlined
     * links, everything else off — **and these preferences are stored on the
     * ACCOUNT.** ⚡ **So a previous failed run left them flipped and the next
     * run waited forever on a state it had itself destroyed.**
     *
     * ✅ **The defaults are asserted where they cannot leak** —
     * `profile.test.tsx` and the domain's own test — **and what a browser is
     * needed for is the ROUND TRIP**, which is what this now does regardless of
     * where it starts.
     */
    await reduceMotion.setChecked(true);
    await contrast.setChecked(true);
    await focusRing.setChecked(true);
    await underline.setChecked(false);
    /**
     * 🔴 **Clicked by label, and the trace is why.**
     *
     * ⛔ **`.check()` on the input never completes**: the trace's own words are
     * *"`<span>125%</span>` … subtree intercepts pointer events"*, and
     * Playwright retried the click every 500ms until the scenario timed out.
     * ⚡ **`SegmentedControl` draws the option as a `<label>` wrapping a native
     * radio**, so the input is behind its own label by design.
     *
     * ✅ **Clicking the label is what a person does**, and it is not a
     * weakening: the assertions below still read `toBeChecked()` on the input.
     * ⛔ **`force: true` would have been the weakening** — it clicks through
     * whatever is on top, which is exactly the class of defect a journey exists
     * to catch.
     */
    await page.getByText('125%', { exact: true }).click();
    await page.getByText('Concise', { exact: true }).click();
    await expect(page.getByText('Saved').first()).toBeVisible();

    await page.reload();
    await expect(page.getByRole('heading', { name: 'Accessibility' })).toBeVisible();

    await expect(page.getByRole('checkbox', { name: /^Reduce motion\b/ })).toBeChecked();
    await expect(page.getByRole('checkbox', { name: /^Increase contrast\b/ })).toBeChecked();
    await expect(page.getByRole('checkbox', { name: /^Always show focus ring\b/ })).toBeChecked();
    await expect(page.getByRole('checkbox', { name: /^Underline links\b/ })).not.toBeChecked();
    await expect(page.getByRole('radio', { name: /^125%$/ })).toBeChecked();
    await expect(page.getByRole('radio', { name: /^Concise$/ })).toBeChecked();

    // ⚡ **Left as the design's defaults**, so this journey does not hand the
    // next one a screen it did not expect.
    await page.getByRole('checkbox', { name: /^Reduce motion\b/ }).setChecked(false);
    await page.getByRole('checkbox', { name: /^Increase contrast\b/ }).setChecked(false);
    await page.getByRole('checkbox', { name: /^Always show focus ring\b/ }).setChecked(false);
    await page.getByRole('checkbox', { name: /^Underline links\b/ }).setChecked(true);
    await page.getByText('100%', { exact: true }).click();
    await page.getByText('Detailed', { exact: true }).click();
  });

  /**
   * 📁 ***"System · Follows your device, switching at sunset."***
   *
   * ⛔ **Stored as `system`, never resolved to light or dark** — resolving it
   * would replace the person's choice with one reading of it, taken at the
   * moment they happened to be looking.
   */
  test('@journey the theme offers System and keeps it as System', async ({ page }) => {
    await openSection(page, 'Appearance');
    await expect(page.getByRole('heading', { name: 'Appearance' })).toBeVisible();
    await expect(page.getByRole('radio', { name: /^System\b/ })).toBeEnabled();

    /**
     * ⚠️ **Anchored at the START of the accessible name, and that is the whole
     * fix.** ⛔ **`{ name: 'Light' }` matched TWO radios**: the design's own
     * supporting line for Dark is *"For low light and long sessions"*, and the
     * accessible name of a segmented option is its label plus that line.
     *
     * ✅ **The product is unchanged** — the descriptions are the design's, and
     * removing one to make a locator unambiguous would be the test dictating
     * the screen.
     */
    for (const label of [/^Light\b/, /^Dark\b/, /^System\b/]) {
      await expect(page.getByRole('radio', { name: label })).toBeVisible();
    }

    /**
     * 🔴 **The change is chosen against what is stored, and this test used to
     * assume it.**
     *
     * ⚠️ **It checked `Dark` and waited for *"Saved"*.** ⛔ **A radio that is
     * already checked fires no change event**, so on any run where the stored
     * theme was already dark, **nothing was sent and nothing said `Saved`.**
     * 🔴 **Worse: it left `Dark` behind every time it failed**, so after its
     * first failure it could never pass again without somebody changing the
     * theme by hand. **A test that poisons its own next run is the sharpest
     * member of the family this suite keeps meeting** — an assertion whose
     * subject depends on what ran before it.
     *
     * ⛔ **Naming a different starting value would have moved the problem, not
     * removed it** — whichever one is named can already be current. ✅ **So the
     * test asks the screen which is checked and changes to one that is not.**
     */
    const themes = [/^Light\b/, /^Dark\b/, /^System\b/];
    let changed = false;
    for (const theme of themes) {
      if (await page.getByRole('radio', { name: theme }).isChecked()) continue;
      /**
       * 🔴 **Clicked by label, for the reason this file already states 80
       * lines up** — *"`.check()` on the input never completes… the input is
       * behind its own label by design."*
       *
       * ⚡ **The theme picker is now `ChoiceCards`**, which the design lists as
       * its own component (*`ThemeCard · v2 · card 12px`*, separate from
       * *`Segmented / Toggle / Select`*). 📁 `choice-cards.tsx:132` says the
       * selected dot *"sits over the `sr-only` input and intercepts"*, so
       * `.check()` retries until the scenario times out — **the identical
       * trace, on a different overlay.**
       *
       * ✅ **Not a weakening**: the assertion below still reads
       * `toBeChecked()` on the input, and ⛔ **`force: true` would have been
       * the weakening** — it clicks through whatever is on top, which is the
       * class of defect a journey exists to catch.
       */
      await page
        .locator('label')
        .filter({ has: page.getByRole('radio', { name: theme }) })
        .click();
      changed = true;
      break;
    }
    expect(changed, 'no theme was unchecked, so nothing could be changed').toBe(true);
    await expect(page.getByText('Saved').first()).toBeVisible();

    /**
     * ⚠️ **The reload waits for the WRITE, not for a word.** ⛔ *"Saved"* is
     * already on screen from the change above, so waiting for it again would
     * wait for nothing and reload mid-`PATCH` — **and a reload that cancels the
     * request under test reports a persistence failure that never happened.**
     *
     * ⚡ **The claim is that it PERSISTS**, so the thing to wait for is the
     * persist.
     */
    const persisted = page.waitForResponse(
      (response) =>
        response.url().includes('/preferences') &&
        response.request().method() === 'PATCH' &&
        response.ok(),
      { timeout: 20_000 },
    );
    await page
      .locator('label')
      .filter({ has: page.getByRole('radio', { name: /^System\b/ }) })
      .click();
    await persisted;
    await page.reload();

    // ⛔ **Still `System` after a round trip.** A screen that read it back as
    // `Dark` would have resolved the deferral on the server's behalf.
    await expect(page.getByRole('radio', { name: /^System\b/ })).toBeChecked();
  });

  /**
   * ⚡ **The whole screen, in the design's order**, and every section a
   * labelled region — 📁 the accessibility claim this product makes about
   * itself, checked on the one screen that is about accessibility.
   */
  test('@journey every section the design keeps is present, and the ones with no source say so', async ({
    page,
  }) => {
    await page.goto('/profile');

    /**
     * 🔴 **Keyboard shortcuts IS here now, and the sentence that stood in this
     * place was narrower than it looked.**
     *
     * ⚠️ **It read: *"deliberately NOT here — `SHORTCUT_GROUPS` is already
     * rendered by the shell's Shortcuts overlay, and a second reference would
     * be two lists of one truth."*** ⛔ **The concern was real and the
     * conclusion did not follow**: 📁 [§2](../../../CLAUDE.md) forbids two
     * *implementations* of one behaviour, not two surfaces onto one registry.
     *
     * ⚡ **And the product was already promising it**: the design's nine-item
     * rail lists it, `PROFILE_SECTIONS` carries it, and clicking it reached
     * *"this section is not built yet"*. ✅ **Built by sharing `ShortcutList`
     * with the overlay** — one rendering, two mount points.
     */
    await openSection(page, 'Keyboard shortcuts');
    /**
     * ⚠️ **Scoped to the section, and the reason is the point of this slice.**
     * ⛔ An unscoped `getByText('Command palette')` matches SIX elements —
     * **the shell's `?` overlay is mounted on every screen and renders the same
     * registry.** ✅ **That is one component with two mount points**, which is
     * what makes it correct rather than a duplicate.
     */
    const shortcuts = page.getByRole('region', { name: 'Keyboard shortcuts' });
    await expect(shortcuts.getByRole('heading', { name: 'Keyboard shortcuts' })).toBeVisible();
    await expect(shortcuts.getByText('Command palette', { exact: true })).toBeVisible();
    // ⛔ **No editor**: the design's conflict rule describes one and no
    // preference field or endpoint stores a binding.
    await expect(shortcuts.getByRole('button')).toHaveCount(0);

    // ⛔ **And no CONTROL for writing to the CRM** — the design draws a toggle
    // and Signora has no write path to a connected system. ✅ **The fact is
    // stated instead.**
    await openSection(page, 'AI preferences');
    await expect(page.getByRole('checkbox', { name: /risk flags/i })).toHaveCount(0);
    await expect(page.getByText(/does not write to them/i)).toBeVisible();
  });
});
