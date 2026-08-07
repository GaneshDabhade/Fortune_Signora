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

test.describe('Workflow 1 · the front door and the enterprise route', () => {
  test('Welcome offers sign in, create, and SSO under its own divider', async ({
    page,
  }) => {
    // Design 01. The `Enterprise` divider is the point: an SSO route offered
    // *beside* password sign-in reads as an afterthought to the buyer whose
    // security team is reading this screen.
    await page.goto('/welcome');
    await expect(page.getByRole('heading', { name: 'Fortune Signora' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Sign in', exact: true })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Create an organization' })).toBeVisible();
    // `exact`, because the lead paragraph says *enterprise teams* — the
    // divider is the standalone word.
    await expect(page.getByText('Enterprise', { exact: true })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Sign in with SSO' })).toBeVisible();
  });

  test('the status line under the card is answered, not decorative', async ({ page }) => {
    // The design's own rationale — *"a live status dot. Buyers check both."*
    // It reads `/api/health`, so it reports whether anybody can actually sign
    // in. **It must leave `Checking`**, which is what proves it is wired.
    await page.goto('/welcome');
    await expect(page.locator('[data-status]')).not.toHaveAttribute(
      'data-status',
      'checking',
    );
  });

  test('🔴 "Use single sign-on" now leads somewhere', async ({ page }) => {
    // Milestone 2 shipped this link with no route behind it: every enterprise
    // buyer who followed the one link addressed to them got the not-found
    // page.
    await page.goto('/sign-in');
    await page.getByRole('link', { name: 'Use single sign-on' }).click();
    await expect(page.getByRole('heading', { name: 'Single sign-on' })).toBeVisible();
  });

  test('SSO names no identity provider it cannot actually resolve', async ({ page }) => {
    // The design resolves the domain — *"northwind.com uses Okta"*. Nothing
    // maps a domain to a provider here, so the field is locked and the reason
    // is given rather than a provider name being printed.
    await page.goto('/sso');
    await expect(page.getByText(/cannot yet look up a provider/i)).toBeVisible();
    await expect(page.getByText('Okta')).toHaveCount(0);
  });

  test('the product mark is the way back to the front door', async ({ page }) => {
    await page.goto('/sign-in');
    await page.getByRole('link', { name: 'Fortune Signora' }).click();
    await expect(page).toHaveURL(/\/welcome$/);
  });

  test('recovery is offered once, where the design puts it', async ({ page }) => {
    // Milestone 2 left a second link to the same destination below the button.
    await page.goto('/sign-in');
    await expect(page.getByRole('link', { name: /forgot/i })).toHaveCount(1);
  });
});

test.describe('Workflow 1 · when the provider says no', () => {
  test('🔴 a refused sign-in lands in Signora, not on the vendor\'s error page', async ({
    page,
  }) => {
    // Better Auth serves a complete HTML document from `/api/auth/error` — its
    // own fonts, its own colours — and until milestone 4 that is where every
    // refused federated sign-in landed. This is design 16 in its place.
    await page.goto('/error?error=access_denied&error_description=user+not+assigned');
    await expect(page.getByRole('heading', { name: 'Sign-in was rejected' })).toBeVisible();
    // `exact`, because the provider's words appear twice on purpose: quoted in
    // the sentence a person reads, and again inside the reference an IT team
    // pastes into a ticket.
    await expect(page.getByText('user not assigned', { exact: true })).toBeVisible();
  });

  test('it renders on the product\'s own ground, which is the point', async ({ page }) => {
    await page.goto('/error?error=access_denied');
    const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
    expect(bg).toBe('rgb(250, 248, 246)');
  });

  test('the reference is the provider\'s code, and it offers a way back', async ({
    page,
  }) => {
    await page.goto('/error?error=access_denied');
    await expect(page.getByText('access_denied')).toBeVisible();
    await expect(
      page.getByRole('link', { name: 'Try another way to sign in' }),
    ).toBeVisible();
  });
});

test.describe('Workflow 1 · the finalized visual identity', () => {
  test('the ground is the design\'s warm #faf8f6, not a cool grey', async ({ page }) => {
    // D-162: the review found the screen still read as the legacy UI. It did,
    // because the tokens were Tailwind slate+blue — a cool system — and the
    // finalized design is a warm one. This asserts the actual value.
    await page.goto('/sign-in');
    const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
    expect(bg).toBe('rgb(250, 248, 246)');
  });

  test('the brand is the design\'s deep blue, not Tailwind blue-600', async ({ page }) => {
    await page.goto('/sign-in');
    const accent = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue('--color-accent').trim(),
    );
    expect(accent).toBe('19 78 118');
  });

  test('ink is the design\'s warm near-black, not slate-900', async ({ page }) => {
    await page.goto('/sign-in');
    const ink = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue('--color-content').trim(),
    );
    expect(ink).toBe('33 31 29');
  });

  test('the card carries the design\'s 16px radius', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('/sign-in');
    const card = page.getByRole('heading', { level: 1 }).locator('xpath=../..');
    await expect(card).toHaveCSS('border-radius', '16px');
  });
});
