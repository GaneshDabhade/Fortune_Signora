/**
 * **`Ask Signora` is the rail's first pinned entry, and it opens the room** —
 * [TASK-1470](../../../docs/BACKLOG.md), §12 door `01`.
 *
 * 🔴 **Position is the claim**, and the row says why: *"a test that only checks
 * `Ask Signora` exists passes against the current defect."* ⛔ **It existed —
 * below the utilities, outside the rail.**
 */
import { expect, test } from './fixtures/signora';

const RAIL = 'nav[aria-label="Primary"]';

test.use({ viewport: { width: 1280, height: 900 } });

test('🔴 the assistant is the first entry of the rail’s pinned group', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('main')).toBeVisible();

  // ⚡ **The pinned group, by the divider the design gives it.**
  const group = page.locator(`${RAIL} .border-t`).first();
  const names = await group.locator('a, button').evaluateAll((nodes) =>
    nodes.map((n) => n.getAttribute('aria-label') ?? n.textContent?.trim() ?? ''),
  );

  expect(names[0]).toBe('Ask Signora');
  expect(names).toEqual(['Ask Signora', 'Settings', 'Shortcuts', 'Docs & support']);
});

test('✅ pressing it opens the assistant, and the panel says what it cannot do', async ({
  page,
}) => {
  await page.goto('/');
  await expect(page.getByRole('main')).toBeVisible();

  await page.locator(RAIL).getByRole('button', { name: 'Ask Signora' }).click();

  const panel = page.getByRole('complementary', { name: /Ask Signora/ });
  await expect(panel).toBeVisible();
  // ⛔ **It refuses honestly rather than offering a field nothing answers.**
  await expect(panel.getByText(/cannot answer questions here yet/i)).toBeVisible();
  await expect(panel.getByRole('textbox')).toHaveCount(0);
});
