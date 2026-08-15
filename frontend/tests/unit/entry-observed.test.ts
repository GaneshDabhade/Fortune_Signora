/**
 * **The observation seam** — [TASK-1401](../../../docs/BACKLOG.md).
 *
 * ⚡ **What is asserted here is not that the values are right** — most of them
 * are stand-ins by definition. ✅ **It is that the ABSENCES stay declared**, so
 * the engine can never quietly acquire a hidden input.
 */
import { describe, expect, it } from 'vitest';

import { resolveEntry } from '@/lib/entry';
import {
  UNOBSERVED,
  UNOBSERVED_MEMBERSHIP,
  observedSession,
  suppressedRules,
} from '@/lib/entry/observed';
import { RULES } from '@/lib/entry/rules';

describe('every fact the product cannot observe is declared, with its cost', () => {
  /**
   * 🔴 **The one that would rot first.** ⛔ **A `because` somebody deleted, or
   * left as `''`, turns a declared absence back into a silent default** — which
   * is the whole thing this file exists to prevent.
   */
  it('⛔ names a reason for every absent fact — an empty one is a hidden input again', () => {
    for (const [field, u] of [
      ...Object.entries(UNOBSERVED),
      ...Object.entries(UNOBSERVED_MEMBERSHIP),
    ]) {
      expect(u.because.trim(), `${field} declares no reason`).not.toBe('');
      // ⚡ **A sentence, not a word.** *"n/a"* passes a non-empty check and
      // tells the next lane nothing.
      expect(u.because.length, `${field}'s reason is too short to be one`).toBeGreaterThan(20);
    }
  });

  /**
   * 🔴 **Every rule named as suppressed must EXIST.** ⛔ **A typo'd rule number
   * makes the cost look accounted for when it is not** — and the count below
   * would be wrong in the reassuring direction.
   */
  it('🔴 only names rules the engine actually has', () => {
    const known = new Set(RULES.map((r) => r.n));
    for (const n of suppressedRules()) {
      expect(known.has(n), `rule ${n} is declared suppressed and does not exist`).toBe(true);
    }
  });

  /**
   * ⚡ **The measurement, pinned so a change has to be deliberate.**
   *
   * ⚠️ **Fifteen of twenty-four rules cannot fire today.** ⛔ **This assertion
   * is not a target — it is a tripwire**: a slice that supplies one of the ten
   * absent facts should see this number FALL, and a slice that adds a rule
   * without a source should see it rise and be made to say so.
   */
  it('⚠️ pins how much of the engine is currently unreachable', () => {
    expect(suppressedRules()).toEqual([
      '01', '02', '03', '04', '05', '15', '16', '17', '18', '19', '20', '21', '22', '23',
    ]);
    expect(RULES).toHaveLength(24);
  });
});

describe('the session it builds is the one the engine reads', () => {
  it('✅ preserves the order the API returned, because rule 14 needs *next*', () => {
    const session = observedSession({
      workspaceIds: ['ws-c', 'ws-a', 'ws-b'],
      lastUsedWorkspaceId: null,
    });
    expect(session.memberships.map((m) => m.workspaceId)).toEqual(['ws-c', 'ws-a', 'ws-b']);
  });

  /**
   * 🔴 **The behaviour-preservation claim, tested rather than asserted.**
   *
   * ⛔ **Every suppressed rule must be unreachable for a person the product can
   * actually describe** — otherwise a stand-in value is deciding entry, which
   * is the decorative-logic class exactly.
   */
  it('🔴 never reaches a suppressed rule, whatever the membership shape', () => {
    const suppressed = new Set(suppressedRules());
    const shapes = [[], ['ws-1'], ['ws-1', 'ws-2'], ['ws-1', 'ws-2', 'ws-3']];

    for (const workspaceIds of shapes) {
      for (const lastUsedWorkspaceId of [null, 'ws-1', 'ws-gone']) {
        const decision = resolveEntry(observedSession({ workspaceIds, lastUsedWorkspaceId }));
        const rule = RULES.find((r) => r.reason === decision.reason);
        expect(rule, `no rule carries ${decision.reason}`).toBeDefined();
        expect(
          suppressed.has(rule?.n ?? ''),
          `rule ${rule?.n} is declared unreachable and just fired for ${JSON.stringify(workspaceIds)}`,
        ).toBe(false);
      }
    }
  });

  /**
   * ⚠️ **The three that have no screen** — 📁 the warning at gate 4 in
   * [`rules.ts`](../../lib/entry/rules.ts).
   *
   * ⛔ **This is the assertion that turns *"harmless today"* into something a
   * change has to break on purpose.** ✅ **The day `standing` becomes
   * observable, this test fails** — and it fails in the file that says why.
   */
  it('⛔ cannot route to /w/:id/suspended, /archived or /deleted — no such routes exist', () => {
    for (const workspaceIds of [['ws-1'], ['ws-1', 'ws-2']]) {
      const { route } = resolveEntry(observedSession({ workspaceIds, lastUsedWorkspaceId: null }));
      expect(route).not.toMatch(/\/(suspended|archived|deleted)$/);
    }
  });
});
