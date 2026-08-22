/**
 * 🔴 **[B-297](../../docs/BUGS.md) — the skeleton had fifteen implementations
 * and one of them was the component.**
 *
 * ## ⛔ Why the row read as a one-line change and was not
 *
 * 📁 **§13**: *"Skeletons keep the layout and gain rounded blocks with a
 * three-cycle shimmer."* ⚡ **Changing `animate-pulse` to that gradient looks
 * like editing one `className`** — 🔴 **it was twenty-one sites**: fourteen
 * hand-rolled copies of `animate-pulse rounded bg-surface-sunken`, the
 * primitive, and six test locators selecting skeletons *by their animation*.
 *
 * ⚠️ **The duplication is 📁 [§2](../../CLAUDE.md)** — truth has one
 * representation — **and [§20c](../../CLAUDE.md)'s *"another bespoke version of
 * an existing common component"*, fourteen times over. ⛔ **It also cost
 * behaviour**: `Skeleton` carries `aria-hidden` for the reason 🔴
 * [B-1057](../../docs/BUGS.md) records — *three pulsing rectangles are not a
 * status message* — **and not one of the fourteen copies did.**
 *
 * ## ✅ What this guard actually pins, and what it deliberately does not
 *
 * ⛔ **Not *"nothing may use `animate-pulse`"***. 📁
 * [`app-shell.tsx`](../../components/shell/app-shell.tsx)'s refresh bar is a
 * `role="progressbar"` on `bg-accent` that pulses, and **it is not a
 * skeleton** — ⚠️ **every `[class*="animate-pulse"]` locator in the suite was
 * counting it as one.** ✅ **The signature is the PAIRING** — a pulsing block
 * on `--surface-sunken` — which is the placeholder and nothing else.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';
import { globSync } from 'glob';

const ROOT = join(__dirname, '..', '..');

/** 📁 The primitive itself, which is the one place the pairing belongs. */
const PRIMITIVE = join('components', 'ui', 'skeleton.tsx');

function sources(): string[] {
  const files = globSync('{app,components,lib}/**/*.{ts,tsx}', { cwd: ROOT });
  // ⚡ **The instrument before the subject** — an empty glob would report a
  // clean product, and a clean product is exactly what a broken glob looks
  // like. 🔴 It has happened twice in this suite's history.
  expect(files.length, 'the source glob matched nothing, so nothing below was checked').toBeGreaterThan(
    100,
  );
  return files;
}

/**
 * ⚠️ **Per STRING, never per file — and the first draft of this guard got it
 * wrong.**
 *
 * ⛔ **Checking whether a file contains both tokens flagged
 * 📁 [`app-shell.tsx`](../../components/shell/app-shell.tsx)**, which holds
 * `'animate-pulse motion-reduce:animate-none'` on the refresh bar and
 * `'h-[2px] … bg-surface-sunken'` on the track it runs in — **two elements, two
 * strings, no skeleton.** ⚡ **A file is not the unit the pairing lives in**;
 * one class attribute is. 🔴 **An instrument whose population is wider than the
 * thing it asserts about fails the same way a narrow one does** — it just fails
 * loudly instead of silently, which is the only reason this one was caught.
 */
function classStrings(body: string): string[] {
  return body.match(/(['"`])(?:\\.|(?!\1)[^\\])*\1/g) ?? [];
}

describe('🔴 B-297 — the skeleton has one implementation', () => {
  it('no file outside the primitive pairs a pulse with the sunken surface', () => {
    const offenders = sources().filter((file) => {
      if (file === PRIMITIVE) return false;
      const body = readFileSync(join(ROOT, file), 'utf8');
      return classStrings(body).some(
        (value) => value.includes('animate-pulse') && value.includes('bg-surface-sunken'),
      );
    });

    expect(
      offenders,
      'a hand-rolled skeleton: use <Skeleton className="…" />, which carries aria-hidden and the B-297 hook',
    ).toEqual([]);
  });

  /**
   * ⚡ **The half a source scan cannot see.** ⛔ **A test that finds skeletons
   * by their animation breaks silently when the animation changes** — and
   * 📁 `visual.spec.ts`'s is a `waitForFunction`, so it would not fail: **it
   * would stop waiting and assert against a loading screen**, which is 🔴
   * [B-1065](../../docs/BUGS.md) reintroduced by a cosmetic edit.
   */
  it('no test finds a skeleton by the class that says how it looks', () => {
    const specs = globSync('tests/**/*.{ts,tsx}', { cwd: ROOT });
    expect(specs.length).toBeGreaterThan(50);

    const offenders = specs.filter((file) => {
      if (file.endsWith('skeleton-single-source.test.tsx')) return false;
      const body = readFileSync(join(ROOT, file), 'utf8');
      // ⛔ **Comments stripped first.** 🔴 Three guards in this repository have
      // matched the contract quoted in their own docblock rather than the
      // code — including one of mine.
      const code = body.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '');
      return /animate-pulse/.test(code);
    });

    expect(offenders, 'select `[data-skeleton]`, which survives §13\'s shimmer').toEqual([]);
  });
});
