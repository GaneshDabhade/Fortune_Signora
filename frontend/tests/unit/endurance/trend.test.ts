/**
 * The endurance judgement, tested without a browser and without an hour.
 *
 * **This is the reason the harness is split in two.** Every case below is a
 * degradation somebody would want caught, and each is expressed as eight
 * numbers rather than as a session that has to actually leak. Verifying this
 * arithmetic by running a real long session would be the most expensive way
 * ever devised to check a division — and it could only ever test the case the
 * product happens to exhibit today.
 *
 * The synthetic series here are the failures the recorder has **not** seen yet,
 * which is exactly the set a real run cannot cover.
 */

import { describe, expect, it } from 'vitest';

import { judge, LIMITS, MINIMUM_CYCLES, summarise, type Sample } from '../../endurance/trend';

/** Twelve minutes a cycle, so ten cycles put exactly one hour between the two
 * halves' midpoints and every rate below reads directly as its per-hour limit. */
const CYCLE_MS = 12 * 60_000;

function sample(cycle: number, over: Partial<Sample> = {}): Sample {
  return {
    cycle,
    elapsedMs: cycle * CYCLE_MS,
    heapBytes: 40_000_000,
    nodes: 2_000,
    listeners: 400,
    documents: 1,
    requests: cycle * 20,
    tokenMints: cycle * 7,
    dataReads: cycle * 7,
    consoleErrors: 0,
    unintended: 0,
    rendered: true,
    firstContentMs: 2_400,
    ...over,
  };
}

/** A healthy session: identical cycles, nothing accumulating. */
function healthy(count = 10): Sample[] {
  return Array.from({ length: count }, (_, index) => sample(index + 1));
}

/** A quantity that climbs steadily, the shape every leak has. */
function climbing(count: number, key: keyof Sample, from: number, per: number): Sample[] {
  return Array.from({ length: count }, (_, index) =>
    sample(index + 1, { [key]: from + per * index } as Partial<Sample>),
  );
}

function verdict(samples: readonly Sample[], name: string) {
  const found = judge(samples).find((entry) => entry.name.includes(name));
  if (!found) throw new Error(`no verdict matching "${name}"`);
  return found;
}

describe('a series too short to judge', () => {
  it('refuses to report a trend rather than computing one from two numbers', () => {
    const only = judge(healthy(MINIMUM_CYCLES - 1));
    expect(only).toHaveLength(1);
    expect(only.at(0)?.passed).toBe(false);
    // The wording matters: the run was short, the product was not judged.
    expect(only.at(0)?.detail).toContain('are needed before a trend');
  });

  it('judges the full set the moment there is enough to divide', () => {
    expect(judge(healthy(MINIMUM_CYCLES)).length).toBeGreaterThan(1);
  });

  it('refuses when the cycles are numerous but crammed into a few minutes', () => {
    // Twenty cycles, four seconds apart. Plenty of samples, no elapsed time —
    // dividing by that span turns sampling noise into a confident-looking rate.
    const rushed = Array.from({ length: 20 }, (_, index) =>
      sample(index + 1, { elapsedMs: (index + 1) * 4_000 }),
    );
    const only = judge(rushed);
    expect(only).toHaveLength(1);
    expect(only.at(0)?.detail).toContain('a guess wearing a number');
  });
});

describe('a healthy session', () => {
  it('passes every check', () => {
    for (const entry of judge(healthy())) {
      expect(entry.passed, `${entry.name} — ${entry.detail}`).toBe(true);
    }
  });
});

describe('the leaks it exists to catch', () => {
  it('catches a heap that keeps climbing', () => {
    // 40MB rising to 130MB — a tab that would not survive an afternoon.
    expect(verdict(climbing(10, 'heapBytes', 40e6, 10e6), 'grow without bound').passed).toBe(
      false,
    );
  });

  it('catches DOM left behind by identical work', () => {
    // The signature of a route that never unmounts.
    expect(verdict(climbing(10, 'nodes', 2_000, 400), 'leaves no DOM behind').passed).toBe(false);
  });

  it('catches listeners that are never released', () => {
    expect(verdict(climbing(10, 'listeners', 400, 60), 'let go of their listeners').passed).toBe(
      false,
    );
  });

  it('catches a product that gets slower as the day goes on', () => {
    expect(
      verdict(climbing(10, 'firstContentMs', 2_000, 600), 'does not get slower').passed,
    ).toBe(false);
  });
});

describe('the failures a memory graph cannot see', () => {
  it('catches a tab that stopped showing data, even with a flat heap', () => {
    const samples = healthy();
    samples[7] = sample(8, { rendered: false });
    const entry = verdict(samples, 'still shows data');
    expect(entry.passed).toBe(false);
    // Naming the cycle is the difference between a finding and an alarm.
    expect(entry.detail).toContain('#8');
  });

  it('catches authentication minting a token per request', () => {
    const samples = healthy().map((entry) =>
      sample(entry.cycle, { tokenMints: entry.cycle * 20, dataReads: entry.cycle * 7 }),
    );
    expect(verdict(samples, 'does not run away').passed).toBe(false);
  });

  it('catches an uncaught exception, which is never intentional', () => {
    const samples = healthy();
    samples[samples.length - 1] = sample(10, { unintended: 2, consoleErrors: 2 });
    const entry = verdict(samples, 'nothing unintended');
    expect(entry.passed).toBe(false);
    expect(entry.detail).toContain('2 uncaught exception(s) or server error(s)');
  });

  it('does not fail a session for the product deliberately answering 404', () => {
    // **The correction the first real run forced.** 107 console errors turned
    // out to be two deliberate 404s per brief — `/narration` and `/research`
    // answer *"nobody has ever asked"* with the same 404 an account you may
    // not see gives, so it cannot be enumerated. The backend is right, and a
    // check that fails every healthy session is a check nobody keeps.
    const samples = healthy().map((entry) =>
      sample(entry.cycle, { consoleErrors: entry.cycle * 2, unintended: 0 }),
    );
    const entry = verdict(samples, 'nothing unintended');
    expect(entry.passed).toBe(true);
    // Still reported, so nobody has to rediscover them.
    expect(entry.detail).toContain('console line(s), reported not asserted');
  });
});

describe('the run length must not change the verdict', () => {
  /** **One leak, watched for different lengths of time.** The heap climbs at a
   * fixed 40MB per hour from a 40MB baseline — the same physical defect — and
   * `minutes` only changes how long somebody stood and watched it. */
  function leakWatchedFor(minutes: number): Sample[] {
    return Array.from({ length: 10 }, (_, index) => {
      const elapsedMs = (index + 1) * minutes * 60_000;
      return sample(index + 1, {
        elapsedMs,
        heapBytes: 40e6 + (40e6 * elapsedMs) / 3_600_000,
      });
    });
  }

  it('reports one leak identically whether it was watched for half an hour or five', () => {
    // **This case caught two wrong models in a row.** A plain ratio measures
    // the leak *and* the length of the run. A ratio normalised per hour still
    // does, more subtly: a linear leak raises the baseline it is divided by, so
    // its fractional rate falls the longer you watch. Only an absolute rate
    // answers the same question after ten minutes and after five hours — which
    // matters because short runs are the ones anybody will actually do.
    const brief = verdict(leakWatchedFor(6), 'grow without bound');
    const long = verdict(leakWatchedFor(30), 'grow without bound');

    expect(brief.passed).toBe(false);
    expect(long.passed).toBe(false);
    // Not merely both failing — both reporting the same number, because it is
    // the same leak. This is the property the whole normalisation exists for.
    expect(brief.detail).toContain('+40.0MB/hour');
    expect(long.detail).toContain('+40.0MB/hour');
  });

  it('does not fail a slow drift merely because somebody watched it all day', () => {
    // 4MB per hour on a 40MB baseline is a tab that ends an eight-hour day
    // 32MB heavier. That is a product working, and an eight-hour run must not
    // punish it for having been observed for eight hours.
    const drift = Array.from({ length: 10 }, (_, index) => {
      const elapsedMs = (index + 1) * 48 * 60_000;
      return sample(index + 1, {
        elapsedMs,
        heapBytes: 40e6 + (4e6 * elapsedMs) / 3_600_000,
      });
    });
    expect(verdict(drift, 'grow without bound').passed).toBe(true);
  });
});

describe('a stall is not a slowdown, and the first real run proved it', () => {
  /** Eighty-one cycles at 1.5 seconds and one at 1301 — exactly what the first
   * 43-minute session produced. */
  function steadyThenFrozen(): Sample[] {
    const samples = healthy(12).map((entry) => sample(entry.cycle, { firstContentMs: 1_500 }));
    samples[samples.length - 1] = sample(12, { firstContentMs: 1_301_000 });
    return samples;
  }

  it('does not call a product that froze once "gradually getting slower"', () => {
    // **The mean is destroyed by one outlier.** The original check reported
    // +168801ms/hour on a product that had been steady at 1.5s for eighty-one
    // consecutive cycles — a false description, and the sort of false
    // description that gets a check switched off.
    const entry = verdict(steadyThenFrozen(), 'does not get slower');
    expect(entry.passed).toBe(true);
    expect(entry.detail).toContain('typically 1.5s');
  });

  it('reports the freeze as its own finding, naming the cycle and the duration', () => {
    const entry = verdict(steadyThenFrozen(), 'never simply stops');
    expect(entry.passed).toBe(false);
    expect(entry.detail).toContain('#12');
    expect(entry.detail).toContain('1301s');
  });

  it('still catches a genuine gradual slowdown, with no stall anywhere', () => {
    const creeping = healthy(10).map((entry, index) =>
      sample(entry.cycle, { firstContentMs: 2_000 + 600 * index }),
    );
    expect(verdict(creeping, 'does not get slower').passed).toBe(false);
    expect(verdict(creeping, 'never simply stops').passed).toBe(true);
  });
});

describe('the arithmetic itself', () => {
  it('is unmoved by a cold start, which is why halves are compared', () => {
    // A first cycle four times heavier than the rest — cold bundle, cold cache.
    // A slope over the whole series would call this a leak; halving does not.
    const samples = healthy();
    samples[0] = sample(1, { heapBytes: 160_000_000 });
    expect(verdict(samples, 'grow without bound').passed).toBe(true);
  });

  it('reports growth from zero as an ordinary number, with no infinity to special-case', () => {
    // A baseline of zero is a division by zero under any ratio model, and every
    // ratio model therefore needs a branch for it. A subtraction has no
    // denominator, so this one does not — and a branch that never has to exist
    // cannot be wrong.
    const samples = healthy().map((entry) =>
      sample(entry.cycle, { listeners: entry.cycle <= 5 ? 0 : 400 }),
    );
    const entry = verdict(samples, 'let go of their listeners');
    expect(entry.passed).toBe(false);
    expect(entry.detail).toContain('+400/hour');
  });

  it('treats a quantity that was zero and stayed zero as flat, not as a failure', () => {
    const samples = healthy().map((entry) => sample(entry.cycle, { listeners: 0 }));
    expect(verdict(samples, 'let go of their listeners').passed).toBe(true);
  });

  it('holds a limit at exactly its boundary rather than just inside it', () => {
    // A check that fails *at* its stated limit makes the documented number a
    // lie by one. `CYCLE_MS` puts exactly an hour between the halves, so a
    // second half `nodesPerHour` above the first sits precisely on it.
    const atLimit = healthy(10).map((entry, index) =>
      sample(entry.cycle, { nodes: index < 5 ? 2_000 : 2_000 + LIMITS.nodesPerHour }),
    );
    expect(verdict(atLimit, 'leaves no DOM behind').passed).toBe(true);
  });

  it('does not call a settling heap a leak', () => {
    // Memory that *falls* after the caches warm is the healthiest shape there
    // is, and a check that reported it would be switched off by lunchtime.
    const settling = healthy(10).map((entry, index) =>
      sample(entry.cycle, { heapBytes: 80e6 - 2e6 * index }),
    );
    const entry = verdict(settling, 'grow without bound');
    expect(entry.passed).toBe(true);
    expect(entry.detail).toContain('-');
  });
});

describe('the summary a person reads', () => {
  it('leads with the outcome and the duration', () => {
    const samples = healthy();
    expect(summarise(samples, judge(samples))).toContain('held up');
  });

  it('says how many checks failed rather than only that something did', () => {
    const samples = climbing(10, 'nodes', 2_000, 400);
    expect(summarise(samples, judge(samples))).toMatch(/degraded: \d+ of \d+ checks failed/);
  });
});
