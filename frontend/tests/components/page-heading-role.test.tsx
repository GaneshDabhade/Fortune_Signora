import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

import { describe, expect, it } from 'vitest';

import { screenDocument } from '../support/design-snapshot';

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

/**
 * 🔴 **Settings — the design's own sentences, asserted against the document.**
 *
 * ⛔ **Not against a copy of them.** 📁 The subtitle read *"The organizations you
 * belong to"*, which describes the LAST CARD on the page rather than the page,
 * and nothing could have caught it because nothing compared the screen to the
 * design.
 */
describe('📁 Settings says what the design says', () => {
  it("carries the design's subtitle, read out of the design document", () => {
    // 🔴 **[B-1063](../../../docs/BUGS.md), found by QE — this read the product
    // owner's uncommitted `Design Documents/` behind `if (!existsSync(path))
    // return`.** ⛔ **A bare `return` is not a skip: it is REPORTED AS A PASS,
    // and QE certifies on a machine WITHOUT that corpus** — so the one
    // assertion comparing this screen to its design could never fail where it
    // mattered, and the same commit certified differently on two machines.
    // ⚡ **`docs/design-snapshot/` is committed and is the implementation
    // authority (D-138), so reading it removes the hidden input rather than
    // making it visible.** 📁 **Verified byte-for-byte: the snapshot carries
    // this sentence exactly once.**
    const markup = screenDocument('Fortune Signora Settings.dc.html');

    const subtitle = 'Every change is attributed, reversible and visible in the audit log';
    expect(markup, 'the design states this subtitle').toContain(subtitle);

    const page = readFileSync(join(process.cwd(), 'app', '(app)', 'settings', 'page.tsx'), 'utf8');
    expect(page, 'the screen states it too').toContain(subtitle);

    // ⚠️ **Comments stripped before the negative assertion.** 🔴 **This failed on
    // its first run against the comment that RECORDS the old sentence** — the
    // same false positive the design-token guard produced, and the same fix.
    // ⛔ **A guard that reads documentation as code teaches people not to
    // document.**
    const bare = page.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');
    expect(bare, 'and not the sentence it replaced').not.toContain(
      'The organizations you belong to',
    );
  });
});

/**
 * 🔴 **A production string was renamed and the tests asserting it were not —
 * twice, in one day, by the same lane.**
 *
 * ⛔ **First: QE found three journey tests failing on a certified candidate.**
 * ⛔ **Then, having "fixed" it, three MORE failed** — because the fix updated
 * the file QE named and nothing grepped for the rest. **`accessibility.spec.ts`,
 * `golden-journey.spec.ts` and the `brief` page object all carried it too.**
 *
 * ⚡ **A unit test cannot catch this** — the strings live in Playwright specs,
 * which vitest never loads — **so the guard has to read them as text.**
 *
 * ⚠️ **This asserts the ABSENCE of retired vocabulary**, which is the shape that
 * caught the false `Recommendations` affordance earlier today. **A guard that
 * says *this must not appear* is the one that survives a rename.**
 */
describe('⛔ retired heading vocabulary never returns', () => {
  /**
   * 📁 **Each of these appears ZERO times in the 35-document design snapshot**,
   * verified independently by QE. ⚡ **The replacement is the design's own word.**
   */
  const RETIRED: Record<string, string> = {
    'What contributed': 'Account score',
    'Who you compete against': 'Competitors',
    // ⚡ **The seventh, and the guard is why it is here rather than in a third
    // round of failures**: `pages/brief.ts` carried it too, and a page object
    // is the third time this lane has missed one. ⛔ **A page object is the
    // worst place to miss a rename** — it takes every spec that uses it down,
    // in files the rename never touched.
    'What has happened': 'Recent activity',
  };

  /**
   * ⚠️ **Scoped to the Account 360 record surface, where the vocabulary was
   * retired — and the exclusion is a finding rather than a convenience.**
   *
   * 🔴 **This guard immediately caught `components/commercial/competitors.tsx`**,
   * which the rename had missed. ⛔ **It is a DIFFERENT thing**: the
   * `CompetitorsEditor` on `/settings/products`, where a customer *declares*
   * competitors, against the Account 360 card that *reads* them.
   *
   * ⛔ **Renaming it now would be premature.** 📁 `/settings/products` appears in
   * **no** final design document's Settings nav, and whether that page should
   * exist at all is an open question recorded in the Settings audit. **A heading
   * on a page whose existence is unresolved is not a heading to settle first.**
   */
  const SETTINGS_SURFACE = /^(components\/commercial|app\/\(app\)\/settings)\//;

  function sources(dir: string): string[] {
    const out: string[] = [];
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const path = join(dir, entry.name);
      if (entry.isDirectory()) out.push(...sources(path));
      else if (/\.tsx?$/.test(entry.name)) out.push(path);
    }
    return out;
  }

  it('appears in no assertion, in any suite', () => {
    const offenders: string[] = [];
    for (const file of [
      ...sources(join(process.cwd(), 'app')),
      ...sources(join(process.cwd(), 'components')),
      ...sources(join(process.cwd(), 'tests', 'e2e')),
    ]) {
      // ⚠️ **Comments blanked first.** ⛔ **The record of WHY a string was
      // retired must not be read as the string returning** — the same false
      // positive this file already produced once, and the design-token guard
      // before it.
      const bare = readFileSync(file, 'utf8')
        .replace(/\/\*[\s\S]*?\*\//g, '')
        .replace(/^\s*\/\/.*$/gm, '');
      const where = relative(process.cwd(), file);
      if (SETTINGS_SURFACE.test(where)) continue;
      for (const [retired, instead] of Object.entries(RETIRED)) {
        if (bare.includes(retired)) {
          offenders.push(`${where} — "${retired}", use "${instead}"`);
        }
      }
    }
    expect(offenders, 'retired vocabulary is still asserted here').toEqual([]);
  });
});
