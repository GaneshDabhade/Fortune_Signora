/**
 * **Review 3 — the first hour, from a person who has never existed.**
 *
 *     make review-first-hour
 *
 * Every review so far began signed in, inside an organization with twelve
 * scored accounts. **That is the one state a real trial never starts in.** This
 * one registers a brand new person through the product's own sign-up form and
 * follows them until they either reach something valuable or run out of things
 * to click.
 *
 * ## What it is looking for
 *
 * Not correctness — Review 1 and 2 covered that. **Clarity, confidence,
 * excitement, discoverability, and the learning curve.** The specific question
 * at every step is *"does this person know what to do next, and do they want
 * to?"*
 *
 * ## It creates a real person
 *
 * Through the real sign-up route, with a real password, into the lane's own
 * database. **No seeding, no fixture, no direct write** — the whole point is
 * to see what the product does for somebody it has never met, and a seeded
 * shortcut would skip precisely the hour under review.
 */

import { chromium, type Page } from '@playwright/test';

import { browserEnvironment, resolveAppUrl } from '../e2e/fixtures/environment';

const PACE = Number(process.env.PACE ?? 900);

/** A person who has never used Signora. New on every run, so the hour is
 * genuinely a first one rather than a replay. */
const NEWCOMER = {
  name: 'Priya Raman',
  email: `priya.raman.${Date.now()}@northwind.example`,
  password: 'signora-first-hour-password',
} as const;

function say(heading: string, body?: string): void {
  process.stdout.write(`\n${'─'.repeat(72)}\n${heading}\n${'─'.repeat(72)}\n`);
  if (body) process.stdout.write(`${body}\n`);
}

/** What this person can see, and — the question of this review — what the
 * product is inviting them to do next. */
async function moment(page: Page, label: string): Promise<void> {
  await page.waitForLoadState('networkidle').catch(() => undefined);
  await page.waitForTimeout(PACE);
  const seen = await page.evaluate(() => {
    const main = document.querySelector('main') ?? document.body;
    const actions = [...main.querySelectorAll('button:not([disabled]), a[href]')]
      .map((el) => (el.getAttribute('aria-label') ?? el.textContent ?? '').trim())
      .filter(Boolean);
    return {
      text: (main.innerText ?? '').split('\n').map((l) => l.trim()).filter(Boolean).slice(0, 30),
      actions: [...new Set(actions)],
      nav: [...document.querySelectorAll('nav a')].map((a) => a.textContent?.trim()),
    };
  });
  say(`${label}   ${page.url()}`);
  process.stdout.write(seen.text.map((l) => `  │ ${l}`).join('\n'));
  process.stdout.write(`\n\n  next steps offered: ${seen.actions.join(' · ') || '(NONE)'}\n`);
  process.stdout.write(`  navigation:        ${seen.nav.join(' · ') || '(none)'}\n`);
}

async function main(): Promise<void> {
  const baseURL = resolveAppUrl();
  const browser = await chromium.launch({
    channel: 'chromium',
    headless: false,
    slowMo: 250,
    env: browserEnvironment(),
    args: ['--window-size=1400,950'],
  });
  const page = await (
    await browser.newContext({ baseURL, viewport: { width: 1360, height: 880 } })
  ).newPage();

  say('The first hour', `${NEWCOMER.name} has never heard of Signora. ${NEWCOMER.email}`);

  await page.goto('/sign-up');
  await moment(page, '1 · The sign-up form');

  // Fill whatever this form actually asks for, rather than assuming.
  for (const [label, value] of [
    ['Name', NEWCOMER.name],
    ['Email', NEWCOMER.email],
    ['Password', NEWCOMER.password],
  ] as const) {
    const field = page.getByLabel(label, { exact: false }).first();
    if (await field.count()) await field.fill(value).catch(() => undefined);
  }
  await page
    .getByRole('button', { name: /create|sign up|get started/i })
    .first()
    .click()
    .catch(() => undefined);
  await page.waitForTimeout(5000);
  await moment(page, '2 · The moment after signing up');

  // **The seam, and it is the finding.** The hour stops here for anybody who
  // is not reading a terminal: the verification link is written to the dev
  // server's stdout, because `console` is the only transport this build has.
  // Verifying through Better Auth's own route — exactly what the approved
  // `demo-users` seeder does — is the only way to see the other 55 minutes.
  const { auth: createAuth } = await import('../../lib/auth/server');
  const { createEmailVerificationToken } = await import('better-auth/api');
  const { loadAuthConfig } = await import('../../lib/auth/config');
  const config = loadAuthConfig();
  const token = await createEmailVerificationToken(config.betterAuthSecret, NEWCOMER.email);
  await createAuth().api.verifyEmail({ query: { token } });
  process.stdout.write(
    '\n  [ the link that would have been emailed was redeemed here, through\n' +
      '    Better Auth\'s own route — see PX-319. The rest of the hour follows. ]\n',
  );

  await page.goto('/sign-in');
  await page.getByLabel('Email').fill(NEWCOMER.email);
  await page.getByLabel('Password').fill(NEWCOMER.password);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.waitForTimeout(4000);

  await page.goto('/');
  await moment(page, '3 · The first screen, with nothing in it');

  await page.goto('/settings');
  await moment(page, '4 · Settings, for somebody who has configured nothing');

  await page.goto('/settings/products');
  await moment(page, '5 · Your business, empty');

  // The one thing the empty state asks for: a first product.
  const add = page.getByRole('button', { name: 'Add product' }).first();
  if (await add.count()) {
    await add.click();
    await page.getByLabel(/name/i).first().fill('Revenue Cloud').catch(() => undefined);
    await page
      .getByRole('button', { name: /save|add/i })
      .last()
      .click()
      .catch(() => undefined);
    await page.waitForTimeout(3000);
    await moment(page, '6 · Having done the one thing the product asked for');
  }

  await page.goto('/');
  await moment(page, '7 · Back to the first screen. Has anything changed?');

  await page.goto('/settings/connections');
  await moment(page, '8 · Connections — the only remaining lead');

  say(
    'The end of the first hour',
    'Whatever this person can reach, they have now reached.',
  );
  await page.waitForTimeout(4000);
  await browser.close();
}

main().catch((error: unknown) => {
  process.stderr.write(`\nthe first hour stopped: ${String(error)}\n`);
  process.exitCode = 1;
});
