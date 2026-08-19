import { expect, test } from './fixtures/signora';

/**
 * **The bell and its panel** — [TASK-495](../../../docs/BACKLOG.md) slice ⓑ,
 * against 📁 `Fortune Signora App Shell.dc.html` §10.
 *
 * ## ⚠️ Why the populated panel is stubbed and the empty one is not
 *
 * 🔴 **The Playground has no notifications, and the reason is measured**: it
 * holds **442 research tasks and 714 findings**, and **5 `ai_research.requested`
 * events sitting unprocessed in the outbox** — ⛔ **no worker drains it during
 * seeding**, so the producer never completes and never publishes
 * `notification.requested`. ⚡ **The producer exists**
 * (`ai_research_engine/application/run.py`); nothing runs it.
 *
 * ✅ **So the empty path is the Playground's real state and is walked as such.**
 * ⚡ **The populated path is stubbed at the production read boundary** — the
 * feed endpoint, returning the shape the server returns — which verifies the
 * rendering without pretending the workspace has data it does not.
 */

async function openShell(page: import('@playwright/test').Page) {
  await page.goto('/');
  await page.waitForURL(/\/w\/[0-9a-f-]{36}\/home$/, { timeout: 30_000 });
  await expect(page.getByTestId('home')).toBeVisible({ timeout: 30_000 });
}

test('@journey the bell opens a panel, names the workspace, and closes to itself', async ({
  page,
}) => {
  await openShell(page);

  const bell = page.getByRole('button', { name: /^Notifications/ });
  await expect(bell).toBeVisible();
  // 📁 *"32 × 32"* — the slot's declared size, measured rather than read.
  const box = await bell.boundingBox();
  expect(Math.round(box?.width ?? 0)).toBe(32);
  expect(Math.round(box?.height ?? 0)).toBe(32);

  await bell.click();

  const panel = page.getByTestId('notification-panel');
  await expect(panel).toBeVisible();
  // 📁 *"Opens a 400px panel, not a page."* ⛔ **The URL is unchanged** — a
  // notifications page would lose the customer's context, which is the design's
  // stated reason for a popover.
  expect(Math.round((await panel.boundingBox())?.width ?? 0)).toBe(400);
  await expect(page).toHaveURL(/\/home$/);

  // 📁 §*Multi-workspace* — the panel carries the workspace name.
  await expect(page.getByRole('dialog', { name: /Notifications — / })).toBeVisible();

  // 📁 The design's three groups.
  for (const tab of ['Needs you', 'Mentions', 'All']) {
    await expect(page.getByRole('tab', { name: tab })).toBeVisible();
  }

  // ♿ Escape closes it and focus returns to the bell.
  await page.keyboard.press('Escape');
  await expect(panel).toBeHidden();
  await expect(bell).toBeFocused();
});

test('@journey a workspace with nothing to say draws no badge and says so', async ({
  page,
}) => {
  await openShell(page);

  // ⛔ **No badge at zero.** 📁 A `0` badge is a count nobody acts on wearing
  // the shape of one they would.
  await expect(page.getByTestId('notification-badge')).toHaveCount(0);

  await page.getByRole('button', { name: /^Notifications/ }).click();
  await page.getByRole('tab', { name: 'All' }).click();

  await expect(page.getByTestId('notifications-empty')).toBeVisible();
});

test('@journey an item carries its dot until it is opened', async ({ page }) => {
  const now = new Date().toISOString();
  const feed = {
    notifications: [
      {
        id: '11111111-1111-1111-1111-111111111111',
        category: 'needs_you',
        actor_kind: 'agent',
        actor_person_id: null,
        actor_agent_name: 'Renewal risk sweep',
        subject_kind: 'account',
        subject_id: '22222222-2222-2222-2222-222222222222',
        summary: 'finished researching Vantage Logistics',
        expectation: 'Review what it found',
        occurred_at: now,
        read_at: null,
      },
    ],
  };

  await page.route('**/api/proxy/**/notifications', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(feed) }),
  );
  await page.route('**/api/proxy/**/notifications/unread', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ unread: 1, capped: false, cap: 99 }),
    }),
  );

  await openShell(page);

  // 📁 *"Count badge caps at 99+"* — and below the cap it is the figure.
  await expect(page.getByTestId('notification-badge')).toHaveText('1');
  await expect(page.getByRole('button', { name: 'Notifications, 1 unread' })).toBeVisible();

  await page.getByRole('button', { name: /^Notifications/ }).click();

  // 📁 *"Grouped by day with sticky day heads"*, and *"unread is a 6px dot"*.
  // ⚠️ **Scoped to the panel** — Home's own attention card also labels a region
  // *Today*, and an unscoped query matched both.
  const panel = page.getByTestId('notification-panel');
  await expect(panel.getByRole('region', { name: 'Today' })).toBeVisible();
  const dot = panel.getByTestId('unread-dot');
  await expect(dot).toHaveCount(1);
  expect(Math.round((await dot.boundingBox())?.width ?? 0)).toBe(6);
});
