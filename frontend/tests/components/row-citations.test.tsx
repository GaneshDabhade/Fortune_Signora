/**
 * 🔴 **Every row this codebase cites must exist** — 📁
 * [B-1069](../../docs/BUGS.md), and the finding that produced it.
 *
 * ## ⛔ A citation IS the evidence, so nobody checks the evidence
 *
 * ⚠️ **`tests/unit/shortcut-registry.test.ts` ended an argument with *"this
 * lane has already shipped that exact shape once, in **B-3180***"* — **a row
 * that has never existed.** 📁 The highest identifier ever filed is `B-1068`,
 * and `git log -S` finds no commit that ever added a `B-3180` heading. ⚡ **An
 * invented row, cited as the precedent for an argument about registers not
 * carrying untrue claims.**
 *
 * ⛔ **And one was written the same day this class was fixed elsewhere.**
 * 📁 [C-1550](../../docs/LANE_COORDINATION.md) was cited in
 * `components/settings/sections.tsx` four hours after 📁
 * [B-1045](../../docs/BUGS.md) — *a comment describing behaviour the line
 * beneath it did not have* — **and it had not been filed.** ⚡ **Knowing the
 * failure mode did not prevent committing it**, which is an argument for a
 * guard rather than for care.
 *
 * ## ⚡ Neither was found by reading
 *
 * **198 identifiers are cited across 654 source files and 196 resolved.**
 * ⛔ **Every one of the 198 looks correct in place** — that is the property
 * that makes this class invisible: **the reader's check IS the thing being
 * checked.** 🔴 So the instrument is a count, not a review.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';
import { globSync } from 'glob';

const ROOT = join(__dirname, '..', '..');
const REPO = join(ROOT, '..');

/** 📁 Where each block of identifiers is filed. */
const REGISTERS = {
  B: join(REPO, 'docs', 'BUGS.md'),
  C: join(REPO, 'docs', 'LANE_COORDINATION.md'),
} as const;

/**
 * ⛔ **Two to four digits, so `B-12` and `B-99999` are both out of range** —
 * and 📁 the identifier blocks in [§20e](../../../CLAUDE.md) are three and four
 * digits. ⚡ **`\b` on both sides**: without the trailing one this matches the
 * `B-106` inside `B-1066` and reports a row that exists as missing.
 */
const CITATION = /\b([BC])-(\d{2,4})\b/g;

function sources(): string[] {
  const files = globSync('{app,components,lib,tests}/**/*.{ts,tsx}', { cwd: ROOT });
  // ⚡ **The instrument before the subject.** An empty glob reports a codebase
  // with no false citations, which is indistinguishable from a clean one.
  expect(files.length, 'the source glob matched nothing, so nothing was checked').toBeGreaterThan(
    400,
  );
  return files;
}

/** Every identifier cited in source, with the files that cite it. */
function citations(): Map<string, string[]> {
  const found = new Map<string, string[]>();
  for (const file of sources()) {
    // ⛔ **This file is excluded, and the reason is not convenience.** 🔴 The
    // first run reported `B-12` as dangling — from the sentence above
    // explaining the digit range. ⚡ **A guard that reads comments cannot read
    // its own**, because everything it says about identifiers becomes an
    // identifier. **The cost is a real blind spot**: nothing checks the
    // citations in here, and the two in the docblock above are deliberately
    // the only ones.
    if (file.endsWith('row-citations.test.tsx')) continue;
    const body = readFileSync(join(ROOT, file), 'utf8');
    for (const [, block, digits] of body.matchAll(CITATION)) {
      const id = `${block}-${digits}`;
      found.set(id, [...(found.get(id) ?? []), file]);
    }
  }
  return found;
}

/**
 * ⛔ **The heading that IS the row, not a heading that MENTIONS it.**
 *
 * 🔴 **The first draft asked for `^#{2,4} .*\bID\b` and passed on `B-3180`** —
 * because 📁 [B-1069](../../docs/BUGS.md) is titled *"A docstring cites
 * `B-3180` as precedent, and no such row has ever existed"*. ⚡ **A row filed
 * ABOUT a fabricated identifier made the fabricated identifier look filed**,
 * so the guard would have gone green the moment somebody documented the defect
 * it exists to catch. ⛔ **That is worse than not having it.**
 *
 * ✅ **The identifier must LEAD its heading**, after any decoration.
 *
 * ⚠️ **The second draft required it immediately after the hashes and rejected
 * a row that IS filed** — `### ⚡ B-1400 — classification, recorded by QE` —
 * because an emoji sat in front of it.
 *
 * 🔴 **And the check that "verified" that convention was circular**: it counted
 * `^### B-\d+ ·` against `^### B-\d+` — **both queries presupposed the very
 * placement they were confirming**, so both returned 365 of 365 and neither
 * could have seen the 29 headings that do not. ⚡ **Measured properly** — every
 * heading naming an identifier, then asking where the identifier sits:
 *
 * ```
 * BUGS.md               396 headings name an id   367 lead   29 elsewhere
 * LANE_COORDINATION.md  297                       287        10
 * ```
 *
 * ⛔ **The 39 that do not lead are sub-headings ABOUT other rows** — *"Why it
 * is the same class as B-290"* — **and they must not count as filing.** That is
 * the same distinction the B-1069 case turns on, one shape along.
 */
function isFiled(id: string): boolean {
  const register = REGISTERS[id[0] as 'B' | 'C'];
  for (const heading of readFileSync(register, 'utf8').match(/^#{2,4} .*$/gm) ?? []) {
    // Hashes, then any decoration — emoji, brackets, whitespace — then the id.
    const subject = heading.replace(/^#{2,4}\s*/, '').replace(/^[^A-Za-z0-9]+/, '');
    if (new RegExp(`^${id}\\b`).test(subject)) return true;
  }
  return false;
}

describe('🔴 every row cited in source is a row that exists', () => {
  it('⚡ both sides were read, so nothing below is vacuous', () => {
    const cited = citations();
    expect(cited.size, 'no identifiers parsed from source').toBeGreaterThan(100);

    // ⛔ **The control.** If `isFiled` cannot find a row we know is filed, a
    // clean result below means the lookup is broken rather than the codebase
    // clean — and this guard exists because that failure looks like success.
    expect(isFiled('B-1045'), 'the register lookup cannot see a known row').toBe(true);
    expect(isFiled('C-1550'), 'the coordination lookup cannot see a known row').toBe(true);
    // ⚡ And it must say no to something absent, or it says yes to everything.
    expect(isFiled('B-3180'), 'the lookup accepts a row that never existed').toBe(false);
  });

  it('no source file cites a row that was never filed', () => {
    const dangling = [...citations().entries()]
      .filter(([id]) => !isFiled(id))
      .map(([id, files]) => `${id} (cited in ${files.join(', ')})`)
      .sort();

    expect(
      dangling,
      'file the row, or remove the citation — never renumber it to something that happens to exist',
    ).toEqual([]);
  });
});
