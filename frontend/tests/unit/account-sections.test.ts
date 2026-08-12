/**
 * **What Account 360 can honestly show** — [TASK-1415](../../../docs/BACKLOG.md).
 *
 * 🔴 **The row claims every section is *"a composition of intelligence the
 * platform ALREADY produces"*.** ⚠️ **These assert the measurement instead**,
 * because the claim is half true and a screen built on the claim would invent
 * the other half.
 */
import { describe, expect, it } from 'vitest';

import {
  ACCOUNT_SECTIONS,
  absent,
  onThisPage,
  supplied,
} from '@/lib/accounts/sections';
import * as hooks from '@/lib/query/hooks';
import * as commercialHooks from '@/lib/query/hooks/commercial';
import * as timelineHooks from '@/lib/query/hooks/timeline';

describe("🔴 every supplied section names a read that EXISTS", () => {
  it('and the name resolves to an exported hook', () => {
    /**
     * ⛔ **This is the assertion that stops the file becoming a wish list.**
     * ⚡ **`source` starts with the hook's name**, so a section claiming
     * `useAccountHealth` fails here rather than at runtime — **and a section
     * whose read is deleted fails here too.**
     */
    // ⚠️ **THREE modules, because the reads live in three, and finding that
    // out is what this assertion is for.** ⛔ Account-scoped reads are in
    // `hooks.ts`, the workspace-level declarations in `hooks/commercial.ts`,
    // and the timeline in `hooks/timeline.ts`. **Checking only the first would
    // have let two files' worth of claims through unverified** — and it did,
    // twice, before this test named them.
    const exported = { ...hooks, ...commercialHooks, ...timelineHooks };

    for (const section of supplied()) {
      const named = section.source.split(' ')[0]!;
      if (!named.startsWith('use')) continue;
      expect(named in exported, `${section.id} names ${named}, which is not exported`).toBe(true);
    }
  });

  it('⚡ at least one supplied section names each of the account-scoped reads it claims', () => {
    // ⚠️ **Vacuity guard.** If `supplied()` returned nothing, the assertion
    // above would pass over an empty list.
    expect(supplied().length).toBeGreaterThan(5);
  });
});

describe('🔴 a workspace-wide declaration is never an account fact', () => {
  /**
   * 📁 **[TASK-1476](../../../docs/BACKLOG.md), 2026-08-12.** ⛔ **`contacts`
   * was marked `supplied` and sourced from `useBuyingCommittee`**, hedged in a
   * comment as *"partially"*.
   *
   * ⚡ **It is a different question with the same words.** `GET
   * /buying-committee` is `commercial_profile`'s and its own summary is *"who
   * decides about what this workspace **sells**"* — **the ICP's committee,
   * declared once and identical on every account.** 🔴 **Under the heading
   * *Contacts & decision makers* it tells a rep that THIS company has those
   * people.**
   *
   * ⚠️ **The guard is at the seam that failed** ([B-191](../../../docs/BUGS.md)):
   * the defect was a workspace-scoped read claimed as an account-scoped one,
   * **so the assertion is about the source and not about the rendering.**
   */
  it('⛔ no section claims the ICP buying committee as this account’s people', () => {
    for (const section of ACCOUNT_SECTIONS) {
      expect(
        section.source,
        `${section.id} sources a workspace-wide declaration as an account fact`,
      ).not.toContain('useBuyingCommittee');
    }
  });

  it('🔴 and Contacts stays absent while nothing supplies a name', () => {
    /**
     * ⛔ **Not a stylistic pin.** 📁 `people` has no name column, [C-221]
     * is its specification rather than a limitation, and whether a provider
     * could supply one is ❓1 of ADR-0400, gated on **TASK-429 — a commercial
     * decision.** ⚡ **The day that lands, this test is the thing that says
     * the section may change**, which is what a trigger looks like when it is
     * checkable rather than remembered.
     */
    const contacts = ACCOUNT_SECTIONS.find((s) => s.id === 'contacts');
    expect(contacts?.supply).toBe('absent');
    // ⚡ **The near miss is named in the source**, so the next reader does not
    // re-derive that `people` exists and stops there — which is the mistake
    // this correction is fixing.
    expect(contacts?.source).toContain('people');
    expect(contacts?.source).toContain('never a name');
  });
});

describe('⛔ an absent section says what Signora cannot answer', () => {
  it('every absent section carries an absence sentence', () => {
    // 📁 §20c: a screen with no module behind it ships a DESIGNED empty state.
    // ⛔ A section that vanished would read as a bug; one that said nothing
    // would read as an empty account.
    for (const section of absent()) {
      expect(section.absence, `${section.id} is absent and says nothing`).toBeTruthy();
      expect(section.absence!.length).toBeGreaterThan(40);
    }
  });

  it('🔴 and never says "coming soon"', () => {
    /**
     * 📁 **The rail already paid for that once** — *"at M12.3, three of six
     * said `coming soon` on the screen a customer sees first."* ⚡ **An absence
     * states what the section would show and what is missing**, which is
     * something a customer can act on.
     */
    for (const section of absent()) {
      expect(section.absence!.toLowerCase()).not.toContain('coming soon');
      expect(section.absence!.toLowerCase()).not.toContain('under construction');
    }
  });

  it("⛔ speaks the customer's language, not this repository's", () => {
    // 📁 ADR-0034: the translation lives at the frontend edge.
    for (const section of absent()) {
      const sentence = section.absence!.toLowerCase();
      for (const ours of ['workspace', 'endpoint', 'module', 'provider port', 'hook']) {
        expect(sentence, `${section.id} says "${ours}"`).not.toContain(ours);
      }
    }
  });

  it('⚡ names what is missing in engineering terms where a customer will not read it', () => {
    // `source` is for the next lane and never reaches a screen, so it is
    // allowed — and required — to be specific about the gap.
    for (const section of absent()) {
      expect(section.source.length).toBeGreaterThan(20);
    }
  });
});

describe("📁 the rail lists EVERY section, including what cannot be filled", () => {
  it('so the gap is visible rather than inferred from an omission', () => {
    // ⛔ **A page that silently omits a section is indistinguishable from one
    // with a bug**, and the next lane cannot tell which.
    expect(onThisPage()).toHaveLength(ACCOUNT_SECTIONS.length);
    expect(supplied().length + absent().length).toBe(ACCOUNT_SECTIONS.length);
  });

  it('🔴 records the measurement this row turns on — most of the design is not yet supplied', () => {
    /**
     * ⚠️ **Asserted as a RANGE rather than an exact count**, so adding a
     * capability does not fail a test that has nothing to do with it — ⛔ **but
     * a slice that quietly marked everything `supplied` would.**
     */
    expect(absent().length).toBeGreaterThan(3);
    expect(supplied().length).toBeGreaterThan(3);
  });

  it('every section has a stable id and the design’s own label', () => {
    const ids = ACCOUNT_SECTIONS.map((s) => s.id);
    expect(new Set(ids).size).toBe(ids.length);
    for (const section of ACCOUNT_SECTIONS) {
      expect(section.label.length).toBeGreaterThan(2);
    }
  });
});
