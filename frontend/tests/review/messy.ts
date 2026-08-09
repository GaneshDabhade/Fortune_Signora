/**
 * **Review 2 — the world when it is not tidy.**
 *
 *     make review-messy
 *
 * Review 1 opened the account at the top of the list, which is the one the
 * product is proudest of. **This opens the ones it is not**: the account whose
 * sources disagree about its own name, the one whose evidence has expired, the
 * one two sellers are contesting, and the one nobody has named at all.
 *
 * ## Why no new scenario was written
 *
 * `playground@2` **already produces every one of those states**, and produces
 * them the honest way — from provider readings over five months, so that
 * *"contested"* and *"stale"* emerge from the pipeline rather than being
 * declared. Authoring a second messy dataset before reading the first would
 * have been work that proved nothing.
 *
 * ## It also measures the text
 *
 * The product owner's own observation was *"far too much text… it doesn't feel
 * like modern SaaS."* That is testable rather than arguable: words per screen,
 * paragraphs over forty words, and the reading time each screen demands before
 * a customer can act. **An opinion about density is worth less than the number.**
 */

import { chromium, type Page } from '@playwright/test';

import { browserEnvironment, resolveAppUrl } from '../e2e/fixtures/environment';
import { OWNER, PASSWORD } from '../e2e/fixtures/personas';

const PACE = Number(process.env.PACE ?? 700);

function say(heading: string, body?: string): void {
  process.stdout.write(`\n${'─'.repeat(72)}\n${heading}\n${'─'.repeat(72)}\n`);
  if (body) process.stdout.write(`${body}\n`);
}

/** **Reading load, measured.** 238 words a minute is the usual adult average
 * for screen prose; what matters here is the ratio between how much a screen
 * asks somebody to read and how little it asks them to decide. */
async function density(page: Page, label: string): Promise<void> {
  const m = await page.evaluate(() => {
    const main = document.querySelector('main') ?? document.body;
    const text = (main.innerText ?? '').trim();
    const words = text.split(/\s+/).filter(Boolean).length;
    const paragraphs = [...main.querySelectorAll('p')]
      .map((p) => (p.textContent ?? '').trim())
      .filter((t) => t.split(/\s+/).length > 5);
    const long = paragraphs.filter((t) => t.split(/\s+/).length >= 25);
    return {
      words,
      paragraphs: paragraphs.length,
      longParagraphs: long.length,
      longest: long.sort((a, b) => b.length - a.length)[0]?.slice(0, 200) ?? '(none)',
      actions: main.querySelectorAll('button:not([disabled]), a[href]').length,
    };
  });
  process.stdout.write(
    `\n  ${label}\n` +
      `    ${m.words} words · ${(m.words / 238).toFixed(1)} min to read · ` +
      `${m.paragraphs} paragraphs, ${m.longParagraphs} of them 25+ words\n` +
      `    ${m.actions} things a customer can actually do\n` +
      `    words per action: ${(m.words / Math.max(m.actions, 1)).toFixed(0)}\n` +
      `    longest paragraph: "${m.longest}"\n`,
  );
}

async function screen(page: Page, label: string): Promise<void> {
  await page.waitForLoadState('networkidle').catch(() => undefined);
  await page.waitForTimeout(PACE);
  const seen = await page.evaluate(() => {
    const main = document.querySelector('main') ?? document.body;
    return (main.innerText ?? '').split('\n').map((l) => l.trim()).filter(Boolean).slice(0, 45);
  });
  say(label, seen.map((l) => `  │ ${l}`).join('\n'));
}

async function main(): Promise<void> {
  const baseURL = resolveAppUrl();
  const browser = await chromium.launch({
    channel: 'chromium',
    headless: false,
    slowMo: 200,
    env: browserEnvironment(),
    args: ['--window-size=1400,950'],
  });
  const page = await (
    await browser.newContext({ baseURL, viewport: { width: 1360, height: 880 } })
  ).newPage();

  await page.goto('/signin');
  await page.getByLabel('Email').fill(OWNER.email);
  await page.getByLabel('Password').fill(PASSWORD);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.waitForURL((url) => url.pathname === '/', { timeout: 30_000 });

  say('Review 2 — the accounts the product is not proud of');

  // The rows whose badges say something went wrong, in the order a sceptical
  // evaluator would click them.
  const suspects = ['Adobe', 'MongoDB', 'Stripe', 'no source has named'];
  for (const name of suspects) {
    // **Navigate first, then wait for the rows, then look.** The first version
    // asked whether a row existed while the list was still empty and concluded
    // the account was not in the book — reporting nothing four times over, and
    // reporting it confidently.
    await page.goto('/');
    await page
      .locator('main a[href^="/accounts/"]')
      .first()
      .waitFor({ state: 'visible', timeout: 30_000 })
      .catch(() => undefined);

    const row = page.locator('main a[href^="/accounts/"]').filter({ hasText: name }).first();
    if ((await row.count()) === 0) {
      say(`(no account matching "${name}" in this book)`);
      continue;
    }
    await row.click();
    await page.waitForTimeout(3500);
    await screen(page, `An account where the world was messy — matched on "${name}"`);
  }

  say('Reading load, per screen');
  for (const [label, path] of [
    ['the attention list', '/'],
    ['your business', '/settings/products'],
    ['settings', '/settings'],
    ['connections', '/settings/connections'],
  ] as const) {
    await page.goto(path);
    await page.waitForLoadState('networkidle').catch(() => undefined);
    await page.waitForTimeout(PACE);
    await density(page, label);
  }

  await page.goto('/');
  await page.locator('main a[href^="/accounts/"]').first().click();
  await page.waitForTimeout(3500);
  await density(page, 'an account brief');

  say('What a customer can reach from the shell');
  const nav = await page.evaluate(() =>
    [...document.querySelectorAll('nav a')].map(
      (a) => `${a.textContent?.trim()} → ${a.getAttribute('href')}`,
    ),
  );
  process.stdout.write(nav.map((n) => `    · ${n}`).join('\n') + '\n');

  await page.waitForTimeout(3000);
  await browser.close();
}

main().catch((error: unknown) => {
  process.stderr.write(`\nthe walk stopped: ${String(error)}\n`);
  process.exitCode = 1;
});
