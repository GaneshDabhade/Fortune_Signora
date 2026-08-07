/**
 * **TASK-441 — *where does everything stand*, as a view rather than a screen.**
 *
 * [C-229](../../../docs/LANE_COORDINATION.md)'s answer B: *"a stage-grouped
 * **view** of the attention list, travelling in the URL beside `owner`, which
 * delivers* where does everything stand *with no fourth sidebar entry and no
 * second copy of the list."*
 *
 * ⛔ **The last clause is the one worth a test.** Every deliverable on this row
 * already renders — on Account 360 and on this page — so the failure mode is
 * not a missing feature but a **duplicated** one, and a duplicate passes every
 * test written about the thing it duplicates.
 */
import { describe, expect, it } from 'vitest';

import {
  STANDING_WORDS,
  standingFrom,
  withStanding,
  type Standing,
} from '@/lib/state/standing';

describe('the arrangement travels in the URL', () => {
  it('reads the two arrangements it defines', () => {
    expect(standingFrom('stage')).toBe('stage');
    expect(standingFrom('flat')).toBe('flat');
  });

  it.each([null, undefined, '', 'by-stage', 'STAGE', 'anything'])(
    'reads %s as the flat list rather than failing',
    (value) => {
      // `scopeFrom`'s reasoning exactly: a stale or hand-edited link shows a
      // seller their list, not an error. There is nothing here to protect.
      expect(standingFrom(value)).toBe('flat');
    },
  );

  it('leaves both defaults out of the link', () => {
    // A clean URL is the one a seller copies into a message.
    expect(withStanding('/', 'all', 'flat')).toBe('/');
  });

  it('keeps the scope when the arrangement changes', () => {
    expect(withStanding('/', 'mine', 'stage')).toBe('/?owner=mine&by=stage');
  });

  it('keeps the arrangement when the scope changes', () => {
    // **One click is one change.** Switching whose work you are reading must
    // not silently rearrange the list underneath it.
    expect(withStanding('/', 'unassigned', 'stage')).toBe('/?owner=unassigned&by=stage');
  });

  it('carries the arrangement alone when the scope is the default', () => {
    expect(withStanding('/', 'all', 'stage')).toBe('/?by=stage');
  });

  it('carries the scope alone when the arrangement is the default', () => {
    expect(withStanding('/', 'mine', 'flat')).toBe('/?owner=mine');
  });
});

describe('it is a view, and the words say so', () => {
  it('neither word names a place', () => {
    // ⚡ **The whole of D38's objection.** *Opportunities* was removed from
    // navigation from first principles — "adding one back is a claim that
    // needs defending" — so this had to arrange one list rather than become a
    // second destination. A noun here would be that destination by another
    // name.
    for (const word of Object.values(STANDING_WORDS)) {
      expect(word.startsWith('By ')).toBe(true);
    }
  });

  it('defines exactly the two arrangements the page renders', () => {
    const defined = Object.keys(STANDING_WORDS) as Standing[];
    expect(defined.sort()).toEqual(['flat', 'stage']);
  });
});

describe('no second copy of the list', () => {
  it('the stage view is rendered by the page that already owns the list', async () => {
    const { readFileSync } = await import('node:fs');
    const { join } = await import('node:path');

    const page = readFileSync(join(process.cwd(), 'app', '(app)', 'page.tsx'), 'utf8');

    // **`ByStage` lives inside the page and renders `AccountRow`.** A separate
    // route rendering its own row component is the "second copy" C-229 refuses,
    // and it would look correct in every screenshot.
    expect(page).toMatch(/function ByStage\(/);
    const byStage = page.slice(page.indexOf('function ByStage('));
    expect(byStage).toMatch(/<AccountRow/);
  });

  it('there is no /opportunities route', async () => {
    const { existsSync } = await import('node:fs');
    const { join } = await import('node:path');

    // D38 removed the entry from navigation, and reversing that is the product
    // owner's. **A route is how the reversal happens by accident.**
    for (const route of ['opportunities', 'opportunity', 'deals', 'pursuits']) {
      expect(
        existsSync(join(process.cwd(), 'app', '(app)', route)),
        `app/(app)/${route} exists — D38's entry is being reinstated without the decision`,
      ).toBe(false);
    }
  });

  it('the stage vocabulary has one definition', async () => {
    const { readFileSync } = await import('node:fs');
    const { join } = await import('node:path');

    const page = readFileSync(join(process.cwd(), 'app', '(app)', 'page.tsx'), 'utf8');
    // **`STAGE_MARK` is imported, never restated.** A second table would be a
    // second vocabulary, and the copy is the one that drifts.
    expect(page).toMatch(/STAGE_MARK/);
    expect(page).not.toMatch(/tracking:\s*'/);
  });
});
