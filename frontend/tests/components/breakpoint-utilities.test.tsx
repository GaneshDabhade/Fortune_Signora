import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

import { globSync } from 'glob';
import { describe, expect, it } from 'vitest';

/**
 * **No utility may name a breakpoint the config does not define** —
 * [B-424](../../../docs/BUGS.md).
 *
 * ## 🔴 The defect this exists for was silent in every gate
 *
 * ⛔ **[TASK-1443](../../../docs/BACKLOG.md) replaced Tailwind's `screens`
 * rather than extending them** — `phone · smalllaptop · laptop · desktop`, and
 * the config's own comment says *"OVERRIDES rather than extends"*.
 * ⚡ **That was correct, and it left 45 `sm:` and `lg:` utilities across 11
 * files naming prefixes that no longer exist.**
 *
 * 🔴 **A Tailwind utility with an undefined prefix does not error — it simply
 * is not generated.** ⚠️ **So every one of those responsive rules silently
 * stopped applying**, and nothing in the repository noticed: **`tsc` sees a
 * string, `eslint` sees a string, and the component tests asserted the string
 * was PRESENT rather than that it resolved.**
 *
 * ⛔ **`auth-shell.test.tsx` is the worked example**: it asserted
 * `toMatch(/lg:/)` under the name *"centred on a desktop"* and passed
 * throughout — **proving a class name was in an attribute while the behaviour
 * it described had stopped happening.**
 *
 * ## ⚡ So the check is the config against the source
 *
 * ✅ **Both sides are read.** The prefixes come from `tailwind.config.ts` and
 * the utilities from the source, so **a future rename of a band fails here
 * rather than passing over dead classes** — and 📁 [§2](../../../CLAUDE.md)'s
 * *a guard that cannot fail is documentation pretending to be code* is what
 * the `it` below about vacuity is for.
 */

const ROOT = process.cwd();
/** 📁 The committed snapshot — D-138's implementation authority, never `Design Documents/`. */
const SNAPSHOT = join(ROOT, '..', 'docs', 'design-snapshot', 'screens');

/** The bands the config actually defines. */
function definedScreens(): string[] {
  return screenBands().map(([name]) => name);
}

/**
 * ⚡ **Name AND value.** 🔴 **This helper captured both and returned only the
 * NAME**, so every assertion below was green about `tablet` while saying
 * nothing about `768px` — **and changing it to `800px` would have passed.**
 *
 * ⚠️ **The band names are this repository's; the NUMBERS are the design's**, and
 * a config that keeps the names while moving a number reflows 24 documents'
 * worth of screens somewhere they are not drawn to.
 */
function screenBands(): [string, number][] {
  const config = readFileSync(join(ROOT, 'tailwind.config.ts'), 'utf8');
  const block = config.slice(config.indexOf('screens: {'));
  const end = block.indexOf('}');
  return [...block.slice(0, end).matchAll(/(\w+):\s*'(\d+)px'/g)].map((m) => [
    m[1] as string,
    Number(m[2]),
  ]);
}

/**
 * 📁 **Every number inside a `range:` declaration, across the whole snapshot.**
 *
 * ⛔ **This is what makes the assertion a CHECK rather than a restatement** —
 * 📁 the file's own docblock: *"a guard is only ever as wide as the population
 * it was written from, and this one inherited its population from the config it
 * was checking."* ⚡ **Reading the design corpus is the only way the config can
 * be wrong about it.**
 */
function corpusBreakpoints(): Set<number> {
  const found = new Set<number>();
  for (const file of globSync('*.dc.html', { cwd: SNAPSHOT })) {
    const text = readFileSync(join(SNAPSHOT, file), 'utf8');
    for (const m of text.matchAll(/range:\s*'([^']*)'/g)) {
      for (const n of (m[1] ?? '').matchAll(/\d{3,4}/g)) found.add(Number(n[0]));
    }
  }
  return found;
}

/** Every `prefix:utility` in the source, with the file it is in. */
function responsiveUtilities(): { prefix: string; where: string; text: string }[] {
  const found: { prefix: string; where: string; text: string }[] = [];
  const walk = (dir: string) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const path = join(dir, entry.name);
      if (entry.isDirectory()) {
        if (entry.name === 'node_modules' || entry.name === '.next') continue;
        walk(path);
        continue;
      }
      if (!/\.tsx?$/.test(entry.name)) continue;
      for (const line of readFileSync(path, 'utf8').split('\n')) {
        const trimmed = line.trimStart();
        // ⛔ **Comments are skipped deliberately.** The only `md:` left in the
        // tree is inside a comment explaining why it was removed, and a guard
        // that fails on its own explanation is a guard nobody keeps.
        if (trimmed.startsWith('*') || trimmed.startsWith('//') || trimmed.startsWith('/*')) continue;
        for (const match of line.matchAll(/(?<![\w-])([a-z]+[a-z0-9]*):(?=[a-z[])[a-z[]/g)) {
          found.push({ prefix: match[1] as string, where: path, text: line.trim().slice(0, 90) });
        }
      }
    }
  };
  for (const dir of ['app', 'components', 'lib']) walk(join(ROOT, dir));
  return found;
}

/**
 * ⚠️ **Tailwind's non-breakpoint prefixes are legitimate and are not screens.**
 * `hover:`, `focus:`, `dark:` and friends are variants; this guard is only
 * about the responsive ones, so the check is *does it look like a dead
 * BREAKPOINT* rather than *is it an unknown prefix*.
 */
const TAILWIND_DEFAULT_SCREENS = ['sm', 'md', 'lg', 'xl'];

describe('🔴 B-424 — no utility names a breakpoint the config does not define', () => {
  it('⚡ both sides were actually read, so nothing below is vacuous', () => {
    // ⛔ The shape of the defect it exists to catch: if either side came back
    // empty every assertion would pass over a comparison that never happened.
    expect(definedScreens().length, 'no screens parsed from tailwind.config.ts').toBeGreaterThan(3);
    expect(responsiveUtilities().length, 'no prefixed utilities found in the source').toBeGreaterThan(20);
  });

  /**
   * 🔴 **This asserted FOUR bands, and 📁 [B-298](../../docs/BUGS.md) is the
   * reason it is now five.**
   *
   * ⚠️ **The four were right for the document they came from and for no
   * other.** 📁 `tailwind.config.ts` named its own source — *"TASK-1443, **App
   * Shell** `breakpoints`"* — and **this guard pinned that answer as though it
   * were the corpus's.** ⛔ **Measured across all 35 design documents, inside
   * `range:` declarations, `768` is the most-used breakpoint there is** — 24
   * uses across 12 documents, against `1280`'s 13 — **and it was the one band
   * with no token.**
   *
   * ⚡ **So the guard held, and what it held was one document's model.** 🔴
   * **A guard is only ever as wide as the population it was written from**,
   * and this one inherited its population from the config it was checking —
   * which makes it a restatement rather than a check. **The fix is not to
   * loosen it**: it still pins an exact set, and adding a sixth band still
   * fails here. **The set is now derived from all 35 documents rather than
   * from one.**
   */
  it('📁 the config defines the corpus’s five bands', () => {
    expect(definedScreens().sort()).toEqual([
      'desktop',
      'laptop',
      'phone',
      'smalllaptop',
      'tablet',
    ]);
  });

  it('🔴 B-298 — and every band sits on a number the DESIGN actually names', () => {
    /**
     * 🔴 **The assertion above pins the NAMES and said nothing about the
     * numbers** — 📁 `definedScreens()` captured both and returned one.
     * ⛔ **`tablet: '800px'` would have passed it**, while 📁 24 design
     * documents reflow at `768`.
     *
     * ⚡ **Read out of the snapshot rather than transcribed**, which is what
     * makes this a check: **a config value that no `range:` declaration
     * mentions is one this repository invented.**
     */
    const corpus = corpusBreakpoints();
    // ⚠️ **The instrument before the subject** — an empty corpus would report
    // every band as valid.
    expect(corpus.size, 'no `range:` declarations were read from the snapshot').toBeGreaterThan(3);

    const invented = screenBands()
      .filter(([, px]) => !corpus.has(px))
      .map(([name, px]) => `${name}: ${px}px`);

    expect(
      invented,
      'these breakpoints appear in no design document’s `range:` declaration',
    ).toEqual([]);

    // ⛔ **And the one the row is about, named explicitly** — 📁 `768` is the
    // most-used breakpoint in the corpus and was the one band with no token.
    expect(screenBands()).toContainEqual(['tablet', 768]);
  });

  it('⛔ no Tailwind default breakpoint survives as a live utility', () => {
    /**
     * 🔴 **This is the assertion B-424 is about.** ⚡ **`sm:` and `lg:` were
     * renamed to `phone:` and `smalllaptop:` at IDENTICAL pixel values** — 640
     * and 1024 — **so no layout changed and 45 dead rules came back to life.**
     */
    const dead = responsiveUtilities()
      .filter((u) => TAILWIND_DEFAULT_SCREENS.includes(u.prefix))
      .map((u) => `${u.where.replace(ROOT + '/', '')}: ${u.text}`);

    expect(
      dead,
      'these name a Tailwind breakpoint the config replaced, so they generate no CSS at all',
    ).toEqual([]);
  });
});
