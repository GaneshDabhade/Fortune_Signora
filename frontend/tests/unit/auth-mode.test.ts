/**
 * **Which authentication mode is running** —
 * [TASK-473](../../../docs/BACKLOG.md), on
 * [ADR-0406](../../../docs/architecture/adr/0406-authentication-execution-modes.md) §2.
 *
 * 🔴 **The row names the shape of these tests and it is not the obvious one:**
 *
 * > 📁 ***"a test asserts the reported value CHANGES with the configuration —
 * > not that it equals today's value. [B-130](../../../docs/BUGS.md)'s lesson:
 * > the test that catches a constant is not one that checks today's number, it
 * > is one that changes the input and requires the output to follow."***
 *
 * ⚡ **So the load-bearing case is `every mode is reachable`** below: it drives
 * three different configurations through one function and demands three
 * different answers. **A `return 'development'` stub passes every
 * equality assertion in this file and fails that one.**
 */
import { afterEach, describe, expect, it, vi } from 'vitest';

import { authMode, environmentName } from '@/lib/auth/config';

/** `SIGNORA_ENVIRONMENT` is read at call time, so each case sets and restores it. */
function withEnvironment<T>(value: string | undefined, run: () => T): T {
  const before = process.env.SIGNORA_ENVIRONMENT;
  if (value === undefined) delete process.env.SIGNORA_ENVIRONMENT;
  else process.env.SIGNORA_ENVIRONMENT = value;
  try {
    return run();
  } finally {
    if (before === undefined) delete process.env.SIGNORA_ENVIRONMENT;
    else process.env.SIGNORA_ENVIRONMENT = before;
  }
}

afterEach(() => {
  vi.unstubAllEnvs();
});

describe('🔴 the reported value changes with the configuration', () => {
  it('⚡ every mode is reachable, and no two configurations agree', () => {
    /**
     * ⛔ **This is the case [B-130](../../../docs/BUGS.md) asks for.** A
     * function that returned a constant would satisfy every other assertion
     * in this file. **Three inputs, three distinct outputs, and the set is
     * checked rather than the members** — so the test says *the output
     * follows the input* rather than *the output is what I typed today*.
     */
    const observed = [
      withEnvironment('local', authMode),
      withEnvironment('demo', authMode),
      withEnvironment('production', authMode),
    ];
    expect(new Set(observed).size).toBe(3);
  });

  it('⛔ and the same configuration twice gives the same answer', () => {
    // Determinism (§2): nothing here may depend on a clock, a cache or an
    // insertion order.
    expect(withEnvironment('demo', authMode)).toBe(withEnvironment('demo', authMode));
  });
});

describe('📁 ADR-0406 §2 names three modes, and these are they', () => {
  it('an unconfigured clone is Development — the backend defaults the same way', () => {
    expect(withEnvironment(undefined, authMode)).toBe('development');
    expect(withEnvironment(undefined, environmentName)).toBe('local');
  });

  it('⚡ `demo` is Demo, and it is read from the registry rather than invented', () => {
    // `demo` is already a row in infra/environments.py — slot 7, its own
    // database and compose project. Recognising it is reading configuration
    // that exists; a new variable meaning the same thing would be §2's
    // second representation.
    expect(withEnvironment('demo', authMode)).toBe('demo');
  });

  it('a deployed environment is Production', () => {
    expect(withEnvironment('production', authMode)).toBe('production');
    expect(withEnvironment('staging', authMode)).toBe('production');
  });

  it('🔴 `demo` is checked BEFORE deployment, and the order is the safe one', () => {
    /**
     * ⛔ **`demo` is not in `isDeployed()`'s three-name allowlist, so a
     * deployment-first ordering would report a seeded demonstration as
     * PRODUCTION** — ⚠️ **which hides the single fact a reviewer needs, and
     * is the failure [C-320](../../../docs/LANE_COORDINATION.md) already
     * measured going unnoticed for three days.**
     */
    expect(withEnvironment('demo', authMode)).not.toBe('production');
  });

  it('`local` and `test` are Development, matching the transport guard', () => {
    // The same two names `isDeployed()` allows. If these ever disagree, the
    // badge and the console-transport guard would describe different
    // repositories.
    expect(withEnvironment('local', authMode)).toBe('development');
    expect(withEnvironment('test', authMode)).toBe('development');
  });

  it('🔴 `development` is not in the vocabulary, so it reports as PRODUCTION', () => {
    /**
     * ⚡ **This assertion was the opposite until today, and the change is
     * [ADR-0412](../../../docs/architecture/adr/0412-environment-and-secret-safe-logging.md)'s.**
     * 📁 The vocabulary is closed — `local`, `test`, `demo`, `production-local`,
     * `staging`, `production` — and **`development` was retired because it and
     * `local` were two spellings of one environment**: it meant *local* in this
     * tier and *deployed* in the AI Platform's guard, so the console transport
     * wrote verification links to stdout where the deterministic mock refused.
     *
     * ⛔ **The mode named `development` still exists and this is not a
     * contradiction** — `AuthMode` is what a reviewer is shown; the environment
     * name is what configuration says. **`local` is the environment that
     * produces that mode**, and nothing is spelled two ways any more.
     *
     * ✅ **A retired name reporting as PRODUCTION is the allow-list working**,
     * not a gap: an unknown name refuses, which is the safe direction for a
     * value nobody has thought about yet.
     */
    expect(withEnvironment('development', authMode)).toBe('production');
  });
});

describe('⚠️ the gap this function makes visible and does not close', () => {
  it('🔴 a lane name from the environment registry reports as PRODUCTION', () => {
    /**
     * ⛔ **`isDeployed()` is a denylist of three names and the registry in
     * `infra/environments.py` contains none of them** — it holds `review`,
     * `lane-qe`, `lane-a`…`lane-e` and `demo`. **A lane that exported
     * `SIGNORA_ENVIRONMENT=lane-a`, which is what the registry calls it,
     * would be classified deployed and its auth tier would refuse to start.**
     *
     * ✅ **Latent rather than live**: nothing sets the variable for the
     * frontend today. ⛔ **Asserted rather than fixed** — widening the
     * allowlist would make the console transport, which writes a credential
     * to stdout, permissible in more environments, and that is a weakened
     * guard whatever it is called (§13). **Reported as
     * [B-223](../../../docs/BUGS.md), and this test is what will fail on the
     * day somebody repairs it** — which is the point of writing it down as an
     * assertion rather than a comment.
     */
    expect(withEnvironment('lane-a', authMode)).toBe('production');
  });
});

describe('🔴 nothing in an authentication path may branch on the mode', () => {
  it('⛔ ADR-0406 §5 is falsifiable, so it is falsified here', async () => {
    /**
     * 📁 ***"No code path changes. Only configuration changes… an
     * `if (mode === …)` in an authentication path is the defect this ADR
     * exists to prevent."*** ⚡ **`authMode` is an OBSERVABLE: read by things
     * that DISPLAY, never by things that DECIDE.**
     *
     * ⛔ **The guard scans `lib/auth/` — the authentication tier — and
     * excludes the file that DEFINES the function and the one that renders
     * it.** A caller appearing there is the violation.
     */
    const { readdirSync, readFileSync } = await import('node:fs');
    const { join } = await import('node:path');

    const dir = join(process.cwd(), 'lib', 'auth');
    const offenders = readdirSync(dir)
      .filter((f) => f.endsWith('.ts') && f !== 'config.ts')
      .filter((f) => /\bauthMode\s*\(/.test(readFileSync(join(dir, f), 'utf8')));

    expect(offenders).toEqual([]);
  });

  it('⚡ and the guard can fire — it is not counting an empty directory', async () => {
    // B-162's lesson: a guard proven only by passing is a guard nobody has
    // seen work. This asserts the scan has something to scan, and that the
    // pattern it scans WITH matches a real call rather than only failing to.
    const { readdirSync } = await import('node:fs');
    const { join } = await import('node:path');

    const files = readdirSync(join(process.cwd(), 'lib', 'auth')).filter((f) =>
      f.endsWith('.ts'),
    );
    expect(files.length).toBeGreaterThan(1);
    expect(/\bauthMode\s*\(/.test('const m = authMode();')).toBe(true);
  });
});
