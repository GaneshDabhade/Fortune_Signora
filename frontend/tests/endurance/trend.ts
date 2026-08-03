/**
 * **What a long session is allowed to do to a browser tab.**
 *
 * A long-session run produces a *series*, not a result. That distinction is the
 * whole architecture: a regression test asks *"did this work?"* and stops at the
 * first no; endurance asks *"is this getting worse?"*, which cannot be answered
 * by a single observation and must not stop at the first one.
 *
 * So the recorder observes and this judges, and the two are separated because
 * **the judgement is pure arithmetic over numbers and deserves ordinary unit
 * tests**, while the observation needs a browser and an hour. Testing the
 * arithmetic by running an hour-long browser session would be the most
 * expensive way ever devised to check a division.
 *
 * ## Why growth is measured between halves rather than as a slope
 *
 * The first cycles of any session are unrepresentative: caches are cold, the
 * bundle is still arriving, and V8 has not settled. A least-squares slope over
 * the whole series is dominated by that warm-up and reports a leak in a healthy
 * tab. **Comparing the second half against the first** asks the question a
 * customer would — *"is the tab worse after lunch than it was before?"* — and
 * is unmoved by how the morning started.
 *
 * ## Why every growth limit is **absolute, per hour**
 *
 * This took two corrections, both made by the unit tests rather than by
 * reasoning, and both worth recording because the wrong answers were the
 * plausible ones.
 *
 * **A plain ratio of second half to first was wrong**, because it measures the
 * leak *and the length of the run*: the identical defect passed at twenty
 * minutes and failed at three hours. That makes short runs quietly reassuring,
 * and short runs are the ones anybody will actually do.
 *
 * **A ratio normalised per hour was also wrong**, less obviously. A linear leak
 * raises the baseline it is divided by, so its *fractional* rate falls as the
 * run gets longer — the same 40MB/hour reads as +87%/hour over ten minutes and
 * +40%/hour over five. Better, and still duration-dependent.
 *
 * **Absolute growth per hour is invariant**, which is the whole requirement: a
 * tab gaining 100MB an hour is dead by the afternoon whether it started at
 * 40MB or 400MB, and a ten-minute look and an eight-hour look report the same
 * number for it. It is also the unit an engineer can act on without converting
 * anything.
 *
 * One honest refusal remains: below `MINIMUM_SPAN_MS` between the midpoints the
 * denominator is small enough that ordinary noise dominates, so the answer is
 * *"too short to say"* rather than a confident number.
 *
 * ## Why a garbage collection is forced before every sample
 *
 * Heap that a collection would reclaim is not a leak; it is a heap that has not
 * been collected. Without forcing one, every series slopes upward and every run
 * reports a leak, which is the fastest way to make a signal worthless.
 * `Node` and `JSEventListener` counts do not need it and are the stronger
 * signal anyway — **a DOM that grows across identical cycles is a leak with no
 * innocent explanation.**
 */

/** One observation, taken at the end of one identical cycle of work. */
export interface Sample {
  /** Which cycle produced it. 1-based; cycle 0 is never sampled, because it
   * includes the sign-in and the cold bundle and resembles nothing after it. */
  readonly cycle: number;
  /** Milliseconds since the session began. */
  readonly elapsedMs: number;
  /** After a forced collection. Bytes. */
  readonly heapBytes: number;
  /** Live DOM nodes across every document. The clearest leak signal there is. */
  readonly nodes: number;
  /** Registered event listeners. Grows when a component unmounts badly. */
  readonly listeners: number;
  /** Documents held alive. A detached one is a leaked iframe or a stale route. */
  readonly documents: number;
  /** Every request the tab has issued since it opened. */
  readonly requests: number;
  /** Of those, requests for an access token. */
  readonly tokenMints: number;
  /** Of those, reads of business data through the proxy. */
  readonly dataReads: number;
  /** `console.error` lines since the tab opened, including the browser's own
   * *"failed to load resource"* for every non-2xx response. **Reported, never
   * asserted on** — see `judge`. */
  readonly consoleErrors: number;
  /** Uncaught exceptions, and responses of 500 or worse. **Never intentional**,
   * which is what makes this the one worth failing a session over. */
  readonly unintended: number;
  /** Whether the attention list still rendered rows this cycle. **The
   * staleness question**: a tab that has stopped showing data is the failure a
   * customer actually reports, and it is invisible to a memory graph. */
  readonly rendered: boolean;
  /** How long this cycle's first meaningful content took, in ms. */
  readonly firstContentMs: number;
}

export interface Verdict {
  readonly name: string;
  readonly passed: boolean;
  /** What was measured, in a sentence a person can act on. */
  readonly detail: string;
}

/**
 * **Thresholds, and why each is where it is.**
 *
 * Every one is deliberately generous. A threshold tuned tight enough to catch a
 * subtle leak also fires on a healthy session, and a check that fires on
 * healthy sessions is switched off within a week. These are set to catch
 * *unbounded* growth — the kind that ends a working day — and to stay silent
 * otherwise.
 */
export const LIMITS = {
  /** **Megabytes of live heap gained per hour.** Twenty ends an eight-hour day
   * 160MB heavier, which a laptop absorbs. Caches legitimately fill; this is
   * generous enough not to call that a leak, and bounded, which a leak is not. */
  heapMbPerHour: 20,
  /** **The strict one, deliberately.** Identical cycles that leave more DOM
   * behind have no innocent explanation, so the allowance is small: enough for
   * a list that grew a few rows, nowhere near a route that never unmounts. */
  nodesPerHour: 500,
  /** Listeners are the classic unmount leak, and cheap to count. */
  listenersPerHour: 200,
  /** Half a second added to **typical** first content, per hour. This is the
   * number the customer actually perceives, whatever the memory graph says. */
  slowdownMsPerHour: 500,
  /** **A single cycle that took this long is a stall, not slowness**, and the
   * two are different findings with different causes. Thirty seconds is far
   * beyond any load this product does; the first real run produced one cycle
   * of **1301 seconds**, which a mean-based slowdown check reported as gradual
   * degradation of a product that had been steady at 1.5s for eighty-one
   * cycles. */
  stallMs: 30_000,
  /** **Not a rate.** One access token per data read is the resting state at
   * any moment; above this, something is minting per request rather than per
   * session, and it would be just as wrong in the first minute as the last. */
  tokensPerRead: 1.5,
} as const;

/**
 * **How far apart the two halves must be before a rate means anything.**
 *
 * The rate divides by the gap between the halves' midpoints, so a small gap
 * turns ordinary sampling noise into a large number. Five minutes is the point
 * below which this stops reporting and starts guessing.
 */
export const MINIMUM_SPAN_MS = 5 * 60_000;

function mean(values: readonly number[]): number {
  return values.reduce((total, value) => total + value, 0) / values.length;
}

/**
 * The final sample.
 *
 * `noUncheckedIndexedAccess` types every index as possibly `undefined`, and it
 * is right to: nothing in the type of an array says it has a last element.
 * **Throwing is not a guard against a runtime condition** — `judge` has already
 * returned for any series shorter than `MINIMUM_CYCLES` — it converts a
 * programming error into a loud one rather than letting `undefined` propagate
 * silently into arithmetic and come out as `NaN` in a verdict somebody trusts.
 */
function finalSample(series: readonly Sample[]): Sample {
  const last = series[series.length - 1];
  if (!last) throw new Error('judge() reached the verdicts with an empty series');
  return last;
}

/** The first half and the second half of a series, in that order. */
function halves<T>(series: readonly T[]): readonly [readonly T[], readonly T[]] {
  const middle = Math.floor(series.length / 2);
  return [series.slice(0, middle), series.slice(middle)];
}

/**
 * **The typical value, not the average one.**
 *
 * A mean over `firstContentMs` is destroyed by a single stall: eighty-one
 * cycles at 1.5 seconds and one at 1301 turned into *"the product is getting
 * slower"*, which is a false description of a product that had not changed at
 * all. A median asks the question a customer would — *"what is it usually
 * like?"* — and the outlier gets its own check, because a 22-minute freeze is
 * a finding in its own right rather than a slow afternoon.
 */
function median(values: readonly number[]): number {
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  const lower = sorted[middle - 1];
  const upper = sorted[middle];
  if (upper === undefined) return 0;
  return sorted.length % 2 === 0 && lower !== undefined ? (lower + upper) / 2 : upper;
}

/** Hours between the two halves' midpoints — the denominator of every rate. */
function spanHours(series: readonly Sample[]): number {
  const [first, second] = halves(series);
  return (mean(second.map((s) => s.elapsedMs)) - mean(first.map((s) => s.elapsedMs))) / 3_600_000;
}

/**
 * **How much of a quantity is gained per hour**, in that quantity's own units.
 * `0` is flat, negative means it settled.
 *
 * No special case for a baseline of zero, and none is needed — a subtraction
 * has no denominator, so nothing here can produce an infinity. Growth from
 * nothing is an ordinary number, which is one branch fewer to be wrong in
 * (`CLAUDE.md` §2, a guard that cannot fail is documentation pretending to be
 * code).
 */
function ratePerHour(
  series: readonly Sample[],
  of: (sample: Sample) => number,
  summary: (values: readonly number[]) => number = mean,
): number {
  const [first, second] = halves(series);
  return (summary(second.map(of)) - summary(first.map(of))) / spanHours(series);
}

function perHour(value: number, unit: string): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(value >= 100 || value <= -100 ? 0 : 1)}${unit}/hour`;
}

/**
 * **The minimum series worth judging.** Six cycles gives three per half, which
 * is enough for a mean to mean anything. Below that the honest answer is *"the
 * session was too short"*, and saying so beats reporting a confident verdict
 * computed from two numbers.
 */
export const MINIMUM_CYCLES = 6;

export function judge(samples: readonly Sample[]): readonly Verdict[] {
  if (samples.length < MINIMUM_CYCLES) {
    return [
      {
        name: 'the session was long enough to judge',
        passed: false,
        detail:
          `${samples.length} cycles recorded; ${MINIMUM_CYCLES} are needed before a ` +
          'trend means anything. Run for longer rather than believing this.',
      },
    ];
  }

  const span = spanHours(samples);
  if (span * 3_600_000 < MINIMUM_SPAN_MS) {
    return [
      {
        name: 'the session was long enough to judge',
        passed: false,
        detail:
          `only ${(span * 60).toFixed(1)} minutes separate the two halves of this ` +
          'series; below five, ordinary noise dominates the rate and any verdict ' +
          'would be a guess wearing a number.',
      },
    ];
  }

  const last = finalSample(samples);
  const heap = ratePerHour(samples, (sample) => sample.heapBytes / 1e6);
  const nodes = ratePerHour(samples, (sample) => sample.nodes);
  const listeners = ratePerHour(samples, (sample) => sample.listeners);
  const slowdown = ratePerHour(samples, (sample) => sample.firstContentMs, median);
  const stalls = samples.filter((sample) => sample.firstContentMs > LIMITS.stallMs);
  const tokens = last.dataReads === 0 ? 0 : last.tokenMints / last.dataReads;
  const stale = samples.filter((sample) => !sample.rendered);

  return [
    {
      name: 'the tab does not grow without bound',
      passed: heap <= LIMITS.heapMbPerHour,
      detail:
        `heap ${(last.heapBytes / 1e6).toFixed(0)}MB, ${perHour(heap, 'MB')} ` +
        `(limit ${perHour(LIMITS.heapMbPerHour, 'MB')})`,
    },
    {
      name: 'identical work leaves no DOM behind',
      passed: nodes <= LIMITS.nodesPerHour,
      detail:
        `${last.nodes} live nodes, ${perHour(nodes, '')} ` +
        `(limit ${perHour(LIMITS.nodesPerHour, '')})`,
    },
    {
      name: 'components let go of their listeners',
      passed: listeners <= LIMITS.listenersPerHour,
      detail:
        `${last.listeners} listeners, ${perHour(listeners, '')} ` +
        `(limit ${perHour(LIMITS.listenersPerHour, '')})`,
    },
    {
      name: 'the product still shows data at the end',
      passed: stale.length === 0,
      detail:
        stale.length === 0
          ? `every one of ${samples.length} cycles rendered the list`
          : `the list was empty on ${stale.length} cycle(s): ${stale
              .map((sample) => `#${sample.cycle}`)
              .join(', ')}`,
    },
    {
      name: 'authentication does not run away',
      passed: tokens <= LIMITS.tokensPerRead,
      detail:
        `${last.tokenMints} tokens for ${last.dataReads} reads ` +
        `(${tokens.toFixed(2)} per read, limit ${LIMITS.tokensPerRead})`,
    },
    {
      name: 'the product does not get slower as the day goes on',
      passed: slowdown <= LIMITS.slowdownMsPerHour,
      detail:
        `typically ${(median(samples.map((s) => s.firstContentMs)) / 1000).toFixed(1)}s to ` +
        `first content, ${perHour(slowdown, 'ms')} ` +
        `(limit ${perHour(LIMITS.slowdownMsPerHour, 'ms')})`,
    },
    {
      name: 'the product never simply stops',
      passed: stalls.length === 0,
      detail:
        stalls.length === 0
          ? `no cycle took longer than ${LIMITS.stallMs / 1000}s to show the list`
          : `${stalls.length} cycle(s) stalled: ` +
            stalls
              .map((s) => `#${s.cycle} for ${(s.firstContentMs / 1000).toFixed(0)}s`)
              .join(', '),
    },
    {
      // **Not "the console stayed empty", and the distinction was earned.**
      // The first version failed every session on 107 console errors that
      // turned out to be two deliberate 404s per brief: `/narration` and
      // `/research` answer *"nobody has ever asked"* with **the same 404 an
      // account you may not see gives**, so it cannot be enumerated. The
      // backend is right and the check was wrong — and a check that fires on
      // every healthy session is switched off within a week.
      //
      // **An uncaught exception or a 5xx is never intentional**, which is the
      // principled line rather than a whitelist of paths. The failure this
      // might be thought to hide — B-303's 404 — is caught far more strongly
      // by `rendered`: a browser that cannot reach the API shows no list.
      name: 'nothing unintended happened',
      passed: last.unintended === 0,
      detail:
        (last.unintended === 0
          ? 'no uncaught exceptions and no server errors'
          : `${last.unintended} uncaught exception(s) or server error(s)`) +
        ` · ${last.consoleErrors} console line(s), reported not asserted`,
    },
  ];
}

/** A short human summary, for the end of a run and for a commit message. */
export function summarise(samples: readonly Sample[], verdicts: readonly Verdict[]): string {
  const failed = verdicts.filter((verdict) => !verdict.passed);
  const minutes = samples.length ? (finalSample(samples).elapsedMs / 60_000).toFixed(0) : '0';
  const head =
    failed.length === 0
      ? `A ${minutes}-minute session held up: ${verdicts.length} checks, all passed.`
      : `A ${minutes}-minute session degraded: ${failed.length} of ${verdicts.length} checks failed.`;
  return [head, ...verdicts.map((v) => `  ${v.passed ? '·' : '✗'} ${v.name} — ${v.detail}`)].join(
    '\n',
  );
}
