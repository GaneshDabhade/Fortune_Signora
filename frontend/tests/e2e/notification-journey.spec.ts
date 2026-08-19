/**
 * **Research finishes → the bell says so → the reader opens it** —
 * 📁 [TASK-495](../../../docs/BACKLOG.md) slice ⓑ, the journey
 * [§19](../../../CLAUDE.md) requires and the row names by hand:
 *
 * > 📁 ***"Playwright — an event occurs and the customer sees it without
 * > reloading."***
 *
 * ## 🔴 Why this is a journey and not three component tests
 *
 * ⚡ **It is the only test in the repository that crosses the whole mechanism**:
 * a customer's click → a background run → `notification.requested` on the
 * outbox → the relay → `workspace_tenancy`'s consumer → a row → the feed → the
 * badge on a screen nobody reloaded. ⛔ **Every component test above it stubs
 * the read**, and stubbing is exactly what hid the defects this journey found.
 *
 * ## ⚠️ What it found on its first run, before it ever passed
 *
 * 🔴 **The badge issued a `GET` to a `POST` route and took a `405` on every
 * authenticated screen** — so the bell had never shown a count for anybody.
 * 🔴 **`Mark as read` double-encoded its body**, because `apiRequest` stringifies
 * and the caller stringified first. ⛔ **Neither was visible to a test that
 * mocked the hook**, and both are the reason §19 makes the journey part of Done
 * rather than a nicety after it.
 */
import { expect, test } from './fixtures/signora';

/**
 * ⚠️ **Three minutes, and the figure is the pipeline's rather than a guess.**
 * 📁 `useAccountResearch` documents *"a research run takes about a minute"*, and
 * the bell polls every 30s — ⛔ the suite's 60s default would time out on a
 * product working exactly as designed.
 */
test.describe('Research → notified → open', () => {
  test('@journey an agent finishes work and the bell says so, without a reload', async ({
    page,
  }) => {
    test.setTimeout(180_000);

    /**
     * ⚡ **An account with a name**, read from the workspace rather than written
     * here — 📁 the reason `search-journey.spec.ts` has the same filter: some
     * Playground accounts show a hex fragment because no source has named them.
     */
    await page.goto('/accounts');
    const rows = page.locator('main a[href^="/accounts/"]');
    await expect(rows.first()).toBeVisible({ timeout: 20_000 });
    const named = (
      await rows.evaluateAll((els) =>
        els.map((el) => ({
          href: el.getAttribute('href') ?? '',
          name: ((el.textContent ?? '').trim().split('\n')[0] ?? '').trim(),
        })),
      )
    ).find((row) => /^[A-Za-z][A-Za-z' ]{4,}$/.test(row.name));
    expect(named, 'no account in this workspace has a legal name to research').toBeTruthy();

    await page.goto(named!.href);

    /* 📁 *"Research this account"* on an account nobody has researched,
       *"Refresh research"* on one somebody has — **the design has one label in
       one place and which one depends on the workspace, not on this test.** */
    const ask = page.getByRole('button', { name: /^(Research this account|Refresh research)$/ });
    await expect(ask).toBeVisible({ timeout: 30_000 });
    await expect(ask, 'a run was already in flight, so this journey has nothing to start').toBeEnabled();

    const bell = page.getByRole('button', { name: /^Notifications/ });
    await expect(bell).toBeVisible();
    /* ⛔ **Read the badge BEFORE the click**, so what follows is a change rather
       than a state — the workspace may already hold notifications. */
    const before = await page.getByTestId('notification-badge').count();
    expect(before, 'the bell already carries a badge, so an arrival cannot be observed').toBe(0);

    await ask.click();

    /**
     * 🔴 **The claim, and the whole reason the journey exists.**
     *
     * ⛔ **No `reload`, no `goto`, no navigation** between the click and this
     * assertion. ⚡ **The badge arrives because the feed polls** — 📁
     * `lib/query/hooks/notifications.ts`, and before that poll existed the bell
     * described the moment the screen was opened and nothing after it.
     */
    await expect(
      page.getByTestId('notification-badge'),
      [
        'the run finished and the bell never said so without a reload.',
        'If this timed out with nothing in `notification`, the background tier is',
        'not running: this journey needs `arq apps.worker.main.WorkerSettings` on',
        'the `ai_research` pool AND `python -m apps.worker.relay_main`. It is the',
        'first journey in the suite that does — see docs/LANE_COORDINATION.md.',
      ].join(' '),
    ).toBeVisible({ timeout: 150_000 });
    await expect(bell).toHaveAccessibleName(/Notifications, \d+ unread/);

    await bell.click();
    const panel = page.getByTestId('notification-panel');
    await expect(panel).toBeVisible();

    /**
     * 📁 ***"Each item states who or what acted, on which record, and what is
     * expected of the reader"*** — ⚡ **who acted** is the agent's own name, and
     * 📁 *"agent and AI notifications are marked with the intelligence hue so a
     * generated nudge never reads as a colleague's request."*
     */
    const item = panel.getByRole('listitem').first();
    await expect(item).toContainText('Research');
    await expect(item.getByTestId('agent-mark')).toBeVisible();
    /* ⛔ **On which record — the name, not the id.** ⚡ Resolved by the shell
       from the identity surface, so this is the account the reader pressed the
       button on rather than the run's internal artifact. */
    await expect(item.getByTestId('notification-record')).toHaveText(named!.name);
    /* 📁 *"Unread is a 6px dot on the right, never a coloured row."* */
    await expect(item.getByTestId('unread-dot')).toBeVisible();

    /**
     * 🔴 📁 ***"Opening the panel does not mark items read; opening an item
     * does"*** — ⛔ **the dot was still there after the panel opened**, which is
     * the first half of that sentence, and this is the second. ⚡ **And it goes
     * to the record**, which is 📁 `navigate-to-context`.
     */
    /* ⛔ **A link, not a button** — ⚡ the row goes somewhere, so it is one. */
    const row = item.getByRole('link');
    await expect(row).toHaveAttribute('href', named!.href);
    await row.click();
    await page.waitForURL(new RegExp(`${named!.href}$`), { timeout: 20_000 });

    /* ⛔ **The bell, re-read on the page it took us to** — ⚡ the badge is the
       feed's own count, so this asserts the mark reached the server rather than
       that a panel repainted. */
    await expect(
      page.getByTestId('notification-badge'),
      'the item was opened and the bell still counts it',
    ).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Notifications' })).toBeVisible();
  });
});
