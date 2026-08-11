import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { join, relative } from 'node:path';
import { describe, expect, it } from 'vitest';

import {
  SHORTCUT_GROUPS,
  allShortcuts,
  coverage,
  keysFor,
  pressable,
} from '@/lib/shell/shortcuts';

/**
 * **The keyboard map against the keyboard** — [TASK-1445](../../../docs/BACKLOG.md).
 *
 * ## 🔴 A registry of what works is only worth anything if something checks it
 *
 * 📁 **[`command-palette.tsx`](../../components/ui/command-palette.tsx) states
 * the rule for its own four keys**: ⛔ ***"a legend that can drift from the
 * behaviour it documents is worse than no legend — it is read as a
 * contract."*** ⚡ **It enforces that by construction: one table feeds both the
 * hint and the handler.** ⚠️ **A product-wide map cannot do that** — the
 * handlers live in nine files and a shared table would put shell code inside a
 * data structure every one of them imports.
 *
 * ✅ **So the enforcement is static and it runs in BOTH directions.**
 *
 * ⚡ **Direction 1 — a claim needs a binding.** A `live` shortcut naming a file
 * that binds nothing is a promise the reference makes and the product breaks.
 *
 * 🔴 **Direction 2 is the one that matters, and it is the direction a registry
 * rots in.** ⛔ **A file that binds a global key without appearing here fails.**
 * **Without it, the ordinary failure is invisible**: somebody implements `G H`,
 * ships it, and the reference goes on saying `Not bound` — **the register
 * telling a customer a working feature does not exist**, which is
 * [§2](../../../CLAUDE.md)'s defect pointed the other way. ⚠️ **This lane has
 * already shipped that exact shape once**, in [B-3180](../../../docs/BUGS.md):
 * a defect fixed in code and left reading `OPEN` in the register.
 */

const FRONTEND = join(process.cwd());
const SCANNED = ['app', 'components', 'lib'];

/**
 * ⛔ **Keydown listeners that are NOT product shortcuts**, each with the reason
 * it is not one.
 *
 * ⚡ **An allowlist rather than a pattern**, because the distinction is
 * intent and not syntax: **a dialog closing on Escape is the component
 * implementing its own contract; `⌘⇧W` is a promise the product makes to a
 * customer who read the reference.** ⚠️ **Adding a line here is a decision, and
 * a decision that has to be typed is a decision somebody sees.**
 */
const LOCAL_TO_A_COMPONENT: Readonly<Record<string, string>> = {
  'components/ui/tooltip.tsx': 'Escape dismisses the tooltip it belongs to',
  'components/ui/drawer.tsx': 'Escape closes the drawer it belongs to',
  'components/shell/account-menu.tsx': 'Escape and arrows move within the open menu',
};

/**
 * ⚡ **Source with its comments removed, string-aware.**
 *
 * 🔴 **Needed because this suite found its own false positive on the first
 * run**: [`shortcuts.ts`](../../lib/shell/shortcuts.ts) DOCUMENTS that it was
 * measured against *"every `addEventListener('keydown'`"*, and the scan matched
 * the sentence describing the search. ⛔ **A file was reported as binding a key
 * because it explained the rule.**
 *
 * ⚠️ **And [B-162](../../../docs/BUGS.md) is the same defect in the other
 * direction** — a guard narrowed to strip comments started treating `//` in a
 * URL as the start of one, and stopped catching real matches. 📁 **Its lesson
 * is this function's shape**: *"narrowing a guard is only safe if you measure
 * what STOPS firing"* — ✅ **so the walker tracks quotes and template literals,
 * and both directions are fire-tested below.**
 */
export function withoutComments(source: string): string {
  let out = '';
  let i = 0;
  let quote: string | null = null;

  while (i < source.length) {
    const c = source[i];
    const next = source[i + 1];

    if (quote !== null) {
      out += c;
      if (c === '\\') {
        out += source[i + 1] ?? '';
        i += 2;
        continue;
      }
      if (c === quote) quote = null;
      i += 1;
      continue;
    }

    if (c === "'" || c === '"' || c === '`') {
      quote = c;
      out += c;
      i += 1;
      continue;
    }

    if (c === '/' && next === '/') {
      while (i < source.length && source[i] !== '\n') i += 1;
      continue;
    }

    if (c === '/' && next === '*') {
      i += 2;
      while (i < source.length && !(source[i] === '*' && source[i + 1] === '/')) i += 1;
      i += 2;
      continue;
    }

    out += c;
    i += 1;
  }

  return out;
}

function sourceFiles(dir: string): string[] {
  const found: string[] = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) {
      found.push(...sourceFiles(path));
    } else if (/\.tsx?$/.test(entry.name) && !/\.test\.tsx?$/.test(entry.name)) {
      found.push(path);
    }
  }
  return found;
}

/** ⚡ Every file that asks the window or the document for keystrokes. */
function filesBindingKeys(): string[] {
  return SCANNED.flatMap((dir) => sourceFiles(join(FRONTEND, dir)))
    .filter((path) =>
      /addEventListener\(\s*'keydown'/.test(withoutComments(readFileSync(path, 'utf8'))),
    )
    .map((path) => relative(FRONTEND, path).replaceAll('\\', '/'));
}

describe('the shortcut registry describes the product', () => {
  it('gives every shortcut a unique id', () => {
    const ids = allShortcuts().map((shortcut) => shortcut.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('carries the eighteen the App Shell design publishes, in three groups', () => {
    expect(SHORTCUT_GROUPS.map((group) => group.label)).toEqual([
      'Surfaces',
      'Navigate',
      'Work',
    ]);
    expect(allShortcuts()).toHaveLength(18);
  });

  it('never claims a shortcut works without naming what binds it', () => {
    for (const shortcut of allShortcuts().filter(pressable)) {
      expect(shortcut.boundIn, `${shortcut.id} is ${shortcut.state}`).toBeDefined();
    }
  });

  it('never names a binding for a shortcut it calls unbound', () => {
    for (const shortcut of allShortcuts().filter((s) => s.state === 'unbound')) {
      expect(shortcut.boundIn, `${shortcut.id}`).toBeUndefined();
    }
  });

  /**
   * ⚠️ **A `partial` with no limit is the worst row in the table**: it reads as
   * live to anybody skimming, and the narrowness — the only reason the state
   * exists — is invisible.
   */
  it('says where a partial shortcut works', () => {
    for (const shortcut of allShortcuts().filter((s) => s.state === 'partial')) {
      expect(shortcut.limit, `${shortcut.id}`).toBeTruthy();
    }
  });
});

describe('direction 1 — every claim has a binding behind it', () => {
  it('points at a file that exists and reads keystrokes', () => {
    for (const shortcut of allShortcuts().filter(pressable)) {
      const path = join(FRONTEND, shortcut.boundIn as string);
      expect(existsSync(path), `${shortcut.id} -> ${shortcut.boundIn}`).toBe(true);
      const source = readFileSync(path, 'utf8');
      expect(
        /keydown|onKeyDown|KeyboardEvent/.test(source),
        `${shortcut.boundIn} binds no key, but ${shortcut.id} says it does`,
      ).toBe(true);
    }
  });
});

describe('direction 2 — every binding appears in the registry', () => {
  /**
   * 🔴 **The guard that keeps this file honest as the product grows.**
   *
   * ⛔ **Fire-tested**: pointing a registry entry at a different file, or
   * adding a `window.addEventListener('keydown'` to a file named by nothing,
   * turns this red. **A guard nobody has seen fail is a guard nobody has
   * tested** ([§2](../../../CLAUDE.md)).
   */
  it('leaves no global key binding undeclared', () => {
    const declared = new Set(
      allShortcuts()
        .map((shortcut) => shortcut.boundIn)
        .filter((path): path is string => path !== undefined),
    );

    const undeclared = filesBindingKeys().filter(
      (path) => !declared.has(path) && LOCAL_TO_A_COMPONENT[path] === undefined,
    );

    expect(
      undeclared,
      'each file here binds a key that no shortcut in lib/shell/shortcuts.ts describes — ' +
        'register it, or declare it local in LOCAL_TO_A_COMPONENT with the reason',
    ).toEqual([]);
  });

  it('keeps the local allowlist from outliving the files in it', () => {
    for (const path of Object.keys(LOCAL_TO_A_COMPONENT)) {
      expect(existsSync(join(FRONTEND, path)), path).toBe(true);
    }
  });
});

describe('the scan can tell code from prose, in both directions', () => {
  const binds = (source: string) =>
    /addEventListener\(\s*'keydown'/.test(withoutComments(source));

  it('⛔ does not see a binding that is only being described', () => {
    expect(binds("/** measured against addEventListener('keydown' */")).toBe(false);
    expect(binds("// see addEventListener('keydown' in the shell")).toBe(false);
  });

  /**
   * 🔴 **The half [B-162](../../../docs/BUGS.md) says is skipped**: it is easy
   * to prove a stripper removes something and hard to remember to prove it
   * still lets the real thing through.
   */
  it('✅ still sees the real one, beside a comment that mentions it', () => {
    expect(
      binds("// the shell's own addEventListener('keydown'\nwindow.addEventListener('keydown', f)"),
    ).toBe(true);
  });

  it('⚠️ does not treat a // inside a string as the start of a comment', () => {
    expect(binds("const u = 'https://x.test';\nwindow.addEventListener('keydown', f)")).toBe(true);
    expect(binds("const u = `https://x.test`;\nwindow.addEventListener('keydown', f)")).toBe(true);
  });

  it('⚠️ does not let an escaped quote end a string early', () => {
    expect(binds("const s = 'it\\'s /* not a comment */';\ndocument.addEventListener('keydown', f)"))
      .toBe(true);
  });
});

describe('what the reference tells a customer', () => {
  /**
   * ⛔ **The count is derived.** ⚠️ **A hand-typed tally is a fact that goes
   * stale on the next binding** — and a reference whose own summary is wrong
   * is the register asserting something untrue of the thing it describes.
   */
  it('counts the working shortcuts rather than stating a number', () => {
    const working = allShortcuts().filter(pressable).length;
    const dead = allShortcuts().length - working;
    expect(coverage()).toContain(`${working} of these 18`);
    expect(coverage()).toContain(`other ${dead}`);
  });

  it('never says coming soon', () => {
    const text = [coverage(), ...allShortcuts().map((s) => s.limit ?? '')].join(' ');
    expect(text.toLowerCase()).not.toContain('coming soon');
  });

  /**
   * 📁 **Every modifier binding in this product reads
   * `event.metaKey || event.ctrlKey`.** ⛔ **Showing `⌘` to somebody on Windows
   * names a key their keyboard does not have**, and they conclude the shortcut
   * is not for them.
   */
  it('translates the design ⌘ for a keyboard that has no ⌘', () => {
    expect(keysFor('⌘K', true)).toBe('⌘K');
    expect(keysFor('⌘K', false)).toBe('Ctrl K');
    expect(keysFor('⌘⇧A', false)).toBe('Ctrl ⇧A');
    expect(keysFor('⌘[ / ⌘]', false)).toBe('Ctrl [ / Ctrl ]');
  });

  it('leaves ⇧ and ↵ alone, which every keyboard has', () => {
    expect(keysFor('⇧X', false)).toBe('⇧X');
    expect(keysFor('↵', false)).toBe('↵');
  });
});
