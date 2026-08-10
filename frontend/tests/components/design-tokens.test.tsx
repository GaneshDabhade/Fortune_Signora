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
/** **Added at M12.3 (ADR-0033), and it found something.** This check scanned
 * `components/` and nothing else, so `app/(auth)` — **the first screen every
 * customer sees** — had been using `bg-white`, `border-slate-200` and
 * `text-slate-500` since M1.5, forbidden everywhere the check could reach.
 *
 * A rule with a gap in its enforcement is a rule the code eventually finds the
 * gap in. The authentication screens are now inside it. */
const AUTH_DIR = join(process.cwd(), 'app', '(auth)');
/** Tenancy-state UI. Composed from the design system on the same terms as
 * `components/intelligence/` — never added to it. */
const WORKSPACE_DIR = join(process.cwd(), 'components', 'workspace');
/** **Added 2026-08-03, and they are where [B-200](../../../docs/BUGS.md) lived
 * undetected.** Both compose from the design system, and both were outside
 * every assertion in this file — so 30 uses of a token that does not exist
 * accumulated across five files, one of them on the account brief.
 *
 * The omission was not a judgement that these directories mattered less. They
 * simply were not written down, which is the failure mode of any list a human
 * maintains: **it is correct on the day it is written and silently incomplete
 * every day after.** */
const INTEGRATIONS_DIR = join(process.cwd(), 'components', 'integrations');
const TIMELINE_DIR = join(process.cwd(), 'components', 'timeline');
const COMMERCIAL_DIR = join(process.cwd(), 'components', 'commercial');
/** The application's own routes, on the same reasoning as `app/(auth)` above:
 * `settings/connections` carried four of B-200's thirty. */
const APP_DIR = join(process.cwd(), 'app', '(app)');

function sourceFiles(dir: string, prefix?: string): { name: string; source: string }[] {
  const label = prefix ?? (dir.split('/').pop() as string);
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name);
    // Route segments are directories, so this walks rather than listing.
    if (entry.isDirectory()) return sourceFiles(path, `${label}/${entry.name}`);
    if (!entry.name.endsWith('.tsx') && !entry.name.endsWith('.ts')) return [];
    return [{ name: `${label}/${entry.name}`, source: readFileSync(path, 'utf8') }];
  });
}

const ALL_COMPONENTS = [
  ...sourceFiles(UI_DIR),
  ...sourceFiles(SHELL_DIR),
  ...sourceFiles(FEEDBACK_DIR),
  ...sourceFiles(INTELLIGENCE_DIR),
  ...sourceFiles(AUTH_DIR, '(auth)'),
  ...sourceFiles(WORKSPACE_DIR),
  ...sourceFiles(INTEGRATIONS_DIR),
  ...sourceFiles(TIMELINE_DIR),
  ...sourceFiles(COMMERCIAL_DIR),
  ...sourceFiles(APP_DIR, '(app)'),
];

/**
 * The colour names this repository actually defines, read from the config
 * rather than restated here.
 *
 * **Restating them would make this file the second authoritative list**, and
 * the check would then pass against its own copy while the config said
 * something else (§2 — truth has one authoritative representation).
 */
function definedColours(): { names: Set<string>; roots: Set<string> } {
  const config = readFileSync(join(process.cwd(), 'tailwind.config.ts'), 'utf8');
  const start = config.indexOf('colors: {');
  const block = config.slice(config.indexOf('\n', start) + 1, config.indexOf('borderRadius:'));

  const names = new Set<string>();
  const roots = new Set<string>();
  let root: string | null = null;

  for (const raw of block.split('\n')) {
    const line = raw.trim();
    const opens = /^([A-Za-z]+):\s*\{$/.exec(line);
    if (opens?.[1]) {
      root = opens[1];
      names.add(root);
      roots.add(root);
      continue;
    }
    if (line.startsWith('}')) {
      root = null;
      continue;
    }
    const leaf = /^([A-Za-z]+):\s*'rgb\(/.exec(line);
    if (!leaf?.[1]) continue;
    if (root === null) {
      names.add(leaf[1]);
      roots.add(leaf[1]);
    } else if (leaf[1] !== 'DEFAULT') {
      names.add(`${root}-${leaf[1]}`);
    }
  }
  return { names, roots };
}

const COLOUR_PREFIX = 'bg|text|border|ring|fill|stroke|divide|outline|from|via|to';

/** A `-foreground` name is shadcn's vocabulary, and this repository does not
 * use it — the config defines `content`, `content-muted`, `content-subtle`
 * and `content-inverted`, and no `foreground` at all. */
const FOREGROUND_TOKEN = new RegExp(`\\b(?:${COLOUR_PREFIX})-(?:[a-z]+-)*foreground\\b`);

const COLOUR_UTILITY = new RegExp(`\\b(?:${COLOUR_PREFIX})-([a-z]+(?:-[a-z]+)*)\\b`, 'g');

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

  /**
   * **The opposite defect from the two above, and nothing could see it.**
   *
   * Those catch a component *pinning* a colour a theme swap cannot reach.
   * This catches one naming a colour that **does not exist** — an undefined
   * utility generates no CSS at all, so the element silently inherits and the
   * text renders in the primary colour. [B-200](../../../docs/BUGS.md): 30
   * uses across five files, every gate green throughout.
   *
   * **A wrong colour is visible. No colour is not** — it looks like a design
   * decision somebody made, which is why it survived a repository-wide
   * customer-experience audit and three product reviews.
   */
  it.each(ALL_COMPONENTS)('$name names no colour that does not exist', ({ source }) => {
    expect(
      FOREGROUND_TOKEN.exec(source)?.[0] ?? null,
      'The `-foreground` names are shadcn\'s convention and resolve to nothing here. ' +
        'Secondary text is `text-content-muted`; quieter still is `text-content-subtle`.',
    ).toBeNull();

    const { names, roots } = definedColours();
    const unresolvable = [...source.matchAll(COLOUR_UTILITY)]
      .map((match) => match[1])
      .filter((name): name is string => name !== undefined)
      .filter((name) => roots.has(name.split('-')[0] as string) && !names.has(name));

    expect(
      [...new Set(unresolvable)],
      'A variant of a defined colour that the config does not declare.',
    ).toEqual([]);
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

/**
 * **The same rule as colour, applied to the two scales that did not have it —
 * TASK-448.**
 *
 * `design-tokens.test.tsx` has always asserted that a *theme* change is a
 * token edit. It said nothing about type or radius, and the code found the
 * gap exactly as the file's own header predicts: **fifteen arbitrary
 * `text-[…]` values** and **fifteen uses of `rounded-md`, a step no token
 * declared**, resolving to a Tailwind default nothing controlled.
 *
 * **So a colour change was one edit and a radius change was a sweep**, which
 * is the difference this file exists to remove.
 */
describe('the type and radius scales are tokens too', () => {
  /** An arbitrary value is to a scale what a hex colour is to the palette:
   * correct today, and invisible to whoever changes the scale tomorrow. */
  const ARBITRARY_TYPE = /\btext-\[/;
  const ARBITRARY_RADIUS = /\brounded-\[/;

  it.each(ALL_COMPONENTS)('$name uses no arbitrary type size', ({ source }) => {
    expect(
      ARBITRARY_TYPE.test(source),
      'an arbitrary text-[…] survives a type-scale change unaltered, which is the bug',
    ).toBe(false);
  });

  it.each(ALL_COMPONENTS)('$name uses no arbitrary radius', ({ source }) => {
    expect(ARBITRARY_RADIUS.test(source), 'arbitrary rounded-[…] found').toBe(false);
  });

  it('every type size a component uses is a declared token', () => {
    /** **Membership, not merely absence of arbitraries.** Tailwind's own
     * scale still resolves — `extend` merges — so a component could reach
     * `text-3xl` and no token would control it. This is what stops that. */
    const declared = declaredScale('fontSize');
    const used = new Set<string>();
    for (const { source } of ALL_COMPONENTS) {
      for (const [, step] of source.matchAll(/\btext-([a-z0-9]+)\b/g)) {
        used.add(step as string);
      }
    }
    // **`text-` is three utilities wearing one prefix**: size, colour and
    // alignment. Only the first is this check's business — the palette check
    // above governs colour, and alignment has no scale to belong to. So the
    // declared colour tokens, Tailwind's colour keywords and the alignment
    // words are removed before what is left is held to the type scale.
    const colours = definedColours().names;
    const KEYWORDS = /^(current|inherit|transparent|left|right|center|justify|start|end|wrap|nowrap|balance|pretty|ellipsis|clip)$/;
    const sizes = [...used].filter(
      (step) => !colours.has(step) && !KEYWORDS.test(step),
    );

    expect(sizes.filter((step) => !declared.includes(step))).toEqual([]);
  });

  it('every radius a component uses is a declared token', () => {
    const declared = [...declaredScale('borderRadius'), 'full', 'none'];
    const used = new Set<string>();
    for (const { source } of ALL_COMPONENTS) {
      for (const [, step] of source.matchAll(/\brounded-([a-z0-9]+)\b/g)) {
        used.add(step as string);
      }
    }

    expect([...used].filter((step) => !declared.includes(step))).toEqual([]);
  });

  it('both scales are defined in exactly one place', () => {
    // The same property the colour set is held to: a second definition is a
    // second thing to edit, and the one nobody edits is the one that drifts.
    const css = readFileSync(join(process.cwd(), 'app', 'globals.css'), 'utf8');
    for (const step of declaredScale('fontSize')) {
      expect(css, `--text-${step} is not declared in globals.css`).toContain(`--text-${step}:`);
    }
  });
});

describe('control heights are tokens', () => {
  /** **The three components that render an interactive box.** Everything else
   * sizing itself with `h-…` is an icon or a layout, which have no control
   * scale to belong to — and a check that forbade every literal height would
   * be forbidding the wrong thing to catch the right one. */
  const CONTROLS = ['ui/button.tsx', 'ui/input.tsx', 'ui/select.tsx'];

  it.each(CONTROLS)('%s takes its height from a control token', (name) => {
    const { source } = ALL_COMPONENTS.find((c) => c.name === name)!;
    // `h-4` on the button's spinner is an icon, not the control box; the
    // check is that no *control size* is a literal, so it looks at the
    // size table rather than the whole file.
    const sizes = source.slice(source.indexOf('sm:'), source.indexOf('};'));
    expect(/\bh-\d/.test(sizes), `${name} hardcodes a control height`).toBe(false);
  });

  it('every control height is declared in exactly one place', () => {
    const css = readFileSync(join(process.cwd(), 'app', 'globals.css'), 'utf8');
    const config = readFileSync(join(process.cwd(), 'tailwind.config.ts'), 'utf8');
    const steps = [...config.matchAll(/'control-([a-z]+)':\s*'var\(--control-\1\)'/g)].map(
      ([, step]) => step as string,
    );

    expect(steps.length, 'no control steps are configured').toBeGreaterThan(0);
    for (const step of steps) {
      expect(css, `--control-${step} is not declared`).toContain(`--control-${step}:`);
    }
  });

  it('no control component invents a height of its own', () => {
    /** **The duplication this slice removed, asserted so it cannot return.**
     * `input` and `select` each hardcoded the middle step independently, so a
     * control-height change was three edits that had to agree — and nothing
     * would have noticed if they stopped agreeing. */
    const offenders = CONTROLS.filter((name) => {
      const { source } = ALL_COMPONENTS.find((c) => c.name === name)!;
      return /\bh-\d+\s+rounded/.test(source);
    });

    expect(offenders).toEqual([]);
  });
});

/** The steps Tailwind is configured with, read from the config rather than
 * restated here — a list copied into a test is a second source of truth. */
function declaredScale(key: 'fontSize' | 'borderRadius'): string[] {
  const config = readFileSync(join(process.cwd(), 'tailwind.config.ts'), 'utf8');
  const block = config.slice(config.indexOf(`${key}: {`));
  const body = block.slice(0, block.indexOf('},'));
  /**
   * ⚡ **Two declaration forms, one requirement** — TASK-1453.
   *
   * `xl: 'var(--text-xl)'` and
   * `title: ['var(--text-title)', { lineHeight: … }]` both declare a step.
   * 📁 **Design System v2 §04 gives every role FOUR numbers** — size, leading,
   * weight and tracking — **and a size-only entry silently drops three**, so
   * the roles this scale added use Tailwind's tuple form.
   *
   * ⛔ **The contract is NOT widened, only the parser** — **the value must
   * still be a `var(…)`.**
   *
   * ⚠️ **Fire-tested, and the first attempt proved the wrong thing.** Making
   * `title` a literal on its own changed nothing, because **the caller checks
   * only the steps a component actually USES** and nothing uses `text-title`
   * yet. **With a component using it, the literal fails and the `var()` form
   * passes** — so the guard bites on the property it claims, and the claim is
   * narrower than *any literal fails*.
   */
  return [...body.matchAll(/^\s*'?([A-Za-z0-9]+)'?:\s*\[?'var\(/gm)].map(([, name]) =>
    name === 'DEFAULT' ? '' : (name as string),
  );
}
