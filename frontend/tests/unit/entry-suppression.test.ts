/**
 * 🔴 **`UNOBSERVED.suppresses` says it is not documentation, and nothing
 * asserted it.**
 *
 * 📁 `observed.ts`, in its own words: ***"`suppresses` is not documentation. It
 * is the cost of the absence"*** — and every rule it names is a rule the entry
 * engine can never reach, because the fact that would trigger it has no
 * producer.
 *
 * ⛔ **No test read `UNOBSERVED` or `suppresses` at any point.** ⚡ **A
 * structure that records which rules are dead, typed and reviewed and never
 * checked, is the shape this lane has closed five times today** — the
 * `app-shell.tsx` comment describing behaviour nothing implements, the
 * `cards.ts` correction written and never applied, `B-1069`'s citation of a row
 * that never existed.
 *
 * ⚠️ **These guard the CLAIM, not the reachability.** ⛔ **Whether a rule is
 * genuinely unreachable given the assumed values is not asserted here** and
 * would need every rule's `when()` exercised against a constructed session.
 * **Saying so is the point** — a guard that overstated its reach would be the
 * defect it is written against.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import { RULES } from '@/lib/entry/rules';
import { UNOBSERVED, UNOBSERVED_MEMBERSHIP } from '@/lib/entry/observed';

const ids = RULES.map((rule) => rule.n);

/**
 * 🔴 **BOTH registers, and reading only one is the defect this file was
 * written to prevent, occurring inside the file that prevents it.**
 *
 * ⛔ **`observed.ts` exports two**: `UNOBSERVED` suppresses ten rules and
 * **`UNOBSERVED_MEMBERSHIP` suppresses four — `15`, `16`, `17` and `19`** —
 * **and this file read only the first.**
 *
 * ⚠️ **Its own comment below says *"14 of 24 rules are suppressed"*, which is
 * the total across both.** ⛔ **The prose counted fourteen and the assertion
 * saw ten**, so four suppression claims were unguarded — including the one
 * carrying the register's most consequential warning:
 *
 * > 📁 *"Rules 15, 16 and 17 route to `/w/:id/suspended`, `/archived` and
 * > `/deleted`, and none of those routes exists… **whichever slice adds the
 * > standing MUST add the three screens in the same change**, or it turns
 * > three unreachable rules into three 404s on the same day."*
 *
 * ⚡ **A renumbering would have silently orphaned that warning**, which is
 * exactly the stale-claim class the first assertion names.
 */
const REGISTERS = [UNOBSERVED, UNOBSERVED_MEMBERSHIP] as const;
const suppressed = REGISTERS.flatMap((register) =>
  Object.values(register).flatMap((fact) => fact.suppresses),
);

describe('🔴 every suppressed rule is a rule that exists', () => {
  it('names no rule number the engine does not have', () => {
    /**
     * ⛔ **The stale-claim class, pointed at a register instead of a comment.**
     * ⚡ A rule renumbered or removed leaves its id behind in a `suppresses`
     * list, and the next reader believes an absence that has moved.
     */
    const unknown = suppressed.filter((id) => !ids.includes(id));
    expect(unknown, `suppresses names rules that do not exist: ${unknown.join(', ')}`).toEqual(
      [],
    );
  });

  it('⛔ and the engine has no duplicate rule ids', () => {
    // ⚡ Two rules sharing an id makes every `suppresses` entry ambiguous —
    // it would name one of them and silence both to a reader.
    expect(new Set(ids).size).toBe(ids.length);
  });
});

describe('⚡ the cost of the absences is visible rather than derivable', () => {
  it('records how many of the engine’s rules are dead, so the number cannot drift quietly', () => {
    /**
     * 🔴 **14 of 24 rules are suppressed by a fact nothing publishes**, and
     * that is not a defect — 📁 each carries a `because` naming what is
     * missing: no account lifecycle, no step-up policy, no completion field,
     * no workspace standing.
     *
     * ⚠️ **This asserts the SHAPE, not the exact number**, so adding a rule or
     * observing a fact does not fail it. ⛔ **What it refuses is the two
     * degenerate ends**: nothing suppressed, which would mean the register had
     * been emptied rather than earned, and everything suppressed, which would
     * mean the engine resolves nothing at all.
     */
    expect(suppressed.length).toBeGreaterThan(0);
    expect(suppressed.length).toBeLessThan(ids.length);
  });

  /**
   * ⚠️ **The guard that catches a THIRD register**, and it is the one this
   * file needed and did not have.
   *
   * ⛔ **A new `UNOBSERVED_*` export would be invisible to `REGISTERS` above**,
   * exactly as `UNOBSERVED_MEMBERSHIP` was — **and the failure is silent**: the
   * suite stays green while a set of suppression claims goes unchecked.
   *
   * ⚡ **So the source is asked directly.** ✅ A register that exists and is not
   * read is a register whose ids can drift, and this is the only assertion
   * here that can see one.
   */
  it('🔴 reads EVERY suppression register the source declares', () => {
    const source = readFileSync(
      join(process.cwd(), 'lib/entry/observed.ts'),
      'utf8',
    );
    const declared = [...source.matchAll(/export const (UNOBSERVED[A-Z_]*)\b/g)].map(
      (match) => match[1]!,
    );

    // ⚡ **Vacuity half** — a regex that matched nothing would pass the
    // comparison below against an empty list.
    expect(declared.length, 'the register scan found nothing').toBeGreaterThan(1);
    expect(
      declared.sort(),
      'a suppression register exists that this test does not read',
    ).toEqual(['UNOBSERVED', 'UNOBSERVED_MEMBERSHIP']);
  });
});
