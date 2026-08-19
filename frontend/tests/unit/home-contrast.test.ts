/**
 * **Home's `1.4.3`, measured** — 📁 `Fortune Signora Home.dc.html` §11:
 *
 * > *"Briefing text on the AI tint measures 6.9:1. **Every tag pairs a 600-weight
 * > label with a tint clearing 4.5:1, verified per composition per theme in
 * > CI.**"*
 *
 * ## 🔴 The design says *in CI* and there was no check
 *
 * ⚡ **`design-tokens.test.tsx` asserts that a colour is a TOKEN**; ⛔ **nothing
 * asserted what the token's value does to a reader.** 📁 A theme change is one
 * edit precisely so it can be made — and **an edit that keeps every rule and
 * halves a ratio passes every gate this repository had.**
 *
 * ## ⚡ Computed from `globals.css`, not from a table
 *
 * ⛔ **A list of expected ratios would be a second representation of the palette**
 * ([§2](../../../CLAUDE.md)) and would go stale on the first token edit — which is
 * the edit this exists to catch. ✅ **The values are read from the stylesheet and
 * the ratio is computed**, so the check has no opinion of its own.
 *
 * ## ⚠️ Both themes, because the design says *per theme*
 *
 * 📁 The dark palette is not the light one inverted — `--color-warning` is
 * `165 105 31` light and `211 160 90` dark — **so a pair that clears in one can
 * fail in the other**, and a check that read only `:root` would say nothing about
 * half the product.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

const CSS = readFileSync(join(process.cwd(), 'app', 'globals.css'), 'utf8');

/**
 * ⚡ **The dark block is `:root[data-theme='dark']`**, and the light values are
 * everything before it. ⛔ **Read positionally rather than by parsing CSS**: a
 * parser here would be a dependency, and the file's own structure is the
 * contract — the light palette is defined once at the top and overridden below.
 */
const DARK_AT = CSS.indexOf(":root[data-theme='dark']");

function token(name: string, theme: 'light' | 'dark'): [number, number, number] {
  const source = theme === 'light' ? CSS.slice(0, DARK_AT) : CSS.slice(DARK_AT);
  const matches = [...source.matchAll(new RegExp(`--color-${name}:\\s*([\\d\\s]+);`, 'g'))];
  const last = matches.at(-1);
  if (last === undefined) throw new Error(`--color-${name} has no ${theme} value`);
  const parts = last[1]!.trim().split(/\s+/).map(Number);
  return [parts[0]!, parts[1]!, parts[2]!];
}

/** WCAG 2.1 relative luminance. */
function luminance([r, g, b]: [number, number, number]): number {
  const channel = (value: number) => {
    const v = value / 255;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
}

/** WCAG 2.1 contrast ratio, `(L1 + 0.05) / (L2 + 0.05)`. */
function ratio(foreground: string, background: string, theme: 'light' | 'dark'): number {
  const a = luminance(token(foreground, theme));
  const b = luminance(token(background, theme));
  const [light, dark] = a > b ? [a, b] : [b, a];
  return (light + 0.05) / (dark + 0.05);
}

/**
 * 📁 **Home's own tag pairs.** ⚡ `card.attention` draws a tag per posture — 📁
 * *"attention severity uses the left rule, the tag word and the tint together"* —
 * and the strips reuse the same three tints.
 *
 * ⛔ **The list is Home's, not the palette's.** A check over every token pair
 * would fail on combinations nothing renders, and 📁 §2's *"a guard that cannot
 * fail is documentation pretending to be code"* has a twin: **a guard that fails
 * on something nobody ships teaches people to ignore it.**
 */
const TAG_PAIRS: readonly [string, string, string][] = [
  ['risk tag — card.attention, and state 10\'s strip', 'danger', 'danger-subtle'],
  ['warn tag — card.attention, and states 05 and 11', 'warning', 'warning-subtle'],
  ['positive tag — card.attention, and state 04\'s strip', 'success', 'success-subtle'],
];

/** 📁 Body copy Home renders on its own surfaces, at every card. */
const TEXT_PAIRS: readonly [string, string, string][] = [
  ['card body on a card', 'content', 'surface'],
  ['card body muted on a card', 'content-muted', 'surface'],
  ['the scope line on the page ground', 'content-muted', 'canvas'],
  ['a strip sentence on the danger tint', 'content', 'danger-subtle'],
  ['a strip sentence on the warning tint', 'content', 'warning-subtle'],
  ['a strip sentence on the success tint', 'content', 'success-subtle'],
  ['a card heading on a skeleton ground', 'content', 'surface-sunken'],
];

/**
 * 📁 **`1.4.3`'s floor for the design's own claim** — *"a tint clearing 4.5:1"*.
 * ⚡ This is AA for normal text, which is what a tag word and a card sentence are.
 */
const AA = 4.5;

/**
 * 🔴 **[B-286](../../../docs/BUGS.md) — the design's own light warn pair is
 * 4.08:1**, against its own stated floor of 4.5:1.
 *
 * ⛔ **Not an implementation defect.** ⚡ `--color-warning: 165 105 31` is the
 * design's `#a5691f` exactly and `--color-warning-subtle` is its `#fbf2e4`
 * exactly — **the tokens are faithful and the claim is what fails.** 📁 Its three
 * siblings clear it: risk `5.90`, positive `4.69`, and the dark warn `6.73`.
 *
 * ⛔ **Changing the token is not this lane's** — [§20c](../../../CLAUDE.md) makes
 * the design the authority for the palette, and diverging from it silently would
 * be worse than the gap.
 *
 * ✅ **`it.fails` rather than an exception list.** ⚡ It **turns red the moment
 * somebody fixes the palette**, which is the property a skip or a lowered floor
 * does not have — the same device `interaction-boundaries.spec.ts` used for
 * `B-312` and deleted when it was fixed.
 */
const KNOWN_SHORTFALL = new Set(["warn tag — card.attention, and states 05 and 11|light"]);

describe.each(['light', 'dark'] as const)('📁 1.4.3 — the %s theme', (theme) => {
  for (const [what, foreground, background] of TAG_PAIRS) {
    const test = KNOWN_SHORTFALL.has(`${what}|${theme}`) ? it.fails : it;
    test(`${what} clears 4.5:1`, () => {
      expect(ratio(foreground, background, theme)).toBeGreaterThanOrEqual(AA);
    });
  }

  it.each(TEXT_PAIRS)('%s clears 4.5:1', (_what, foreground, background) => {
    expect(ratio(foreground, background, theme)).toBeGreaterThanOrEqual(AA);
  });
});

describe('⚡ the measurement itself', () => {
  /**
   * 🔴 **The vacuity guard.** ⛔ If `token()` silently returned the same value for
   * both themes — a changed selector, a moved block — **every assertion above
   * would still pass**, and the check would be measuring one theme twice.
   */
  it('reads genuinely different values for the two themes', () => {
    expect(token('surface', 'light')).not.toEqual(token('surface', 'dark'));
    expect(token('warning', 'light')).not.toEqual(token('warning', 'dark'));
  });

  /** ⚡ **A known answer**, so an arithmetic error cannot hide behind a pass. */
  it('computes black on white as 21:1', () => {
    expect(
      (luminance([255, 255, 255]) + 0.05) / (luminance([0, 0, 0]) + 0.05),
    ).toBeCloseTo(21, 1);
  });
});
