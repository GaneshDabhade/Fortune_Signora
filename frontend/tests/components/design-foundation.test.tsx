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
    // **TASK-491 gap ②.** `--color-ai` was Tailwind `indigo-600` — the one
    // legacy value that survived TASK-490's pass, on the hue §14 reserves for
    // AI-authored content. It was invisible because no test asserted the
    // *value* of a token that every component correctly used.
    ['--ai', '--color-ai'],
    ['--ai-tint', '--color-ai-subtle'],
    // **Gap ③.** The design specifies two hairline weights and only the
    // strong one had a token, so every divider was drawn heavy — which is
    // exactly what Design System v2's own critique is about.
    ['--line-soft', '--color-border-soft'],
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

  it('carries all four elevations, and they are the design\'s own casts', () => {
    // **TASK-491 gap ⑤.** Three of four shipped. `--e4` is what a surface
    // cast *over* the page looks like, and the session-expired overlay is the
    // first thing that needs it — the design draws that card at `--e4`
    // precisely because content stays visible underneath it.
    //
    // Compared as numbers so `rgba(33,31,29,.04)` and `rgb(33 31 29 / 0.04)`
    // are one value written two ways rather than a failure about syntax.
    const cast = (raw: string) => (raw.match(/[\d.]+/g) ?? []).map(Number);
    for (const [ours, theirs] of [
      ['--shadow-sm', '--e1'],
      ['--shadow', '--e2'],
      ['--shadow-lg', '--e3'],
      ['--shadow-xl', '--e4'],
    ] as [string, string][]) {
      expect(cast(cssToken(ours)), `${ours} is the design's ${theirs}`).toEqual(
        cast(designToken(theirs)),
      );
    }
  });

  it('carries the card width as a token, and no screen restates it', () => {
    // **TASK-491 gap ⑦**, and D-162 ④ named the line: `auth-shell.tsx` held
    // `sm:max-w-[400px]` — an arbitrary value on the measurement the design
    // states most often, *"a single 400px card carries all 24 screens."*
    expect(cssToken('--card-width')).toBe('25rem');

    // ⚡ **The refusal, not just the token.** A token nothing consumes is a
    // token that drifts; the point of gap ⑦ is that the arbitrary class is
    // gone from the screen, so this asserts its absence rather than the
    // token's presence.
    const shell = readFileSync(
      join(__dirname, '..', '..', 'app', '(auth)', 'auth-shell.tsx'),
      'utf8',
    );
    expect(shell).toContain('max-w-card');
    expect(shell, 'no screen restates the card width').not.toMatch(/max-w-\[\d/);
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

  it('casts the design\'s dark elevations, not Tailwind\'s', () => {
    // ⚠️ **The audit did not name this one.** The *light* `--shadow-lg` was
    // already the design's `--e3` and the dark one had never been moved — so
    // the two themes cast different shapes, and every check passed because
    // none of them ever read the dark block.
    const darkBlock = /\[data-theme='dark'\]\s*\{([\s\S]*?)\n {2}\}/.exec(CSS);
    expect(darkBlock, 'the dark block is found').not.toBeNull();
    const value = (token: string) =>
      (new RegExp(`${token}:\\s*([^;]+);`).exec(darkBlock![1] ?? '')?.[1] ?? '')
        .match(/[\d.]+/g)
        ?.map(Number);
    // The design's dark casts are deeper and wider: a shadow on a dark ground
    // has almost no contrast to work with.
    const designDark = (token: string) => {
      const all = [...DESIGN.matchAll(new RegExp(`'${token}'\\s*:\\s*'([^']*)'`, 'g'))];
      // The dark theme is the *second* definition in the design's tokens().
      return (all[1]?.[1] ?? '').match(/[\d.]+/g)?.map(Number);
    };
    for (const [ours, theirs] of [
      ['--shadow-lg', '--e3'],
      ['--shadow-xl', '--e4'],
    ] as [string, string][]) {
      expect(value(ours), `dark ${ours} is the design's ${theirs}`).toEqual(
        designDark(theirs),
      );
    }
  });
});

describe('containers consume the design’s soft hairline, not the strong one', () => {
  /**
   * 🔴 **The token values were never the problem. The consumption was.**
   *
   * 📁 **Measured across all 34 finalized design documents**: borders naming
   * `--line-soft` outnumber `--line` **1873 to 323** — the soft hairline is the
   * ordinary divider and the strong one is the exception. ⛔ **The
   * implementation was inverted, 11 to 137**, so nearly every card edge,
   * divider, panel and rail rendered one step darker than the design.
   *
   * ⚠️ **`design-foundation`'s existing tests all passed throughout**, because
   * they assert that each token HOLDS the design's value — ⚡ **and both tokens
   * did.** ✅ **This asserts which token a container REACHES FOR**, which is the
   * half no value check can see.
   *
   * ⛔ **Interactive control outlines are deliberately absent**: 📁 the design
   * outlines its own buttons with `border:1px solid var(--line)`, so `input`
   * and `select` keeping the strong token is correct rather than an oversight.
   */
  const CONTAINERS = [
    'components/ui/card.tsx',
    'components/ui/table.tsx',
    'components/ui/dialog.tsx',
    'components/ui/drawer.tsx',
    'components/ui/empty-state.tsx',
    'components/ui/error-state.tsx',
    'components/shell/app-shell.tsx',
    'components/shell/navigation.tsx',
    'components/shell/top-bar.tsx',
  ];

  for (const file of CONTAINERS) {
    it(`${file.split('/').pop()} draws its edges with the soft hairline`, () => {
      const source = readFileSync(join(process.cwd(), file), 'utf8');
      // ⛔ **`border-border` with a word boundary** — `border-border-soft` and
      // `border-border-strong` are both legitimate and must not match.
      const strong = source.match(/border-border(?![-\w])/g) ?? [];
      expect(
        strong,
        `${file} reaches for the strong hairline; the design uses --line-soft for containers`,
      ).toEqual([]);
    });
  }
});
