/**
 * **TASK-478 — Design System v2 slice 3: the canonical set, from the design's
 * own enumeration.**
 *
 * ### The row this replaces asserted a number nothing could check
 *
 * TASK-448's third slice read *"the eighteen canonical components"*, and
 * [C-230](../../../docs/LANE_COORDINATION.md) held it because **no document in
 * the repository enumerated which eighteen.** The correction is not a better
 * list — it is that **the design enumerates itself**: nineteen sections, each
 * carrying a `data-screen-label`, most of them foundations rather than
 * components. ⛔ **The old cell was wrong on kind as well as on count.**
 *
 * ### So this file reads the design instead of restating it
 *
 * ⚡ **Every expectation below is derived from the snapshot at run time.**
 * [D-137](../../../docs/DECISION_REGISTER.md) forbids a copied specification,
 * an exported checklist and an intermediate implementation guide — **and a
 * list of component names typed into this file would be all three**, with the
 * usual consequence: the copy is the one somebody reads, and it is the one
 * that drifts.
 *
 * **What that buys is a test that can fail for the right reason.** When the
 * design gains an overlay, this file fails without being edited. A hand-written
 * list would have passed, which is [§2](../../../CLAUDE.md)'s *guard that
 * cannot fail* — and the reason TASK-448's third slice was stuck for two days.
 */
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import { KEY_MAP } from '@/components/ui/command-palette';
import * as canonical from '@/components/ui';

const SNAPSHOT = join(
  process.cwd(),
  '..',
  'docs',
  'design-snapshot',
  'screens',
  'Fortune Signora Design System v2.dc.html',
);

const design = readFileSync(SNAPSHOT, 'utf8');

/** The design's own section labels, in document order. */
function sections(): string[] {
  return [...design.matchAll(/data-screen-label="([^"]*)"/g)].map((m) => m[1] as string);
}

const ENTITIES: Record<string, string> = { amp: '&', lt: '<', gt: '>', quot: '"', '#39': "'" };
const unescape = (text: string): string =>
  text.replace(/&(amp|lt|gt|quot|#39);/g, (_, name: string) => ENTITIES[name] as string);

/** The raw markup of one section, from its label to the next section's. */
function markup(label: string): string {
  const all = sections();
  const start = design.indexOf(`data-screen-label="${label}"`);
  const after = all
    .slice(all.indexOf(label) + 1)
    .map((next) => design.indexOf(`data-screen-label="${next}"`))
    .find((offset) => offset > start);
  return design.slice(start, after ?? design.length);
}

/** One section's prose, tags stripped. The design is a rendered document, so
 * its sentences are the specification and the markup is not. */
function prose(label: string): string {
  return unescape(markup(label).replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' '));
}

/**
 * A section's own `<h2>`.
 *
 * ⚠️ **The `data-screen-label` is not the heading, and §13 is where that
 * matters**: it is labelled *"13 States"* and headed *"Empty, loading &
 * error"*. **The label names the section; the heading enumerates it** — so a
 * check about what a section contains must read the heading.
 */
function heading(label: string): string {
  const found = /<h2[^>]*>([\s\S]*?)<\/h2>/.exec(markup(label));
  expect(found, `${label} has no <h2> to read its enumeration from`).not.toBeNull();
  return unescape((found?.[1] as string).replace(/<[^>]+>/g, '').trim());
}

describe('the design enumerates itself', () => {
  it('carries nineteen labelled sections, which is where the count comes from', () => {
    // **The number is read, never asserted from memory.** This is the exact
    // check that would have refused the "eighteen canonical components" cell.
    expect(sections()).toHaveLength(19);
  });

  it('numbers its sections from 01, so the order in the file is the order in the design', () => {
    const numbers = sections().map((label) => Number(label.slice(0, 2)));
    expect(numbers).toEqual(Array.from({ length: 19 }, (_, i) => i + 1));
  });
});

/**
 * §12 is the section that names its members in one sentence — *"Dialog,
 * drawer, palette and toast share one language"* — which makes it the one
 * place a set can be extracted rather than assumed.
 */
describe('§12 Overlays — every member of the language the design names exists', () => {
  const overlays = (): string[] => {
    const sentence = /([A-Za-z]+(?:,\s*[a-z]+)*\s+and\s+[a-z]+)\s+share one language/.exec(
      prose('12 Overlays'),
    );
    expect(sentence, 'the design no longer states the overlay set in one sentence').not.toBeNull();
    return (sentence?.[1] as string)
      .split(/,\s*|\s+and\s+/)
      .map((word) => word.trim().toLowerCase());
  };

  it('names four overlays', () => {
    expect(overlays()).toEqual(['dialog', 'drawer', 'palette', 'toast']);
  });

  it.each(['dialog', 'drawer', 'palette'])(
    'the canonical set exports a component for %s',
    (member) => {
      // `toast` is deliberately excluded from this table and checked below:
      // it lives in `components/feedback`, and moving it is not this slice's.
      const exported = Object.keys(canonical).map((name) => name.toLowerCase());
      expect(
        exported.some((name) => name.includes(member.replace('palette', 'commandpalette'))),
        `§12 names "${member}" and the canonical set exports nothing for it`,
      ).toBe(true);
    },
  );

  it('toast is IN components/ui, where §12 groups it', () => {
    /**
     * ⚡ **This test previously pinned the misplacement**, and its own words
     * said why that was honest: *"relocating a live component is a change to
     * every caller — not a design-system slice."*
     *
     * ✅ **[TASK-1449](../../../docs/BACKLOG.md) is that slice**, so the fact
     * it kept true has changed and the assertion moves with it. ⛔ **Re-aimed
     * rather than deleted** — 📁 [§20c](../../../CLAUDE.md): *"a genuinely new
     * component belongs in `components/ui` with its tokens and its test."*
     */
    const toast = readFileSync(join(process.cwd(), 'components', 'ui', 'toast.tsx'), 'utf8');
    expect(toast).toContain('export function ToastProvider');
    expect(existsSync(join(process.cwd(), 'components', 'feedback', 'toast.tsx'))).toBe(false);
  });

  it('the shared plane is a token, because the design gives one radius for all four', () => {
    // §12: "16px radius, hairline border, --e4". The scale stopped at 12px
    // before this slice, so the only way to render the plane was an
    // arbitrary value — precisely what slice 1 spent thirty edits removing.
    expect(prose('12 Overlays')).toMatch(/16px radius/);

    const css = readFileSync(join(process.cwd(), 'app', 'globals.css'), 'utf8');
    expect(css, '--radius-xl is not declared').toContain('--radius-xl: 1rem;');

    for (const file of ['drawer.tsx', 'command-palette.tsx']) {
      const source = readFileSync(join(process.cwd(), 'components', 'ui', file), 'utf8');
      expect(source, `${file} does not use the shared plane`).toMatch(/rounded-xl/);
      expect(source, `${file} hardcodes a radius`).not.toMatch(/rounded-\[/);
    }
  });
});

/**
 * §13's title is its enumeration — *"Empty, loading & error"* — so the three
 * are read off the label rather than out of the prose.
 */
describe('§13 States — all three states the section titles exist', () => {
  const states = (): string[] => {
    const label = sections().find((s) => s.startsWith('13')) as string;
    return heading(label)
      .split(/,\s*|\s*&\s*/)
      .map((word) => word.trim().toLowerCase().split(' ')[0] as string);
  };

  it('names empty, loading and error', () => {
    expect(states()).toEqual(['empty', 'loading', 'error']);
  });

  it('exports a component for each', () => {
    expect(canonical.EmptyState, 'empty').toBeTypeOf('function');
    expect(canonical.Skeleton, 'loading').toBeTypeOf('function');
    expect(canonical.ErrorState, 'error').toBeTypeOf('function');
  });

  it('the error state keeps a correlation id and copies it, which §13 requires', () => {
    expect(prose('13 States')).toMatch(/copyable correlation ID/i);

    const source = readFileSync(
      join(process.cwd(), 'components', 'ui', 'error-state.tsx'),
      'utf8',
    );
    // Copyable, not merely rendered. `clipboard.writeText` is the difference
    // between an id an engineer receives correctly and one they retype.
    expect(source).toMatch(/clipboard\.writeText/);
    // And the failure path exists: a swallowed copy failure produces a
    // support ticket carrying whatever was in the clipboard before.
    expect(source).toMatch(/Copy failed/);
  });

  it('an error boundary is not the error state, and both exist', () => {
    /**
     * ⚠️ **Re-pointed by [TASK-1429](../../../docs/BACKLOG.md), and the
     * PROPERTY is unchanged.** This read `components/feedback/error-boundary.tsx`,
     * which that row retired: its five call sites now render through
     * `RegionBoundary` and the ladder. ⛔ **The distinction it guards is what
     * matters and it still holds** — **a boundary is the MECHANISM that
     * catches a throw; an error state is the PRESENTATION** — so the check
     * follows the mechanism to its new file rather than being deleted with the
     * old one.
     */
    const boundary = readFileSync(
      join(process.cwd(), 'components', 'ui', 'region-boundary.tsx'),
      'utf8',
    );
    expect(boundary).toMatch(/class RegionBoundary/);
    expect(canonical.ErrorState).toBeTypeOf('function');

    // 🔴 **And the mechanism must still not write its own copy.** The retired
    // boundary did, which is why four surfaces said four different things.
    // `StatedAbsence` owns the sentence; this file may not grow a second one.
    expect(boundary).toMatch(/StatedAbsence/);
  });
});

/**
 * §12 states the palette's key map in the design itself. That makes it a
 * specification rather than an implementation detail, and therefore checkable.
 */
/**
 * §14 is the one section that states a prohibition, and a prohibition is the
 * cheapest thing in a design system to lose.
 */
describe('§14 AI system — the reserved hue is actually reserved', () => {
  it('the design reserves it, in those words', () => {
    const text = prose('14 AI system');
    expect(text).toMatch(/reserved hue/);
    expect(text).toMatch(/Nothing else in the product may use that combination/);
  });

  it('the hue is a token with both themes, like every other role', () => {
    const css = readFileSync(join(process.cwd(), 'app', 'globals.css'), 'utf8');
    const light = css.slice(css.indexOf(':root {'), css.indexOf("[data-theme='dark']"));
    const dark = css.slice(css.indexOf("[data-theme='dark']"));
    for (const token of ['--color-ai:', '--color-ai-subtle:']) {
      expect(light, `${token} missing from the light theme`).toContain(token);
      expect(dark, `${token} missing from the dark theme`).toContain(token);
    }
  });

  it('nothing outside the AI grammar uses the reserved pairing', () => {
    // **This is what makes "reserved" true rather than aspirational.** The
    // pairing §14 names is the hue *and* its tint field; a component reaching
    // for `bg-ai-subtle`/`text-ai` to mean "notice" would quietly retire the
    // one distinction the section exists to keep — whether a machine wrote
    // what you are reading.
    // ⚡ **`table.tsx` joined the AI grammar with [TASK-1452](../../../docs/BACKLOG.md),
    // and it meets this test's own criterion rather than being excused from
    // it.** 📁 §11 rule ④: the summary row is *"tinted with the intelligence
    // hue"* — and what it summarises is machine-written, which is the exact
    // distinction the sentence above says the pairing keeps. ⛔ **Only the
    // summary row uses it**; no data cell, header or selection state does.
    const allowed = new Set(['badge.tsx', 'confidence.tsx', 'table.tsx']);
    const dir = join(process.cwd(), 'components', 'ui');
    const offenders = readdirSync(dir)
      .filter((file) => file.endsWith('.tsx') && !allowed.has(file))
      .filter((file) => /\b(?:bg|text|border|ring)-ai\b|-ai-subtle\b/.test(
        readFileSync(join(dir, file), 'utf8'),
      ));

    expect(
      offenders,
      'the reserved hue is being used outside the AI grammar §14 defines',
    ).toEqual([]);
  });

  it('confidence is legible without the pips, because §17 says decoration carries nothing', () => {
    const source = readFileSync(
      join(process.cwd(), 'components', 'ui', 'confidence.tsx'),
      'utf8',
    );
    expect(prose('17 Accessibility')).toMatch(/nothing depends on them to be understood/);
    // The pips are hidden and the sentence is the value — the inverse would
    // render a figure a screen reader cannot report.
    expect(source).toMatch(/aria-hidden/);
    expect(source).toMatch(/Confidence \$\{filled\} of \$\{SCALE\}/);
  });
});

describe('§12 — the palette binds the keys the design names', () => {
  it('the design states the map', () => {
    const text = prose('12 Overlays');
    expect(text).toMatch(/↑↓ navigate/);
    expect(text).toMatch(/↵ open/);
    expect(text).toMatch(/⌘↵ open in panel/);
  });

  it('every hint the footer renders is a key the handler binds', () => {
    const source = readFileSync(
      join(process.cwd(), 'components', 'ui', 'command-palette.tsx'),
      'utf8',
    );
    // **This is the anti-drift check.** The legend and the switch are one
    // table; if somebody deletes the modifier branch, the hint promising
    // "⌘↵ open in panel" becomes a false claim and this fails.
    const handled = source.slice(source.indexOf('handleKeyDown'));
    for (const entry of KEY_MAP) {
      for (const key of entry.key.split('/')) {
        const token = key.replace('Meta+', '');
        expect(handled, `${entry.hint} is rendered but ${key} is not handled`).toContain(
          `'${token}'`,
        );
      }
    }
    expect(handled, '⌘↵ is promised but no modifier is read').toMatch(
      /metaKey \|\| event\.ctrlKey/,
    );
  });

  it('the palette does not filter, because §12 says it answers rather than matches', () => {
    const source = readFileSync(
      join(process.cwd(), 'components', 'ui', 'command-palette.tsx'),
      'utf8',
    );
    // A local `.filter` over items would silently discard a ranking the
    // caller computed — and "answers questions directly" means the result
    // set can come from somewhere substring matching cannot reach.
    const body = source.slice(source.indexOf('export function CommandPalette'));
    expect(body).not.toMatch(/items\.filter\(/);
  });
});
