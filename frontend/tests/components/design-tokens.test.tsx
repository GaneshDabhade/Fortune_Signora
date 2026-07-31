/**
 * AC-15 — Design System Stability.
 *
 * These assert the property that makes a design system worth having: that
 * a theme change is a token edit, not a sweep through every component.
 *
 * The check is structural rather than visual. A screenshot test would
 * catch a colour changing; only this catches a component *hardcoding* one,
 * which is the thing that makes the next colour change expensive.
 */
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

const UI_DIR = join(process.cwd(), 'components', 'ui');
const SHELL_DIR = join(process.cwd(), 'components', 'shell');
const FEEDBACK_DIR = join(process.cwd(), 'components', 'feedback');
/** **Added at M12.2.** These compose *from* the design system rather than
 * belonging to it, and were therefore outside this check while there were two
 * of them. A third made the omission worth closing: the rule that a theme
 * change is a token edit is not weaker for a component that renders a buying
 * score than for one that renders a button. */
const INTELLIGENCE_DIR = join(process.cwd(), 'components', 'intelligence');

function sourceFiles(dir: string): { name: string; source: string }[] {
  return readdirSync(dir)
    .filter((file) => file.endsWith('.tsx') || file.endsWith('.ts'))
    .map((file) => ({
      name: `${dir.split('/').pop()}/${file}`,
      source: readFileSync(join(dir, file), 'utf8'),
    }));
}

const ALL_COMPONENTS = [
  ...sourceFiles(UI_DIR),
  ...sourceFiles(SHELL_DIR),
  ...sourceFiles(FEEDBACK_DIR),
  ...sourceFiles(INTELLIGENCE_DIR),
];

// Tailwind's default palette. A shared component reaching for any of these
// has pinned a colour that a theme swap cannot reach.
const PALETTE_UTILITY =
  /\b(?:bg|text|border|ring|fill|stroke|from|via|to)-(?:slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-\d{2,3}\b/;

const HEX_COLOUR = /#[0-9a-fA-F]{3,8}\b/;
const RAW_COLOUR_FUNCTION = /\b(?:rgba?|hsla?)\(\s*\d/;

describe('components consume design tokens', () => {
  it.each(ALL_COMPONENTS)('$name uses no hardcoded palette utility', ({ source }) => {
    const match = PALETTE_UTILITY.exec(source);

    expect(
      match?.[0] ?? null,
      'Use a semantic token (bg-surface, text-content-muted, border-border) instead. ' +
        'A palette utility survives a theme change unaltered, which is exactly the bug.',
    ).toBeNull();
  });

  it.each(ALL_COMPONENTS)('$name uses no literal colour value', ({ source }) => {
    expect(HEX_COLOUR.test(source), 'hex colour found').toBe(false);
    expect(RAW_COLOUR_FUNCTION.test(source), 'literal rgb()/hsl() found').toBe(false);
  });

  it('the token set is defined in exactly one place', () => {
    const css = readFileSync(join(process.cwd(), 'app', 'globals.css'), 'utf8');

    // Every semantic colour must have both a light and a dark value. A
    // token defined only in `:root` silently keeps its light value in dark
    // mode, which is how "mostly dark" themes happen.
    const light = css.slice(css.indexOf(':root {'), css.indexOf("[data-theme='dark']"));
    const dark = css.slice(css.indexOf("[data-theme='dark']"));

    const names = [...light.matchAll(/--color-([a-z-]+):/g)].map((m) => m[1]);
    expect(names.length).toBeGreaterThan(10);

    const missing = names.filter((name) => !dark.includes(`--color-${name}:`));
    expect(missing, 'tokens with no dark-theme value').toEqual([]);
  });
});

describe('theme switching requires no component change', () => {
  it('no component reads the active theme', () => {
    // Only the toggle itself may know a theme exists. Any other component
    // branching on it would need editing when a third theme is added.
    const readers = ALL_COMPONENTS.filter(
      ({ name, source }) =>
        name !== 'shell/theme-toggle.tsx' && source.includes('useTheme'),
    );

    expect(readers.map((r) => r.name)).toEqual([]);
  });

  it('no component uses a dark: variant', () => {
    // A `dark:` variant is a component encoding theme knowledge. Tokens
    // make it unnecessary: the value changes underneath the same class.
    // `dark:bg-x` (Tailwind variant, no space) rather than `dark: 'Dark'`
    // (object key, space). The looser form flagged the theme toggle's own
    // label map, which is not a styling decision at all.
    const offenders = ALL_COMPONENTS.filter(({ source }) =>
      /\bdark:[a-z[-]/.test(source),
    );

    expect(offenders.map((o) => o.name)).toEqual([]);
  });
});
