import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import { screenDocument } from '../support/design-snapshot';

/**
 * 🔴 **Each shared surface carries the radius §05 assigns it and the elevation
 * §06 assigns it — both read out of the design.**
 *
 * ⛔ **Five divergences existed at once and every gate was green**: the dialog
 * cast `--e3`, a tooltip's shadow · the toast was `8px`/`--e2` where both
 * scales name it at `12px`/`--e3` · the table plane had **no elevation at all**
 * · the scrim was `40%` against §12's `24%`.
 *
 * ⚡ **The scales name these elements BY NAME**, so this needs no interpretation
 * — which is why it can be a test rather than a coordination item.
 */
const SYSTEM = 'Fortune Signora Design System v2.dc.html';

/** ⚡ Tailwind's class for each design token, so the assertion reads as CSS does. */
const RADIUS_CLASS: Record<string, string> = {
  '--r-xs': 'rounded-xs',
  '--r-sm': 'rounded-sm',
  '--r-md': 'rounded',
  '--r-lg': 'rounded-lg',
  '--r-xl': 'rounded-xl',
  '--r-full': 'rounded-full',
};
const ELEVATION_CLASS: Record<string, string> = {
  '--e1': 'shadow-sm',
  '--e2': 'shadow',
  '--e3': 'shadow-lg',
  '--e4': 'shadow-xl',
};

/**
 * ⚠️ **The one transcription in this file, and it is deliberately small.** The
 * design names an ELEMENT (*"toast"*); only a person can say which file renders
 * it. ⛔ **Everything else — which token, which value — is read from the
 * document**, so a scale change fails here rather than being silently absorbed.
 */
const SURFACES: { element: string; file: string; label: string }[] = [
  { element: 'toast', file: join('components', 'ui', 'toast.tsx'), label: 'Toast' },
  { element: 'dialog', file: join('components', 'ui', 'dialog.tsx'), label: 'Dialog' },
  { element: 'card', file: join('components', 'ui', 'card.tsx'), label: 'Card' },
];

function assignments(array: 'radii' | 'elevation'): { token: string; use: string }[] {
  const text = screenDocument(SYSTEM);
  const start = text.indexOf(`${array}: [`);
  if (start < 0) throw new Error(`no ${array} array in ${SYSTEM}`);
  const region = text.slice(start, start + 1600);
  const out = [...region.matchAll(/token:\s*'([^']*)'[^}]*?use:\s*'([^']*)'/g)].map((m) => ({
    token: m[1] ?? '',
    use: m[2] ?? '',
  }));
  if (out.length === 0) throw new Error(`parsed no ${array} rows from ${SYSTEM}`);
  return out;
}

/**
 * ⚡ The token the design assigns to an element, by reading the `use` prose.
 *
 * 🔴 **It matches a LIST ITEM, never a substring, and that distinction is not
 * cosmetic.** ⛔ **`--e1`'s use is *"Cards, tables, panels, page headers"* and
 * `Flush`'s is *"Nested groups inside a card. The only shadowless plane."*** —
 * **a substring search finds `card` in BOTH** and returned *border only* for
 * `Card`, which would have asserted that a card has no shadow. ✅ **Splitting
 * the first clause on commas excludes the sentence and keeps the list.**
 */
function tokenFor(array: 'radii' | 'elevation', element: string): string | undefined {
  return assignments(array).find((row) => {
    const listed = (row.use.split('.')[0] ?? '').split(',').map((item) => item.trim().toLowerCase());
    return listed.some((item) => item === element || item === `${element}s`);
  })?.token;
}

describe('📁 shared surfaces carry the radius and elevation the design assigns them', () => {
  for (const { element, file, label } of SURFACES) {
    it(`${label} — §05 radius and §06 elevation, both read from the design`, () => {
      const radius = tokenFor('radii', element);
      const elevation = tokenFor('elevation', element);
      expect(radius, `§05 names ${element}`).toBeDefined();
      expect(elevation, `§06 names ${element}`).toBeDefined();

      // ⚠️ Comments stripped — this file's own docblocks quote the wrong values
      // as the ones that were FIXED, and a guard that reads them is a guard
      // that reports its own history as a defect.
      const source = readFileSync(join(process.cwd(), file), 'utf8')
        .replace(/\/\*[\s\S]*?\*\//g, '')
        .replace(/^\s*\/\/.*$/gm, '');

      const wantRadius = RADIUS_CLASS[radius ?? ''] ?? 'UNMAPPED';
      const wantElevation = ELEVATION_CLASS[elevation ?? ''] ?? 'UNMAPPED';
      // ⛔ **Word-bounded**: `rounded` must not be satisfied by `rounded-lg`,
      // and `shadow` must not be satisfied by `shadow-sm`.
      expect(source, `${label} is ${wantRadius} (${radius})`).toMatch(
        new RegExp(`\\b${wantRadius}\\b`),
      );
      expect(source, `${label} is ${wantElevation} (${elevation})`).toMatch(
        new RegExp(`\\b${wantElevation}\\b`),
      );
    });
  }

  it('📁 the dialog scrim is §12’s 24%-ink, with no blur', () => {
    const prose = screenDocument(SYSTEM).replace(/<[^>]+>/g, ' ');
    const stated = /(\d+)%-ink scrim/.exec(prose)?.[1];
    expect(stated, '§12 states a scrim percentage').toBeDefined();

    const dialog = readFileSync(join(process.cwd(), 'components', 'ui', 'dialog.tsx'), 'utf8')
      .replace(/\/\*[\s\S]*?\*\//g, '')
      .replace(/^\s*\/\/.*$/gm, '');
    expect(dialog).toContain(`backdrop:bg-backdrop/${stated}`);
    // 📁 *"with no blur"* — stated in §12 and again in §16's dialog row.
    expect(dialog).not.toMatch(/backdrop-blur/);
  });
});
