import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import { tokenTable, type Theme } from '../support/design-snapshot';

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

/**
 * 🔴 **[B-1051](../../../docs/BUGS.md) — this file could only ever see one
 * theme, and that is how two defects lived here.**
 *
 * ⛔ **`designToken` took the first match and `cssToken` took the first
 * declaration**, and in both files the light block comes first. ⚡ **So every
 * assertion below was a light-theme assertion wearing a role's name**, and
 * `--color-accent-hover` (holding the design's `--brand-ink`) and
 * `--color-accent-soft` (holding `--brand-line`) were correct in light and
 * wrong in dark for as long as the mapping has existed.
 *
 * ✅ **Both halves are split by theme now**, and every mapping is asserted
 * twice. ⚠️ **QE's own criterion, and it is the right one**: *"a test that
 * only forbids literal colours is not sufficient — the assertion must be
 * value-against-design"*, in **both** themes.
 */
/**
 * 🔴 **The authority is ALL 35 screen documents, not the Design System file
 * alone** — and that correction is what this row turned on.
 *
 * ⛔ **`Design System v2.dc.html` does not declare `--pos-line`, `--warn-line`
 * or `--risk-line`; eighteen of the other screens do**, unanimously. ⚡ **So
 * reading one document answers *is this role in the summary* rather than *what
 * is this role's value***, and the first question is not the one a token guard
 * is asking.
 *
 * ⚠️ **The extraction is NOT written here.** 📁
 * [`tests/support/design-snapshot.ts`](../support/design-snapshot.ts) owns it,
 * and this file imports it — ⛔ **because two lanes measuring the same 35
 * documents already produced two different sets of numbers once**, and a
 * second copy inside this repository would be the same failure at closer
 * range. ✅ **The precedent is
 * [`support/source.ts`](../support/source.ts)**, extracted for
 * [B-252](../../../docs/BUGS.md) for exactly this reason.
 */
const DESIGN_TABLE = tokenTable();

it('reads the token block from every screen document', () => {
  // ⚡ **A guard that silently read one file would still pass every assertion
  // below** — 📁 the truncation-that-reads-as-a-result failure this lane has
  // now met four times.
  expect(DESIGN_TABLE.read).toBeGreaterThanOrEqual(30);
});

it('proves the premise it relies on — the documents agree', () => {
  // ⛔ **A disagreement is a finding, never a resolution.** ⚠️ Silently taking
  // the first value is how a snapshot refresh becomes invisible.
  expect(DESIGN_TABLE.conflicts).toEqual([]);
});

function designToken(name: string, theme: Theme = 'light'): string {
  const pattern = new RegExp(`'${name}'\\s*:\\s*'([^']*)'`);
  // ⚡ **Theme-independent roles live in the `base` object**, outside both
  // blocks — `--font-body` and `--ease` are the same in light and dark, and the
  // design says so by declaring them once. ⛔ **So the block is preferred and
  // the document is the fallback**, rather than the document being searched
  // first, which is the behaviour that hid the dark values.
  const fromTable = DESIGN_TABLE.values[theme].get(name);
  if (fromTable !== undefined) return fromTable;
  const match = pattern.exec(DESIGN);
  expect(match, `the design defines ${name} in ${theme}`).not.toBeNull();
  return match![1] ?? '';
}

function hexToRgb(hex: string): string {
  const h = hex.replace('#', '');
  return `${parseInt(h.slice(0, 2), 16)} ${parseInt(h.slice(2, 4), 16)} ${parseInt(h.slice(4, 6), 16)}`;
}

/**
 * ⚠️ **Comments are stripped first.** 📁 QE's own note on the method: a doc
 * comment quoting `` `--line-soft: #eae5df` `` is indistinguishable from a
 * declaration to a regex, and reading one as the other produces a finding that
 * is not there.
 */
const CSS_BARE: string = CSS.replace(/\/\*[\s\S]*?\*\//g, '');

function themeBlock(theme: Theme): string {
  const selector = theme === 'light' ? ':root {' : ":root[data-theme='dark'] {";
  const start = CSS_BARE.indexOf(selector);
  expect(start, `globals.css declares ${selector}`).toBeGreaterThan(-1);
  const end = CSS_BARE.indexOf('\n  }', start);
  return CSS_BARE.slice(start, end === -1 ? undefined : end);
}

const CSS_BLOCKS: Record<Theme, string> = { light: themeBlock('light'), dark: themeBlock('dark') };

function cssToken(name: string, theme: Theme = 'light'): string {
  const match = new RegExp(`${name}:\\s*([^;]+);`).exec(CSS_BLOCKS[theme]);
  expect(match, `globals.css defines ${name} in ${theme}`).not.toBeNull();
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
    // ⛔ **Both themes.** 🔴 One theme is how `--color-accent-hover` and
    // `--color-accent-soft` passed this file while holding another role's
    // colour in dark ([B-1051](../../../docs/BUGS.md)).
    for (const theme of ['light', 'dark'] as const) {
      it(`${ours} is the design's ${design} in ${theme}`, () => {
        expect(cssToken(ours, theme)).toBe(hexToRgb(designToken(design, theme)));
      });
    }
  }

  /**
   * 🔴 **The ramp, asserted as a RAMP** — 📁 [B-1050](../../../docs/BUGS.md)'s
   * own criterion: *"no two of canvas / surface / raised / sunken resolve to
   * the same value in either theme."*
   *
   * ⚡ **A four-step ramp that loses a step still passes a value-by-value
   * check if the values it holds are each some real token** — which is exactly
   * how dark `sunken` came to be the canvas colour.
   */
  it('keeps four DISTINCT surface steps in both themes', () => {
    const steps = [
      '--color-canvas',
      '--color-surface',
      '--color-surface-raised',
      '--color-surface-sunken',
    ];
    for (const theme of ['light', 'dark'] as const) {
      const values = steps.map((token) => cssToken(token, theme));
      expect(new Set(values).size, `${theme}: ${values.join(' | ')}`).toBe(steps.length);
    }
  });
});

/**
 * 🔴 **[B-1051](../../../docs/BUGS.md) — five design roles had no token at all.**
 *
 * ⚡ **The authority is the 35 screen documents, not the Design System's prose
 * table**: every one carries the same `tokens()` block, and a comparison across
 * all of them finds zero disagreements. ⛔ **This corrects a ruling this lane
 * had established** — that `--ai-ink` and `--ai-line` were "mock chrome" —
 * **which was drawn from the summary table rather than from the token block.**
 */
describe('the roles the design publishes and the repository had no token for', () => {
  const added: [string, string][] = [
    ['--brand-ink', '--color-accent-ink'],
    ['--brand-line', '--color-accent-line'],
    ['--ai-ink', '--color-ai-ink'],
    ['--ai-line', '--color-ai-line'],
    ['--pos-line', '--color-success-line'],
    ['--warn-line', '--color-warning-line'],
    ['--risk-line', '--color-danger-line'],
  ];

  for (const [design, ours] of added) {
    for (const theme of ['light', 'dark'] as const) {
      it(`${ours} is the design's ${design} in ${theme}`, () => {
        expect(cssToken(ours, theme)).toBe(hexToRgb(designToken(design, theme)));
      });
    }
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
