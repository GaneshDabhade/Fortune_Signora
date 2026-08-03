/**
 * **The review instrument. Not a test, and deliberately not one.**
 *
 *     make review-product          watch it, and read what it reports
 *
 * ## Why this exists at all
 *
 * The product owner's direction (2026-08-03) is to stop writing assertions and
 * start behaving like a demanding customer on day one of a trial. **A person
 * doing that needs eyes.** This session has none, so this walks the product at
 * human pace in a **headed** browser — which the product owner watches — and
 * reads every screen back as text, which is what this session judges.
 *
 * **It asserts nothing and can never fail.** A review that could fail would
 * start being maintained like a test, and the next person would tune it green
 * instead of reading it. The only output is *what a customer would see*.
 *
 * ## What it deliberately does not do
 *
 * It does not seed, does not write, does not clean up. It is a pair of eyes.
 * Anything it finds is recorded by a human judgement afterwards, categorised by
 * what it would cost a purchase decision — never by how hard it is to fix.
 */

import { chromium, type Page } from '@playwright/test';

import { browserEnvironment, resolveAppUrl } from '../e2e/fixtures/environment';
import { OWNER, PASSWORD } from '../e2e/fixtures/personas';

/** Slow enough that a person can follow what is happening on screen. */
const PACE = Number(process.env.PACE ?? 900);

function say(heading: string, body?: string): void {
  process.stdout.write(`\n${'─'.repeat(72)}\n${heading}\n${'─'.repeat(72)}\n`);
  if (body) process.stdout.write(`${body}\n`);
}

/** Everything a customer can read and do on the screen right now. */
async function screen(page: Page, label: string): Promise<void> {
  await page.waitForLoadState('networkidle').catch(() => undefined);
  await page.waitForTimeout(PACE);

  const seen = await page.evaluate(() => {
    const main = document.querySelector('main') ?? document.body;
    const text = (main.innerText ?? '').split('\n').map((l) => l.trim()).filter(Boolean);
    const controls = [...main.querySelectorAll('button, a[href], input, select, textarea')].map(
      (el) => {
        const name =
          el.getAttribute('aria-label') ??
          (el as HTMLInputElement).placeholder ??
          el.textContent?.trim() ??
          '';
        const disabled = (el as HTMLButtonElement).disabled ? ' (disabled)' : '';
        return `${el.tagName.toLowerCase()}: ${name.slice(0, 48)}${disabled}`;
      },
    );
    return {
      title: document.title,
      headings: [...main.querySelectorAll('h1,h2,h3')].map(
        (h) => `${h.tagName} ${h.textContent?.trim()}`,
      ),
      text: text.slice(0, 60),
      controls: [...new Set(controls)].slice(0, 25),
    };
  });

  say(`${label}   ${page.url()}`);
  process.stdout.write(`  tab title: ${seen.title}\n`);
  process.stdout.write(`  headings:  ${seen.headings.join(' · ') || '(none)'}\n\n`);
  process.stdout.write(seen.text.map((l) => `  │ ${l}`).join('\n'));
  process.stdout.write(`\n\n  what a customer can do here:\n`);
  process.stdout.write(seen.controls.map((c) => `    · ${c}`).join('\n') + '\n');
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

  say('A trial, day one', `Nobody is explaining this product. ${baseURL}`);

  await page.goto('/');
  await screen(page, '1 · What a stranger sees at the front door');

  await page.getByLabel('Email').fill(OWNER.email);
  await page.getByLabel('Password').fill(PASSWORD);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.waitForURL((url) => url.pathname === '/', { timeout: 30_000 });
  await screen(page, '2 · The first screen after signing in');

  const first = page.locator('main a[href^="/accounts/"]').first();
  if (await first.count()) {
    await first.click();
    await screen(page, '3 · An account, opened because the product said it mattered');

    const citation = page.locator('main button').filter({ hasText: /·/ }).first();
    if (await citation.count()) {
      await citation.click();
      await page.waitForTimeout(1500);
      const dialog = await page
        .getByRole('dialog')
        .innerText()
        .catch(() => '(no dialog)');
      say('3a · "Prove it" — the evidence behind one line', dialog);
      await page.keyboard.press('Escape');
    }
  }

  for (const [label, path] of [
    ['4 · Settings — what a new customer must configure', '/settings'],
    ['5 · Your business — what the product needs to know first', '/settings/products'],
    ['6 · Connections — where the data is supposed to come from', '/settings/connections'],
  ] as const) {
    await page.goto(path);
    await screen(page, label);
  }

  say('End of the walk', 'The browser stays open for a moment.');
  await page.waitForTimeout(4000);
  await browser.close();
}

main().catch((error: unknown) => {
  process.stderr.write(`\nthe walk stopped: ${String(error)}\n`);
  process.exitCode = 1;
});
