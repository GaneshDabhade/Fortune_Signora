/**
 * **Home is a slot, not a screen** — [TASK-1405](../../../docs/BACKLOG.md).
 *
 * 🔴 **The property worth protecting is TOTALITY**: 📁 *"a composition always
 * resolves, so Home ALWAYS renders."* The App Shell depends on it, so a
 * resolver that could return nothing would be a shell with a hole in it.
 */
import { describe, expect, it } from 'vitest';

import {
  COMPOSITION_NAME,
  COMPOSITION_QUESTION,
  resolveComposition,
  type Composition,
  type CompositionInput,
} from '@/lib/home/composition';

const ALL: Composition[] = ['executive', 'seller', 'revenue_operations', 'activation'];

describe('🔴 a composition always resolves', () => {
  it('⛔ every combination of inputs returns one, and never undefined', () => {
    // ⚡ Exhaustive over the input space rather than a sample: two booleans
    // times four role values is eight cases, so there is no reason to guess.
    const roles: CompositionInput['primaryRole'][] = [
      'executive',
      'seller',
      'revenue_operations',
      null,
    ];
    for (const workspaceIsEmpty of [true, false]) {
      for (const primaryRole of roles) {
        const got = resolveComposition({ workspaceIsEmpty, primaryRole });
        expect(ALL).toContain(got);
      }
    }
  });

  it('⚡ and it is a pure function — the same input gives the same answer', () => {
    const input: CompositionInput = { workspaceIsEmpty: false, primaryRole: 'seller' };
    expect(resolveComposition(input)).toBe(resolveComposition(input));
  });
});

describe('📁 emptiness wins over role, and that ordering is the design’s', () => {
  it('🔴 an executive whose workspace is empty is asked how to begin', () => {
    /**
     * 📁 Activation's qualifier is *"Any role, empty workspace"*. ⛔ **The
     * failure this prevents is a dashboard of six empty cards** — an executive
     * composition rendered for a workspace that holds nothing would report on
     * nothing and look broken rather than new.
     */
    expect(resolveComposition({ workspaceIsEmpty: true, primaryRole: 'executive' })).toBe(
      'activation',
    );
  });

  it('⚡ and a populated workspace uses the role once one exists', () => {
    // ⛔ This is the case NOTHING can produce today — C-268: no primary role is
    // published. It is asserted anyway, because the resolver is the thing that
    // must already be right when the field arrives.
    expect(resolveComposition({ workspaceIsEmpty: false, primaryRole: 'executive' })).toBe(
      'executive',
    );
    expect(resolveComposition({ workspaceIsEmpty: false, primaryRole: 'seller' })).toBe('seller');
    expect(
      resolveComposition({ workspaceIsEmpty: false, primaryRole: 'revenue_operations' }),
    ).toBe('revenue_operations');
  });
});

describe('⛔ an unknown person is not guessed at', () => {
  it('🔴 no role and a populated workspace falls back to Activation, never to a guess', () => {
    /**
     * ⚠️ **The tempting wrong move is to default to `seller` because most
     * people are sellers.** ⛔ That is inventing what a person is from a
     * population statistic, and it would show an AE's working day to a CFO.
     * ✅ **Activation is the only composition that is honest about knowing
     * nothing** — it asks how to begin.
     */
    expect(resolveComposition({ workspaceIsEmpty: false, primaryRole: null })).toBe('activation');
  });
});

describe('📁 the four are the design’s four', () => {
  it('⛔ every composition has a question and a name, and there is no fifth', () => {
    expect(Object.keys(COMPOSITION_QUESTION).sort()).toEqual([...ALL].sort());
    expect(Object.keys(COMPOSITION_NAME).sort()).toEqual([...ALL].sort());
  });

  it('⚡ the questions are the design’s, not paraphrases', () => {
    expect(COMPOSITION_QUESTION.executive).toBe('How are we doing?');
    expect(COMPOSITION_QUESTION.seller).toBe('What do I do today?');
    expect(COMPOSITION_QUESTION.revenue_operations).toBe('Is the system healthy?');
    expect(COMPOSITION_QUESTION.activation).toBe('How do I begin?');
  });

  it('⛔ and the tables are frozen, so a caller cannot add a fifth at runtime', () => {
    expect(Object.isFrozen(COMPOSITION_QUESTION)).toBe(true);
    expect(Object.isFrozen(COMPOSITION_NAME)).toBe(true);
  });
});
