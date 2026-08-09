import { expect, test } from '@playwright/test';

/**
 * **Workflow 8 · Initial Onboarding** — [TASK-469](../../../docs/BACKLOG.md)
 * milestone 1, the guided run a customer walks.
 *
 * ⚡ **Two scenarios, and the row names both**: the whole run, and **the
 * interruption** — *"the interruption path is the one a journey normally omits
 * and the one screen `08` exists for."*
 *
 * ⚠️ **Milestone 1 ends at Goals.** Screen `07 Connect & AI personalisation`
 * and the skip *confirmation dialog* are milestone 2's; what exists here is
 * the leaving and the resuming, which is the half the run's persistence makes
 * checkable. **The scenario for `08`'s dialog lands with `08`.**
 */

/**
 * 🔴 **Serial, and the order is load-bearing.**
 *
 * ⚡ **A person onboards once.** The scenarios share one signed-in owner and
 * one workspace, so they share one run — and **finishing it is terminal**: the
 * aggregate refuses every later change with `409`, because *"onboarding
 * answers become settings the moment the run ends."*
 *
 * ⚠️ **Found by running this headed, not by reasoning about it.** The first
 * draft put the completion journey first and both banner scenarios failed on a
 * run that was already finished — **the product was right and the suite was
 * wrong.** ⛔ **The fix is the order, never a reset endpoint**: a route that
 * un-finished a run would exist only for tests, and it would be a way to edit
 * a settled record that no customer has.
 *
 * **So the run is completed last**, and everything needing it in progress runs
 * before.
 */
test.describe.configure({ mode: 'serial' });

test.describe('Workflow 8 · a person is guided in', () => {
  test('🔴 the fourth goal is disabled, not silently ignored', async ({ page }) => {
    /**
     * **The design says it in terms**, and it is the one interaction on this
     * screen a customer notices going wrong: a control that stops responding
     * without saying why reads as a bug.
     */
    await page.goto('/onboarding/goals');

    for (const name of [/forecast accurately/i, /stop deals slipping/i, /protect renewals/i]) {
      await page.getByRole('checkbox', { name }).check();
    }

    await expect(page.getByRole('checkbox', { name: /coach the team/i })).toBeDisabled();
    // ⚡ **The reason is stated in the count**, not left to the dimming.
    await expect(page.getByRole('status')).toContainText(/3 of 3/);
    // ⛔ **And an already-chosen one is still live**, or the limit would trap
    // somebody at their first three guesses.
    await expect(page.getByRole('checkbox', { name: /forecast accurately/i })).toBeEnabled();
  });

  test('🔴 screen 08 · skipping the rest states the consequence and lets them go', async ({
    page,
  }) => {
    /**
     * **Milestone 2, and the header above promised it would land here.**
     *
     * 📁 *"States the consequence in product terms and lets them go. No dark
     * pattern, no second ask."* ⛔ **The second half is the one a browser can
     * check and a unit test cannot**: that pressing `Skip` actually leaves the
     * flow, rather than opening something else.
     */
    await page.goto('/onboarding/you');
    await page.getByRole('button', { name: 'Skip setup' }).click();

    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();
    // ⚡ The consequence, in product terms — never "2 steps remaining".
    await expect(dialog).toContainText(/general benchmarks/i);
    await expect(dialog).toContainText(/home page will show everything/i);

    // ✅ Continuing is the ABSENCE of a navigation — they stay where they were.
    await dialog.getByRole('button', { name: /Finish setup/ }).click();
    await expect(dialog).toBeHidden();
    await expect(page).toHaveURL(/\/onboarding\/you$/);

    // ⛔ And skipping leaves, with no second ask.
    await page.getByRole('button', { name: 'Skip setup' }).click();
    await page.getByRole('dialog').getByRole('button', { name: 'Skip' }).click();
    await expect(page).toHaveURL((url) => !url.pathname.startsWith('/onboarding'));
  });

  test('@journey leaving part-way through, and coming back to what was answered', async ({
    page,
  }) => {
    /**
     * ⚡ **The interruption path.** *"Everything saved as you go… you can leave
     * at any point"* — this is that promise as a scenario rather than a claim,
     * and it is the one the row says a journey normally omits.
     */
    await page.goto('/onboarding/you');
    await page.getByRole('radio', { name: /sales operations/i }).check();
    await page.getByLabel(/how many people/i).fill('12');
    await page.getByRole('button', { name: 'Continue' }).click();
    await expect(page.getByRole('heading', { level: 1 })).toContainText(/trying to fix/i);

    // Leaves the flow entirely — the browser, not a control.
    await page.goto('/');

    // **The resume banner is onboarding's only entrance**, and it appears
    // because the run is unfinished rather than because a flag was set.
    const banner = page.getByRole('status').filter({ hasText: /setup is unfinished/i });
    await expect(banner).toBeVisible();
    await banner.getByRole('link', { name: /finish setting up/i }).click();

    // ⛔ **Not an empty form.** *"Returning to a step shows what was chosen."*
    await page.goto('/onboarding/you');
    await expect(page.getByRole('radio', { name: /sales operations/i })).toBeChecked();
    await expect(page.getByLabel(/how many people/i)).toHaveValue('12');
  });

  test('⚠️ dismissing the banner is final — no second ask', async ({ page }) => {
    /**
     * *"No second ask, no guilt copy — the resume banner does the remaining
     * work quietly."* ⛔ **A banner that returned on the next page load would
     * be exactly the second ask the design forbids**, delivered more often.
     */
    await page.goto('/onboarding/company');
    await page.goto('/');

    const banner = page.getByRole('status').filter({ hasText: /setup is unfinished/i });
    await expect(banner).toBeVisible();
    await banner.getByRole('button', { name: /not now/i }).click();
    await expect(banner).toBeHidden();

    await page.reload();
    await expect(
      page.getByRole('status').filter({ hasText: /setup is unfinished/i }),
    ).toHaveCount(0);
  });

  test('team size is validated on blur, never per keystroke', async ({ page }) => {
    // The design states this behaviour rather than implying it, and it is the
    // kind of thing a later refactor "tidies" into `onChange`.
    await page.goto('/onboarding/you');
    const field = page.getByLabel(/how many people/i);

    await field.fill('0');
    // Nothing yet — they may still be typing `0` into `10`.
    await expect(page.getByText(/team of one counts/i)).toHaveCount(0);

    await field.blur();
    await expect(page.getByText(/team of one counts/i)).toBeVisible();
  });

  test('@journey the guided run, from welcome to a working workspace', async ({ page }) => {
    await page.goto('/onboarding');

    // `01`/`02` — it asks nothing and states what the product does.
    await expect(page.getByRole('heading', { level: 1 })).toContainText(/welcome/i);
    await expect(page.getByText('Evidence, always')).toBeVisible();

    // ⛔ **The rail is an ordered list with one current step** — 1.3.1, and
    // the design names it by number.
    const rail = page.getByRole('navigation', { name: 'Setup progress' });
    await expect(rail.getByRole('listitem')).toHaveCount(6);

    await page.getByRole('link', { name: 'Get started' }).click();

    // `04` — four confirmations, no typing.
    await expect(page.getByRole('heading', { level: 1 })).toContainText(/your company/i);
    await page.getByRole('radio', { name: 'Software' }).check();
    await page.getByRole('button', { name: 'Continue' }).click();

    // `05` — role and team size.
    await expect(page.getByRole('heading', { level: 1 })).toContainText(/what do you do/i);
    await page.getByRole('radio', { name: /revenue leader/i }).check();
    await page.getByLabel(/how many people/i).fill('24');
    await page.getByRole('button', { name: 'Continue' }).click();

    // `06` — up to three outcomes, and they replace a feature menu.
    await expect(page.getByRole('heading', { level: 1 })).toContainText(/trying to fix/i);
    await page.getByRole('checkbox', { name: /forecast accurately/i }).check();
    await expect(page.getByRole('status')).toContainText('1 of 3 chosen.');

    await page.getByRole('button', { name: 'Continue' }).click();

    // **It ends in the product**, which is what makes it a journey rather than
    // a form: the run is finished and the person is where they work.
    await expect(page).toHaveURL(/\/$|\/business/);
  });
});
