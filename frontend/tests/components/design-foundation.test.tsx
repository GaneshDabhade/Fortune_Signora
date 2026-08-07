import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

/**
 * TASK-490 — **the design foundation, verified against its canonical source.**
 *
 * ⚡ **[D-163](../../../docs/DECISION_REGISTER.md) fixes the hierarchy**:
 * *Design System v2 → workflow design → screen*. So this reads the token
 * values out of `Fortune Signora Design System v2.dc.html` itself and asserts
 * `globals.css` carries them. ⛔ **Nothing here is a transcription** — if the
 * design is refreshed and a value moves, this fails rather than agreeing with
 * a copy somebody made once.
 *
 * ⚠️ **This is the check that would have caught D-162 before the product
 * owner did.** The palette was Tailwind slate while the design was warm, and
 * every existing token test passed throughout, because they asserted that
 * components *use* tokens and never what the tokens *are*.
 */

const ROOT = join(__dirname, '..', '..', '..');
const DESIGN: string = readFileSync(
  join(ROOT, 'docs/design-snapshot/screens/Fortune Signora Design System v2.dc.html'),
  'utf8',
);
const CSS: string = readFileSync(join(__dirname, '..', '..', 'app', 'globals.css'), 'utf8');

/** The design's own `tokens()` block, light theme — the first definition wins. */
function designToken(name: string): string {
  const match = new RegExp(`'${name}'\\s*:\\s*'([^']*)'`).exec(DESIGN);
  expect(match, `the design defines ${name}`).not.toBeNull();
  return match![1] ?? '';
}

function hexToRgb(hex: string): string {
  const h = hex.replace('#', '');
  return `${parseInt(h.slice(0, 2), 16)} ${parseInt(h.slice(2, 4), 16)} ${parseInt(h.slice(4, 6), 16)}`;
}

/** The light-theme value, which is the first occurrence in `globals.css`. */
function cssToken(name: string): string {
  const match = new RegExp(`${name}:\\s*([^;]+);`).exec(CSS);
  expect(match, `globals.css defines ${name}`).not.toBeNull();
  return (match![1] ?? '').trim();
}

describe('the palette is the finalized one, value by value', () => {
  const mapping: [string, string][] = [
    ['--bg', '--color-canvas'],
    ['--surface', '--color-surface'],
    ['--sunken', '--color-surface-sunken'],
    ['--line', '--color-border'],
    ['--ink', '--color-content'],
    ['--ink-2', '--color-content-muted'],
    ['--ink-3', '--color-content-subtle'],
    ['--brand', '--color-accent'],
    ['--brand-strong', '--color-accent-hover'],
    ['--brand-soft', '--color-accent-soft'],
    ['--brand-tint', '--color-accent-subtle'],
    ['--pos', '--color-success'],
    ['--warn', '--color-warning'],
    ['--risk', '--color-danger'],
  ];

  for (const [design, ours] of mapping) {
    it(`${ours} is the design's ${design}`, () => {
      expect(cssToken(ours)).toBe(hexToRgb(designToken(design)));
    });
  }
});

describe('the scales the Design System defines', () => {
  it('carries the full radius scale, 4 through 20', () => {
    for (const [token, px] of [
      ['--radius-xs', 4],
      ['--radius-sm', 6],
      ['--radius-md', 8],
      ['--radius-lg', 12],
      ['--radius-xl', 16],
      ['--radius-2xl', 20],
    ] as [string, number][]) {
      expect(cssToken(token), token).toBe(`${px / 16}rem`);
    }
  });

  it('carries the shared motion curve rather than a per-screen one', () => {
    // The Design System defines --ease once for everything; a screen picking
    // its own easing is the workflow-specific override D-163 forbids.
    // Compared as numbers: `.32` and `0.32` are one value written two ways,
    // and a test that failed on the leading zero would be asserting spelling.
    const curve = (raw: string) => (raw.match(/[\d.]+/g) ?? []).map(Number);
    expect(curve(cssToken('--ease'))).toEqual(curve(designToken('--ease')));
  });

  it('names Archivo as the body face, and self-hosts it', () => {
    expect(cssToken('--font-body')).toContain('Archivo');
    const layout = readFileSync(join(__dirname, '..', '..', 'app', 'layout.tsx'), 'utf8');
    // `next/font` emits the files from our own origin. A <link> to a font CDN
    // would be a third-party request at runtime and a content-policy problem
    // for a customer.
    expect(layout).toContain("from 'next/font/google'");
    expect(layout).toContain('Archivo');
  });
});

describe('the dark theme is the design\'s, not an inversion', () => {
  it('uses the design\'s own dark ground rather than a computed one', () => {
    // #0d1418 — the design paints it explicitly. A dark theme derived by
    // inverting the light one lands somewhere else entirely.
    const dark = /\[data-theme='dark'\][^}]*--color-canvas:\s*([^;]+);/s.exec(CSS)
      ?? /prefers-color-scheme: dark[\s\S]*?--color-canvas:\s*([^;]+);/.exec(CSS);
    expect(dark, 'a dark canvas is defined').not.toBeNull();
    expect((dark![1] ?? '').trim()).toBe(hexToRgb('#0d1418'));
  });
});
