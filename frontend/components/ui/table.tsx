'use client';

import {
  useState,
  type HTMLAttributes,
  type KeyboardEvent,
  type ReactNode,
  type TdHTMLAttributes,
  type ThHTMLAttributes,
} from 'react';

import { cn } from '@/lib/design/cn';

/**
 * **The table** — [TASK-1452](../../../docs/BACKLOG.md), rebuilt against 📁
 * [Design System v2](../../../docs/design-snapshot/screens/) §11 *Tables*
 * ([D-138](../../../docs/DECISION_REGISTER.md), [D-220](../../../docs/DECISION_REGISTER.md)).
 *
 * ## 🔴 Scrapped and rebuilt, because the structure encoded the old design
 *
 * ⛔ **The previous component was `border-collapse` with a `border-b` on every
 * row** — 📁 **which IS the pattern §11's critique names**: *"toolbars, footers
 * and headers all carried 2px rules and full-width fills, so the data competed
 * with its own container."* ⚡ **Adding the four rules to it would have produced
 * the hybrid [D-220](../../../docs/DECISION_REGISTER.md) §3 calls E and
 * [D-229A](../../../docs/DECISION_REGISTER.md) forbids by name.**
 *
 * ⚠️ **The row said twelve callers. Measured: TWO files, three tables, 33
 * element usages.** ✅ **Reported rather than accepted** — and it makes the
 * migration cheaper than the row assumed, not dearer.
 *
 * ## 📁 The four rules, each with the sentence it implements
 *
 * **① Pinned identity** — *"the first column pins with a 24px gradient fade
 * instead of a border, so horizontal scroll never produces a hard seam."*
 * ⛔ **A `border-r` here would be the hard seam the rule exists to remove.**
 *
 * **② Hover and selection** — *"hover is the sunken tint. Selection adds a 2px
 * brand edge and a brand-tint fill — **distinguishable without colour
 * vision**."* ⚡ **The edge is what carries that**, not the fill: a tint alone
 * is a colour difference, and the rule's own clause rules it out.
 *
 * **③ Inline editing** — *"editable cells reveal a 6px ring on focus, commit on
 * ⏎ optimistically, and surface undo in the toast for 10 seconds."* 🔴 **This
 * is a product capability rather than styling**: 📁 *"in practice reps edit
 * close dates and amounts dozens of times a day"*, and every correction
 * currently opens a drawer.
 *
 * **④ AI summary row** — *"pinned above the data it describes, tinted with the
 * intelligence hue, dismissible, and **never counted as a data row**."*
 * ⚡ **It is not a `<tr>` at all** — it renders inside the plane above the
 * table, so *counted as a data row* is unrepresentable rather than merely
 * avoided ([§2](../../../CLAUDE.md)).
 */

export interface TableProps extends HTMLAttributes<HTMLTableElement> {
  /**
   * 📁 **Rule ④.** Rendered above the table, inside the plane. ⛔ **Never a row**
   * — see the note above.
   */
  summary?: ReactNode;
  /** ⚡ Called when the summary is dismissed. Absent means it cannot be. */
  onDismissSummary?: () => void;
}

/**
 * 📁 **One rounded 16px plane** — §05 assigns the table `--r-xl`, and the old
 * component had no plane at all.
 */
export function Table({ className, summary, onDismissSummary, ...props }: TableProps) {
  return (
    <div className="overflow-hidden rounded-xl border border-border-soft bg-surface">
      {summary !== undefined ? (
        <div
          // 📁 *"tinted with the intelligence hue"* — `--color-ai`'s subtle
          // pair, which is the token the design's `--ai-tint` maps to.
          className="flex items-start gap-3 border-b border-border-soft bg-ai-subtle px-4 py-3"
          data-summary-row=""
        >
          <div className="min-w-0 flex-1 text-sm leading-6 text-ai">{summary}</div>
          {onDismissSummary !== undefined ? (
            <button
              type="button"
              onClick={onDismissSummary}
              // ♿ Names what it removes, not the glyph.
              aria-label="Dismiss summary"
              className="shrink-0 rounded px-1 text-sm text-ai transition-opacity hover:opacity-70 "
            >
              ✕
            </button>
          ) : null}
        </div>
      ) : null}

      {/* ⚡ **The scroll region is inside the plane**, so the rounded edge is
          never clipped by a horizontally scrolling child. */}
      <div className="w-full overflow-x-auto">
        {/* ⛔ **`border-separate`, not `border-collapse`.** Collapse is what
            made a per-row rule the only way to draw a line, and it is also
            what prevents a sticky first column from painting over what it
            scrolls past. */}
        <table
          className={cn('w-full border-separate border-spacing-0 text-sm', className)}
          {...props}
        />
      </div>
    </div>
  );
}

/**
 * 📁 **Sticky header on a tinted surface** — §11. ⚡ **`sticky` needs the cells
 * to carry it**, not the section, because `<thead>` is not a positioning
 * context in every engine.
 */
export function THead({ className, ...props }: HTMLAttributes<HTMLTableSectionElement>) {
  return <thead className={cn('bg-surface-sunken', className)} {...props} />;
}

export function TBody(props: HTMLAttributes<HTMLTableSectionElement>) {
  return <tbody {...props} />;
}

export interface TRProps extends HTMLAttributes<HTMLTableRowElement> {
  /** 📁 **Rule ②.** Adds the 2px brand edge AND the tint — never one alone. */
  selected?: boolean;
}

/**
 * ⚠️ **`h-row` and `h-row-compact` exist and NOTHING USES THEM** — measured,
 * zero occurrences in `components/` and `app/`. 📁 They carry the design's
 * `--row-h: 44px` and `--row-h-compact: 34px` from §18.
 *
 * ⛔ **Rows here are PADDING-DERIVED, not fixed.** ⚡ **Measured in a browser**:
 * a cell is `12px` top and bottom around a `14px/21px` line, so a single-line
 * row computes to **45px** against §11's `44px` — **a one-pixel consequence of
 * leading, not a decision** — and a row whose content wraps reaches `122px` on
 * `/settings/team`.
 *
 * ⛔ **Not changed to `h-row`, deliberately**: a fixed height on a cell whose
 * content wraps either clips it or overflows the plane, and 📁 §11's own table
 * draws single-line cells. **Whether these tables may wrap at all is a product
 * question about the data, not a token swap.** ✅ **Recorded so the next reader
 * does not assume `h-row` is what a table uses.**
 */
export function TR({ className, selected = false, ...props }: TRProps) {
  return (
    <tr
      // ♿ `aria-selected` carries the state for assistive technology, because
      // neither an edge nor a tint reaches a screen reader.
      aria-selected={selected || undefined}
      data-selected={selected || undefined}
      className={cn(
        'group transition-colors',
        // 📁 *"Hover is the sunken tint."* — ✅ **corroborated in three
        // documents**, including the Design System itself.
        //
        // ⚠️ **§11's prose adds *"with a 2px brand edge"* and NOTHING DRAWS
        // ONE.** ⛔ **Measured across all 35 documents: zero `2px`/`inset` brand
        // edges, on hover or otherwise.** ⚡ **So the tint alone is the drawn
        // treatment**, and this is the fourth place §-prose names something its
        // own markup does not — 📁 §17's *"2px ring at 2px offset"* against 21
        // unanimous 3px rings, §13's *"three-cycle"* against `infinite`
        // ([B-297](../../../docs/BUGS.md)), §17's AA claim against an unmeasured
        // ramp ([C-1548](../../../docs/LANE_COORDINATION.md)).
        'hover:bg-surface-sunken',
        selected && 'bg-accent-subtle',
        className,
      )}
      {...props}
    />
  );
}

/**
 * ⚡ **The cell classes shared by `TH` and `TD`**, including rule ①'s pin.
 *
 * ⛔ **The fade is a `::after` gradient, never a border** — 📁 *"a 24px gradient
 * fade instead of a border, so horizontal scroll never produces a hard seam."*
 */
function pinned(pin: boolean): string {
  return cn(
    pin && 'sticky left-0 z-10',
    pin &&
      // The fade sits OUTSIDE the cell's right edge, 24px wide, and is drawn
      // from the cell's own background so it works on hover and selection
      // alike rather than assuming the surface colour.
      'after:pointer-events-none after:absolute after:inset-y-0 after:left-full after:w-6 ' +
        'after:bg-gradient-to-r after:from-black/[0.06] after:to-transparent',
  );
}

export interface CellProps {
  /** 📁 **Rule ①** — the identity column. ⛔ At most one per row. */
  pin?: boolean;
}

export function TH({
  className,
  pin = false,
  ...props
}: ThHTMLAttributes<HTMLTableCellElement> & CellProps) {
  return (
    <th
      scope="col"
      className={cn(
        // 📁 Sticky header, and the border is on the cell because
        // `border-separate` no longer collapses a section's edge.
        // ⚠️ **No trailing `relative`.** ⛔ **`cn` is tailwind-merge, and
        // `relative` and `sticky` are the same property** — appending it
        // silently removed the pin. **Measured by printing the rendered class
        // list, not reasoned about**: `sticky` was simply absent.
        // ⚡ `sticky` already establishes the positioning context the `::after`
        // fade needs, so nothing is lost.
        'sticky top-0 border-b border-border-soft bg-surface-sunken',
        'px-4 py-2.5 text-left font-medium text-content-muted',
        pinned(pin),
        // The pinned header outranks the sticky header it sits inside, so the
        // z-order is stated last where tailwind-merge cannot reorder it.
        pin ? 'z-30' : 'z-20',
        className,
      )}
      {...props}
    />
  );
}

export function TD({
  className,
  pin = false,
  ...props
}: TdHTMLAttributes<HTMLTableCellElement> & CellProps) {
  return (
    <td
      className={cn(
        // ⚠️ `relative` is safe here and is NOT safe on `TH` — see the note
        // there. A pinned `TD` gets `sticky` from `pinned()` below, which
        // tailwind-merge resolves in that call's favour because it comes after.
        'relative border-b border-border-soft px-4 py-3 text-content last:border-b-0',
        // 📁 **Rule ②'s edge, on the pinned cell** so it reads at the row's
        // start where the eye lands — and it is 2px, which is what makes
        // selection legible without colour.
        'group-data-[selected]:before:absolute group-data-[selected]:before:inset-y-0',
        pin &&
          'bg-surface group-hover:bg-surface-sunken group-data-[selected]:bg-accent-subtle',
        pin &&
          'group-data-[selected]:before:left-0 group-data-[selected]:before:w-0.5 group-data-[selected]:before:bg-accent',
        pinned(pin),
        className,
      )}
      {...props}
    />
  );
}

export interface EditableCellProps extends CellProps {
  value: string;
  /**
   * 📁 **Rule ③** — *"commit on ⏎ optimistically."* ⚡ **The caller performs the
   * optimism**: this reports the new value and the previous one, so an undo
   * has something to restore without this component holding a history.
   */
  onCommit: (next: string, previous: string) => void;
  /** ♿ Required — an editable cell with no name is unusable by keyboard. */
  label: string;
  className?: string;
}

/**
 * 📁 **Rule ③, the product capability.**
 *
 * > *"Editable cells reveal a 6px ring on focus, commit on ⏎ optimistically,
 * > and surface undo in the toast for 10 seconds."*
 *
 * ⛔ **This component does NOT raise the toast.** The undo affordance belongs
 * to whoever owns the mutation — it is the only thing that knows how to
 * reverse it — so `onCommit` hands back both values and the caller decides.
 * ⚡ **A table that raised its own undo toast would be the frame taking a
 * product decision**, which is the rule the shell already works to.
 *
 * ⚠️ **Escape reverts without committing**, which the design does not state and
 * every editable field in this product already does — 📁 the consistency is
 * the argument, not an invention.
 */
export function EditableCell({
  value,
  onCommit,
  label,
  pin = false,
  className,
}: EditableCellProps) {
  const [draft, setDraft] = useState(value);
  const [editing, setEditing] = useState(false);

  const commit = () => {
    setEditing(false);
    if (draft !== value) onCommit(draft, value);
  };

  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      commit();
      return;
    }
    if (event.key === 'Escape') {
      event.preventDefault();
      setDraft(value);
      setEditing(false);
    }
  };

  return (
    <TD pin={pin} className={cn('p-0', className)}>
      <input
        aria-label={label}
        value={editing ? draft : value}
        onFocus={() => {
          setDraft(value);
          setEditing(true);
        }}
        onChange={(event) => setDraft(event.target.value)}
        onKeyDown={onKeyDown}
        onBlur={commit}
        className={cn(
          'w-full bg-transparent px-4 py-3 text-content',
          // ⛔ **The ring is the affordance** — the cell must look like ordinary
          // text until it is focused — ⚡ **but it is the product's ONE focus
          // treatment**, drawn by `globals.css` ([B-1058](../../../docs/BUGS.md)).
          //
          // ⚠️ **The design disagrees with itself here and this follows the
          // markup.** 📁 Design System v2's prose says *"Editable cells reveal a
          // **6px** ring on focus"*; 📁 **its own inline-edit element is drawn as
          // `border:1px solid var(--brand); box-shadow:0 0 0 3px
          // var(--brand-tint)`** — the same pair as every other focused control,
          // and `0 0 0 6px` appears nowhere in any of the 35 documents.
          // **Recorded as [C-1540](../../../docs/LANE_COORDINATION.md); not
          // resolved in code beyond following the thing that is drawn.**
          'focus:relative focus:z-10 focus:rounded',
        )}
      />
    </TD>
  );
}
