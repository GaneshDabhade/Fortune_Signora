/**
 * **The bulk action bar** — [TASK-466](../../../docs/BACKLOG.md), against 📁
 * `Fortune Signora Companies.dc.html`.
 *
 * ## 🔴 The design draws six actions and this renders the ones that can act
 *
 * 📁 **The design's `bulkActions`**: *Assign owner · Add tag · Add to segment ·
 * Create tasks · Export 41 · ✦ Draft outreach.*
 *
 * ⛔ **A bulk bar whose buttons cannot act is the false-affordance class**, and
 * [TASK-466](../../../docs/BACKLOG.md)'s own row says so in the cell recording
 * why this work was skipped once: ***"the shared data table was NOT shipped as
 * a down-payment: a bulk bar whose six buttons cannot act is the
 * false-affordance class."***
 *
 * ⚡ 📁 [D-156](../../../docs/DECISION_REGISTER.md) ⑤ is the rule and it is
 * narrow: **build every customer-visible state *where backed by implemented
 * capability*.** ⛔ Not *"build the layout and grey the rest"* — a disabled
 * control still teaches somebody the feature exists.
 *
 * | | |
 * |---|---|
 * | **Export** | ✅ **Shipped.** `toCsv` already builds the file the toolbar downloads |
 * | **Add tag** | ✅ **Shipped**, 📁 [D-235](../../../docs/DECISION_REGISTER.md) ① — it proposes a batch somebody approves, and ⛔ **tags nothing on its own** |
 * | **Assign owner** · **Add to segment** | ⚠️ **[ADR-0411](../../../docs/architecture/adr/0411-customer-organized-account-metadata.md) ratifies both and neither is built yet** |
 * | **Create tasks** · **✦ Draft outreach** | ⛔ **No capability anywhere in `backend/modules/`** — measured, not assumed |
 *
 * ✅ **Each absence is a line in this table rather than a greyed button**, so
 * the next lane reads why rather than rediscovering it.
 */
import type { ReactNode } from 'react';

import { Button } from '@/components/ui/button';

export interface BulkBarProps {
  /** How many companies an action would touch. **The bar's own headline.** */
  readonly count: number;
  /**
   * 📁 *"41 selected of 312 in view · Select all 312"* — ⛔ **absent when the
   * whole filtered set is already on screen**, because a control that changes
   * nothing is worse than no control.
   */
  readonly onSelectAll?: () => void;
  readonly selectAllCount?: number;
  readonly onClear: () => void;
  /**
   * ⛔ **`undefined` when the selection cannot be enumerated.** 📁 *"Select all
   * 312"* on a table holding 50 names a set the server resolves — **exporting
   * the 50 would produce a file called *"all companies"* containing a sixth of
   * them**, which is [`table.ts`](../../lib/accounts/table.ts)'s own words:
   * *"the worst kind of wrong — silently plausible."*
   */
  readonly onExport?: () => void;
  /**
   * ⚡ **The *Add tag* control**, passed in rather than built here — the bar
   * knows how many are selected and nothing about labels.
   */
  readonly addTag?: ReactNode;
}

export function BulkBar({
  count,
  onSelectAll,
  selectAllCount,
  onClear,
  onExport,
  addTag,
}: BulkBarProps) {
  if (count === 0) return null;
  return (
    <div
      // ⚡ **A region rather than a toolbar**: it is a persistent summary the
      // customer returns to, and its heading is the count.
      role="region"
      aria-label="Selected companies"
      data-testid="bulk-bar"
      className="flex flex-wrap items-center gap-3 rounded-md bg-accent px-4 py-2 text-accent-contrast"
    >
      {/* ⚡ **`aria-live` so a screen reader hears the count change** as rows
          are ticked — the visual bar announces itself by appearing, and this
          is the equivalent. */}
      <span aria-live="polite" className="text-sm font-medium">
        {count} selected
      </span>

      {onSelectAll !== undefined && selectAllCount !== undefined ? (
        <Button variant="ghost" onClick={onSelectAll}>
          Select all {selectAllCount}
        </Button>
      ) : null}

      {addTag}

      {onExport !== undefined ? (
        <Button variant="ghost" onClick={onExport}>
          Export {count}
        </Button>
      ) : null}

      <Button variant="ghost" onClick={onClear}>
        Clear selection
      </Button>
    </div>
  );
}
