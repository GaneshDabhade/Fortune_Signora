import { describe, expect, it } from 'vitest';

import { SETTINGS_NAV, SETTINGS_SECTIONS } from '@/lib/settings/sections';
import { screenDocument } from '../support/design-snapshot';

/**
 * 🔴 **Settings' structure, asserted against the design document rather than
 * against a transcription of it.**
 *
 * ⚡ **The design carries its own navigation as a literal array** — `navGroups`,
 * with a `label`, an `href` and a `badge` per item — **so this guard reads the
 * real thing.** 📁 **The eleven section anchors are read the same way**, from
 * the document's own `id="…"` attributes, in document order.
 *
 * ⛔ **The point is that a transcription cannot be checked.** The screen this
 * replaced was six index cards that appear nowhere in the design, and nothing
 * could see that, because nothing compared the screen to the design.
 *
 * 🔴 **[B-1063](../../../docs/BUGS.md) is why it reads `docs/design-snapshot/`
 * and never `Design Documents/`** — the latter is uncommitted, so a guard
 * reading it passes vacuously on the machine that certifies.
 */
const SETTINGS_DOC = 'Fortune Signora Settings.dc.html';

/**
 * ⚡ **A capture group that must have matched.**
 *
 * ⛔ **It throws rather than falling back**, for the reason the whole file
 * exists: a guard that quietly substitutes a value for a thing it could not
 * read is a guard that cannot fail.
 */
function group(match: RegExpMatchArray, index: number): string {
  const value = match[index];
  if (value === undefined) throw new Error(`group ${index} did not match in ${SETTINGS_DOC}`);
  return value;
}

/** 📁 The document's `id="…"` attributes, in document order. */
function designAnchors(): string[] {
  return [...screenDocument(SETTINGS_DOC).matchAll(/id="([a-z0-9-]+)"/g)].map((m) => group(m, 1));
}

interface DesignItem {
  readonly group: string;
  readonly label: string;
  readonly section: string;
  readonly badge: string;
}

/**
 * 📁 **The design's `navGroups` array, parsed out of the document.**
 *
 * ⚠️ **It throws when it finds nothing** rather than returning an empty list —
 * an empty expectation is a guard that cannot fail, and this file exists
 * because of one that could not.
 */
function designNav(): DesignItem[] {
  const text = screenDocument(SETTINGS_DOC);
  const start = text.indexOf('navGroups: [');
  if (start < 0) throw new Error(`no navGroups array in ${SETTINGS_DOC}`);
  const region = text.slice(start, text.indexOf('].map(', start));

  const items: DesignItem[] = [];
  let current = '';
  for (const line of region.matchAll(
    /\{\s*label:\s*'([^']*)',\s*items:|\{\s*label:\s*'([^']*)',\s*href:\s*'#([a-z0-9-]+)',\s*badge:\s*'([^']*)'/g,
  )) {
    if (line[1] !== undefined) current = line[1];
    else {
      items.push({
        group: current,
        label: group(line, 2),
        section: group(line, 3),
        badge: group(line, 4),
      });
    }
  }
  if (items.length === 0) throw new Error(`parsed no nav items out of ${SETTINGS_DOC}`);
  return items;
}

/** ⚡ `&amp;` is markup; the screen renders the character. */
const decode = (label: string) => label.replace(/&amp;/g, '&');

/**
 * ⛔ **The design's word is not always the screen's word, and that is a RULE
 * rather than a divergence.**
 *
 * 📁 **[ADR-0034](../../../docs/architecture/adr/0034-ubiquitous-language.md)**:
 * *"a customer says Organization; the platform says workspace… the translation
 * lives at the frontend edge and never travels inward."* ⚡ **The design
 * documents are written in the platform's vocabulary throughout** — *"Name
 * your workspace"*, *"Workspace URL"* — **and every screen translates them.**
 *
 * 🔴 **Without this, the guard demanded an ADR-0034 violation.** ⛔ **Two
 * rules, both binding, pointing opposite ways** — and the guard was the louder
 * one, so the register's word won on screen until a render test asked.
 *
 * ⚠️ **Applied to the DESIGN's side, never to the implementation's**, so the
 * implementation still cannot introduce the platform word: `Workspace` in
 * `SETTINGS_NAV` would be compared against a translated `Organization` and
 * fail, which is exactly what should happen.
 *
 * ⚡ **This is the same KIND of transformation `decode` is** — markup to
 * rendered text, platform vocabulary to customer vocabulary — **and it is
 * spelled out rather than folded into a looser comparison.**
 */
const CUSTOMER_WORD: readonly (readonly [RegExp, string])[] = [
  [/\bWorkspace\b/g, 'Organization'],
  [/\bworkspace\b/g, 'organization'],
];

function asShown(label: string): string {
  return CUSTOMER_WORD.reduce((text, [term, word]) => text.replace(term, word), decode(label));
}

describe('📁 Settings is the design’s page', () => {
  it('carries the design’s eleven sections, in the design’s order', () => {
    expect(SETTINGS_SECTIONS.map((section) => section.id)).toEqual(designAnchors());
  });

  it('carries the design’s four groups and fourteen items, in order', () => {
    const design = designNav();
    // ⚠️ **Asserted as one flat list including the group each item sits under**,
    // so moving an item between two groups fails rather than cancelling out.
    expect(
      SETTINGS_NAV.flatMap((group) =>
        group.items.map((item) => `${group.label} / ${item.label} → ${item.section}`),
      ),
    ).toEqual(
      design.map((item) => `${asShown(item.group)} / ${asShown(item.label)} → ${item.section}`),
    );
  });

  /**
   * ⚠️ **The translation must not silently become a no-op.**
   *
   * ⛔ **If the design were ever refreshed without the platform word, `asShown`
   * would still pass on every comparison while enforcing nothing** — and the
   * next person to reintroduce `Workspace` into `SETTINGS_NAV` would find the
   * guard agreeing with them. ✅ **So the guard asserts that it is actually
   * doing work**, and fails loudly if the premise stops holding.
   */
  it('⚡ and the ADR-0034 translation is load-bearing, not decorative', () => {
    const design = designNav();
    const raw = design.map((item) => `${item.group} / ${decode(item.label)}`);
    const shown = design.map((item) => `${asShown(item.group)} / ${asShown(item.label)}`);

    expect(
      raw.filter((entry, i) => entry !== shown[i]),
      'the design no longer uses the platform word here — remove the translation ' +
        'rather than leaving one that enforces nothing',
    ).not.toEqual([]);
  });

  /**
   * 🔴 **Zero dead entries — the property that was measured in a browser and is
   * executable here.**
   *
   * ⛔ **A navigation entry pointing at nothing is the defect this screen
   * replaced**, one direction over: the Connection Center was a page with no
   * door, and a door with no page is the same failure reflected.
   */
  it('points every navigation entry at a section that exists', () => {
    const sections = new Set(SETTINGS_SECTIONS.map((section) => section.id));
    const dead = SETTINGS_NAV.flatMap((group) =>
      group.items.filter((item) => !sections.has(item.section)).map((item) => item.label),
    );
    expect(dead, 'these scroll to nothing').toEqual([]);
  });

  /**
   * ⛔ **The design's badges are deliberately NOT carried, and this is the
   * assertion that keeps them out.**
   *
   * 📁 **The design shows `312` seats, `3` flags, `2` API keys, `4` webhooks
   * and two `!` warnings.** ⚡ **Every one is a count of something this product
   * does not have — and a badge is a measurement.** 🔴 **The design states them
   * because a design states what a full product looks like; repeating them here
   * would be this repository authoring a number nobody measured.**
   *
   * ⚠️ **Asserted on the shape, not on the rendering** — an item that carries no
   * count cannot render one, which is the stronger of the two.
   */
  it('carries none of the design’s badges, because nothing has measured them', () => {
    const withBadges = designNav().filter((item) => item.badge !== '');
    expect(withBadges.length, 'the design does state badges').toBeGreaterThan(0);

    const carried = SETTINGS_NAV.flatMap((group) =>
      group.items.filter((item) =>
        Object.keys(item).some((key) => key !== 'label' && key !== 'section'),
      ),
    );
    expect(carried, 'a badge is a measurement and none was taken').toEqual([]);
  });
});
