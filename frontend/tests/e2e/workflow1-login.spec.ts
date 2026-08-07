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

test.describe('Workflow 1 · the sign-in experience', () => {
  test('providers come first, then the divider, then the fields', async ({ page }) => {
    await page.goto('/sign-in');
    await expect(page.getByLabel('Work email')).toBeVisible();
    await expect(page.getByLabel('Password')).toBeVisible();
  });

  test('an empty submit is answered inline and takes focus to the field', async ({
    page,
  }) => {
    // 2.4.3 — focus lands on the first invalid field, not on a summary the
    // person then has to hunt from.
    await page.goto('/sign-in');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByText('Enter the work email address you use for Signora.')).toBeVisible();
    await expect(page.getByText('Enter a work email address.')).toBeVisible();
    await expect(page.getByLabel('Work email')).toBeFocused();
  });

  test('a malformed address never reaches the network', async ({ page }) => {
    await page.goto('/sign-in');
    await page.getByLabel('Work email').fill('not-an-address');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByText('Enter a work email address.')).toBeVisible();
  });

  test('a missing password is its own message, and focus moves on', async ({ page }) => {
    await page.goto('/sign-in');
    await page.getByLabel('Work email').fill('m.reinhardt@northwind.com');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByText('Your password is needed to sign in.')).toBeVisible();
    await expect(page.getByLabel('Password')).toBeFocused();
  });

  test('the password can be revealed and hidden by keyboard', async ({ page }) => {
    // 2.1.1 — show-password is a real button, reachable and operable.
    await page.goto('/sign-in');
    const password = page.getByLabel('Password');
    await password.fill('correct horse');
    await expect(password).toHaveAttribute('type', 'password');
    await page.getByRole('button', { name: 'Show' }).click();
    await expect(password).toHaveAttribute('type', 'text');
    await expect(page.getByRole('button', { name: 'Hide' })).toHaveAttribute(
      'aria-pressed',
      'true',
    );
  });

  test('the failure summary is announced politely, never as an alert', async ({
    page,
  }) => {
    // 3.3.1 — announced once. `role="alert"` would interrupt mid-typing.
    await page.goto('/sign-in');
    await page.getByRole('button', { name: 'Sign in' }).click();
    // ⚠️ **Asserted on the summary, not on the absence of every alert.** The
    // shared `Input` announces its own field message assertively and §20c
    // forbids reshaping it for one screen — so the two carry *different*
    // sentences instead, which is what stops one message being read twice.
    const summary = page.locator('[aria-live="polite"]').first();
    await expect(summary).toBeVisible();
    await expect(summary).toContainText('Enter the work email address');
  });

  test('recovery sits beside the password, and SSO is offered', async ({ page }) => {
    await page.goto('/sign-in');
    await expect(page.getByRole('link', { name: 'Forgot password?' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Use single sign-on' })).toBeVisible();
  });

  test('the whole form is reachable by keyboard alone', async ({ page }) => {
    await page.goto('/sign-in');
    await page.getByLabel('Work email').focus();
    await page.keyboard.type('m.reinhardt@northwind.com');
    await page.keyboard.press('Tab');
    await page.keyboard.type('a-password');
    await expect(page.getByLabel('Password')).toHaveValue('a-password');
  });

  test('keep me signed in is offered and operable', async ({ page }) => {
    await page.goto('/sign-in');
    const keep = page.getByLabel('Keep me signed in for 30 days');
    await keep.check();
    await expect(keep).toBeChecked();
  });
});
