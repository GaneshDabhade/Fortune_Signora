/**
 * **The scope ladder, checked against the design rather than against my
 * reading of it** — [TASK-1409](../../../docs/BACKLOG.md).
 *
 * ⚡ **The assertions parse
 * `docs/design-snapshot/screens/Fortune Signora System States.dc.html` and
 * compare.** ⛔ **A test that restated the four scopes in its own literals
 * would pass forever against a transcription error**, and a transcription
 * error is the likeliest defect in a file that is entirely data.
 *
 * 📁 **This is [D-138](../../../docs/DECISION_REGISTER.md)'s snapshot doing
 * the job it exists for**: the document is in the repository, so a test can
 * read it.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  LEGAL_STATES,
  SCOPES,
  SEVERITY,
  SURVIVES,
  IllegalScopeError,
  atLeast,
  escalate,
  isLegal,
  scopeOf,
  type Scope,
} from '@/lib/system-states/ladder';

const DESIGN = readFileSync(
  join(process.cwd(), '../docs/design-snapshot/screens/Fortune Signora System States.dc.html'),
  'utf8',
);

/** The design's `scopes` array, read out of the document's own script. */
function designScopes(): { t: string; when: string; survives: string; states: string }[] {
  // ⚠️ **Anchor on the declaration, not the first occurrence of the word.**
  // The document mentions `{{ scopes }}` as a template reference ~600 bytes
  // earlier, and `indexOf('scopes')` finds that instead — which parsed to
  // nothing. **The empty result failed the test rather than passing it**,
  // which is the only reason this was caught here and not in review.
  // It is an object property (`scopes: [`), not a bare assignment.
  const decl = /\bscopes\s*[:=]\s*\[/.exec(DESIGN);
  if (decl === null) throw new Error('the design document declares no `scopes` array');
  const open = DESIGN.indexOf('[', decl.index);
  let depth = 0;
  let end = open;
  for (let i = open; i < DESIGN.length; i += 1) {
    if (DESIGN[i] === '[') depth += 1;
    else if (DESIGN[i] === ']') {
      depth -= 1;
      if (depth === 0) {
        end = i;
        break;
      }
    }
  }
  const raw = DESIGN.slice(open, end + 1);
  const out: { t: string; when: string; survives: string; states: string }[] = [];
  for (const m of raw.matchAll(/\{\s*t:\s*'([^']+)'[\s\S]*?when:\s*'([^']+)'[\s\S]*?survives:\s*'([^']+)'[\s\S]*?states:\s*'([^']+)'\s*\}/g)) {
    const [, t, when, survives, states] = m;
    if (t === undefined || when === undefined || survives === undefined || states === undefined) {
      continue;
    }
    out.push({ t, when, survives, states });
  }
  return out;
}

describe('the ladder is the design’s, not a transcription of it', () => {
  it('⚡ reads four scopes out of the design document itself', () => {
    // The guard is proved able to fire: if the parse returned nothing, every
    // assertion below would pass vacuously.
    const scopes = designScopes();
    expect(scopes).toHaveLength(4);
    expect(scopes.map((s) => s.t.toLowerCase())).toEqual([...SCOPES]);
  });

  it('🔴 every state the design lists is legal at that scope, and nowhere else', () => {
    for (const scope of designScopes()) {
      const name = scope.t.toLowerCase() as Scope;
      // The design writes them as prose — "Retry, skeleton, region error,
      // empty result" — so compare on a normalised form rather than by
      // demanding the document use our identifiers.
      const listed = scope.states.split(',').map((s) => s.trim().toLowerCase().replace(/\s+/g, '-'));
      const ours = [...LEGAL_STATES[name]];
      expect(listed.length).toBe(ours.length);
      for (const state of listed) {
        // ⛔ Owned by this scope, and by no other — the property `isLegal`
        // exists to enforce.
        expect(scopeOf(state)).toBe(name);
      }
    }
  });

  it('states what survives, in the design’s own terms', () => {
    for (const scope of designScopes()) {
      const name = scope.t.toLowerCase() as Scope;
      expect(SURVIVES[name]).toBe(scope.survives);
    }
  });
});

describe('🔴 a scope refuses a state it does not own', () => {
  it('⛔ a 500 cannot render at region scope', () => {
    /**
     * ⚡ **This is the defect the ladder exists to prevent, inverted.** A
     * `500` drawn inside a region claims the page survived a failure that
     * took the application — and the person keeps clicking a page that is
     * already gone.
     */
    expect(isLegal('region', '500')).toBe(false);
    expect(() => {
      throw new IllegalScopeError('region', '500');
    }).toThrow(/app-scope state/);
  });

  it('⛔ an empty result cannot render at app scope', () => {
    // The opposite mistake, and the more damaging one: it tells somebody the
    // product is broken when one list happens to have nothing in it.
    expect(isLegal('app', 'empty-result')).toBe(false);
  });

  it('names what the scope does own, so the message is actionable', () => {
    expect(new IllegalScopeError('region', '404').message).toMatch(
      /region scope owns: retry, skeleton, region-error, empty-result/,
    );
  });

  it('⛔ refuses a state the design never defined at all', () => {
    expect(scopeOf('teapot')).toBeNull();
    expect(new IllegalScopeError('page', 'teapot').message).toMatch(/not a system state/);
  });
});

describe('⚡ severity is a property of the state, never of the scope', () => {
  it('🔴 absence and failure are different colours at the same scope', () => {
    /**
     * 📁 **The grammar**: *"Neutral for absence, warn for permission and
     * interruption, risk for genuine failure… The colour is never
     * decorative."* ⛔ **Deriving severity from scope would paint a missing
     * record like a broken one** — the same conflation
     * [TASK-445](../../../docs/BACKLOG.md)'s *stated absence* exists to keep
     * apart.
     */
    expect(SEVERITY['404']).toBe('neutral');
    expect(SEVERITY['500']).toBe('risk');
    // Both page scope, different severities.
    expect(SEVERITY['404']).not.toBe(SEVERITY['403']);
    // Both region scope, different severities.
    expect(SEVERITY['empty-result']).toBe('neutral');
    expect(SEVERITY['region-error']).toBe('risk');
  });

  it('every state the ladder defines has a severity', () => {
    for (const scope of SCOPES) {
      for (const state of LEGAL_STATES[scope]) {
        expect(SEVERITY[state]).toBeDefined();
      }
    }
  });

  it('📁 maintenance is brand, because a planned event is not a failure', () => {
    expect(SEVERITY.maintenance).toBe('brand');
  });
});

describe('📁 escalating is a decision with a reason', () => {
  it('orders the ladder region → page → app → platform', () => {
    expect(atLeast('app', 'region')).toBe(true);
    expect(atLeast('region', 'app')).toBe(false);
    expect(atLeast('page', 'page')).toBe(true);
  });

  it('🔴 refuses an escalation with no stated reason', () => {
    /**
     * 📁 **§01: *"Escalating to page or app requires a stated reason in the
     * component, not a default."*** ⚡ **The friction is the design's intent**
     * — escalation costs the person their filters and their scroll position,
     * so it is made awkward exactly where an author would reach for it.
     */
    expect(() => escalate('region', 'page', '')).toThrow(/stated reason/);
    expect(() => escalate('region', 'page', '   ')).toThrow(/stated reason/);
    expect(escalate('region', 'page', 'the record itself is missing')).toBe('page');
  });

  it('⛔ refuses to escalate downward, which is not escalation', () => {
    expect(() => escalate('app', 'region', 'a reason')).toThrow(/up the ladder/);
  });
});
