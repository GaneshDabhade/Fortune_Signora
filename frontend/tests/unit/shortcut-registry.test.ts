import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { join, relative } from 'node:path';
import { describe, expect, it } from 'vitest';

import { withoutComments } from '../support/source';

import {
  SHORTCUT_GROUPS,
  allShortcuts,
  coverage,
  keysFor,
  pressable,
  publishedByHome,
  publishedByTheDesign,
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
 * [§2](../../../CLAUDE.md)'s defect pointed the other way.
 *
 * ## ⛔ A sentence was removed from here, and removing it is the point
 *
 * ⚠️ **This paragraph used to end by citing a prior defect as its precedent** —
 * *"this lane has already shipped that exact shape once"* — **naming a row
 * identifier that has never existed.** 📁 The whole finding, including the
 * fabricated identifier itself, is
 * [B-1069](../../../docs/BUGS.md). ⛔ **The number is deliberately not repeated
 * here**: it is not a row, so citing it from source is the defect rather than
 * the record of it, and `row-citations.test.tsx` now fails on exactly that.
 *
 * ✅ **The argument stands without it and is not weakened by its removal**: the
 * failure mode above is derived from what the registry IS — a hand-maintained
 * list beside code that changes — **not from a past occurrence.** ⛔ **A
 * precedent that has to be invented was never carrying the argument**, and
 * replacing the number with a different one would be inventing it twice.
 *
 * ⚡ **Found by counting**: 198 identifiers are cited across 654 frontend
 * source files and 196 resolve to a heading. **This was one of the two.**
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
  // ⚡ **[TASK-495](../../../docs/BACKLOG.md) slice ⓑ.** ⛔ **Escape closes the
  // panel it belongs to and returns focus to its trigger** — 📁 the same
  // contract `drawer.tsx` and `account-menu.tsx` implement, and **not a
  // published chord**: the App Shell's §15 names `⌘⇧N` for OPENING
  // notifications, which is a global binding and would be registered rather
  // than declared here. **This file is the dismissal, which every panel owns.**
  'lib/shell/dismissable.ts': 'Escape closes the anchored panel it belongs to',
  // ⚡ **[TASK-1461](../../../docs/BACKLOG.md) — and this guard is what found
  // it**, on the first full run after the sheet was built. ⛔ **Escape closes
  // the navigation sheet the shell owns**, which is the same contract the
  // drawer above implements — 📁 **not a published chord**: the design's `<1024`
  // band names one control, *"a top-bar button"*, and no key.
  'components/shell/app-shell.tsx': 'Escape closes the navigation sheet while it is open',
  // ⚡ **Account 360's Research summary, focus mode** — 📁 the design says it
  // in terms: *"Esc returns to the record at the same scroll position."*
  // ⛔ **Not a published chord**: it is scoped to a section that is expanded,
  // and it is only bound while it is — the same contract the drawer above
  // implements, one surface along.
  'components/intelligence/research.tsx': 'Escape leaves the section’s focus mode',
};


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
    expect(publishedByTheDesign()).toHaveLength(18);
  });

  /**
   * 🔴 **A second design now publishes a shortcut**, and the count above must not
   * absorb it.
   *
   * 📁 Home §10's keyboard table names `⌘⇧H` — *"**Customise** — opens the
   * card-order panel as a drawer"*. ⛔ **The App Shell's list is a fixed
   * artifact**, and folding another screen's key into it would make a design
   * document appear to have grown.
   */
  it('🔴 keeps Home\'s own published shortcut out of the App Shell\'s eighteen', () => {
    const home = publishedByHome();

    expect(home.map((shortcut) => shortcut.keys)).toEqual(['⌘⇧H']);
    expect(publishedByTheDesign().map((shortcut) => shortcut.id)).not.toContain('customise-home');
    // ⚡ **And it is still in the registry**, because a customer can press it —
    // 📁 B-239's rule: a live shortcut omitted misleads as much as a dead one
    // listed.
    expect(allShortcuts().map((shortcut) => shortcut.id)).toContain('customise-home');
  });

  /**
   * 🔴 **[B-239](../../../docs/BUGS.md)** — ⛔ **the map shipped omitting a
   * live shortcut.** ⚡ **`1`–`9` selects a workspace by position and the
   * design does not publish it**, so a map built from the design alone was
   * silent about a key a customer can press. ⚠️ **A live key omitted is the
   * same defect as a dead key listed**, and it is the quieter one.
   */
  it('carries shortcuts the product binds that the design never published', () => {
    const unpublished = allShortcuts().filter((shortcut) => !shortcut.published);
    expect(unpublished.length).toBeGreaterThan(0);
    // ⛔ **An unpublished entry only earns its place by being REAL** — the map
    // is not a wishlist, so nothing unbound may be added outside the design.
    for (const shortcut of unpublished) {
      expect(pressable(shortcut), shortcut.id).toBe(true);
    }
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
    const all = allShortcuts();
    const working = all.filter(pressable).length;
    const dead = all.length - working;
    // ⚠️ **The total is the MAP's, not the design's** — 📁 [B-239](../../../docs/BUGS.md).
    // ⛔ **Saying *"of these 18"* while rendering nineteen rows is the register
    // miscounting itself in front of the customer.**
    expect(coverage()).toContain(`${working} of these ${all.length}`);
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
