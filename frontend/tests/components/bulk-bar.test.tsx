/**
 * **The bulk action bar** — [TASK-466](../../../docs/BACKLOG.md).
 *
 * 🔴 **The assertions that matter are about what is NOT rendered.** 📁 The
 * design draws six actions; this bar renders the ones backed by an implemented
 * capability ([D-156](../../../docs/DECISION_REGISTER.md) ⑤), **and a disabled
 * control still teaches somebody the feature exists.**
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { BulkBar } from '@/components/accounts/bulk-bar';

describe('⛔ nothing selected renders no bar at all', () => {
  it('not an empty bar, and not a disabled one', () => {
    const { container } = render(<BulkBar count={0} onClear={vi.fn()} />);

    expect(container).toBeEmptyDOMElement();
  });
});

describe('⚡ the bar is the count', () => {
  it('says how many companies an action would touch', () => {
    render(<BulkBar count={41} onClear={vi.fn()} />);

    expect(screen.getByText('41 selected')).toBeVisible();
  });

  it('♿ and announces the change rather than only showing it', () => {
    // ⚡ **The bar announces itself visually by appearing**; `aria-live` is the
    // equivalent for somebody who cannot see it arrive.
    render(<BulkBar count={41} onClear={vi.fn()} />);

    expect(screen.getByText('41 selected')).toHaveAttribute('aria-live', 'polite');
  });

  it('clears', () => {
    const onClear = vi.fn();
    render(<BulkBar count={3} onClear={onClear} />);

    screen.getByRole('button', { name: 'Clear selection' }).click();

    expect(onClear).toHaveBeenCalled();
  });
});

describe('🔴 an action appears only where it can act', () => {
  it('⛔ Export is absent when the selection cannot be enumerated', () => {
    /**
     * 📁 *"Select all 312"* names a set the SERVER resolves, and the client
     * holds 50. ⛔ **Exporting the 50 would produce a file the customer
     * believes holds 312** — 📁 *"the worst kind of wrong: silently
     * plausible."*
     *
     * ✅ **So the control is absent rather than wrong**, and it returns the
     * moment a server-side export exists.
     */
    render(<BulkBar count={312} onClear={vi.fn()} />);

    expect(screen.queryByRole('button', { name: /Export/ })).not.toBeInTheDocument();
  });

  it('✅ and present, naming the count, when it can', () => {
    const onExport = vi.fn();
    render(<BulkBar count={41} onClear={vi.fn()} onExport={onExport} />);

    screen.getByRole('button', { name: 'Export 41' }).click();

    expect(onExport).toHaveBeenCalled();
  });

  it('⛔ the five actions with no capability are not rendered as dead buttons', () => {
    /**
     * 📁 The design's `bulkActions`: *Assign owner · Add tag · Add to segment ·
     * Create tasks · Export 41 · ✦ Draft outreach.*
     *
     * ⛔ **[TASK-466](../../../docs/BACKLOG.md)'s own row names this as the
     * reason the work was skipped once**: *"a bulk bar whose six buttons
     * cannot act is the false-affordance class."* ⚠️ **This assertion is what
     * stops somebody adding them back for visual fidelity**, and each will
     * arrive with its capability.
     */
    render(<BulkBar count={41} onClear={vi.fn()} onExport={vi.fn()} />);

    for (const absent of [
      'Assign owner',
      'Add tag',
      'Add to segment',
      'Create tasks',
      'Draft outreach',
    ]) {
      expect(screen.queryByText(new RegExp(absent, 'i'))).not.toBeInTheDocument();
    }
  });
});

describe('🔴 “Select all N” is offered only with a real N behind it', () => {
  it('⛔ absent when the caller has no count to name', () => {
    /**
     * 📁 `CursorPage` publishes `items`, `next_cursor` and `has_more` and **no
     * total** — measured. ⚡ **Using the loaded count would put the same word
     * in two meanings**: the customer reads *"Select all 312"* and gets the 50
     * in hand. 📁 [C-1505](../../../docs/LANE_COORDINATION.md).
     */
    render(<BulkBar count={41} onClear={vi.fn()} />);

    expect(screen.queryByRole('button', { name: /Select all/ })).not.toBeInTheDocument();
  });

  it('✅ and present once one exists', () => {
    const onSelectAll = vi.fn();
    render(
      <BulkBar
        count={41}
        onClear={vi.fn()}
        onSelectAll={onSelectAll}
        selectAllCount={312}
      />,
    );

    screen.getByRole('button', { name: 'Select all 312' }).click();

    expect(onSelectAll).toHaveBeenCalled();
  });
});

import { PROPOSED_DETAIL, proposedMessage } from '@/lib/accounts/tag-batch';

describe('🔴 the bulk tag proposed a batch and told nobody', () => {
  /**
   * 📁 `router.py:676` — ***"201, and it proposes rather than applies. Nothing
   * is tagged by this request."*** under [ADR-0405](../../../docs/architecture/adr/):
   * *an action is approved before it is effective*.
   *
   * ⛔ **The call site's `onSuccess` cleared the selection and did nothing
   * else.** ⚡ **So a customer selected companies, chose a tag, watched the
   * selection vanish, and saw no row change** — 📁 [B-255](../../../docs/BUGS.md):
   * *a control that silently does nothing is worse than one that is absent.*
   *
   * ⚠️ **These assert the SECOND sentence too**, because *"awaiting approval"*
   * on its own implies an approval that can come, and 📁 the approval screen
   * ADR-0405 names does not exist — `action-batches` has zero frontend
   * consumers. [C-1554](../../../docs/LANE_COORDINATION.md).
   */
  it('says how many companies it proposed for', () => {
    expect(proposedMessage(41)).toBe('Proposed a tag for 41 companies');
  });

  it('says "company" for one, because a count is not a plural', () => {
    expect(proposedMessage(1)).toBe('Proposed a tag for 1 company');
  });

  it('🔴 says nothing is tagged YET, and that approving is not built', () => {
    // ⛔ Both halves. The first alone reads as a failure; the second alone
    // reads as a delay.
    expect(PROPOSED_DETAIL).toMatch(/Nothing is tagged yet/);
    expect(PROPOSED_DETAIL).toMatch(/approving is not built yet/);
  });
});
