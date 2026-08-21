/**
 * **One instrument for reading the design snapshot's token layer.**
 *
 * ⛔ **Written 2026-08-21 after two lanes measured the same 35 documents and
 * got different numbers.** ⚡ **Two instruments that can disagree are worse
 * than one that is wrong**, because a disagreement gets argued instead of
 * fixed.
 *
 * ⚠️ **It lives here, not in `infra/`, and that is not a filing preference.**
 * 📁 **[D-022](../../../docs/DECISION_REGISTER.md) reserves `infra/`, the
 * `Makefile` and the environment profiles to Lane C** — *"Lane C's
 * responsibilities are formally expanded to include Platform Foundation work
 * that belongs to no product bounded context."* ⛔ **A new instrument there
 * from this lane is outside its Change Budget**, and 🔴 **a cross-lane file
 * with two owners is how a shared file starts drifting** — which is the exact
 * failure this module exists to prevent, arriving by the other door.
 * ✅ **Offered to Lane C for adoption as [C-1541](../../../docs/LANE_COORDINATION.md).**
 *
 * ## 🔴 The three errors it makes unrepeatable
 *
 * **① Reading ONE document and calling it the token layer.** ⛔ **This lane
 * ruled that `--ink-4`, `--ai-ink` and `--ai-line` were "mock chrome" and only
 * nine colour tokens were published** — 📁 **from the Design System document's
 * SUMMARY TABLE.** ✅ **The token layer is the `tokens()` block every screen
 * carries: 37 roles, zero disagreements across 35 files.** ⚠️ `Design System
 * v2.dc.html` does not declare `--pos-line`, `--warn-line` or `--risk-line` at
 * all; eighteen of the other screens do.
 *
 * **② Dropping a sparse role as noise.** ⛔ **QE carried `--brand-soft` (1 of
 * 35) and `--brand-strong` (2 of 35) through extraction and then reasoned them
 * away**, which inverted [B-1051](../../../docs/BUGS.md): `--color-accent-soft`
 * is **correct** in light because it implements `--brand-soft`, and wrong in
 * dark. ✅ **A role stated once is still a role**, so `documents` is reported
 * beside every value and is never used to filter.
 *
 * **③ Generalising a count from one population to another.** ⛔ **QE's *"106
 * tint-plus-line pairings"* is a real count of PANELS applied to BADGES**
 * without re-measuring — and badges are **166 borderless to 14 bordered**.
 * ✅ So every population-sensitive reading takes an explicit filter and
 * reports it.
 *
 * ⚠️ **This lane counted `--brand-tint → --brand-ink` at 55/55 and QE at
 * 66/74. Both are right** — one filtered to `fontSizeAtMost: 12.5` and the
 * other did not. **The conclusion was identical and the numbers were not**,
 * which is why the filter is a parameter instead of a habit.
 *
 * ## Usage
 *
 * ```
 * npx tsx tests/support/design-snapshot.ts tokens
 * npx tsx tests/support/design-snapshot.ts usage --role ai-ink
 * npx tsx tests/support/design-snapshot.ts pairings --max-font 12.5
 * npx tsx tests/support/design-snapshot.ts foreground --max-font 12.5
 * npx tsx tests/support/design-snapshot.ts focus
 * ```
 *
 * ⛔ **Read-only. It writes nothing and touches no snapshot file** — 📁
 * `docs/design-snapshot/MANIFEST.md` is Product Office's and its contents are
 * the implementation authority for every lane.
 */

import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

const SCREENS = join(__dirname, '..', '..', '..', 'docs', 'design-snapshot', 'screens');

export type Theme = 'light' | 'dark';
export const THEMES: readonly Theme[] = ['light', 'dark'];

/**
 * ⚡ **The two `Object.assign` payloads inside `tokens()`, in source order:
 * light, then dark.** Anchored on `'--bg'` because every block declares it and
 * nothing else in these files looks like this.
 */
const THEME_BLOCK = /\{[^{}]*'--bg':[^{}]*\}/g;
const DECLARATION = /'(--[a-z0-9-]+)'\s*:\s*'([^']*)'/g;
const STYLE_ATTR = /style="([^"]*)"/g;

export interface TokenTable {
  /** The value of each role, per theme. */
  readonly values: Record<Theme, Map<string, string>>;
  /**
   * ⚡ **How many documents declare each role.** ⛔ **Reported, never used to
   * filter** — see ② above.
   */
  readonly documents: Record<Theme, Map<string, number>>;
  /**
   * 🔴 **A disagreement is a finding, never a resolution.** ⛔ **Silently
   * taking the first value is how a snapshot refresh becomes invisible.**
   */
  readonly conflicts: readonly string[];
  readonly read: number;
}

function documents(): { name: string; text: string }[] {
  const files = readdirSync(SCREENS).filter((name) => name.endsWith('.dc.html'));
  if (files.length === 0) throw new Error(`no design documents under ${SCREENS}`);
  return files.sort().map((name) => ({ name, text: readFileSync(join(SCREENS, name), 'utf8') }));
}

export function tokenTable(): TokenTable {
  const values: Record<Theme, Map<string, string>> = { light: new Map(), dark: new Map() };
  const counts: Record<Theme, Map<string, number>> = { light: new Map(), dark: new Map() };
  const conflicts: string[] = [];
  let read = 0;

  for (const { name, text } of documents()) {
    const start = text.indexOf('tokens() {');
    if (start === -1) continue;
    const blocks = text.slice(start, start + 3200).match(THEME_BLOCK) ?? [];
    if (blocks.length !== 2) continue;
    read += 1;

    THEMES.forEach((theme, index) => {
      for (const [, role, value] of (blocks[index] ?? '').matchAll(DECLARATION)) {
        counts[theme].set(role!, (counts[theme].get(role!) ?? 0) + 1);
        const seen = values[theme].get(role!);
        if (seen === undefined) values[theme].set(role!, value!);
        else if (seen !== value) conflicts.push(`${theme} ${role}: ${seen} vs ${value} (${name})`);
      }
    });
  }

  return { values, documents: counts, conflicts, read };
}

/** Every inline `style="…"` declaration in the snapshot, in document order. */
export function styleDeclarations(): string[] {
  return documents().flatMap(({ text }) => [...text.matchAll(STYLE_ATTR)].map((m) => m[1]!));
}

export interface Population {
  /**
   * ⚡ **Restrict to badge-like elements.** ⛔ **A filter, not a default** —
   * see ③: the same query answers differently for panels and for badges, and
   * neither answer is wrong.
   */
  readonly fontSizeAtMost?: number;
  /** ⚡ Badge-like elements carry a radius; a tinted panel band need not. */
  readonly requireRadius?: boolean;
}

function inPopulation(declaration: string, population: Population): boolean {
  if (population.fontSizeAtMost !== undefined) {
    const size = /font-size:(\d+(?:\.\d+)?)px/.exec(declaration);
    if (size === null || Number(size[1]) > population.fontSizeAtMost) return false;
  }
  if (population.requireRadius === true && !declaration.includes('border-radius:')) return false;
  return true;
}

export interface Pairings {
  readonly bordered: Map<string, number>;
  readonly plain: Map<string, number>;
}

/** Tint fills, split by whether they carry a 1px border. */
export function tintPairings(population: Population = {}): Pairings {
  const bordered = new Map<string, number>();
  const plain = new Map<string, number>();

  for (const declaration of styleDeclarations()) {
    const fill = /background:var\((--[a-z0-9-]*-tint)\)/.exec(declaration);
    if (fill === null || !inPopulation(declaration, population)) continue;
    const edge = /border:1px solid var\((--[a-z0-9-]+)\)/.exec(declaration);
    const key = edge === null ? fill[1]! : `${fill[1]} + ${edge[1]}`;
    const bucket = edge === null ? plain : bordered;
    bucket.set(key, (bucket.get(key) ?? 0) + 1);
  }

  return { bordered, plain };
}

/** What colour the design puts ON each tint. */
export function tintForegrounds(population: Population = {}): Map<string, Map<string, number>> {
  const seen = new Map<string, Map<string, number>>();
  for (const declaration of styleDeclarations()) {
    const fill = /background:var\((--[a-z0-9-]*-tint)\)/.exec(declaration);
    const ink = /(?<!background-)color:var\((--[a-z0-9-]+)\)/.exec(declaration);
    if (fill === null || ink === null || !inPopulation(declaration, population)) continue;
    const inks = seen.get(fill[1]!) ?? new Map<string, number>();
    inks.set(ink[1]!, (inks.get(ink[1]!) ?? 0) + 1);
    seen.set(fill[1]!, inks);
  }
  return seen;
}

export interface RingReading {
  readonly ring: string;
  readonly total: number;
  /** ⚡ **The border beside it, or `null`** — which is the whole finding. */
  readonly paired: Map<string, number>;
}

/**
 * 🔴 **The query [B-1058](../../../docs/BUGS.md) turned on.**
 *
 * ⛔ **The ring alone reads as *"a tint ring, never an outline"*.** ⚡ **The
 * border beside it is what carries the contrast** — `--brand-tint` on the page
 * is about 1.06:1 and `--brand` is 8.33:1, so a ring without its border is not
 * an indicator at all.
 *
 * ⚠️ **It also separates the rings that are not focus, and the description
 * here is QE's correction of this lane's first guess.** 📁 **The six
 * `0 0 0 3px var(--surface)` are STATUS DOTS ON A TIMELINE RAIL** — drawn as
 * `position:absolute; left:-20px; top:4px; width:8px; height:8px;
 * border-radius:999px` — **not the avatar-stack overlap ring this file
 * originally named.** ⚡ **Same mechanism** (a ring in the backdrop's own
 * colour, cutting the shape out of what passes behind it), **different
 * furniture** — ✅ **and *status dot on a rail* is the checkable description,
 * which is why it is the one recorded.**
 *
 * 🔴 **Counting those six as focus is what made the design look like it had
 * four variants.** ✅ **Separated, it has ONE indicator — a paired border and
 * ring — in four status colourways, across 26 instances.**
 */
export function focusRings(): RingReading[] {
  const totals = new Map<string, number>();
  const paired = new Map<string, Map<string, number>>();

  for (const declaration of styleDeclarations()) {
    for (const match of declaration.matchAll(/box-shadow:0 0 0 (\d+)px var\((--[a-z0-9-]+)\)/g)) {
      const ring = `0 0 0 ${match[1]}px var(${match[2]})`;
      totals.set(ring, (totals.get(ring) ?? 0) + 1);
      const edge = /border:1px solid var\((--[a-z0-9-]+)\)/.exec(declaration);
      const label = edge === null ? '(no border)' : `border:1px solid var(${edge[1]})`;
      const byEdge = paired.get(ring) ?? new Map<string, number>();
      byEdge.set(label, (byEdge.get(label) ?? 0) + 1);
      paired.set(ring, byEdge);
    }
  }

  return [...totals.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([ring, total]) => ({ ring, total, paired: paired.get(ring) ?? new Map() }));
}

/** How many times a role is referenced, and in how many documents. */
export function roleUsage(role: string): { uses: number; documents: number; total: number } {
  const needle = `var(${role.startsWith('--') ? role : `--${role}`})`;
  let uses = 0;
  let seen = 0;
  const all = documents();
  for (const { text } of all) {
    const n = text.split(needle).length - 1;
    if (n > 0) {
      seen += 1;
      uses += n;
    }
  }
  return { uses, documents: seen, total: all.length };
}

/* ------------------------------------------------------------------ CLI -- */

function cli(argv: string[]): number {
  const [command, ...rest] = argv;
  const flag = (name: string): string | undefined => {
    const at = rest.indexOf(`--${name}`);
    return at === -1 ? undefined : rest[at + 1];
  };
  const maxFont = flag('max-font');
  const population: Population =
    maxFont === undefined ? {} : { fontSizeAtMost: Number(maxFont), requireRadius: true };
  const describe = maxFont === undefined ? 'every tinted surface' : `font-size <= ${maxFont}px`;

  switch (command) {
    case 'tokens': {
      const table = tokenTable();
      const roles = [...new Set([...table.values.light.keys(), ...table.values.dark.keys()])].sort();
      console.log(`${table.read} documents · ${roles.length} roles`);
      for (const role of roles) {
        const n = table.documents.light.get(role) ?? 0;
        const sparse = n === table.read ? '' : `  (${n}/${table.read})`;
        console.log(
          `${role.padEnd(16)}${(table.values.light.get(role) ?? '—').padEnd(12)}` +
            `${(table.values.dark.get(role) ?? '—').padEnd(12)}${n}${sparse}`,
        );
      }
      if (table.conflicts.length > 0) {
        console.log(`\n🔴 ${table.conflicts.length} disagreement(s):`);
        for (const line of table.conflicts) console.log('   ', line);
        return 1;
      }
      console.log(`\n✅ the ${table.read} documents agree on every role`);
      return 0;
    }
    case 'usage': {
      const role = flag('role');
      if (role === undefined) {
        console.error('usage: usage --role <name>');
        return 2;
      }
      const { uses, documents: seen, total } = roleUsage(role);
      console.log(`${role}: ${uses} uses across ${seen} of ${total} documents`);
      return 0;
    }
    case 'pairings': {
      const { bordered, plain } = tintPairings(population);
      const sum = (m: Map<string, number>) => [...m.values()].reduce((a, b) => a + b, 0);
      console.log(`population: ${describe}`);
      console.log(`  with a 1px border: ${sum(bordered)}`);
      for (const [key, n] of [...bordered].sort((a, b) => b[1] - a[1])) {
        console.log(`     ${String(n).padStart(5)}  ${key}`);
      }
      console.log(`  with NO border:    ${sum(plain)}`);
      for (const [key, n] of [...plain].sort((a, b) => b[1] - a[1])) {
        console.log(`     ${String(n).padStart(5)}  ${key}`);
      }
      return 0;
    }
    case 'foreground': {
      console.log(`population: ${describe}`);
      for (const [fill, inks] of [...tintForegrounds(population)].sort()) {
        const total = [...inks.values()].reduce((a, b) => a + b, 0);
        const top = [...inks]
          .sort((a, b) => b[1] - a[1])
          .slice(0, 3)
          .map(([ink, n]) => `${ink} ×${n}`)
          .join(', ');
        console.log(`  ${fill.padEnd(14)} (n=${String(total).padStart(3)})  ->  ${top}`);
      }
      return 0;
    }
    case 'focus': {
      for (const { ring, total, paired } of focusRings()) {
        console.log(`${String(total).padStart(5)}  box-shadow:${ring}`);
        for (const [edge, n] of [...paired].sort((a, b) => b[1] - a[1])) {
          console.log(`          ${String(n).padStart(5)} ${edge}`);
        }
      }
      return 0;
    }
    default:
      console.error('commands: tokens · usage --role · pairings · foreground · focus');
      return 2;
  }
}

if (require.main === module) process.exit(cli(process.argv.slice(2)));
