import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it, vi } from 'vitest';

import { EditableCell, TBody, TD, TH, THead, TR, Table } from '@/components/ui';

/**
 * **The table** — [TASK-1452](../../../docs/BACKLOG.md), against 📁 Design
 * System v2 §11 *Tables*, `tableRules`.
 *
 * ⛔ **Four rules, each asserted against the sentence that states it.** ⚡ The
 * component was scrapped and rebuilt, so these are not regression tests for the
 * old one — 📁 [D-229A](../../../docs/DECISION_REGISTER.md): *scrap the
 * incorrect implementation and rebuild from the finalized design.*
 */

function grid(props: Record<string, unknown> = {}) {
  return render(
    <Table {...props}>
      <THead>
        <TR>
          <TH pin>Account</TH>
          <TH>Owner</TH>
        </TR>
      </THead>
      <TBody>
        <TR selected>
          <TD pin>Vantage</TD>
          <TD>M. Reinhardt</TD>
        </TR>
        <TR>
          <TD pin>Northwind</TD>
          <TD>J. Okafor</TD>
        </TR>
      </TBody>
    </Table>,
  );
}

describe('🔴 the structure the rebuild exists for', () => {
  it('⛔ border-collapse is GONE — it was the 2px cage v2 replaced', () => {
    /**
     * 📁 §11's critique of v1: *"toolbars, footers and headers all carried 2px
     * rules and full-width fills, so the data competed with its own
     * container."* ⚡ **`border-collapse` with a per-row `border-b` IS that
     * pattern**, and it is also what prevents a sticky first column from
     * painting over what it scrolls past — **so the structure had to change,
     * not the styling.**
     */
    // ⚠️ **Over the class strings, not the file** — ⛔ a plain `toContain`
    // failed on this component's own COMMENT, which names `border-collapse` to
    // explain why it is gone. **A test that reads prose fails when the prose
    // is right**, which is the same trap `design-scale.test.ts` hit.
    const { container } = grid();
    const table = container.querySelector('table');
    expect(table?.className).toContain('border-separate');
    expect(table?.className).not.toContain('border-collapse');

    const source = readFileSync(join(process.cwd(), 'components/ui/table.tsx'), 'utf8');
    expect(source).toContain('border-separate');
  });

  it('📁 one rounded 16px plane, which the old component had no version of', () => {
    // 📁 §05 assigns the table plane `--r-xl` = 16px, and `rounded-xl` is that
    // token. ⛔ The previous component had no plane at all.
    const { container } = grid();
    expect(container.querySelector('.rounded-xl')).not.toBeNull();
  });
});

describe('📁 rule ① — pinned identity', () => {
  it('⛔ the pin is a GRADIENT FADE, never a border', () => {
    /**
     * 📁 *"the first column pins with a 24px gradient fade instead of a
     * border, so horizontal scroll never produces a hard seam."* ⚡ **A
     * `border-r` here would be the exact seam the rule removes**, so its
     * absence is asserted rather than the fade's presence alone.
     */
    const { container } = grid();
    const pinned = container.querySelector('th[scope="col"]');
    expect(pinned?.className).toContain('sticky');
    expect(pinned?.className).toMatch(/after:w-6/); // 24px
    expect(pinned?.className).toMatch(/after:bg-gradient-to-r/);
    expect(pinned?.className).not.toMatch(/\bborder-r\b/);
  });

  it('✅ only the column asked to pin does', () => {
    // ⚡ **Vacuity guard.** If every cell pinned, the assertion above would
    // pass over a table with no identity column at all.
    const { container } = grid();
    const headers = [...container.querySelectorAll('th')];
    expect(headers).toHaveLength(2);
    expect(headers[0]?.className).toContain('sticky left-0');
    expect(headers[1]?.className).not.toContain('left-0');
  });
});

describe('📁 rule ② — hover and selection, without colour vision', () => {
  it('🔴 selection carries a 2px EDGE, not only a tint', () => {
    /**
     * 📁 *"Selection adds a 2px brand edge and a brand-tint fill —
     * **distinguishable without colour vision**."* ⛔ **A tint alone is a
     * colour difference**, which the rule's own clause rules out. ⚡ The edge
     * is what makes the state legible to somebody who cannot see the hue.
     */
    const { container } = grid();
    const selected = container.querySelector('tr[data-selected]');
    expect(selected).not.toBeNull();
    expect(selected?.className).toContain('bg-accent-subtle');

    const pinnedCell = selected?.querySelector('td');
    expect(pinnedCell?.className).toMatch(/before:w-0\.5/); // 2px
    expect(pinnedCell?.className).toMatch(/before:bg-accent/);
  });

  it('♿ and the state reaches assistive technology, which no edge does', () => {
    // ⛔ Neither a tint nor a border is announced. `aria-selected` is.
    const { container } = grid();
    expect(container.querySelector('tr[aria-selected="true"]')).not.toBeNull();
    expect(container.querySelectorAll('tr[aria-selected]')).toHaveLength(1);
  });

  it('📁 hover is the sunken tint', () => {
    const { container } = grid();
    const rows = [...container.querySelectorAll('tbody tr')];
    expect(rows[1]?.className).toContain('hover:bg-surface-sunken');
  });
});

describe('📁 rule ③ — inline editing', () => {
  function cell(onCommit = vi.fn()) {
    render(
      <Table>
        <TBody>
          <TR>
            <EditableCell label="Close date" value="12 Oct" onCommit={onCommit} />
          </TR>
        </TBody>
      </Table>,
    );
    return { input: screen.getByLabelText('Close date'), onCommit };
  }

  it('✅ commits on ⏎, reporting the previous value so undo has something to restore', async () => {
    /**
     * 📁 *"commit on ⏎ optimistically, and surface undo in the toast for 10
     * seconds."* ⛔ **This component does not raise the toast** — the undo
     * belongs to whoever owns the mutation, because it is the only thing that
     * knows how to reverse it. ⚡ **So both values are handed back**, and a
     * table that raised its own undo would be the frame taking a product
     * decision.
     */
    const { input, onCommit } = cell();
    await userEvent.clear(input);
    await userEvent.type(input, '19 Oct{Enter}');
    expect(onCommit).toHaveBeenCalledWith('19 Oct', '12 Oct');
  });

  it('⛔ Escape reverts and commits nothing', async () => {
    const { input, onCommit } = cell();
    await userEvent.clear(input);
    await userEvent.type(input, 'wrong{Escape}');
    expect(onCommit).not.toHaveBeenCalled();
    expect(screen.getByLabelText('Close date')).toHaveValue('12 Oct');
  });

  it('⛔ an unchanged value commits nothing, so undo is never offered for a no-op', async () => {
    const { input, onCommit } = cell();
    await userEvent.click(input);
    await userEvent.tab();
    expect(onCommit).not.toHaveBeenCalled();
  });

  /**
   * 🔴 **This asserted `focus:ring-[6px]` — a CLASS NAME — and that is the
   * shape of assertion [B-1058](../../../docs/BUGS.md) is about.**
   *
   * ⛔ **A class-name check cannot see that four focus treatments coexist**; it
   * only sees that this component has one. ⚡ **Every one of the nine components
   * that opted out of the global rule had a test just as green as this.**
   *
   * ## ⚠️ And the 6px was the design disagreeing with itself
   *
   * 📁 Design System v2's prose: *"Editable cells reveal a **6px** ring on
   * focus."* 📁 **Its own inline-edit element, drawn:** `border:1px solid
   * var(--brand); box-shadow:0 0 0 3px var(--brand-tint)` — **the same pair as
   * every other focused control**, and `0 0 0 6px` appears **nowhere in any of
   * the 35 documents**. ✅ **Recorded as
   * [C-1540](../../../docs/LANE_COORDINATION.md)**; the markup is what ships.
   *
   * ✅ **What this asserts instead is the rule's actual content** — *ordinary
   * text at rest, an affordance on focus* — **which survives a change of ring
   * size and would fail if the cell ever looked like a form.**
   */
  it('📁 the cell reads as ordinary text at rest, and focus is the affordance', () => {
    const { input } = cell();

    // ⛔ **No fill and no border of its own** — the two things that would make
    // a table of these look like a form.
    expect(input.className).toContain('bg-transparent');
    expect(input.className).not.toMatch(/\bborder\b/);
    expect(input.className).not.toMatch(/\bbg-surface\b/);

    // ⚡ **And it declares no focus treatment**, so it inherits the product's
    // one indicator rather than drawing a second.
    expect(input.className).not.toMatch(/(focus|focus-visible|focus-within):-?(outline|ring)/);
    expect(input.className).not.toMatch(/\boutline-none\b/);

    // ⚡ **The one thing focus DOES change here is stacking**, so the indicator
    // is not painted under the neighbouring cells.
    expect(input.className).toContain('focus:relative');
    expect(input.className).toContain('focus:z-10');
  });
});

describe('📁 rule ④ — the AI summary row', () => {
  it('🔴 it is NOT a row, so *counted as a data row* is unrepresentable', () => {
    /**
     * 📁 *"pinned above the data it describes… and **never counted as a data
     * row**."* ⚡ **Rendered outside the `<table>` entirely**, so the
     * prohibition is structural rather than a convention a future caller
     * could break ([§2](../../../CLAUDE.md)).
     */
    const { container } = grid({ summary: 'Two deals slipped this week.' });
    expect(screen.getByText('Two deals slipped this week.')).toBeInTheDocument();
    expect(container.querySelectorAll('tbody tr')).toHaveLength(2);
    expect(container.querySelector('[data-summary-row]')?.closest('table')).toBeNull();
  });

  it('✅ dismissible only when the caller can handle it', async () => {
    // ⛔ **No dismiss handler, no dismiss control.** A control whose action
    // nothing performs is the §2 defect.
    grid({ summary: 'A summary.' });
    expect(screen.queryByRole('button', { name: 'Dismiss summary' })).toBeNull();

    const onDismissSummary = vi.fn();
    grid({ summary: 'A summary.', onDismissSummary });
    await userEvent.click(screen.getAllByRole('button', { name: 'Dismiss summary' })[0] as HTMLElement);
    expect(onDismissSummary).toHaveBeenCalled();
  });

  it('⛔ absent when there is nothing to summarise', () => {
    const { container } = grid();
    expect(container.querySelector('[data-summary-row]')).toBeNull();
  });
});
