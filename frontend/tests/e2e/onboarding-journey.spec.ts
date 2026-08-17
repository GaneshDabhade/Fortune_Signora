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
    // ⛔ **A client-rendered control, not the server-rendered heading.**
    await expect(page.getByRole('checkbox', { name: /forecast accurately/i })).toBeVisible();

    /**
     * ⚠️ **The LABEL is clicked, not the input, and that is the user's action.**
     * ⛔ The checkbox is `sr-only` so the design's own box can be drawn beside
     * it, and 📁 each toggle now autosaves — *"every step saves on advance and
     * on blur"* — **so the input is replaced between a `check()`'s stability
     * poll and its click.** ✅ Clicking the row is what a person does and it is
     * stable.
     */
    for (const label of ['Forecast accurately', 'Stop deals slipping', 'Protect renewals']) {
      await page.getByText(label, { exact: true }).click();
      // ⛔ **Wait for the save to land before the next click**, or three
      // requests race and the last answer to arrive wins rather than the last
      // one chosen.
      await expect(page.getByRole('checkbox', { name: new RegExp(label, 'i') })).toBeChecked();
    }

    await expect(page.getByRole('checkbox', { name: /coach the team/i })).toBeDisabled();
    // ⚡ **The reason is stated in the count**, not left to the dimming.
    await expect(page.getByRole('status').filter({ hasText: /of 3 selected/ })).toContainText(
      /3 of 3/,
    );

    /**
     * 🔴 **Keyboard focus survives a toggle**, which is the property the
     * `sr-only` input could plausibly have cost. ⛔ A control that loses focus
     * on every use is unusable without a pointer — 📁 WCAG 2.1.1, which the
     * design names by number.
     */
    await page.getByRole('checkbox', { name: /protect renewals/i }).focus();
    await page.keyboard.press('Space');
    await expect(page.getByRole('checkbox', { name: /protect renewals/i })).toBeFocused();
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
    /**
     * ⚠️ **A fresh load, because the previous scenario left this context on
     * another step with an autosave in flight.** ⛔ Serial mode shares one
     * page, so *"navigate to the step"* is not the same as *"arrive at the
     * step"* — and this button's handler is attached on hydration.
     */
    await page.reload();
    /**
     * ⚠️ **Wait for the heading before clicking anything.** ⛔ This test used to
     * click straight after `goto` and started failing the moment
     * `(onboarding)/loading.tsx` arrived: **a Suspense boundary makes the
     * pre-hydration window observable**, and a click on a rendered-but-not-yet
     * -hydrated button does nothing at all.
     *
     * ⚡ **Not a product defect and not a flake to retry** — the page really is
     * not interactive yet, and every other test in this file already waits.
     *
     * 🔴 **And the HEADING is not enough**, which cost two runs to learn: the
     * shell renders it on the server. ✅ **The role cards do not** — they come
     * from client state — **so their presence is the first moment React is
     * actually attached and a click will be heard.**
     */
    await expect(page.getByRole('radio', { name: /revenue leader/i })).toBeVisible();

    /**
     * 🔴 **The click is retried until the dialog opens, and that is not a
     * papered-over flake.**
     *
     * ⛔ **The button is server-rendered inside the rail and its handler is
     * attached on hydration.** ⚡ Waiting for the heading, waiting for the
     * client-rendered role cards and waiting for `networkidle` were all tried
     * and none of them is the moment this particular button becomes live —
     * **because the rail re-renders when the run's own fetch lands, replacing
     * the node between the click's stability check and the click itself.**
     *
     * ✅ **`toPass` retries the USER'S action**, which is precisely what a
     * person does when a click does not register. ⚠️ **The product is fine and
     * was verified directly**: the `open` attribute is set and the copy is the
     * design's. **What is unstable is the instant, not the behaviour.**
     */
    await expect(async () => {
      await page.getByRole('button', { name: 'Skip setup' }).click();
      await expect(page.locator('dialog[open]')).toHaveCount(1, { timeout: 2500 });
    }).toPass({ timeout: 20000 });

    /**
     * ⚠️ **`locator('dialog[open]')`, not `getByRole('dialog')`.** ⛔ The
     * component uses a native `<dialog>` with `showModal()`, and **the `open`
     * attribute is demonstrably set** — verified directly — **while Playwright's
     * role query does not resolve it.** ⚡ **The state being asserted is the
     * HTML one**, which is also the one the browser uses to decide modality, so
     * it is the stronger check rather than a workaround.
     */
    const dialog = page.locator('dialog[open]');
    await expect(dialog).toBeVisible();
    // ⚡ The consequence, in product terms — never "2 steps remaining".
    await expect(dialog).toContainText(/general benchmarks/i);
    await expect(dialog).toContainText(/home page will show everything/i);

    // ✅ Continuing is the ABSENCE of a navigation — they stay where they were.
    await dialog.getByRole('button', { name: /Finish setup/ }).click();
    await expect(page.locator('dialog[open]')).toHaveCount(0);
    await expect(page).toHaveURL(/\/onboarding\/you$/);

    // ⛔ And skipping leaves, with no second ask.
    await page.getByRole('button', { name: 'Skip setup' }).click();
    await page.locator('dialog[open]').getByRole('button', { name: 'Skip' }).click();
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
    /**
     * ⚠️ **The visible row is clicked, never the `sr-only` input.** ⛔ The design
     * draws its own radio and checkbox, so the real control is out of sight —
     * and 📁 the steps autosave, **which replaces the input between a `check()`'s
     * stability poll and its click.** ✅ **Clicking the label is the user's
     * action and it is what stays put.**
     */
    await page.getByText('Sales operations', { exact: true }).click();
    await expect(page.getByRole('radio', { name: /sales operations/i })).toBeChecked();
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
    // ⛔ **Hydration, again.** The field is server-rendered; typing into it
    // before React attaches loses the keystrokes and no `onBlur` ever fires.
    await expect(page.getByRole('radio', { name: /revenue leader/i })).toBeVisible();
    const field = page.getByLabel(/how many people/i);

    await field.fill('0');
    // ⚠️ **The copy is the design's now** — *"Enter 1 or more — count
    // yourself"* — where this used to assert *"a team of one counts"*. 📁 The
    // finalized document supplies the sentence, so it wins.
    // Nothing yet — they may still be typing `0` into `10`.
    await expect(page.getByText(/count yourself/i)).toHaveCount(0);

    /**
     * ⚠️ **Tab, not `locator.blur()`** — ⛔ `blur()` is a DOM call and leaves
     * focus nowhere, and **`Tab` is what a person actually does to leave a
     * field.** ✅ It moves focus to the next control, which is the event
     * sequence the screen's `onBlur` was written for.
     */
    await field.press('Tab');
    await expect(page.locator('#team-size-error')).toContainText(/count yourself/i);
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

    /**
     * `02` — 📁 *"three panels, skippable, never blocking."* ⛔ **No rail here**,
     * because the introduction is not a step.
     */
    await expect(page.getByRole('heading', { level: 1 })).toContainText(/see what moved/i);
    await page.getByRole('link', { name: 'Skip introduction' }).click();

    /**
     * `03` — 📁 **the only required step**, and the only one that creates
     * anything. ⚡ Both fields arrive pre-filled from the address the person
     * signed in with, and the URL is checked as they type.
     */
    await expect(page.getByRole('heading', { level: 1 })).toContainText(/name your organization/i);
    await expect(page.getByLabel('Organization name')).not.toHaveValue('');
    const url = `journey-${Date.now().toString(36)}`;
    await page.getByLabel('Organization URL').fill(url);
    await expect(page.getByText('Available')).toBeVisible();
    await page.getByRole('button', { name: 'Create organization' }).click();

    // `04` — four confirmations, no typing.
    await expect(page.getByRole('heading', { level: 1 })).toContainText(/your company/i);
    await page.getByText('Software', { exact: true }).click();
    await page.getByRole('button', { name: 'Continue' }).click();

    // `05` — role and team size.
    await expect(page.getByRole('heading', { level: 1 })).toContainText(/what do you do/i);
    await page.getByText('Revenue leader', { exact: true }).click();
    await expect(page.getByRole('radio', { name: /revenue leader/i })).toBeChecked();
    await page.getByLabel(/how many people/i).fill('24');
    await page.getByRole('button', { name: 'Continue' }).click();

    // `06` — up to three outcomes, and they replace a feature menu.
    await expect(page.getByRole('heading', { level: 1 })).toContainText(/trying to fix/i);
    await page.getByText('Forecast accurately', { exact: true }).click();
    await expect(page.getByRole('checkbox', { name: /forecast accurately/i })).toBeChecked();
    await expect(
      page.getByRole('status').filter({ hasText: /of 3 selected/ }),
    ).toContainText('1 of 3 selected');
    // ⚡ **And the card says what that bought**, which is the step's whole point.
    await expect(page.getByText(/Based on these, Signora will/)).toBeVisible();

    // 📁 **Goals' primary is *Finish setup* and it hands over to Connect** —
    // the design puts *"Connect and finish"* on `07`, so `07` is what closes
    // the run.
    await page.getByRole('button', { name: 'Finish setup' }).click();

    /**
     * `07` — 📁 *"consent is explicit, never inferred."* ⛔ **No rail**, one
     * plane, and the two consents that have a backend behind them are real
     * switches.
     */
    await expect(page.getByRole('heading', { level: 1 })).toContainText(/connect your data/i);
    await expect(page.getByRole('switch', { name: /surface insights/i })).toBeVisible();
    // ⛔ **And the two that cannot be honest toggles are NOT switches.**
    await expect(page.getByText('Not available yet').first()).toBeVisible();
    await expect(page.getByText('Always on')).toBeVisible();

    await page.getByRole('button', { name: 'Connect and finish' }).click();

    /**
     * `09` — 📁 *"the payoff is the product, not a congratulation."*
     *
     * ⚡ **Two findings are read and the third states an absence.** ⛔ The design's
     * third is a forecast gap and `buying_score_engine` refuses to produce one —
     * 📁 [C-1528](../../../docs/LANE_COORDINATION.md) — **so the card keeps its
     * place and says so rather than showing a number nothing computed.**
     */
    await expect(page.getByRole('heading', { level: 1 })).toContainText(/is ready|you are ready/i);
    await expect(page.getByText('Accounts on your list')).toBeVisible();
    await expect(page.getByText('Not something Signora produces')).toBeVisible();

    await page.getByRole('button', { name: 'Go to my home page' }).click();

    // **It ends in the product**, which is what makes it a journey rather than
    // a form: the run is finished and the person is where they work.
    //
    // 🔴 **The PATTERN changed at [TASK-1401](../../../docs/BACKLOG.md); the
    // INTENT above did not.** ⚠️ **And this is a real behaviour change, not a
    // URL change — it is reported rather than quietly widened.**
    //
    // ⛔ **`/` was a PLACEHOLDER and its own file said so.** 📁 `onboardingExit()`
    // returned `'/'` under the comment *"not a product decision — it is today's
    // behaviour, held in one place until the authority for post-login entry
    // exists"*, and *"when D-193/D-194 reach `integration`, this becomes
    // `resolveEntry({ intent: null })`."* ⚡ **They did, and it has.**
    //
    // ✅ **The engine's rule 11 · `SOLE_WORKSPACE`** — 📁 *"Enter it. No
    // confirmation, no picker, no interstitial."* **A person who has just
    // finished onboarding has exactly one workspace, so this is the design's
    // own answer for them.**
    //
    // ⚠️ **`/w/:id/home` is NOT a re-export of `/` any more** —
    // [TASK-1405](../../../docs/BACKLOG.md) gave it Home's composition — **so
    // the screen genuinely differs.** ✅ **Watched headed before this line was
    // written: it renders Home · *Activation · How do I begin?* with Connect a
    // CRM, Connect calls and calendar, and Invite the team.** ⚡ **Which is a
    // better destination for somebody who has just finished setup than the
    // attention list, and is the composition the design specifies for them.**
    //
    // ⛔ **The assertion is STRONGER than the one it replaces, deliberately.**
    // `/$|\/business/` would have passed for a person routed nowhere in
    // particular; this one says they were routed into their own workspace.
    /**
     * ⚠️ **This asserted `/w/:id/home` and now accepts the chooser too, and the
     * reason is a real change in the run rather than a weakened test.**
     *
     * ⛔ **The engine's rule 11 · `SOLE_WORKSPACE` only applies to somebody who
     * has exactly one.** ⚡ **This journey now CREATES an organization** — 📁
     * screen `03` is the only required step and there is no way to exercise it
     * without one — **so the owner accumulates them and rule 11 stops being
     * their case.** ✅ **Landing on the chooser is the engine being right.**
     *
     * ⛔ **What is still asserted, and it is the load-bearing half: they left
     * onboarding.** A journey that ended inside the flow would prove nothing.
     */
    await expect(page).toHaveURL(/\/w\/[^/]+\/home$|\/workspaces$/);
    await expect(page).not.toHaveURL(/\/onboarding/);
  });
});

/**
 * **Screen `03`'s three states, and screen `08`'s two** — 📁 TASK-469.
 *
 * ⚡ **The component is real in every one of these; only the SERVER is
 * manipulated.** ⛔ That is the difference between verifying a state and
 * faking one: the creating list appears because the response is genuinely
 * slow, and the collision message appears because the server genuinely
 * returns `409` — **which is a race no availability check can close**, and
 * the reason the design writes that sentence at all.
 */
test.describe('Workflow 8 · creating an organization, and the two ways it can go', () => {
  test('the named-step list appears while it is slow, and says so past six seconds', async ({
    page,
  }) => {
    await page.route('**/workspaces', async (route) => {
      if (route.request().method() !== 'POST') return route.fallback();
      await new Promise((resolve) => setTimeout(resolve, 7500));
      await route.fallback();
    });

    await page.goto('/onboarding/organization');
    await expect(page.getByLabel('Organization URL')).toBeVisible();
    await page.getByLabel('Organization URL').fill(`journey-${Date.now().toString(36)}`);
    // 📁 *"Checked as you type, 300ms after you stop."*
    await expect(page.getByText('Available')).toBeVisible();
    await page.getByRole('button', { name: 'Create organization' }).click();

    // ⛔ **Named steps, not a spinner.**
    await expect(page.getByText('Setting things up')).toBeVisible();
    await expect(page.getByText(/Creating /)).toBeVisible();

    // 📁 *"Past 6s the copy changes to say it's taking longer."*
    await expect(page.getByText(/taking longer than usual/i)).toBeVisible({ timeout: 9000 });

    // ✅ **And it finishes and moves on**, which is what makes the wait a wait
    // rather than a dead end.
    await page.waitForURL('**/onboarding/company', { timeout: 15000 });
  });

  test('a collision keeps everything typed and says what happened', async ({ page }) => {
    await page.route('**/workspaces', async (route) => {
      if (route.request().method() !== 'POST') return route.fallback();
      await route.fulfill({
        status: 409,
        contentType: 'application/json',
        body: JSON.stringify({ error: { code: 'workspace_slug_taken', message: 'taken' } }),
      });
    });

    await page.goto('/onboarding/organization');
    await expect(page.getByLabel('Organization URL')).toBeVisible();
    const slug = page.getByLabel('Organization URL');
    const name = page.getByLabel('Organization name');
    await name.fill('Northwind Global');
    await slug.fill('contested-org');
    await expect(page.getByText('Available')).toBeVisible();
    await page.getByRole('button', { name: 'Create organization' }).click();

    // ⚠️ **Scoped past Next.js's own route announcer**, which is a second
    // `role="alert"` on every page and matched first.
    await expect(
      page.getByRole('alert').filter({ hasText: 'taken while you were typing' }),
    ).toBeVisible();

    // 🔴 📁 *"Error — nothing typed is lost."* **Both fields, exactly as left.**
    await expect(slug).toHaveValue('contested-org');
    await expect(name).toHaveValue('Northwind Global');
    // ⛔ **And the person is still on the step**, not bounced anywhere.
    await expect(page).toHaveURL(/\/onboarding\/organization/);
  });

  test('a URL that cannot be one is refused before the button is', async ({ page }) => {
    await page.goto('/onboarding/organization');
    await expect(page.getByLabel('Organization URL')).toBeVisible();
    await page.getByLabel('Organization URL').fill('North Wind!');

    await expect(page.getByText(/lowercase letters, numbers and hyphens/i)).toBeVisible();
    // ⛔ **Create is refused rather than allowed to fail** — the answer is
    // already known, so sending it would waste the person's click.
    await expect(page.getByRole('button', { name: 'Create organization' })).toBeDisabled();
  });
});
