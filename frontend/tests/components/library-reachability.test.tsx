import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

import { SHELL_REGIONS } from '@/lib/shell/constitution';

/**
 * **A component nobody imports fails the suite** —
 * [TASK-1451](../../../docs/BACKLOG.md).
 *
 * ⚠️ **Separate from `reachability.test.tsx`, which is about ROUTES.** That
 * file asks *can a customer get to this screen*; this one asks *does anything
 * render this component at all*. **Two different absences, and the first
 * version of this row overwrote that file by taking its name.**
 *
 * ## 🔴 The class this detects has been found SEVEN times, every time by accident
 *
 * 📁 The entry engine ([500](../../../docs/architecture/500-authenticated-entry-reconciliation.md)
 * §1) · `lib/shell/scope.ts` · `lib/shell/top-bar.ts`, **six exports and zero
 * callers** · `lib/shell/rail.ts`, **six of nine** · `CommandPalette`
 * ([C-259](../../../docs/LANE_COORDINATION.md)) · `Confidence`
 * ([C-266](../../../docs/LANE_COORDINATION.md)) · `Drawer` and `CopyableId`
 * ([498](../../../docs/architecture/498-common-platform-audit.md) §5.1).
 *
 * ⛔ **Each was found by a separate accident** — a conformance sweep, a lane's
 * pre-claim read, an audit. ⚡ **A class found seven times by accident is a
 * class with no detector**, and the defect is silent by construction: **the
 * component is written, tested, reviewed and green, and the only missing thing
 * is that nothing renders it.**
 *
 * ## ⛔ It must not pass by deleting anything
 *
 * 📁 The row is explicit, and it is the whole design of this guard: **three of
 * the four are named by a shell rule or an AI pattern and are wanted.**
 * ✅ **So the allowlist requires a ROW ID per entry** — ⚡ **an orphan with a
 * row is scheduled; an orphan without one is a mistake**, and that distinction
 * is the only thing separating this from a test somebody silences.
 */

const UI = join(process.cwd(), 'components', 'ui');
// ⛔ `hooks/` does not exist in this repository — the first version listed it
// and the walk threw `ENOENT` before a single assertion ran.
const ROOTS = ['app', 'components', 'lib'];

/**
 * 🔴 **Every orphan names the row that will give it a caller.**
 *
 * ⛔ **Adding a name here without a row is the failure this test exists to
 * prevent** — and `it('every allowlisted orphan names a real row')` below
 * refuses one.
 */
const AWAITING_A_CALLER: Readonly<Record<string, string>> = {
  // 📁 Shell rule 07 depends on it; mounting it is TASK-1442's scope, which
  // C-259 closed on explicitly.
  CommandPalette: 'TASK-1442',
  // 📁 498 §5.1. Wanted by the utility panel.
  Drawer: 'TASK-1433',
  CopyableId: 'TASK-1409',
  // ⚠️ **The four below are this lane's own, built this turn**, and they are
  // listed rather than quietly excused. Each names the row that renders it.
  // 📁 §11's editable table — *"reps edit close dates and amounts dozens of
  // times a day"* — is the Deals screen, which does not exist.
  EditableCell: 'TASK-1452',
  // 📁 §08's record half; the migration is named in TASK-1446's own sweep.
  RecordHeader: 'TASK-1446',
  // 📁 The Executive Dashboard's metric cards and Reports draw these, and
  // TASK-1450 was explicit that it builds the primitives those two screens
  // need rather than a charting library.
  Sparkline: 'TASK-1450',
  BarSeries: 'TASK-1450',
};

/** ⚡ Components only. ⛔ `SCREAMING_CASE` constants are not components. */
function exportedComponents(): Map<string, string> {
  const found = new Map<string, string>();
  for (const file of readdirSync(UI)) {
    if (file === 'index.ts' || !/\.tsx?$/.test(file)) continue;
    const source = readFileSync(join(UI, file), 'utf8');
    for (const match of source.matchAll(/export (?:function|const) ([A-Za-z0-9_]+)/g)) {
      const name = match[1];
      if (name === undefined) continue;
      // A component is PascalCase and is not a constant.
      if (!/^[A-Z][a-zA-Z0-9]*$/.test(name)) continue;
      if (name === name.toUpperCase()) continue;
      found.set(name, file);
    }
  }
  return found;
}

function corpusOutsideTheLibrary(): string {
  const chunks: string[] = [];
  const walk = (dir: string) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const path = join(dir, entry.name);
      if (entry.isDirectory()) {
        if (entry.name === 'node_modules') continue;
        walk(path);
        continue;
      }
      if (!/\.tsx?$/.test(entry.name)) continue;
      if (path.startsWith(UI)) continue;
      chunks.push(readFileSync(path, 'utf8'));
    }
  };
  for (const root of ROOTS) walk(join(process.cwd(), root));
  return chunks.join('\n');
}

const COMPONENTS = exportedComponents();
const CORPUS = corpusOutsideTheLibrary();

describe('🔴 every component in the library is reachable, or scheduled', () => {
  it('⚡ the walk found the library, so nothing below is vacuous', () => {
    // ⛔ **Vacuity guard.** If the walk returned nothing, every assertion here
    // would pass over an empty library — which is exactly the shape of failure
    // this whole test exists to catch.
    expect(COMPONENTS.size).toBeGreaterThan(30);
    expect(CORPUS.length).toBeGreaterThan(10_000);
  });

  it('⛔ no component is orphaned without a row that will render it', () => {
    /**
     * 🔴 **The defect is silent by construction**: written, tested, reviewed,
     * green — and nothing renders it. ⚡ **This is the first thing in the
     * repository that can see it.**
     */
    const orphans = [...COMPONENTS.entries()]
      .filter(([name]) => !new RegExp(`\\b${name}\\b`).test(CORPUS))
      .filter(([name]) => AWAITING_A_CALLER[name] === undefined)
      .map(([name, file]) => `${name} (${file})`);

    expect(
      orphans,
      'these components are complete and no customer can reach them — give them a caller, or list them with the row that will',
    ).toEqual([]);
  });

  it('⛔ every allowlisted orphan names a REAL row, so the list cannot become a silencer', () => {
    /**
     * ⚡ **This is what stops the allowlist being a way to switch the guard
     * off.** ⛔ **An orphan with a row is scheduled; an orphan without one is
     * a mistake** — and a row id that does not exist in the backlog is the
     * same thing as no row at all.
     */
    const backlog = readFileSync(join(process.cwd(), '..', 'docs', 'BACKLOG.md'), 'utf8');
    for (const [name, row] of Object.entries(AWAITING_A_CALLER)) {
      expect(row, `${name} is allowlisted without a row`).toMatch(/^TASK-\d+$/);
      expect(backlog, `${name} names ${row}, which is not in the backlog`).toContain(`### ${row} `);
    }
  });

  it('⛔ and the allowlist holds nothing that already has a caller', () => {
    /**
     * ⚠️ **An entry that has quietly gained a caller is a stale exemption**,
     * and a stale exemption is how an allowlist grows until it covers
     * everything. ✅ **The list shrinks on its own.**
     */
    const stale = Object.keys(AWAITING_A_CALLER).filter((name) =>
      new RegExp(`\\b${name}\\b`).test(CORPUS),
    );
    expect(stale, 'these are reachable now and should leave the allowlist').toEqual([]);
  });
});

describe('🔴 a declared shell region that nothing renders', () => {
  /**
   * 📁 **The row asks for the same check one level up**: `SHELL_REGIONS` names
   * regions, and **a region declared and never rendered is the same defect as
   * a component nobody imports** — the frame promising a place that does not
   * exist.
   *
   * ⚠️ **The first version grepped the shell for each region's NAME and
   * reported the two banner regions as missing.** ⛔ **That was the wrong
   * measurement**: `ShellBanners` renders both, and it does not contain the
   * strings `environment-banner` or `trial-banner`. ✅ **A region needs a
   * RENDERER, and the mapping is declared here** — so the check asks whether
   * the renderer is mounted rather than whether a word appears.
   */
  const RENDERED_BY: Readonly<Record<string, string>> = {
    'environment-banner': 'ShellBanners',
    'trial-banner': 'ShellBanners',
    'top-bar': 'TopBar',
  };

  /**
   * ⛔ **Held on rows this lane raised and Product Office sequenced**, each
   * for a stated reason rather than for effort: 📁
   * [TASK-1432](../../../docs/BACKLOG.md) — no module reads `scope.ts`, so
   * four chips would narrow nothing · [TASK-1433](../../../docs/BACKLOG.md) —
   * an empty 300px panel takes space from the screen in use.
   */
  const SCHEDULED: Readonly<Record<string, string>> = {
    'filter-strip': 'TASK-1432',
    'utility-panel': 'TASK-1433',
  };

  it('⛔ every region is either rendered or scheduled, and nothing is neither', () => {
    const unaccounted = SHELL_REGIONS.filter(
      (region) => RENDERED_BY[region] === undefined && SCHEDULED[region] === undefined,
    );
    expect(unaccounted, 'the constitution names these regions and nothing accounts for them').toEqual(
      [],
    );
  });

  it('✅ and each region with a renderer has that renderer MOUNTED in the shell', () => {
    // ⚡ **This is the half that can actually fail.** A mapping nobody checks
    // is a comment; asserting the component is mounted is the property.
    const shell = readFileSync(
      join(process.cwd(), 'components', 'shell', 'app-shell.tsx'),
      'utf8',
    );
    for (const [region, component] of Object.entries(RENDERED_BY)) {
      expect(shell, `${region} is rendered by ${component}, which the shell does not mount`).toContain(
        `<${component}`,
      );
    }
  });

  it('⛔ every scheduled region names a real row', () => {
    // Same rule as the component allowlist: scheduled means a row exists.
    const backlog = readFileSync(join(process.cwd(), '..', 'docs', 'BACKLOG.md'), 'utf8');
    for (const [region, row] of Object.entries(SCHEDULED)) {
      expect(backlog, `${region} names ${row}, which is not in the backlog`).toContain(`### ${row} `);
    }
  });
});
