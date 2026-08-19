/**
 * **A working day in one tab.** The endurance recorder.
 *
 *     make endurance                 twenty minutes, the default
 *     make endurance MINUTES=180     an afternoon
 *     make endurance MINUTES=480 HEADED=1   a day, watchable
 *
 * ## Why this is not a Playwright test
 *
 * The design study is in [`480-end-to-end-product-validation.md`](../../../docs/architecture/480-end-to-end-product-validation.md)
 * §6h; the conclusion is short enough to restate. **Playwright's failure model
 * is "stop at the first failed assertion", which is exactly right for a
 * deterministic journey and exactly wrong for endurance**, where the first
 * symptom is the least interesting part of the curve and stopping there
 * discards the observation that would have explained it. An eight-hour test
 * also occupies a worker for eight hours, produces a trace no tool will open,
 * and reports nothing at all until it ends.
 *
 * So the long-running half **observes** and never asserts, and the judgement is
 * pure arithmetic in [`trend.ts`](./trend.ts) with ordinary unit tests behind
 * it. Nothing here is a parallel test harness: the browser is driven with the
 * Playwright *library*, and the page objects, personas and environment guard
 * are the suite's own, unchanged.
 *
 * ## What it does
 *
 * One tab, opened once, signed in once, then the same cycle of a seller's work
 * over and over — the list, a brief, a citation, the product catalog, settings,
 * back to the list, and a pause. **The cycle is identical every time on
 * purpose**: growth across identical work is a leak, and growth across
 * different work is just different work.
 *
 * ## What it is not allowed to do
 *
 * It signs in through the form, reads through the API, and touches no database.
 * `resolveAppUrl()` refuses to point it at Human Review, as it does for the
 * suite — and this is the process that matters most, because it holds a tab
 * open for hours.
 */

import { chromium, type CDPSession, type Page } from '@playwright/test';
import { appendFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';

import { browserEnvironment, resolveAppUrl } from '../e2e/fixtures/environment';
import { honourTheRateLimiter } from '../e2e/fixtures/rate-limit';
import { OWNER } from '../e2e/fixtures/personas';
import { AccountsPage } from '../e2e/pages/accounts';
import { BriefPage } from '../e2e/pages/brief';
import { SignInPage } from '../e2e/pages/signin';
import { judge, summarise, type Sample } from './trend';

/** Where the session's record lands. One file per run, and the newest is what
 * a person reads. Not committed: it is an observation of one machine on one
 * afternoon, and `CLAUDE.md` §2 is clear that a record of the past is dated
 * rather than kept current. */
const RECORD_DIR = join(process.cwd(), 'test-results', 'endurance');

const MINUTES = Number(process.env.MINUTES ?? 20);
/** Long enough that a cycle resembles a person working rather than a load test,
 * short enough that twenty minutes still yields a judgeable series. */
const IDLE_MS = Number(process.env.IDLE_MS ?? 8_000);

interface Counters {
  requests: number;
  tokenMints: number;
  dataReads: number;
  consoleErrors: number;
  /** Uncaught exceptions and 5xx responses. **Never intentional**, which is
   * why this and not `consoleErrors` decides whether a session passed. */
  unintended: number;
}

/**
 * Chromium's own metrics, which is why this is a Chromium-only harness and
 * unapologetically so. `Nodes` and `JSEventListeners` are not available through
 * any cross-browser API, and they are the two numbers that make a leak
 * undeniable. A memory graph without them is a graph people argue about.
 */
async function metrics(cdp: CDPSession): Promise<Record<string, number>> {
  // Collect first: retained-because-uncollected is not a leak, and a series
  // that does not force a collection slopes upward on every healthy run.
  await cdp.send('HeapProfiler.collectGarbage');
  const { metrics: entries } = await cdp.send('Performance.getMetrics');
  return Object.fromEntries(entries.map((entry) => [entry.name, entry.value]));
}

interface CycleResult {
  readonly rendered: boolean;
  /** **From asking for the list to being able to click a row** — and nothing
   * else. An earlier version reported the whole cycle's duration under this
   * name, which was a slowdown signal wearing the label of a customer-perceived
   * one. This is the number a seller feels. */
  readonly firstContentMs: number;
}

/** One cycle of a seller's work. Identical every time — that is the point. */
async function cycle(
  page: Page,
  accounts: AccountsPage,
  brief: BriefPage,
): Promise<CycleResult> {
  const asked = Date.now();
  await accounts.open();

  let rendered = false;
  try {
    await accounts.accountLinks.first().waitFor({ state: 'visible', timeout: 30_000 });
    rendered = (await accounts.accountLinks.count()) > 0;
  } catch {
    // **Recorded, never thrown.** A cycle that failed to render is the single
    // most valuable observation this harness can make, and throwing here would
    // end the session at the exact moment it became interesting.
    rendered = false;
  }
  const firstContentMs = Date.now() - asked;

  if (rendered) {
    await accounts.openFirstAccount();
    await brief.waitForScore().catch(() => undefined);
    await brief.openFirstCitation().catch(() => undefined);
    await page.keyboard.press('Escape');
    await page.goto('/settings/products');
    await page.waitForLoadState('networkidle').catch(() => undefined);
    await page.goto('/settings');
    await page.waitForLoadState('networkidle').catch(() => undefined);
    // **Back to the list before idling, and the sample is taken here.** The
    // first version ended each cycle on Settings, so every measurement
    // described the emptiest screen in the product — 334 DOM nodes, and a
    // reassuring flat line that said nothing about the screen a seller
    // actually leaves open.
    await accounts.open();
    await accounts.accountLinks.first().waitFor({ state: 'visible', timeout: 30_000 })
      .catch(() => undefined);
  }

  // The tab sits open, which is where a polling leak shows itself and where a
  // real seller spends most of their day.
  await page.waitForTimeout(IDLE_MS);
  return { rendered, firstContentMs };
}

async function main(): Promise<void> {
  const baseURL = resolveAppUrl();
  const startedAt = new Date();
  const recordPath = join(
    RECORD_DIR,
    `${startedAt.toISOString().replace(/[:.]/g, '-')}.jsonl`,
  );
  mkdirSync(dirname(recordPath), { recursive: true });

  process.stdout.write(
    `\n  A working day in one tab — ${MINUTES} minutes against ${baseURL}\n` +
      `  signed in as ${OWNER.name}, ${OWNER.persona}\n` +
      `  recording to ${recordPath}\n\n`,
  );

  // **`channel: 'chromium'` is load-bearing, not decoration.** A bare
  // `launch({ headless: true })` starts `chrome-headless-shell`, a separate
  // binary with its own system-library needs — and it does not start at all
  // here, while the full build the suite has always used starts fine. Asking
  // for the same browser the rest of the suite drives is also the honest
  // choice: an endurance measurement taken against a different binary is a
  // measurement of a browser no customer has.
  const browser = await chromium.launch({
    channel: 'chromium',
    headless: process.env.HEADED !== '1',
    env: browserEnvironment(),
  });
  const context = await browser.newContext({ baseURL, viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();

  const counters: Counters = {
    requests: 0,
    tokenMints: 0,
    dataReads: 0,
    consoleErrors: 0,
    unintended: 0,
  };
  page.on('request', (request) => {
    counters.requests += 1;
    const path = new URL(request.url()).pathname;
    if (path === '/api/token') counters.tokenMints += 1;
    if (path.startsWith('/api/proxy/')) counters.dataReads += 1;
  });
  // **The text, not only the count.** A record saying *"165 console errors"*
  // tells the next reader that something is wrong and nothing about what —
  // and these turned out to arrive at a steady two per cycle from the very
  // first one, which is a fact about the product that no count could carry.
  // Distinct messages only: the same line 82 times is one finding.
  const messages = new Map<string, number>();
  const note = (text: string) => {
    counters.consoleErrors += 1;
    messages.set(text, (messages.get(text) ?? 0) + 1);
  };
  page.on('console', (message) => {
    if (message.type() === 'error') note(message.text().slice(0, 200));
  });
  page.on('pageerror', (error) => {
    counters.unintended += 1;
    note(`uncaught: ${String(error).slice(0, 200)}`);
  });
  // **The browser's own console does not say *what* failed.** `Failed to load
  // resource: … 404` is the whole message, so 107 of them across 53 cycles
  // named nothing at all. The response is where the path lives, and the path
  // is the entire finding.
  page.on('response', (response) => {
    if (response.status() < 400) return;
    if (response.status() >= 500) counters.unintended += 1;
    const path = new URL(response.url()).pathname;
    const line = `↳ ${response.status()} ${response.request().method()} ${path}`;
    // Counted separately from `note()`: a failed response is the *explanation*
    // of a console error, not a second error to add to the total.
    messages.set(line, (messages.get(line) ?? 0) + 1);
  });

  const cdp = await context.newCDPSession(page);
  await cdp.send('Performance.enable');

  const accounts = new AccountsPage(page);
  const brief = new BriefPage(page);
  // 🔴 **[C-109](../../../docs/LANE_COORDINATION.md)** — this harness drives
  // the Playwright *library* rather than the runner, so it gets none of the
  // suite's fixtures and installs the interceptor itself.
  await honourTheRateLimiter(page);
  await new SignInPage(page).signIn(OWNER);

  const samples: Sample[] = [];
  const deadline = Date.now() + MINUTES * 60_000;
  const began = Date.now();

  for (let index = 1; Date.now() < deadline; index += 1) {
    const { rendered, firstContentMs } = await cycle(page, accounts, brief);
    const observed = await metrics(cdp);

    const sample: Sample = {
      cycle: index,
      elapsedMs: Date.now() - began,
      heapBytes: observed.JSHeapUsedSize ?? 0,
      nodes: observed.Nodes ?? 0,
      listeners: observed.JSEventListeners ?? 0,
      documents: observed.Documents ?? 0,
      requests: counters.requests,
      tokenMints: counters.tokenMints,
      dataReads: counters.dataReads,
      consoleErrors: counters.consoleErrors,
      unintended: counters.unintended,
      rendered,
      firstContentMs,
    };
    samples.push(sample);

    // **Appended as it goes, never held in memory to the end.** A session that
    // is killed at hour six must still have recorded hours one to five — the
    // observation is the deliverable, and losing it to a crash would make the
    // longest runs the least useful.
    appendFileSync(recordPath, `${JSON.stringify(sample)}\n`);

    process.stdout.write(
      `  cycle ${String(index).padStart(3)}  ` +
        `${(sample.elapsedMs / 60_000).toFixed(1)}m  ` +
        `heap ${(sample.heapBytes / 1e6).toFixed(1)}MB  ` +
        `nodes ${sample.nodes}  listeners ${sample.listeners}  ` +
        `${sample.tokenMints}/${sample.dataReads} tokens/reads  ` +
        `first ${(sample.firstContentMs / 1000).toFixed(1)}s  ` +
        `${rendered ? 'rendered' : '*** EMPTY ***'}\n`,
    );
  }

  await browser.close();

  const verdicts = judge(samples);
  const distinct = [...messages.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([text, count]) => `  ${String(count).padStart(4)}×  ${text}`);
  const report = [
    summarise(samples, verdicts),
    ...(distinct.length ? ['', 'Distinct console errors:', ...distinct] : []),
  ].join('\n');
  process.stdout.write(`\n${report}\n\n`);
  writeFileSync(recordPath.replace(/\.jsonl$/, '.md'), `${report}\n`);

  // The exit code is the judgement, so a scheduled long run is actionable
  // without anybody reading a file. The record survives either way.
  if (verdicts.some((verdict) => !verdict.passed)) process.exitCode = 1;
}

main().catch((error: unknown) => {
  process.stderr.write(`\n  the session ended early: ${String(error)}\n\n`);
  process.exitCode = 1;
});
