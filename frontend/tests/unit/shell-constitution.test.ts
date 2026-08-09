/**
 * **The shell's constitution, checked against the design** —
 * [TASK-1408](../../../docs/BACKLOG.md).
 *
 * 🔴 **The row makes the fourteen rules the acceptance criteria**
 * ([D-210](../../../docs/DECISION_REGISTER.md)), so they are asserted from
 * `Fortune Signora App Shell.dc.html` rather than from my reading of it.
 *
 * ⚠️ **The last time this technique was used it caught two anchoring bugs
 * before it caught anything about the design** ([TASK-1409](../../../docs/BACKLOG.md)'s
 * ladder), which is the argument for the vacuity guard below rather than
 * against the technique.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  MAX_BANNERS,
  SHELL_RULES,
  admitBanners,
  bannerRule,
  rendersInsideShell,
} from '@/lib/shell/constitution';

const DESIGN = readFileSync(
  join(process.cwd(), '../docs/design-snapshot/screens/Fortune Signora App Shell.dc.html'),
  'utf8',
);

/** Reads an array literal out of the design's own script by name. */
function designArray(name: string): string {
  const decl = new RegExp(`\\b${name}\\s*[:=]\\s*\\[`).exec(DESIGN);
  if (decl === null) throw new Error(`the design declares no \`${name}\``);
  const open = DESIGN.indexOf('[', decl.index);
  let depth = 0;
  for (let i = open; i < DESIGN.length; i += 1) {
    if (DESIGN[i] === '[') depth += 1;
    else if (DESIGN[i] === ']') {
      depth -= 1;
      if (depth === 0) return DESIGN.slice(open, i + 1);
    }
  }
  throw new Error(`unterminated \`${name}\``);
}

function designShellRules(): string[] {
  return [...designArray('shellRules').matchAll(/'((?:[^'\\]|\\.)*)'/g)]
    .map((m) => m[1] ?? '')
    .map((r) => r.replace(/\\'/g, "'"))
    .filter((r) => r.length > 0);
}

describe('the fourteen rules are the design’s, verbatim and in order', () => {
  it('⚡ reads them out of the design document itself', () => {
    // The vacuity guard: an empty parse must fail here rather than let every
    // assertion below pass against nothing.
    const rules = designShellRules();
    expect(rules.length).toBeGreaterThan(0);
    expect(rules).toHaveLength(14);
  });

  it('🔴 matches this repository’s copy exactly — no paraphrase, no reordering', () => {
    /**
     * ⛔ **A paraphrased rule is a different rule.** [D-137](../../../docs/DECISION_REGISTER.md)
     * forbids a summarised design artifact for exactly this reason, and the
     * numbering is cited in review, so order is part of the content.
     */
    expect([...SHELL_RULES]).toEqual(designShellRules());
  });

  it('📁 rule 14 is what keeps the other thirteen true', () => {
    // *"Every new shell capability is an amendment to this document, not a
    // local decision."* ⛔ It must be last, because it governs additions.
    expect(SHELL_RULES[SHELL_RULES.length - 1]).toMatch(/amendment to this document/);
  });
});

describe('📁 rule 10 — at most two banners, environment before commercial', () => {
  it('orders environment ahead of commercial whatever order they arrive in', () => {
    const admitted = admitBanners([{ kind: 'commercial' }, { kind: 'environment' }], false);
    expect(admitted.map((b) => b.kind)).toEqual(['environment', 'commercial']);
  });

  it('⛔ never admits a third', () => {
    const admitted = admitBanners(
      [{ kind: 'environment' }, { kind: 'commercial' }, { kind: 'commercial' }],
      false,
    );
    expect(admitted).toHaveLength(MAX_BANNERS);
  });

  it('🔴 suppresses commercial banners entirely inside sandbox', () => {
    /**
     * 📁 *"Suppressed entirely inside sandbox."* ⚡ **Suppressed, not
     * queued** — a trial countdown shown over a copy of production is an
     * upsell against data that is not real.
     */
    const admitted = admitBanners([{ kind: 'environment' }, { kind: 'commercial' }], true);
    expect(admitted.map((b) => b.kind)).toEqual(['environment']);
  });
});

describe('🔴 a risky environment banner cannot be dismissed', () => {
  it('📁 "dismissible only when the state is not risky"', () => {
    /**
     * ⚡ **The sentence this protects is *"Viewing as J. Okafor · every action
     * is logged"*.** ⛔ **Dismissing it leaves somebody acting as another
     * person with nothing on screen saying so**, which is the one banner whose
     * absence changes what a customer believes they are doing.
     */
    expect(bannerRule('environment', true).dismissible).toBe(false);
    expect(bannerRule('environment', false).dismissible).toBe(true);
    // Commercial is always dismissible — it is never load-bearing.
    expect(bannerRule('commercial', true).dismissible).toBe(true);
  });
});

describe('📁 rule 13 — errors render inside the shell unless the shell itself failed', () => {
  it('⚡ agrees with TASK-1409’s ladder without either being adjusted', () => {
    /**
     * **[TASK-1409](../../../docs/BACKLOG.md) says *"app scope renders INSIDE
     * this frame; platform scope replaces it"*, and rule 13 says the same
     * thing from the shell's side.** ✅ **Two rows, two designs, one answer** —
     * recorded because a later slice reading only one of them would otherwise
     * have to guess.
     */
    expect(rendersInsideShell('region')).toBe(true);
    expect(rendersInsideShell('page')).toBe(true);
    expect(rendersInsideShell('app')).toBe(true);
    // ⛔ Only the platform state replaces the frame — it is served statically
    // with no dependency on the application at all.
    expect(rendersInsideShell('platform')).toBe(false);
  });
});
