/**
 * 🔴 **📁 Design System §17 `2.4.7`** — ***"2px brand focus ring at 2px offset
 * plus a border change; **never suppressed**."***
 *
 * ⛔ **Three onboarding inputs carried a bare `outline-none`**, and **measured
 * in a browser against the real cascade it defeated BOTH halves** of the
 * indicator `globals.css` draws:
 *
 * | | outline | ring |
 * |---|---|---|
 * | **with `outline-none`** | `2px solid rgba(0,0,0,0)` | ⛔ **none** |
 * | **without it** | ✅ `1px solid rgb(19,78,118)` | ✅ `3px rgb(230,241,248)` |
 *
 * ⚠️ **A keyboard user had no visible focus on the first screens a customer
 * sees.**
 *
 * ## ⚡ Why a source guard rather than a browser assertion
 *
 * ⛔ **The browser proves it for the element it focuses; it cannot prove the
 * absence of a fourth one.** ⚡ **A Tailwind utility of equal specificity,
 * emitted after `@layer base`, wins outright** — so the property worth
 * protecting is *no interactive element suppresses the outline without
 * providing one*, and that is a statement about the source.
 *
 * 📁 **The one legitimate exception is `focus-proxy`** ([B-1058](../../../docs/BUGS.md)):
 * a control with `overflow-hidden` clips its input's indicator, so the ring is
 * drawn on the wrapper and the inner input suppresses its own. ⚡ **And a
 * `tabIndex={-1}` focus target legitimately suppresses one too** — it receives
 * focus for a screen reader and a ring there would confuse a sighted reader.
 */
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const ROOTS = ['app', 'components'];

function sources(dir: string, out: string[] = []): string[] {
  for (const entry of readdirSync(dir)) {
    const p = join(dir, entry);
    if (statSync(p).isDirectory()) sources(p, out);
    else if (p.endsWith('.tsx')) out.push(p);
  }
  return out;
}

/** ⚡ Bare `outline-none`, never the paired `focus-visible:outline-none`. */
const BARE = /(?<!focus-visible:)(?<!focus:)\boutline-none\b/;

describe('🔴 §17 2.4.7 — a focus indicator is never suppressed without a replacement', () => {
  const files = ROOTS.flatMap((r) => sources(r));

  it('⚠️ vacuity guard — the sweep actually reads the product', () => {
    expect(files.length).toBeGreaterThan(50);
  });

  it('⛔ no element suppresses its outline unless something else draws one', () => {
    const offenders: string[] = [];

    for (const file of files) {
      const lines = readFileSync(file, 'utf8').split('\n');
      lines.forEach((line, index) => {
        const code = line.trim();
        // ⛔ Comments describe the rule; they do not break it.
        if (code.startsWith('*') || code.startsWith('//') || code.startsWith('/*')) return;
        if (!BARE.test(line)) return;

        // ✅ **The two legitimate shapes**, looked for in the surrounding block
        // rather than on the matched line — 📁 the wrapper's `focus-proxy` and
        // the element's own `tabIndex={-1}` are both several lines away, and in
        // this repository's commenting style *"several"* is sixteen.
        //
        // ⚠️ **A window is an approximation and the trade is stated rather than
        // hidden**: too small and it reports two correct elements as offenders,
        // which is what 14 did. ⛔ **Too large and an unrelated `focus-proxy`
        // nearby could excuse a real one** — which is why the window is 24 and
        // not the whole file, and why the vacuity guard above exists.
        //
        // 🔴 **The exception must be CODE, never prose** — and this cost a
        // fire-test to find. ⛔ **The docstring explaining this very rule
        // quotes both `focus-proxy` and `tabIndex={-1}`**, so with comments
        // included the guard excused the offender it was written to catch:
        // **reintroducing `outline-none` on `company-form.tsx` left it green.**
        //
        // ⚡ **The mirror of the offender rule above.** There, a comment must
        // not TRIGGER the check; here, a comment must not SUPPRESS it —
        // ⛔ **and the second direction is the dangerous one, because it fails
        // silently.**
        const block = lines
          .slice(Math.max(0, index - 24), index + 6)
          .filter((l) => {
            const c = l.trim();
            return !c.startsWith('*') && !c.startsWith('//') && !c.startsWith('/*');
          })
          .join('\n');
        if (/focus-proxy/.test(block)) return;
        if (/tabIndex=\{-1\}/.test(block)) return;

        offenders.push(`${file}:${index + 1}`);
      });
    }

    expect(
      offenders,
      `these suppress the focus indicator with nothing in its place:\n  ${offenders.join('\n  ')}`,
    ).toEqual([]);
  });
});
