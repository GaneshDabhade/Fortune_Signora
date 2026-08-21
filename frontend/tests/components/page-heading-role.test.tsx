import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

import { describe, expect, it } from 'vitest';

/**
 * 🔴 **[B-1056](../../../docs/BUGS.md) — two screens fell out of a sweep that was
 * supposed to cover every one.**
 *
 * 📁 **[TASK-1446](../../../docs/BACKLOG.md)'s own words are what make this a gap
 * rather than a preference**: ***"a list of every screen with its own heading,
 * with a migrate/keep verdict each."*** ⛔ **It measured eleven and published
 * nine.** `/signals` and `/profile/security` were the two that fell out, and
 * `/workspaces` had never been asked about at all.
 *
 * ⚠️ **QE's own suggestion, and it is the right one:** ***"a guard would be
 * cheaper than a sweep — a test asserting that every route-level `h1` uses the
 * `Title` role (with named exemptions) makes the eleventh screen
 * unrepresentable rather than merely unlisted."***
 *
 * ✅ **So the list IS this file.** ⛔ **A new screen with an `h1` fails here
 * until somebody writes its verdict down**, which is the property the prose
 * sweep could not have.
 */

const APP = join(process.cwd(), 'app');

/**
 * ⛔ **Every `h1` outside the authenticated shell, with the reason.**
 *
 * ⚡ **`KEEP` is a verdict, not an omission** — 📁 shell rule 03 governs views a
 * customer reaches inside the shell, and a 26px `Title` on an interstitial
 * would make a waypoint look like a destination.
 */
const KEEP: Record<string, string> = {
  // 📁 TASK-1446's own two `KEEP`s, unchanged.
  'app/(app)/join/[workspaceId]/page.tsx':
    'a confirmation card, not a page in the shell — a centred card with no rail beside it',
  'app/dev/mailbox/page.tsx': 'a development tool, not a customer surface',

  // 🔴 **The verdict [B-1056](../../../docs/BUGS.md) asked for and nobody had
  // given.** ⚠️ **QE raised it as a question rather than a defect, and the
  // answer is the same reasoning `/join` got**: the workspace chooser renders
  // OUTSIDE `(app)` — there is no rail, no top bar and no breadcrumb — so it is
  // an interstitial a person passes through, not a destination.
  'app/workspaces/page.tsx': 'the organization chooser — an interstitial outside the shell',

  // ⚡ **Authentication is its own shell** — a centred card the design draws
  // separately, outside the app shell entirely.
  'app/(auth)/auth-shell.tsx': 'the authentication shell — a centred card outside the app shell',
  'app/(auth)/gate/gate-screen.tsx': 'an environment gate, before authentication',
};

// ⚡ **Onboarding is deliberately NOT exempted.** ✅ **Both of its headings
// already consume `text-title`**, so they pass on the rule rather than on a
// verdict — 📁 which is what a KEEP list should shrink toward.

/**
 * ⚠️ **`RecordHeader` and `PageHeader` author the `h1` for their callers**, so a
 * screen that composes one has no literal `<h1` of its own and never reaches
 * this check. ✅ **That is the destination, not a loophole**: those components
 * render `text-title` and 📁 `design-scale.test.ts` asserts the role's values.
 */
function headings(dir: string): { file: string; line: number; source: string }[] {
  const found: { file: string; line: number; source: string }[] = [];
  for (const entry of readdirSync(dir)) {
    const path = join(dir, entry);
    if (statSync(path).isDirectory()) {
      found.push(...headings(path));
      continue;
    }
    if (!entry.endsWith('.tsx')) continue;
    /**
     * ⚠️ **Comments are blanked, not skipped** — line numbers must survive.
     * ⛔ **Three files in this repository QUOTE the design's own `<h1>` markup
     * inside a comment**, and a scanner that reads those as headings reports a
     * defect that is not there — 📁 the same false positive QE had to strip out
     * of [B-1051](../../../docs/BUGS.md)'s method before filing it.
     */
    const bare = readFileSync(path, 'utf8')
      .replace(/\/\*[\s\S]*?\*\//g, (block) => block.replace(/[^\n]/g, ' '))
      .replace(/^\s*\/\/.*$/gm, '');
    const lines = bare.split('\n');
    lines.forEach((source, index) => {
      if (!/<h1\b/.test(source)) return;
      // ⚠️ **The element, not the line.** ⛔ `onboarding-shell.tsx` opens `<h1`
      // and carries its class four lines down, and a line-scoped check reads
      // that as an unstyled heading.
      found.push({
        file: relative(process.cwd(), path),
        line: index + 1,
        source: lines.slice(index, index + 8).join(' '),
      });
    });
  }
  return found;
}

describe('📁 §04 — every route-level heading is the `Title` role', () => {
  it('⛔ has a verdict for every `h1` in the product', () => {
    const all = headings(APP);
    // ⚡ **The sweep measured eleven.** ⛔ **A count that silently fell to two
    // would pass every assertion below** — 📁 the truncation-that-reads-as-a-
    // result failure this lane has met four times.
    expect(all.length).toBeGreaterThanOrEqual(11);

    const undecided = all.filter(
      ({ file, source }) => !(file in KEEP) && !source.includes('text-title'),
    );
    expect(
      undecided.map(({ file, line }) => `${file}:${line}`),
      'these author an h1 with neither the Title role nor a KEEP verdict',
    ).toEqual([]);
  });

  it('⛔ every KEEP names a file that still authors a heading', () => {
    // ⚡ **An exemption for a screen that no longer exists is a list rotting
    // quietly** — the state this guard replaced.
    const authored = new Set(headings(APP).map(({ file }) => file));
    const stale = Object.keys(KEEP).filter((file) => !authored.has(file));
    expect(stale, 'these are exempted and author no h1').toEqual([]);
  });

  /**
   * 🔴 **The two screens the row named**, asserted by name so that a regression
   * says which row it broke rather than only that something drifted.
   */
  it('✅ /signals and /profile/security carry the Title role', () => {
    const byFile = new Map(headings(APP).map(({ file, source }) => [file, source]));
    // ⚡ `/signals` authors its heading through `PageHeader` now, so it has no
    // literal `<h1` — which is the stronger of the two outcomes.
    expect(byFile.has('app/(app)/signals/page.tsx')).toBe(false);
    expect(byFile.get('app/(app)/profile/security/page.tsx')).toContain('text-title');
  });
});
