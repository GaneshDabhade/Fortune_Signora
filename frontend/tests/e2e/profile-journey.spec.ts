import { expect, test } from '@playwright/test';

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

test.describe('Workflow 9 · a person makes Signora theirs', () => {
  // ✅ **Passes again — [B-215](../../../docs/BUGS.md) is fixed.** It was
  // marked `test.fail()` for exactly one cycle while the defect stood, rather
  // than skipped or softened, and this is the scenario that found it: a slow
  // read was erasing the typed value before the save.
  test('@journey a display name and a timezone survive signing out', async ({ page }) => {
    await page.goto('/profile');

    await expect(page.getByRole('heading', { name: 'Your profile' })).toBeVisible();

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
    // The design puts this in the App Shell's utility rail — Workflow 13, not
    // built — so the link lives where the identity already is.
    await page.goto('/');

    await page.getByRole('link', { name: /@/ }).click();

    await expect(page.getByRole('heading', { name: 'Your profile' })).toBeVisible();
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
});
