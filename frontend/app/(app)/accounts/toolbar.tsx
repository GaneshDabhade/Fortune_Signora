'use client';

import { Button, Select } from '@/components/ui';
import {
  COLUMNS,
  type ColumnId,
  conditionsOf,
  without,
  type Density,
  type Filters,
  GROUPABLE,
  type GroupKey,
  NO_FILTERS,
  isFiltered,
  SORTABLE,
  type Sort,
  type SortKey,
} from '@/lib/accounts/table';
import { cn } from '@/lib/design/cn';

/**
 * **The Companies toolbar** — [TASK-1475](../../../../docs/BACKLOG.md), against
 * 📁 `Fortune Signora Companies.dc.html`.
 *
 * ⚡ **Every control here narrows or renders what has already been read.** ⛔
 * **None of them claims to search the book**: 📁 the endpoint publishes `limit`
 * and `cursor` and nothing else, so a filter that looked like it searched
 * 8,412 while searching 50 would be the quietest lie on the screen — **and the
 * count beside them says which it is.**
 */
export interface ToolbarProps {
  readonly density: Density;
  readonly onDensity: (density: Density) => void;
  /** ⚡ **`null` is the endpoint's own order** — oldest first — 📁 and it is a
   *  real choice rather than the absence of one. */
  readonly sort: Sort | null;
  readonly onSort: (sort: Sort | null) => void;
  readonly group: GroupKey | null;
  readonly onGroup: (group: GroupKey | null) => void;
  readonly columns: readonly ColumnId[];
  readonly onColumns: (columns: readonly ColumnId[]) => void;
  readonly filters: Filters;
  readonly onFilters: (filters: Filters) => void;
  readonly kinds: readonly string[];
  readonly sources: readonly string[];
  /**
   * ⚡ **Every account in the workspace, or `null` while the count has not
   * answered** — 📁 `accounts-count`.
   *
   * ⛔ **`null` rather than falling back to the loaded figure.** The design's
   * *"312 of 8,412"* is a claim about the book; **printing the page size in
   * its place would be wrong by more with every page, and look right on the
   * first.**
   */
  readonly total: number | null;
  readonly shown: number;
  readonly loaded: number;
}

/** 📁 **The design's toolbar control** — *"height:30px; padding:0 11px;
 *  border-radius:8px; border:1px solid var(--line); font-size:12px;
 *  font-weight:600"*. ⚡ **Declared once** so Columns and Density are the same
 *  control at the same size, which is what the design's row actually shows. */
/**
 * 📁 **The design's arrangement chip** — *"Group: Renewal quarter ✕"* — which
 * is a different control from the outline pill beside it: **`--sunken`, no
 * border, 600 weight**, because an APPLIED arrangement and an AVAILABLE
 * control should not look the same.
 *
 * ⛔ **A `<select>` inside the chip rather than a bespoke menu.** ⚡ **The
 * native control carries its own keyboard, focus and announcement**, and this
 * is not the place to reimplement any of it — 📁 the same reasoning
 * `AccessibilityPanel` gives for using a real checkbox.
 */
function Chip({
  label,
  options,
  value,
  arrow,
  onChoose,
  onFlip,
}: {
  label: string;
  options: readonly { value: string; label: string }[];
  /** ⚡ **The chosen option's `value`, or `''` when none is chosen.** */
  value: string;
  /** 📁 The design's *"Score ↑"* — ⛔ **omitted where direction is meaningless**,
   *  as it is for a grouping. */
  arrow?: 'asc' | 'desc';
  onChoose: (value: string | null) => void;
  onFlip?: () => void;
}) {
  const applied = value !== '';
  return (
    <span
      className={cn(
        'inline-flex h-control-sm items-center gap-1 rounded-md px-2.5 text-xs font-semibold',
        applied
          ? 'bg-surface-sunken text-content'
          : 'border border-border text-content-muted',
      )}
    >
      <span className={applied ? 'text-content-subtle' : undefined}>{label}</span>
      {/* ♿ **Labelled, because three unlabelled selects on one row are three
          identical controls to a screen reader.** ⛔ **A native select rather
          than a bespoke menu** — it carries its own keyboard, focus and
          announcement, and this is not the place to reimplement any of it. */}
      <select
        aria-label={label}
        value={value}
        onChange={(event) => onChoose(event.target.value === '' ? null : event.target.value)}
        className={cn(
          'cursor-pointer border-0 bg-transparent p-0 pr-1 text-xs font-semibold outline-none',
          applied ? 'text-content' : 'text-content-muted',
        )}
      >
        <option value="">None</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {/* 📁 **The arrow IS the control** — the design writes the direction into
          the chip rather than beside it, so clicking it is what reverses. */}
      {applied && arrow !== undefined && onFlip !== undefined ? (
        <button
          type="button"
          onClick={onFlip}
          aria-label={`Sort ${arrow === 'asc' ? 'descending' : 'ascending'}`}
          className="rounded px-0.5 text-content hover:bg-surface focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent"
        >
          {arrow === 'asc' ? '↑' : '↓'}
        </button>
      ) : null}
      {applied ? (
        <button
          type="button"
          onClick={() => onChoose(null)}
          aria-label={`Remove the ${label.toLowerCase()}`}
          className="rounded text-content-subtle hover:text-content focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent"
        >
          ×
        </button>
      ) : null}
    </span>
  );
}

const PILL =
  'inline-flex h-control-sm items-center gap-1.5 rounded-md border border-border ' +
  'px-2.5 text-xs font-semibold text-content ' +
  'hover:bg-surface-sunken focus-visible:outline focus-visible:outline-2 ' +
  'focus-visible:outline-offset-2 focus-visible:outline-accent';

export function AccountsToolbar({
  density,
  onDensity,
  sort,
  onSort,
  group,
  onGroup,
  columns,
  onColumns,
  filters,
  onFilters,
  kinds,
  sources,
  total,
  shown,
  loaded,
}: ToolbarProps) {
  const chosen = new Set<ColumnId>(columns);
  const sorted = sort === null ? undefined : SORTABLE.find((s) => s.key === sort.key);
  const grouped = group === null ? null : GROUPABLE.find((g) => g.key === group);
  const conditions = conditionsOf(filters);

  return (
    <div
      data-testid="accounts-toolbar"
      className="mb-4 flex flex-col gap-3 border-b border-border-soft pb-4"
    >
      <div className="flex flex-wrap items-center gap-2">

      </div>

      {/* 🔴 **The design's filter row** — 📁 *"FILTERS · chips · ＋ Add
          condition · Smart filter"*.

          ⚡ **A chip per ACTIVE condition, in the design's grammar**: field in
          `--ink-4`, operator in `--ink-3`, value at 600, and a remove.
          ⛔ **Never a chip per available field** — a row reading *"Any kind ·
          Any source · Any time"* would state three conditions where none
          exist.

          ⛔ **Smart filter is absent.** 📁 The design's is *"Procurement never
          engaged"* — a model-derived condition carrying the intelligence tint.
          **Nothing derives one**, and a chip in that hue that ran an ordinary
          predicate would borrow the one treatment §14 reserves: *"nothing
          non-generated may borrow it."* */}
      <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Filters">
        <span className="text-2xs font-semibold uppercase tracking-[0.05em] text-content-subtle">
          Filters
        </span>

        {conditions.map((condition) => (
          <span
            key={condition.id}
            className="inline-flex h-control-sm items-center gap-1.5 rounded-md border border-border bg-surface px-2.5 text-xs text-content"
          >
            <span className="text-content-subtle">{condition.field}</span>
            <span className="text-content-muted">{condition.operator}</span>
            <span className="font-semibold">{condition.value}</span>
            <button
              type="button"
              onClick={() => onFilters(without(filters, condition.id))}
              // ♿ **The name says which condition goes**, because five chips
              // whose buttons all read "Remove" are five identical controls.
              aria-label={`Remove the ${condition.field} condition`}
              className="ml-0.5 rounded text-content-subtle hover:text-content focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent"
            >
              ×
            </button>
          </span>
        ))}

        {/* 📁 *"+ Add condition"* — dashed, `--line`, the design's own
            treatment for an affordance that adds rather than states. */}
        <details className="inline-block">
          <summary className="inline-flex h-control-sm cursor-pointer items-center rounded-md border border-dashed border-border px-2.5 text-xs text-content-muted hover:text-content">
            + Add condition
          </summary>
          <div className="mt-2 flex flex-wrap items-end gap-2 rounded-md border border-border-soft bg-surface p-3">
            <label className="flex flex-col gap-1 text-xs text-content-muted">
          Name contains
          <input
            type="search"
            value={filters.name}
            onChange={(event) => onFilters({ ...filters, name: event.target.value })}
            className="h-control-md rounded border border-border bg-surface px-2 text-sm text-content"
          />
        </label>

        <Select
          label="Kind"
          value={filters.kind ?? ''}
          onChange={(e) => onFilters({ ...filters, kind: e.target.value === '' ? null : e.target.value })}
          options={[{ value: '', label: 'Any kind' }, ...kinds.map((k) => ({ value: k, label: k }))]}
        />

        <Select
          label="Source"
          value={filters.source ?? ''}
          onChange={(e) =>
            onFilters({ ...filters, source: e.target.value === '' ? null : e.target.value })
          }
          options={[
            { value: '', label: 'Any source' },
            ...sources.map((s) => ({ value: s, label: s })),
          ]}
        />

        {/* ⛔ **Two conditions, not one dropdown.** ⚡ *Never observed* is the
            ABSENCE of an observation and *older than* is an old one — 📁 the
            contract's own distinction, and folding them would let a staleness
            filter claim Signora had looked. */}
        <Select
          label="Last observed"
          value={filters.neverObserved ? 'never' : (filters.staleAfterDays?.toString() ?? '')}
          onChange={(event) => {
            const value = event.target.value;
            onFilters({
              ...filters,
              neverObserved: value === 'never',
              staleAfterDays: value === '' || value === 'never' ? null : Number(value),
            });
          }}
          options={[
            { value: '', label: 'Any time' },
            { value: '7', label: 'Older than 7 days' },
            { value: '30', label: 'Older than 30 days' },
            { value: 'never', label: 'Never observed' },
          ]}
        />

        {isFiltered(filters) ? (
          <Button variant="ghost" onClick={() => onFilters(NO_FILTERS)}>
            Clear filters
          </Button>
        ) : null}
          </div>
        </details>

        {/* 🔴 **The sentence that keeps the filters honest**, and it now
            states the design's own figure.
 
            📁 The design prints *"312 of 8,412"*. ⚠️ **This comment used to
            say the total was not published by this read, and that was true
            until `accounts-count` existed** — 📁 [§2](../../../../CLAUDE.md):
            a claim about the present is corrected rather than left standing.
 
            ⛔ **The total is still omitted when the count has not answered**,
            and the loaded figure is never printed in its place: **inventing
            the number a seller trusts most is the quietest lie on the
            screen.** */}
        <p className="ml-auto text-2xs text-content-subtle" data-testid="companies-count">
          {total !== null
            ? `${shown.toLocaleString()} of ${total.toLocaleString()}`
            : isFiltered(filters)
              ? `${shown} of ${loaded} loaded`
              : `${loaded} loaded`}
        </p>
      </div>

      {/* 📁 **The design's second toolbar row** — *"Group · Sort · Columns ·
          Density"* on the left, *"Summarise this view"* on the right, each a
          30px pill. ⚡ **Columns and Density are the two this contract can
          answer**; ⛔ **Group and Sort are absent rather than dead** — the
          design groups by renewal quarter and sorts by score, and neither the
          endpoint nor this page can order the book (only the page in hand).
          📁 [B-255](../../../../docs/BUGS.md): a control that silently does
          nothing is worse than one that is absent. */}
      <div className="flex flex-wrap items-center gap-2">


        {/* 📁 **The design's own chip** — *"Group: Renewal quarter ✕"*, with a
            leading rule glyph and a remove when one is set. ⚡ **`--sunken` and
            600 weight when active**, which is how the design distinguishes an
            applied arrangement from an available control. */}
        <Chip
          label="Group"
          value={grouped?.key ?? ''}
          options={GROUPABLE.map((g) => ({ value: g.key, label: g.label }))}
          onChoose={(value) => onGroup(value === null ? null : (value as GroupKey))}
        />

        {/* 📁 *"Sort: Score ↑, then ACV ↓"* — ⛔ **one key, because the
            design's primary is Signora score and nothing publishes one.** ⚡ The
            arrow is the direction and clicking the chip's value flips it. */}
        <Chip
          label="Sort"
          value={sorted?.key ?? ''}
          arrow={sort?.direction}
          options={SORTABLE.map((option) => ({ value: option.key, label: option.label }))}
          onChoose={(value) =>
            onSort(value === null ? null : { key: value as SortKey, direction: 'asc' })
          }
          onFlip={
            sort === null
              ? undefined
              : () =>
                  onSort({
                    key: sort.key,
                    direction: sort.direction === 'asc' ? 'desc' : 'asc',
                  })
          }
        />

        {/* 📁 *"Density"* — ⚡ **the profile's own vocabulary**, because a person
            already sets this about themselves. ⛔ **A pill that toggles, not a
            native select**: the design draws one control of a size, and a
            dropdown over two values is a menu built for a switch. */}
        <button
          type="button"
          aria-pressed={density === 'compact'}
          onClick={() => onDensity(density === 'compact' ? 'comfortable' : 'compact')}
          className={PILL}
        >
          Density · {density === 'compact' ? 'Compact' : 'Comfortable'}
        </button>

        <details className="text-xs [&_summary::-webkit-details-marker]:hidden">
          {/* ⛔ **`list-none` because the design's control is a pill, not a
              disclosure triangle** — the ▶ is the browser's, and it made a
              designed button read as an outline item. */}
          <summary className={`${PILL} list-none cursor-pointer`}>
            Columns · {chosen.size} of {COLUMNS.length}
          </summary>
          <div className="mt-2 flex flex-col gap-1 rounded-md border border-border-soft bg-surface p-2 shadow-sm">
            {COLUMNS.map((column) => (
              <label key={column.id} className="flex items-center gap-2 text-content">
                <input
                  type="checkbox"
                  checked={column.pinned === true || chosen.has(column.id)}
                  /* ⛔ **Company cannot be turned off** — the design pins it
                     left, and a row you cannot identify is not a narrower
                     table. */
                  disabled={column.pinned === true}
                  onChange={() =>
                    onColumns(
                      chosen.has(column.id)
                        ? columns.filter((id) => id !== column.id)
                        : [...columns, column.id],
                    )
                  }
                />
                {column.label}
              </label>
            ))}
          </div>
        </details>
      </div>
    </div>
  );
}
