/**
 * **What AI Research can honestly show** —
 * [TASK-1418](../../../docs/BACKLOG.md).
 *
 * 🔴 **Measured before any screen**, because
 * [TASK-1415](../../../docs/BACKLOG.md) proved a row's framing cannot be
 * trusted on its own.
 */
import { describe, expect, it } from 'vitest';

import {
  RESEARCH_FEATURES,
  absent,
  partial,
  published,
} from '@/lib/research/capability';
import { edit, regenerate, type NarrativeSentence } from '@/lib/research/edits';

describe('⛔ every feature the platform cannot fill says what is missing', () => {
  it('absent and partial both carry a sentence; published does not need one', () => {
    for (const feature of [...absent(), ...partial()]) {
      expect(feature.absence, `${feature.id} says nothing`).toBeTruthy();
      expect(feature.absence!.length).toBeGreaterThan(30);
    }
  });

  it('🔴 and never says "coming soon"', () => {
    for (const feature of [...absent(), ...partial()]) {
      expect(feature.absence!.toLowerCase()).not.toContain('coming soon');
    }
  });

  it("⛔ speaks the customer's language", () => {
    // 📁 ADR-0034 — the translation lives at the frontend edge.
    for (const feature of [...absent(), ...partial()]) {
      const said = feature.absence!.toLowerCase();
      for (const ours of ['workspace', 'endpoint', 'artifact', 'module', 'hook']) {
        expect(said, `${feature.id} says "${ours}"`).not.toContain(ours);
      }
    }
  });

  it('🔴 records the finding this row turns on — Signora cannot be ASKED anything', () => {
    /**
     * ⚠️ **The design's central promise** — *"Why is EMEA enterprise
     * slipping?"* — **and research is scoped to an ACCOUNT.** ⛔ **A screen
     * with a question box would be inventing the product's headline
     * capability.**
     */
    const ask = RESEARCH_FEATURES.find((f) => f.id === 'ask')!;

    expect(ask.capability).toBe('absent');
    expect(ask.absence).toMatch(/one account at a time/i);
  });

  it('⚡ PARTIAL is its own answer, never collapsed into absent', () => {
    // ⛔ The coarse answer is true — `running` really is published — and
    // hiding it would understate what the product does.
    const ids = partial().map((f) => f.id);

    expect(ids).toContain('progress');
    expect(absent().map((f) => f.id)).not.toContain('progress');
  });

  it('every feature is counted exactly once', () => {
    expect(published().length + partial().length + absent().length).toBe(
      RESEARCH_FEATURES.length,
    );
    const ids = RESEARCH_FEATURES.map((f) => f.id);
    expect(new Set(ids).size).toBe(ids.length);
  });
});

describe('⚡ the edit law is shared, and this is its second caller', () => {
  it('preserves a person’s sentence through a regeneration', () => {
    /**
     * 📁 **AI Research's design**: *"Editable · your edits are preserved
     * through regeneration."* ⛔ **The same sentence Reports writes**, which is
     * why the law moved rather than being written twice.
     */
    const generated = (id: string, text: string): NarrativeSentence => ({
      id,
      text,
      author: 'generated',
      editedBy: null,
    });
    const current = [generated('s1', 'the model said this'), generated('s2', 'and this')];
    const edited = [edit(current[0]!, 'M. Reinhardt asserted this', 'M. Reinhardt'), current[1]!];

    const after = regenerate(edited, [
      generated('s1', 'the model has changed its mind'),
      generated('s2', 'and this, differently'),
    ]);

    expect(after[0]!.text).toBe('M. Reinhardt asserted this');
    expect(after[0]!.author).toBe('person');
    // ⚡ The generated one DID move, which is what makes the first assertion
    // mean something.
    expect(after[1]!.text).toBe('and this, differently');
  });
});
