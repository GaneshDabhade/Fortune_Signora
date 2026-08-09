/**
 * **Which mode a Playwright run is watched in** —
 * [TASK-476](../../../docs/BACKLOG.md).
 *
 * ⚡ **The row's own acceptance assertion is that no SPEC changes**: *"every
 * existing spec must pass UNCHANGED in both modes — a default change that
 * alters a result has changed behaviour, not configuration."* ⛔ **So the
 * property under test is the RESOLUTION, not a journey**, and it is unit-tested
 * because the alternative is running a browser suite twice to learn what one
 * boolean is.
 *
 * 🔴 **The case that earns the file is the precedence one.** Two flags can be
 * set at once, and until this file existed nothing recorded which wins.
 */
import { describe, expect, it } from 'vitest';

import {
  DEMONSTRATION_SLOW_MO,
  resolveRunMode,
  type RunModeEnvironment,
} from '../e2e/fixtures/environment';

/** An explicit empty environment: `process.env` must never leak into a case. */
const NOTHING: RunModeEnvironment = {};

describe('📁 §19 — headed is the default for local development and review', () => {
  it('🔴 an unset environment is HEADED, which is the whole row', () => {
    // ⛔ Before TASK-476 this was `false`. `CLAUDE.md` §19 claimed otherwise
    // and flagged itself for it — the sentence is what changed the code.
    expect(resolveRunMode(NOTHING).headed).toBe(true);
  });

  it('⛔ and carries no slowMo, because every local run would pay for it', () => {
    // 250ms on every action turns a six-minute suite into one nobody runs.
    expect(resolveRunMode(NOTHING).slowMo).toBeUndefined();
  });
});

describe('⚡ the opt-out exists, and there are two spellings of it', () => {
  it('HEADLESS=1 means do not open a window', () => {
    expect(resolveRunMode({ HEADLESS: '1' }).headed).toBe(false);
  });

  it('⛔ HEADED=0 is the same answer — a negative must not read as “unset”', () => {
    // Somebody who exports HEADED=0 has said something, and treating it as
    // absence would hand them the opposite of what they asked for.
    expect(resolveRunMode({ HEADED: '0' }).headed).toBe(false);
  });

  it('neither opt-out slows anything down', () => {
    expect(resolveRunMode({ HEADLESS: '1' }).slowMo).toBeUndefined();
  });
});

describe('📁 HEADED=1 is the demonstration, and it is unchanged', () => {
  it('⚡ still headed, still at a human pace', () => {
    // `make product-demo` sets it. The demonstration's pace rode on this flag
    // before the row and rides on it after — the row moved the DEFAULT, not
    // the demonstration.
    const mode = resolveRunMode({ HEADED: '1' });
    expect(mode.headed).toBe(true);
    expect(mode.slowMo).toBe(DEMONSTRATION_SLOW_MO);
  });
});

describe('🔴 precedence — the case nothing recorded before this file', () => {
  it('⚡ HEADED=1 beats HEADLESS=1', () => {
    /**
     * ⛔ **A demonstration that silently ran headless would lose the only thing
     * it exists for**, and nobody would find out until the day it was put in
     * front of somebody. **`HEADLESS` describes an environment and is the kind
     * of thing a shell exports and forgets; `HEADED=1` is an intent, on the
     * command that carries it.**
     */
    const mode = resolveRunMode({ HEADED: '1', HEADLESS: '1' });
    expect(mode.headed).toBe(true);
    expect(mode.slowMo).toBe(DEMONSTRATION_SLOW_MO);
  });

  it('⛔ and HEADED=0 with HEADLESS=1 agree rather than fight', () => {
    expect(resolveRunMode({ HEADED: '0', HEADLESS: '1' }).headed).toBe(false);
  });
});

describe('⛔ nothing outside the two flags decides this', () => {
  it('🔴 CI is not consulted — §20c-2 says the correct quantity of CI is zero', () => {
    // The row is explicit that certification runs on the SAME MACHINE as
    // development, so a deployment or environment variable cannot separate
    // them. The distinction is which command was run, not where.
    expect(resolveRunMode({ CI: '1' }).headed).toBe(true);
    expect(resolveRunMode({ CI: 'true' }).headed).toBe(true);
  });

  it('🔴 DISPLAY is not consulted either — that would be a hidden input', () => {
    // ⚠️ The tempting safety net: fall back to headless where no display
    // exists. It is the defect `browserEnvironment()` was written to REMOVE —
    // the same command behaving differently because of something outside the
    // declared contract (`CLAUDE.md` §2).
    expect(resolveRunMode({}).headed).toBe(true);
    expect(resolveRunMode({ DISPLAY: ':0' }).headed).toBe(true);
  });

  it('⛔ SIGNORA_ENVIRONMENT is not consulted — the row forbids it by name', () => {
    expect(resolveRunMode({ SIGNORA_ENVIRONMENT: 'certification' }).headed).toBe(true);
  });

  it('⚠️ an unrecognised value is not a flag — HEADED=yes is not HEADED=1', () => {
    // Exact matching, deliberately: a truthy-ish string quietly selecting the
    // demonstration pace is how a suite becomes four times slower for a reason
    // nobody can find.
    const mode = resolveRunMode({ HEADED: 'yes' });
    expect(mode.headed).toBe(true);
    expect(mode.slowMo).toBeUndefined();
  });
});

describe('✅ every branch says which rule decided', () => {
  it('⚡ the reason is what a future reader debugs with, not the boolean', () => {
    const reasons = [
      resolveRunMode(NOTHING),
      resolveRunMode({ HEADED: '1' }),
      resolveRunMode({ HEADLESS: '1' }),
    ].map((m) => m.reason);
    expect(new Set(reasons).size).toBe(3);
    for (const reason of reasons) expect(reason.length).toBeGreaterThan(0);
  });
});
