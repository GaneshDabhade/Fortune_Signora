import { expect, test } from '@playwright/test';

test('@journey probe — can a person actually pick a theme', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/profile?section=appearance');
  const theme = page.getByRole('group', { name: 'Theme' });
  await expect(theme).toBeVisible({ timeout: 30_000 });

  const before = await theme.evaluate(
    (el) =>
      ([...el.querySelectorAll('input')] as HTMLInputElement[]).find((i) => i.checked)?.value ??
      null,
  );

  // What a person does: click the visible card, not the sr-only input.
  await page.getByText('For low light and long sessions.').click();
  // Wait for the ATTRIBUTE rather than a timeout — a fixed sleep cannot tell
  // "not applied" from "not applied yet", which is the whole question here.
  const settled = await page
    .waitForFunction(() => document.documentElement.getAttribute('data-theme') === 'dark', null, {
      timeout: 8000,
    })
    .then(() => true)
    .catch(() => false);
  console.log('SETTLED ' + settled);

  const after = await theme.evaluate(
    (el) =>
      ([...el.querySelectorAll('input')] as HTMLInputElement[]).find((i) => i.checked)?.value ??
      null,
  );
  const applied = await page.evaluate(() => document.documentElement.getAttribute('data-theme'));

  // And the keyboard, which is what the sr-only input is FOR.
  await page.getByText('Follows your device').click();
  await page.waitForTimeout(400);
  const afterSystem = await theme.evaluate(
    (el) =>
      ([...el.querySelectorAll('input')] as HTMLInputElement[]).find((i) => i.checked)?.value ??
      null,
  );

  console.log('CLICK ' + JSON.stringify({ before, after, applied, afterSystem }));
});
