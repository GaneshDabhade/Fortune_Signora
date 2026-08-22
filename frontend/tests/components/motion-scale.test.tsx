import { readFileSync, readdirSync } from 'node:fs';
import { join, relative } from 'node:path';

import { describe, expect, it } from 'vitest';

import { screenDocument } from '../support/design-snapshot';

/**
 * 🔴 **The motion scale, asserted against the design document that publishes
 * it — and every class that uses it proved to exist.**
 *
 * ⛔ **This guard exists because a dead Tailwind class is INVISIBLE.** 📁
 * `onboarding/rail.tsx` wrote `duration-slow ease-premium` and
 * `onboarding/introduction.tsx` wrote `duration-DEFAULT`, both against Design
 * System v2 §18's contract, **and `tailwind.config.ts` carried none of it** —
 * so Tailwind emitted nothing, those elements animated at no duration at all,
 * and **it type-checked, linted, rendered and passed every gate.**
 *
 * ⚡ **Two assertions, because the defect had two halves**: the config must
 * carry what the design publishes, and no file may use a class the config
 * cannot produce.
 */
const SYSTEM = 'Fortune Signora Design System v2.dc.html';

/**
 * ⚡ **Tailwind's own duration steps.** ⛔ **Not the design's**, and listed here
 * only so a class using one is judged *resolvable* rather than *right* — the
 * second assertion asks whether a class RESOLVES, not whether it conforms.
 */
const TAILWIND_STEPS = ['0', '75', '100', '150', '200', '300', '500', '700', '1000'];

/** 📁 §18's `transitionDuration`, read out of the design document. */
function designDurations(): Record<string, string> {
  const text = screenDocument(SYSTEM).replace(/&#123;/g, '{').replace(/&#125;/g, '}');
  const block = /transitionDuration:\s*\{([^}]*)\}/.exec(text);
  if (block === null) throw new Error(`no transitionDuration block in ${SYSTEM}`);
  const out: Record<string, string> = {};
  for (const entry of (block[1] ?? '').matchAll(/(\w+)\s*:\s*"([^"]+)"/g)) {
    if (entry[1] !== undefined && entry[2] !== undefined) out[entry[1]] = entry[2];
  }
  if (Object.keys(out).length === 0) throw new Error(`parsed no durations from ${SYSTEM}`);
  return out;
}

/**
 * ⚠️ **Comments stripped before the config is parsed, and this bit on the first
 * run.** 🔴 **`tailwind.config.ts` QUOTES §18's contract in its own comment**,
 * in the design's double-quoted form — so the first `transitionDuration:` the
 * regex found was the documentation, and the declaration below it was never
 * read. ⛔ **The guard reported an empty config against a config that was
 * correct.** ⚡ **Third time a comment has been read as code here**, and the
 * same fix each time.
 */
function code(path: string): string {
  return readFileSync(path, 'utf8')
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/^\s*\/\/.*$/gm, '');
}

/** ⚡ **`.32` and `0.32` are the same number.** ⛔ A string compare says they are not. */
function curve(value: string): string {
  return value.replace(/\s/g, '').replace(/(^|[(,])0\./g, '$1.');
}

function sources(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...sources(path));
    else if (path.endsWith('.tsx')) out.push(path);
  }
  return out;
}

describe('📁 the motion scale is the design’s, and every class using it exists', () => {
  it('carries §18’s transitionDuration, read out of the design document', () => {
    const design = designDurations();
    const config = code(join(process.cwd(), 'tailwind.config.ts'));
    const block = /transitionDuration:\s*\{([^}]*)\}/.exec(config);
    expect(block, 'tailwind.config.ts declares transitionDuration').not.toBeNull();

    const carried: Record<string, string> = {};
    for (const entry of (block?.[1] ?? '').matchAll(/(\w+)\s*:\s*'([^']+)'/g)) {
      if (entry[1] !== undefined && entry[2] !== undefined) carried[entry[1]] = entry[2];
    }
    expect(carried, 'every step the design publishes, at its value').toEqual(design);
  });

  it('resolves the design’s easing to the token rather than restating the curve', () => {
    const config = code(join(process.cwd(), 'tailwind.config.ts'));
    expect(config).toMatch(/transitionTimingFunction:\s*\{\s*premium:\s*'var\(--ease\)'/);

    // 📁 **The curve itself lives in one place** — ⛔ a second literal here would
    // be the duplicated truth [§2](../../../CLAUDE.md) forbids, and the design's
    // own value is what `--ease` already holds.
    const css = readFileSync(join(process.cwd(), 'app', 'globals.css'), 'utf8');
    const ours = curve(/--ease:\s*([^;]+);/.exec(css)?.[1] ?? 'MISSING');
    expect(curve(screenDocument(SYSTEM)), 'the curve in globals.css is the design’s').toContain(ours);
  });

  /**
   * 🔴 **The half that would have caught the real defect.**
   *
   * ⚠️ **Comments are stripped first.** ⛔ **Two comments in the product record
   * `duration-DEFAULT` and `duration-200` as the values that were FIXED** — the
   * same false positive the vocabulary guard produced, and the same fix. **A
   * guard that reads documentation as code teaches people not to document.**
   */
  it('uses no duration or easing class the config cannot produce', () => {
    const config = code(join(process.cwd(), 'tailwind.config.ts'));
    const durationKeys = [
      ...(/transitionDuration:\s*\{([^}]*)\}/.exec(config)?.[1] ?? '').matchAll(/(\w+)\s*:/g),
    ].map((m) => m[1]);
    const easeKeys = [
      ...(/transitionTimingFunction:\s*\{([^}]*)\}/.exec(config)?.[1] ?? '').matchAll(/(\w+)\s*:/g),
    ].map((m) => m[1]);

    // ⛔ **`DEFAULT` is a Tailwind KEY, never a class.** ⚡ `duration-DEFAULT`
    // was written once and emitted nothing; the DEFAULT value reaches an element
    // through `transition-*` with no duration class at all.
    const durations = new Set([...durationKeys.filter((k) => k !== 'DEFAULT'), ...TAILWIND_STEPS]);
    const eases = new Set([...easeKeys, 'linear', 'in', 'out', 'in-out', 'initial']);

    const offenders: string[] = [];
    for (const file of [...sources(join(process.cwd(), 'components')), ...sources(join(process.cwd(), 'app'))]) {
      const bare = code(file);
      const where = relative(process.cwd(), file);
      for (const use of bare.matchAll(/\b(?:[a-z]+:)?duration-([A-Za-z0-9]+)\b/g)) {
        if (!durations.has(use[1])) offenders.push(`${where} — duration-${use[1]}`);
      }
      for (const use of bare.matchAll(/\b(?:[a-z]+:)?ease-([A-Za-z0-9]+)\b/g)) {
        if (!eases.has(use[1])) offenders.push(`${where} — ease-${use[1]}`);
      }
    }
    expect(offenders, 'these classes emit no CSS at all').toEqual([]);
  });
});
