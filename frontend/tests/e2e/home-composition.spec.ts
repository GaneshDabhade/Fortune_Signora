/**
 * **Home resolves and always renders** —
 * [TASK-1405](../../../docs/BACKLOG.md).
 *
 * ⚠️ **The row says *"no Playwright coverage — not a customer journey"*, and it
 * was right when it was written**: the row's remaining half was a resolver with
 * no surface. ⛔ **It has a surface now** — it is the destination eight of the
 * entry engine's twenty-four rules return, **including the default** — **so it
 * is watched rather than taken on trust.**
 *
 * ⚡ **What only a browser can answer here**: that the route renders at all
 * (jsdom never mounted it), and that the App Shell's *"Home always renders"*
 * guarantee survives a real session.
 */
import { expect, test } from './fixtures/signora';

test('🔴 the rail leads to Home, and Home renders', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('main')).toBeVisible();

  await page
    .getByRole('navigation', { name: 'Primary' })
    .getByRole('link', { name: 'Home' })
    .click();

  await expect(page).toHaveURL(/\/w\/[0-9a-f-]+\/home$/);

  // 📁 *"a composition always resolves, so Home ALWAYS renders."*
  const home = page.getByTestId('home');
  await expect(home).toBeVisible();
  await expect(home).toHaveAttribute('data-composition', /executive|seller|revenue_operations|activation/);
});

test('⛔ it draws no card the platform has not published', async ({ page }) => {
  await page.goto('/');
  await page
    .getByRole('navigation', { name: 'Primary' })
    .getByRole('link', { name: 'Home' })
    .click();
  await expect(page.getByTestId('home')).toBeVisible();

  /**
   * ⚠️ **This asserted `toHaveCount(0)` and the registry is no longer empty.**
   * ⛔ **The property was never *"no cards"*** — it is 📁 [§20c](../../../CLAUDE.md)'s
   * *"a screen with no module behind it ships a designed empty state rather
   * than invented cards"*, **and the way to keep asserting that as cards arrive
   * is to check that every rendered card is one a module registered.**
   */
  const drawn = await page
    .locator('[data-card]')
    .evaluateAll((els) => els.map((e) => e.getAttribute('data-card')));
  const registered = new Set([
    'connect-a-crm',
    'connect-calls',
    'invite-the-team',
    'pipeline-health',
    'needs-you-today',
  ]);
  expect(drawn.every((id) => id !== null && registered.has(id))).toBe(true);

  // ⛔ **Never a placeholder for a card nobody has built** — 📁 the design's own
  // non-goal: *"sample or synthetic data to make an empty Home look populated."*
  await expect(page.getByText(/coming soon/i)).toHaveCount(0);
});

test('📁 the attention card reads signals, not the attention list', async ({ page }) => {
  /**
   * 🔴 **The product owner ruled `AccountAttention` out of Home on 2026-08-17.**
   * ⚡ **Only a browser can assert which requests a page actually makes**, and
   * the whole point of the ruling is a dependency rather than a rendering.
   */
  await page.goto('/');
  await page
    .getByRole('navigation', { name: 'Primary' })
    .getByRole('link', { name: 'Home' })
    .click();
  await expect(page.getByTestId('home')).toBeVisible();

  /**
   * ⛔ **Recorded from a RELOAD, not from the click.** `/` is the Attention
   * screen and it reads `/accounts` legitimately; recording across the
   * navigation would attribute its request to Home and the assertion below
   * would fail on a page that is behaving correctly.
   */
  const asked: string[] = [];
  page.on('request', (r) => asked.push(new URL(r.url()).pathname + new URL(r.url()).search));
  await page.reload();
  await expect(page.getByTestId('home')).toBeVisible();
  await page.waitForTimeout(1200);

  const home = asked.filter((p) => p.includes('/api/proxy/workspaces/'));
  expect(home.some((p) => /\/triage(\?|$)/.test(p))).toBe(true);
  // ⛔ **`/accounts` is the Opportunity Engine's ranked open work.** It remains
  // authoritative for Companies, Account 360 and Triage — **Home simply must
  // not ask for it.**
  expect(home.filter((p) => /\/accounts(\?|$)/.test(p))).toEqual([]);
});
