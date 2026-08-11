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

  // ⛔ **The catalogue names twenty-three cards and the registry is empty** —
  // 📁 [§20c](../../../CLAUDE.md), a screen with no module behind it ships a
  // designed empty state rather than invented cards.
  await expect(page.locator('[data-card]')).toHaveCount(0);
  await expect(page.getByText(/nothing to put on your home yet/i)).toBeVisible();
  await expect(page.getByText(/coming soon/i)).toHaveCount(0);
});
