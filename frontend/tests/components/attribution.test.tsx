import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { AttributionStrip, type AttributionSource } from '@/components/ui';

/**
 * **The AI attribution strip** — [TASK-1411](../../../docs/BACKLOG.md).
 *
 * ⚡ **The row names its own coverage, and every assertion below is one of
 * those sentences rather than a paraphrase of it.**
 */

const source = (over: Partial<AttributionSource> = {}): AttributionSource => ({
  id: 'e1',
  title: 'Renewal moved twice in 30 days',
  readable: true,
  ...over,
});

describe('🔴 confidence is stated or its absence is — never zero', () => {
  it('⛔ renders the ABSENCE where nothing publishes a confidence, and never "0 of 5"', () => {
    /**
     * 📁 **The row**: *"`N of 5` with no confidence renders absence, never
     * `0 of 5`"* — 🔴 ***`0 of 5` reads as certainly wrong where the truth is
     * not known.*** ⚡ **Two opposite claims, and the pips would draw the
     * first one.**
     *
     * ⚠️ **This is not hypothetical.** 📁 `ai_platform/public/` publishes no
     * confidence value at all, so **the absence is the state every consumer
     * gets today** — [C-267](../../../docs/LANE_COORDINATION.md).
     */
    render(<AttributionStrip sources={[source()]} />);

    expect(screen.getByText('Confidence not stated')).toBeInTheDocument();
    expect(screen.queryByText(/0 of 5/)).not.toBeInTheDocument();
    // ⛔ And no pips: a row of dots with none filled is `0 of 5` drawn rather
    // than written, which the sentence above forbids.
    expect(document.querySelectorAll('.bg-border-strong')).toHaveLength(0);
  });

  it('📁 states a published one as "N of 5", which is its accessible name', () => {
    // ♿ The row: *"Confidence 4 of 5 is the accessible name — not a bare
    // graphic."*
    render(<AttributionStrip confidence={4} sources={[]} />);
    expect(screen.getByText('Confidence 4 of 5')).toBeInTheDocument();
  });

  it('⛔ never renders a percentage', () => {
    // 📁 Design System v2 §03: *"pips plus a plain-language basis. Never a
    // synthetic percentage."*
    const { container } = render(<AttributionStrip confidence={3} sources={[source()]} />);
    expect(container.textContent).not.toMatch(/%/);
  });
});

describe('🔴 a source the reader may not open is not listed', () => {
  it('⛔ an unreadable source leaves both the list AND the count', async () => {
    /**
     * ⚡ **The row's Security Invariant**, and the count half is the part that
     * is easy to get wrong: **hiding the row while still counting it tells the
     * reader a source exists that they cannot see**, which is the disclosure
     * the rule forbids — the same rule as
     * [C-245](../../../docs/LANE_COORDINATION.md).
     */
    render(
      <AttributionStrip
        sources={[
          source({ id: 'a', title: 'A call this reader may open' }),
          source({ id: 'b', title: 'A deal in another territory', readable: false }),
        ]}
      />,
    );

    // ⛔ One, not two.
    const control = screen.getByRole('button', { name: '1 source' });
    await userEvent.click(control);

    expect(screen.getByText('A call this reader may open')).toBeInTheDocument();
    expect(screen.queryByText('A deal in another territory')).not.toBeInTheDocument();
  });

  it('⚡ and it bites — the same set with the flag set renders both', async () => {
    /**
     * ⛔ **A filter test that only ever asserts an absence passes just as well
     * when the filter is deleted and the fixture happens to be empty.**
     * ✅ **This is the fire-test**: flip the one field and the count moves.
     */
    render(
      <AttributionStrip
        sources={[source({ id: 'a' }), source({ id: 'b', title: 'The second one' })]}
      />,
    );
    await userEvent.click(screen.getByRole('button', { name: '2 sources' }));
    expect(screen.getByText('The second one')).toBeInTheDocument();
  });
});

describe('📁 the source list opens, and an excluded source is visibly excluded', () => {
  it('♿ the count is a disclosure button carrying aria-expanded', async () => {
    render(<AttributionStrip sources={[source(), source({ id: 'e2' })]} />);

    const control = screen.getByRole('button', { name: '2 sources' });
    expect(control).toHaveAttribute('aria-expanded', 'false');

    await userEvent.click(control);
    expect(control).toHaveAttribute('aria-expanded', 'true');
    // ⚡ The control names the region it opened, so a screen reader can reach it.
    expect(control.getAttribute('aria-controls')).toBe(
      screen.getByRole('list').getAttribute('id'),
    );
  });

  it('⛔ an excluded source is shown WITH its reason, not removed', async () => {
    /**
     * 📁 **AI Research**: *"excluded citations are shown as withheld rather
     * than removed, so the argument stays auditable"* — and *"3 excluded"*
     * appears on the strip itself.
     */
    render(
      <AttributionStrip
        sources={[
          source({ id: 'a' }),
          source({
            id: 'b',
            title: 'Brightwater call transcript',
            excluded: 'still processing',
          }),
        ]}
      />,
    );

    expect(screen.getByText('1 excluded')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: '2 sources' }));
    const row = screen.getByText('Brightwater call transcript').closest('li');
    expect(within(row as HTMLElement).getByText(/Excluded — still processing/)).toBeInTheDocument();
  });

  it('⚡ a source opens at the cited moment through its own control', async () => {
    const onOpen = vi.fn();
    render(<AttributionStrip sources={[source({ onOpen })]} />);

    await userEvent.click(screen.getByRole('button', { name: '1 source' }));
    await userEvent.click(
      screen.getByRole('button', { name: 'Renewal moved twice in 30 days' }),
    );
    expect(onOpen).toHaveBeenCalledOnce();
  });

  it('⛔ a source that opens nothing is not drawn as if it does', () => {
    // ⚡ The narration's own rule, carried forward: *"a citation drawn as
    // clickable and going nowhere costs more trust than the missing feature."*
    render(<AttributionStrip sources={[source()]} />);
    expect(
      screen.queryByRole('button', { name: 'Renewal moved twice in 30 days' }),
    ).not.toBeInTheDocument();
  });
});

describe('📁 Show reasoning is a disclosure, and only where there is reasoning', () => {
  it('⛔ no reasoning renders no button — never one that opens an empty panel', () => {
    render(<AttributionStrip sources={[source()]} />);
    expect(screen.queryByRole('button', { name: 'Show reasoning' })).not.toBeInTheDocument();
  });

  it('📁 collapsed by default, and aria-expanded says so', async () => {
    render(
      <AttributionStrip sources={[]} reasoning={<p>Three deals slipped after pricing.</p>} />,
    );

    const control = screen.getByRole('button', { name: 'Show reasoning' });
    expect(control).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByText(/Three deals slipped/)).not.toBeInTheDocument();

    await userEvent.click(control);
    expect(control).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText(/Three deals slipped/)).toBeInTheDocument();
  });
});

describe('📱 the strip wraps rather than truncating', () => {
  it('⛔ nothing on the strip may truncate — a cut-off source count is a false claim', () => {
    /**
     * 📁 **The row's responsive rule, and its reason**: *"a truncated source
     * count is a false claim about evidence."* ⚡ **`6 sources` clipped to
     * `6 sourc…` is survivable; clipped to `6` beside another number is not.**
     */
    const { container } = render(
      <AttributionStrip
        confidence={4}
        sources={[source()]}
        generatedAt="2026-08-10T09:14:00Z"
      />,
    );

    // ⚡ Found through the content rather than by position: a structural
    // selector would keep passing if the strip moved and stopped wrapping.
    const strip = screen.getByText('Confidence 4 of 5').closest('div');
    expect(strip?.className).toContain('flex-wrap');
    expect(container.innerHTML).not.toContain('truncate');
    expect(container.innerHTML).not.toContain('text-ellipsis');
  });
});
