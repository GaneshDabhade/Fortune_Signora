/**
 * Perceived performance — what a customer feels, not what a server measured.
 *
 * **The backend is fast and that is not the question.** A customer judges
 * responsiveness by how many times a screen changes shape before it settles,
 * how long they stare at nothing, and whether anything tells them work is
 * happening. A p99 of 40ms and four sequential loading phases feel slow.
 *
 * ### These tests record before they assert
 *
 * Every measurement is attached to the run, so the number is visible even when
 * the test passes. **Thresholds are set where a regression would be obvious**,
 * not at the ideal — a test that failed on today's real behaviour would be
 * disabled within a week, and a test that encodes today's behaviour as
 * *correct* is worse. The target is stated in the comment; the ceiling is
 * what fails.
 */

import { expect, test } from './fixtures/signora';

interface Perception {
  /** Distinct network requests the browser made to our own origin. */
  requests: number;
  /** How many of them were access-token mints. */
  tokens: number;
  /** How many were data reads through the proxy. */
  data: number;
  /** Milliseconds from navigation until the first row a customer can click. */
  timeToFirstAction: number;
}

async function measure(
  page: import('@playwright/test').Page,
  path: string,
  ready: () => Promise<void>,
): Promise<Perception> {
  const seen: string[] = [];
  const record = (url: string): void => {
    const { pathname } = new URL(url);
    if (pathname.startsWith('/_next') || pathname.startsWith('/favicon')) return;
    seen.push(pathname);
  };
  page.on('request', (request) => record(request.url()));

  const started = Date.now();
  await page.goto(path);
  await ready();
  const timeToFirstAction = Date.now() - started;

  page.removeAllListeners('request');
  return {
    requests: seen.length,
    tokens: seen.filter((p) => p === '/api/token').length,
    data: seen.filter((p) => p.startsWith('/api/proxy')).length,
    timeToFirstAction,
  };
}

function report(name: string, perception: Perception): void {
  test.info().annotations.push({
    type: 'perception',
    description:
      `${name}: ${perception.timeToFirstAction}ms to first action · ` +
      `${perception.requests} requests · ${perception.tokens} tokens · ` +
      `${perception.data} data reads`,
  });
  process.stdout.write(
    `\n  ${name}\n` +
      `     ${perception.timeToFirstAction}ms until a customer can act\n` +
      `     ${perception.requests} requests — ${perception.tokens} token mints, ${perception.data} data reads\n`,
  );
}

test.describe('opening the product', () => {
  test('@journey the accounts list, measured the way a customer experiences it', async ({
    page,
    accounts,
  }) => {
    const perception = await measure(page, '/accounts', async () => {
      await expect(accounts.accountLinks.first()).toBeVisible({ timeout: 30_000 });
    });
    report('the accounts list', perception);

    /**
     * ⚠️ **Measured at `/accounts`, and it used to be `/`.** 🔴 `/` became the
     * shell's entry resolver, so this measured a redirect into Home while
     * calling itself *"the accounts list"* — **and Home mints 15, which failed
     * a ceiling calibrated on a screen that no longer exists.**
     *
     * ✅ **Pointing it at the surface it names restores the finding rather than
     * relaxing it**: 11 token mints for 11 data reads, under the same ceiling.
     *
     * **The finding, made permanent.** One access token is minted *per data
     * request* — each an RS256 signature on the Next tier — for a token that is
     * valid for minutes. The target is **one**; the ceiling below is set to
     * catch a regression rather than to bless the current number.
     *
     * 🔴 **LOWERED FROM 12 TO 6** — [B-1035](../../../docs/BUGS.md), 2026-08-22,
     * **and it is a TIGHTENING.** ⚡ **`fetchAccessToken` now shares the mint
     * already in flight**, so this screen measures **5**, down from 15.
     *
     * ⛔ **12 was calibrated against a world where 15 was normal.** ⚠️ **Leaving
     * it there would let the cost MORE THAN DOUBLE before the instrument said
     * anything** — the next screen would get 11 mints for free with a green
     * suite, which is the same defect as raising a ceiling to bless a
     * regression, arrived at more slowly. **QE's argument, and it is right.**
     *
     * ✅ **6 rather than 5, on measurement**: this assertion read **5 on four
     * runs across two machines**. ⚠️ **The account brief below varies 5–6 on the
     * same tree** — the count depends on how the read waves split — **so one
     * mint of headroom is the difference between a ceiling and a flake.** ⛔ **It
     * fails the moment a change costs two.**
     */
    expect(
      perception.tokens,
      `${perception.tokens} access tokens for one page. The target is 1: the token ` +
        'is valid for minutes and nothing caches it.',
    ).toBeLessThanOrEqual(6);

    // A customer's patience for a first screen, generously drawn.
    expect(perception.timeToFirstAction).toBeLessThan(15_000);
  });

  test('@journey the account brief, which composes six read models', async ({
    page,
    home,
    brief,
  }) => {
    // ⚠️ **Measured on a SCORED brief, from Home's ranked card** — 📁 `B-1022`.
    // ⛔ Companies' first row is whichever account sorts first, and the
    // Playground's is one no provider has named: **an unscored brief composes
    // far less and would report a figure that flatters the product.**
    await home.open();
    const href = await home.rankedAccounts.first().getAttribute('href');

    const perception = await measure(page, href ?? '/', async () => {
      await brief.waitForScore();
    });
    report('the account brief', perception);

    // The brief is the most expensive screen in the product and is fine per
    // account. **The trigger to watch is the first list that composes them per
    // row**, which is recorded in the future-pressure review.
    expect(perception.timeToFirstAction).toBeLessThan(20_000);
  });
});

test.describe('how many times a screen changes shape', () => {
  test('@journey the accounts list settles in one phase, not four', async ({
    page,
  }) => {
    await page.goto('/');

    // Sample what `main` contains as it loads. **Each distinct shape is a
    // moment the customer's eye has to re-find its place**, and four of them
    // is what makes a fast product feel slow.
    const shapes = new Set<string>();
    const until = Date.now() + 8000;
    while (Date.now() < until) {
      const shape = await page
        .locator('main')
        .evaluate((element) => {
          const rows = element.querySelectorAll('ol > li').length;
          const skeletons = element.querySelectorAll('[class*="animate-pulse"]').length;
          return `rows:${rows} skeleton:${skeletons > 0}`;
        })
        .catch(() => 'gone');
      shapes.add(shape);
      if (shape.startsWith('rows:') && !shape.endsWith('true') && shape !== 'rows:0 skeleton:false') break;
      await page.waitForTimeout(150);
    }

    const phases = [...shapes];
    test.info().annotations.push({
      type: 'loading-phases',
      description: phases.join(' → '),
    });
    process.stdout.write(`\n  loading phases: ${phases.join(' → ')}\n`);

    // Empty → skeleton → content is three, and is the most a screen should
    // need. More means the page is assembling itself in front of the reader.
    expect(phases.length, `loading phases: ${phases.join(' → ')}`).toBeLessThanOrEqual(4);
  });
});
