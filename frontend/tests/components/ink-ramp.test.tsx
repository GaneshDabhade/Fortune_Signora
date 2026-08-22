import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import { THEMES, tokenTable, type Theme } from '../support/design-snapshot';

/**
 * 🔴 **[B-1064](../../../docs/BUGS.md), found by QE — the content ramp's DEPTH,
 * not its values.**
 *
 * 📁 **The design's ink ramp is four steps** — `--ink`, `--ink-2`, `--ink-3`,
 * `--ink-4` — **and the product's content ramp was three.** ⛔ **So everything
 * the design draws in `--ink-4` fell back to `--ink-3`, one step too dark, on
 * `440` uses across all 35 documents.**
 *
 * ⚠️ **A per-token check could not see it.** Every token the product HAD was
 * correct; the ramp was **short**, not wrong — which is why this asserts that
 * each of the design's steps has a content token at all.
 *
 * 🔴 **And it must look in the CONTENT ramp specifically.** ⛔ **`#a39a91` was
 * already in `globals.css` — as `--color-border-strong`, a BORDER role** — so a
 * guard asking *"does this value exist anywhere?"* would have passed on the
 * broken tree. ⚡ **That is the same defect as counting panels and calling them
 * badges: the right value against the wrong population.**
 */
function contentRamp(theme: Theme): Map<string, string> {
  const css = readFileSync(join(process.cwd(), 'app', 'globals.css'), 'utf8');
  // ⚡ **`:root` is light and `[data-theme='dark']` is dark**, in source order,
  // which is the same two-payload shape the design documents use.
  const blocks = css.split(/\[data-theme=['"]dark['"]\]|\.dark\b/);
  const region = theme === 'light' ? blocks[0] : blocks.slice(1).join('\n');
  const found = new Map<string, string>();
  for (const m of (region ?? '').matchAll(/(--color-content[a-z-]*):\s*([0-9]+ [0-9]+ [0-9]+)\s*;/g)) {
    const name = m[1];
    const value = m[2];
    if (name !== undefined && value !== undefined && !found.has(name)) found.set(name, value);
  }
  return found;
}

/** ⚡ The design states hex; the product states an unparenthesised RGB triplet. */
function triplet(hex: string): string {
  const bare = hex.trim().replace('#', '');
  return [0, 2, 4].map((i) => parseInt(bare.slice(i, i + 2), 16)).join(' ');
}

describe('📁 the content ramp is as deep as the design’s ink ramp', () => {
  for (const theme of THEMES) {
    it(`carries a content token for every ink step the design declares — ${theme}`, () => {
      const design = tokenTable().values[theme];
      const inks = [...design.keys()].filter((role) => /^--ink(-[0-9]+)?$/.test(role)).sort();
      // ⛔ **Four, and asserted rather than assumed** — if the design gains a
      // fifth step this fails here rather than silently covering three of five.
      expect(inks.length, 'the design declares this many ink steps').toBeGreaterThanOrEqual(4);

      const ramp = contentRamp(theme);
      // ⛔ **`-inverted` is a different role** — text ON a filled surface, not a
      // step down the ramp — so it cannot stand in for one.
      const steps = new Set(
        [...ramp.entries()].filter(([name]) => name !== '--color-content-inverted').map(([, v]) => v),
      );

      const missing = inks.filter((role) => {
        const value = design.get(role);
        return value === undefined || !steps.has(triplet(value));
      });
      expect(missing, `these design ink steps have no content token in ${theme}`).toEqual([]);
    });
  }
});
