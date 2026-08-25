/**
 * 🔴 **A file whose purpose ended, that nothing retracted.**
 *
 * ## ⛔ `tmp-` is a claim about lifetime the repository cannot enforce
 *
 * ⚠️ **`tests/e2e/tmp-theme-click.spec.ts` reached a certification candidate.**
 * It was an investigation probe for 📁 [B-1072](../../docs/BUGS.md) — it did its
 * job, the row records what it found, **and the investigation ended while the
 * file did not.** ⛔ **QE caught it in the candidate, not the author.**
 *
 * ⚡ **This is the day's own class from the other end.** Every stale-blocker
 * this lane filed — 📁 [C-207](../../docs/LANE_COORDINATION.md) cited as live
 * eighteen days after it closed, C-002 cited in the present tense after it was
 * answered — **was a COMMENT whose subject went away and nothing retracted.**
 * **This is a FILE whose purpose went away.** 🔴 **`tmp-` is exactly as
 * load-bearing as *"blocked on C-207"* was: a promise in prose that no
 * mechanism keeps.**
 *
 * ## ⛔ Why it had to be removed rather than left
 *
 * ⚡ **Tagged `@journey`**, so `make e2e` and every browser gate would run it —
 * a fourth consumer of prod-local per run, while 📁 [B-1071](../../docs/BUGS.md)
 * already prevents a 460 from finishing.
 *
 * 🔴 **And it ASSERTED THE DEFECT'S CURRENT STATE.** ⛔ **A probe that waits for
 * `data-theme` to stay wrong goes RED the day B-1072 is fixed** — a test that
 * fails when the product is repaired is worse than no test, because it argues
 * against the fix.
 *
 * ## ✅ What this guard pins
 *
 * ⛔ **Not "no temporary work"** — a probe is the right tool and this lane will
 * write more. ✅ **It pins that one never SHIPS**, which is the step that
 * actually failed. **The scratchpad is where an unshipped probe belongs.**
 */
import { describe, expect, it } from 'vitest';

import { globSync } from 'glob';

/**
 * ⚠️ **Names that announce their own impermanence.** ⛔ **Deliberately not a
 * `tmp` substring test**: `tests/unit/template-*.ts` would match, and a guard
 * that fires on innocent names is one somebody edits rather than obeys.
 */
const TEMPORARY = /(^|\/)(tmp|temp|scratch|wip|probe|draft)[-._]/i;

describe('🔴 no temporary spec ships', () => {
  it('⚡ the glob sees the test tree, so a clean result means something', () => {
    // ⛔ **The instrument before the subject.** An empty glob reports a clean
    // repository, which is indistinguishable from a clean repository.
    const all = globSync('tests/**/*.{ts,tsx}', { cwd: process.cwd() });
    expect(all.length, 'the test glob matched nothing').toBeGreaterThan(150);
  });

  it('no spec file announces itself as temporary', () => {
    const offenders = globSync('tests/**/*.{ts,tsx}', { cwd: process.cwd() }).filter((file) =>
      TEMPORARY.test(file),
    );

    expect(
      offenders,
      'an investigation probe reached the tree — keep it in the scratchpad, and let the row it produced carry the finding',
    ).toEqual([]);
  });
});
