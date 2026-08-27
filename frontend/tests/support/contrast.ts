/**
 * **WCAG contrast, computed from `app/globals.css` rather than tabulated.**
 *
 * ⛔ **A list of expected ratios would be a second representation of the
 * palette** ([§2](../../../CLAUDE.md)) and would go stale on the first token
 * edit — **which is the edit these checks exist to catch.** ✅ **The values are
 * read from the stylesheet and the ratio is computed**, so the check has no
 * opinion of its own.
 *
 * ⚡ **Extracted from `tests/unit/home-contrast.test.ts` when a second caller
 * arrived** — 📁 §17 `1.4.11`'s non-text pairs. ⛔ **Copying the helper would
 * have been two implementations of one arithmetic**, and the two would
 * eventually disagree about a rounding.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const CSS = readFileSync(join(process.cwd(), 'app', 'globals.css'), 'utf8');

/**
 * ⚡ **The dark block is `:root[data-theme='dark']`**, and the light values are
 * everything before it. ⛔ **Read positionally rather than by parsing CSS**: a
 * parser here would be a dependency, and the file's own structure is the
 * contract.
 */
const DARK_AT = CSS.indexOf(":root[data-theme='dark']");

export type Theme = 'light' | 'dark';

export function token(name: string, theme: Theme): [number, number, number] {
  const source = theme === 'light' ? CSS.slice(0, DARK_AT) : CSS.slice(DARK_AT);
  const matches = [...source.matchAll(new RegExp(`--color-${name}:\\s*([\\d\\s]+);`, 'g'))];
  const last = matches.at(-1);
  if (last === undefined) throw new Error(`--color-${name} has no ${theme} value`);
  const parts = last[1]!.trim().split(/\s+/).map(Number);
  return [parts[0]!, parts[1]!, parts[2]!];
}

/** WCAG 2.1 relative luminance. */
export function luminance([r, g, b]: [number, number, number]): number {
  const channel = (value: number) => {
    const v = value / 255;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
}

/** WCAG 2.1 contrast ratio, `(L1 + 0.05) / (L2 + 0.05)`. */
export function ratio(foreground: string, background: string, theme: Theme): number {
  const a = luminance(token(foreground, theme));
  const b = luminance(token(background, theme));
  const [light, dark] = a > b ? [a, b] : [b, a];
  return (light + 0.05) / (dark + 0.05);
}
