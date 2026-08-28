import { readFileSync } from 'node:fs';

import { globSync } from 'glob';
import { describe, expect, it } from 'vitest';

/**
 * 🔴 **[B-1063](../../../docs/BUGS.md) — a certification gate contained an
 * assertion that silently passed on the machine that certifies.**
 *
 * ```js
 * const SETTINGS = join(process.cwd(), '..', 'Design Documents', '…');
 * if (!existsSync(SETTINGS)) return;      // ← a PASS, not a skip
 * ```
 *
 * ⛔ **`Design Documents/` is the product owner's local corpus and is
 * deliberately not committed** — 📁 [D-138](../../../docs/DECISION_REGISTER.md)
 * makes `docs/design-snapshot/` the implementation authority, and a second
 * corpus from a third owner is the drift that decision prevents.
 *
 * ⚠️ **So the assertion's EXISTENCE depended on an untracked directory**, and
 * the same commit certified differently on two machines. **QE found it by
 * asking why their run reported one failure where the lane's reported two.**
 *
 * ## ⚡ The row was closed; the CLASS was not
 *
 * ⛔ **Fixing the one instance leaves nothing stopping the next.** 📁 This is
 * the population lesson this repository keeps relearning — **`subject` was a
 * population of props, `ROOTS` a population of directories, `resolved()` a
 * population of callers** — and each was fixed once and returned somewhere
 * else.
 *
 * ✅ **Measured before this guard was written: the population is currently
 * clean.** ⚡ **So this cannot fail today, which is exactly the moment to add
 * it** — a guard written while the defect is live is a guard nobody can
 * distinguish from the fix.
 */

const SPECS = globSync('tests/**/*.{ts,tsx}', { cwd: process.cwd() }).filter(
  (path) => !path.endsWith('no-vacuous-skip.test.ts'),
);

/**
 * ⚠️ **Comments stripped, and that is not a convenience.** ⛔ **The comment
 * recording B-1063 quotes the defect verbatim**, and a guard that reads
 * documentation as code would fire on the note explaining itself — **which
 * teaches people not to document.** 📁 The same repair the design-token guard
 * and the heading guard both needed.
 */
function code(path: string): string {
  return readFileSync(path, 'utf8')
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/^\s*\/\/.*$/gm, '');
}

describe('⛔ no assertion may depend on a file the repository does not carry', () => {
  it('⚡ the population is real — an empty glob would report a clean suite', () => {
    // 🔴 **The instrument before the subject.** ⛔ **A broken glob and a clean
    // repository are indistinguishable from the result**, and this suite has
    // been fooled that way before.
    expect(SPECS.length).toBeGreaterThan(150);
  });

  it('⛔ no test READS the uncommitted `Design Documents/` corpus', () => {
    /**
     * ⚡ **`docs/design-snapshot/` is committed and is the authority** — 📁
     * D-138. **Reading it removes the hidden input rather than making it
     * visible**, which is the difference between this guard and a warning.
     */
    const offenders = SPECS.filter((path) => code(path).includes('Design Documents'));

    expect(
      offenders,
      'read `docs/design-snapshot/` through `tests/support/design-snapshot`: ' +
        '`Design Documents/` is not committed, so an assertion reading it cannot ' +
        'fail on the machine that certifies',
    ).toEqual([]);
  });

  it('🔴 no assertion is skipped by a bare return when a file is missing', () => {
    /**
     * ⛔ **A bare `return` is REPORTED AS A PASS.** ⚡ **`it.skip` says the test
     * did not run; `return` says it ran and was satisfied** — and only one of
     * those is true.
     *
     * ⚠️ **The pattern is banned rather than the directory**, because the next
     * instance will name a different path.
     */
    const offenders = SPECS.filter((path) =>
      // ⚠️ **A VALUE-LESS return only.** 🔴 **The first version banned any
      // `return` and fired on `tests/e2e/fixtures/environment.ts` —
      // `if (!existsSync(lib)) return undefined;`, a helper reporting an
      // absent optional path.** ⛔ **That is not an assertion passing; it is a
      // function answering.** ⚡ **A test callback returns nothing, so a bare
      // `return;` is the shape that ends an assertion early** — and narrowing
      // to it is the difference between a guard and a nuisance.
      /if \(\s*!\s*existsSync\([^)]*\)\s*\)\s*(?:\{\s*)?return\s*;/.test(code(path)),
    );

    expect(
      offenders,
      'a missing file must fail the assertion or skip it explicitly — never pass it',
    ).toEqual([]);
  });
});
