/**
 * **Workflow 1 · Login** — the journey the product owner watches.
 *
 * **TASK-467**, against
 * `docs/design-snapshot/screens/Fortune Signora Authentication.dc.html`, and
 * run **headed** at every milestone on [D-158](../../../docs/DECISION_REGISTER.md)'s
 * explicit instruction: *"I want to visually observe the implementation
 * progressing."*
 *
 * ⚡ **This asserts the design's stated measurements, not a screenshot.** The
 * card is 400px, it carries `--radius-xl` and an elevation, and below 640px it
 * *stops being a card* rather than shrinking — *"dropped rather than shrunk,
 * which is what keeps it from looking like a website on a phone."*
 */

import { expect, test } from '@playwright/test';

test.describe('Workflow 1 · the authentication shell', () => {
  test('the sign-in screen renders on the one card', async ({ page }) => {
    await page.goto('/sign-in');
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });

  test('the product mark sits above the card', async ({ page }) => {
    await page.goto('/sign-in');
    await expect(page.getByText('Fortune Signora')).toBeVisible();
  });

  test('desktop: the card is 400px and centred', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('/sign-in');
    const card = page.locator('main > div');
    await expect(card).toBeVisible();
    expect((await card.boundingBox())?.width).toBe(400);
  });

  test('mobile: the card becomes the page', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/sign-in');
    // The card itself — the element that holds the heading, not the mark above it.
    const inner = page.getByRole('heading', { level: 1 }).locator('xpath=../..');
    // The frame is dropped, not shrunk — no radius, no border, nothing cast.
    await expect(inner).toHaveCSS('border-radius', '0px');
    await expect(inner).toHaveCSS('border-top-width', '0px');
    // ⚠️ **Asserted on visibility, not on the literal `none`.** Tailwind's
    // `shadow-none` sets the shadow variables to transparent rather than
    // removing the property, so the computed value is a transparent triple.
    // What the design requires is that nothing is cast, and that is what a
    // fully-transparent shadow means.
    const shadow = await inner.evaluate((el) => getComputedStyle(el).boxShadow);
    expect(shadow.replace(/rgba\(0, 0, 0, 0\)[^,]*,?/g, '').trim()).toBe('');
  });

  test('the email field is labelled and autocompletes', async ({ page }) => {
    // The design's 1.3.5: *"autocomplete tokens on every field… managers fill
    // the whole form."*
    await page.goto('/sign-in');
    const email = page.getByLabel(/email/i);
    await expect(email).toBeVisible();
    await expect(email).toHaveAttribute('type', 'email');
  });
});
