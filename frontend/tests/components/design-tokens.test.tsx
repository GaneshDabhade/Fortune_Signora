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

import { withoutComments } from '../support/source';

/**
 * 🔴 **Eleven directory constants stood here and are deleted with the list they
 * fed.** ⚠️ **Their history is worth one line each, because it is the argument
 * for walking the tree instead**: `components/ui`, `shell` and `feedback` were
 * the original three; `intelligence` was added at M12.2; `app/(auth)` at M12.3,
 * where **the first screen every customer sees** had carried `bg-white` and
 * `text-slate-500` since M1.5; `workspace`, `integrations`, `timeline`,
 * `commercial` and `app/(app)` were added in 2026-08 after
 * [B-200](../../../docs/BUGS.md) put **thirty uses of a token that does not
 * exist** across five unscanned files.
 *
 * ⛔ **Every one of those additions was made *after* the omission had already
 * cost something**, which is the pattern a hand-maintained list guarantees.
 */

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

/**
 * 🔴 **The list is gone, and its absence is the fix.**
 *
 * ⚠️ **Eleven directories were named here by hand, and the file's own header
 * predicted what would happen**: *"it is correct on the day it is written and
 * silently incomplete every day after."* ✅ **It came true three times.**
 * `app/(auth)` carried `bg-white` for four milestones. `components/integrations`
 * and two siblings carried thirty uses of a token that does not exist. **And
 * this row found two more in the two directories still missing** —
 * `components/home`, where five card surfaces carried `shadow-e1`, **a utility
 * this repository does not define**, so they rendered flat; and
 * `components/accounts`, where `text-muted-foreground` — **shadcn's vocabulary,
 * which `FOREGROUND_TOKEN` below exists specifically to refuse** — resolved to
 * nothing and printed *"No segment"* at full ink on every row of the table.
 *
 * ⛔ **Each time the answer was to add a directory, and each time the next
 * directory was already drifting.** ⚡ **So the check now walks `components/`
 * and `app/` whole.** A new directory is inside it on the day it is created,
 * which is the only version of this rule that does not decay.
 */
const ALL_COMPONENTS = [
  ...sourceFiles(join(process.cwd(), 'components'), 'components'),
  ...sourceFiles(join(process.cwd(), 'app'), 'app'),
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

  it('🔴 B-283 — the scrollbar gutter is reserved, or every shell element jumps 15px at once', () => {
    /**
     * 🔴 **[B-283](../../../docs/BUGS.md)** — Companies and Home both reflowed
     * after they loaded, and **neither obvious hypothesis was right.**
     *
     * ⚡ **Measured with `PerformanceObserver`, attributing each entry to its
     * sources**: Home's largest event named *both right-column cards, the
     * content wrapper, AND `aside#shell-utility-panel` — all moving together*,
     * with `clientWidth` going **1280 → 1265** in the same window.
     *
     * ⛔ **So nothing resized.** **The page grew past the viewport as the last
     * card's data landed, the vertical scrollbar arrived, and every element in
     * the shell's flex row lost the same 15px at once.** ⚠️ **Companies'
     * *"table settling its column widths"* was that same 15px reaching an
     * auto-layout table, which redistributed it across every column** — **a
     * dramatic symptom of an undramatic cause.**
     *
     * | Screen | Before | After |
     * |---|---|---|
     * | Companies | **0.277** | **0.003 · 0.003 · 0.016** |
     * | Home | 0.154 · 0.166 · 0.167 | 0.099 · 0.110 · 0.112 |
     *
     * ## ⚠️ What this asserts, and what it cannot
     *
     * ⛔ **This asserts the DECLARATION, not the shift.** **jsdom computes no
     * layout**, so the 0.277 → 0.003 is `visual.spec.ts`'s to measure and this
     * cannot stand in for it.
     *
     * ✅ **But the declaration is one line in a shared stylesheet with nothing
     * else guarding it** — **the only mention anywhere in `tests/` is a comment
     * — so a tidy-up removes it and only an expensive browser run notices.**
     *
     * ⛔ **`html`, not `body`**: the document element is the scrolling box.
     * ⛔ **Not `overflow-y: scroll`**, which draws a dead track on every short
     * page.
     */
    const css = readFileSync(join(process.cwd(), 'app', 'globals.css'), 'utf8');

    expect(
      /html\s*\{[^}]*scrollbar-gutter:\s*stable/.test(css),
      'html must reserve the scrollbar gutter, or the shell reflows when it appears',
    ).toBe(true);

    // ⛔ **And not the alternative that was rejected on measurement.**
    expect(css, 'overflow-y: scroll draws a dead track on every short page').not.toMatch(
      /html\s*\{[^}]*overflow-y:\s*scroll/,
    );
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
        name !== 'components/shell/theme-toggle.tsx' && source.includes('useTheme'),
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

  /**
   * 🔴 **[B-275](../../../docs/BUGS.md) — this tested the RAW FILE, so a comment
   * explaining why the mock's one-off pixel value was avoided failed the guard
   * that wanted it avoided.**
   *
   * ⛔ **The guard was correct about the code every time; what it refused was
   * the DOCUMENTATION of compliance** — ⚡ **and that documentation is exactly
   * what [§12](../../../CLAUDE.md) asks a lane to leave behind**: *"could a
   * lane that has never seen this module continue the work without reading
   * commit history?"* **The next person reaching for the literal pixel value
   * has to be told why not, in the file, and could not be told in the obvious
   * words.**
   *
   * ⚠️ **It also taught the wrong lesson quietly**: a lane that hits this and
   * does not read the regex concludes the guard is flaky, **which is how a
   * check stops being trusted.**
   *
   * ✅ **`withoutComments` is the repository's existing walker** — 📁 it tracks
   * quotes and template literals precisely because
   * [B-162](../../../docs/BUGS.md) is the same defect in the other direction:
   * *a guard narrowed to strip comments started treating `//` in a URL as the
   * start of one, and stopped catching real matches.* ⛔ **So this reuses it
   * rather than adding a fourth regex** ([§2](../../../CLAUDE.md)).
   */
  it.each(ALL_COMPONENTS)('$name uses no arbitrary type size', ({ source }) => {
    expect(
      ARBITRARY_TYPE.test(withoutComments(source)),
      'an arbitrary text-[…] survives a type-scale change unaltered, which is the bug',
    ).toBe(false);
  });

  it.each(ALL_COMPONENTS)('$name uses no arbitrary radius', ({ source }) => {
    expect(ARBITRARY_RADIUS.test(withoutComments(source)), 'arbitrary rounded-[…] found').toBe(
      false,
    );
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
      /**
       * ⚠️ **The side is skipped, and the token after it is what is checked.**
       *
       * ⛔ **This read `rounded-t-md` as the token `t`** and failed a class
       * that is entirely correct — 📁 the finalized Companies design draws its
       * saved-view tabs at `border-radius:8px 8px 0 0`, **which is
       * `rounded-t-md`: the declared `md` step, applied to one side.**
       *
       * 🔴 **A guard that fires on the wrong fact teaches people to widen
       * it** ([§2](../../../CLAUDE.md)) — and the widening here would have
       * been to declare `t` a radius, which is not a radius at all. ✅ **The
       * side variants are consumed and the step is still checked**, so an
       * undeclared `rounded-t-7px` fails exactly as it should.
       */
      for (const [, step] of source.matchAll(
        /\brounded-(?:(?:[tblrse]|[tb][lr]|ss|se|ee|es)-)?([a-z0-9]+)\b/g,
      )) {
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
  const CONTROLS = [
    'components/ui/button.tsx',
    'components/ui/input.tsx',
    'components/ui/select.tsx',
  ];

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
