/**
 * **A rail entry points at a region that exists** —
 * [TASK-1476](../../../docs/BACKLOG.md).
 *
 * 🔴 **The defect this guards is the rail's own recorded one**: *"the first
 * version linked every section by id while only the ABSENT ones carried one —
 * so `Account score` and `Summary` were links to nowhere."*
 *
 * ⚡ **The guard is at the seam that failed** ([B-191](../../../docs/BUGS.md)):
 * **the section carrying the id**, not the rail that links to it. A rail test
 * would pass against a page with no regions at all.
 */
import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { NarrativeBlock } from '@/components/intelligence/narration';
import { ResearchPanel } from '@/components/intelligence/research';

describe('⛔ a section the rail anchors carries the id in every state', () => {
  it('Summary carries it when it has narration to show', () => {
    const { container } = render(
      <NarrativeBlock
        id="summary"
        narration={{
          statements: [{ text: 'Something happened.', evidence: [] }],
          facts: [],
          evidence_unchanged: true,
        } as never}
      />,
    );
    expect(container.querySelector('#summary')?.tagName).toBe('SECTION');
  });

  /**
   * 🔴 **The half that would have been missed**, and the reason this test
   * exists rather than one assertion. ⛔ **An anchor that worked only when the
   * section had content would break exactly when a reader most needs to find
   * out why it is empty** — 📁 and *"nobody has written one"* is a real answer
   * on this screen, not a failure.
   */
  it('🔴 and carries it when Signora has never written one', () => {
    const { container } = render(<NarrativeBlock id="summary" narration={undefined} notNarrated />);
    expect(container.querySelector('#summary')?.tagName).toBe('SECTION');
  });

  it('Deeper research carries it', () => {
    const { container } = render(
      <ResearchPanel id="research" research={null} onRequest={() => {}} isRequesting={false} />,
    );
    expect(container.querySelector('#research')?.tagName).toBe('SECTION');
  });

  it('⚠️ and neither invents one when the page does not pass it', () => {
    // ⛔ **A component does not get to assume it is a whole section of a
    // screen** — the page owns the map.
    const { container } = render(
      <ResearchPanel research={null} onRequest={() => {}} isRequesting={false} />,
    );
    expect(container.querySelector('#research')).toBeNull();
  });
});

describe('🔴 a component that renders nothing must not leave an anchored region', () => {
  /**
   * ⛔ **The defect this lane introduced and then found by reading** —
   * [TASK-1476](../../../docs/BACKLOG.md). ⚡ **Giving a component an `id` does
   * not make a region appear.** `CompetitorContext` returns `null` when
   * nothing is declared and `NarrativeBlock` returns `null` while its read is
   * in flight, **so a rail entry for either can scroll a reader to blank
   * space** — 📁 the same class as *"links to nowhere"*, and harder to notice
   * because the link resolves.
   */
  it('Summary renders NOTHING while its read is in flight', () => {
    const { container } = render(<NarrativeBlock id="summary" narration={undefined} />);
    // ⚡ **So the page must not advertise `summary` in the rail yet** — which is
    // what `rendersSummary` decides.
    expect(container.querySelector('#summary')).toBeNull();
    expect(container.innerHTML).toBe('');
  });

  it('⚠️ and the not-narrated answer IS content, so it does render', () => {
    // ⛔ **The two must not be conflated**: *in flight* is not *nobody has
    // written one*, and only the second is an answer.
    const { container } = render(<NarrativeBlock id="summary" narration={undefined} notNarrated />);
    expect(container.querySelector('#summary')).not.toBeNull();
  });
});
