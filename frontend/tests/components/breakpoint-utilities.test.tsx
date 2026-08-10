import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

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

/** The bands the config actually defines. */
function definedScreens(): string[] {
  const config = readFileSync(join(ROOT, 'tailwind.config.ts'), 'utf8');
  const block = config.slice(config.indexOf('screens: {'));
  const end = block.indexOf('}');
  return [...block.slice(0, end).matchAll(/(\w+):\s*'(\d+)px'/g)].map((m) => m[1] as string);
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

  it('📁 the config defines the design’s four bands', () => {
    expect(definedScreens().sort()).toEqual(['desktop', 'laptop', 'phone', 'smalllaptop']);
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
