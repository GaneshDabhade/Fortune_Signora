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
  MAX_SORT_KEYS,
  SORTABLE,
  type Sort,
  type SortKey,
  type SortTerm,
} from '@/lib/accounts/table';
import { cn } from '@/lib/design/cn';
import { useBand } from '@/lib/shell/use-band';

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
  readonly sort: Sort;
  readonly onSort: (sort: Sort) => void;
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

/**
 * 📁 **The design's sort chip**, and the one control on this row that carries a
 * sentence rather than a value.
 *
 * ⛔ **The remove `×` clears ONE term, not the whole sort** — ⚡ the same
 * grammar the filter chips use, where each `×` removes the condition it sits
 * on and leaves the others standing.
 */
function SortChip({ sort, onSort }: { sort: Sort; onSort: (sort: Sort) => void }) {
  const applied = sort.length > 0;
  /** ⛔ **A key already used cannot be chosen again** — sorting by Company then
   *  Company is a tie-break that can never fire. */
  const remaining = (index: number) =>
    SORTABLE.filter((option) => !sort.some((term, at) => at !== index && term.key === option.key));

  const setTerm = (index: number, key: string | null) => {
    if (key === null) return onSort(sort.filter((_, at) => at !== index));
    const term: SortTerm = { key: key as SortKey, direction: sort[index]?.direction ?? 'asc' };
    const next = [...sort];
    next[index] = term;
    onSort(next.slice(0, MAX_SORT_KEYS));
  };
  const flip = (index: number) =>
    onSort(
      sort.map((term, at) =>
        at === index
          ? { key: term.key, direction: term.direction === 'asc' ? 'desc' : 'asc' }
          : term,
      ),
    );

  return (
    <span
      className={cn(
        'inline-flex h-control-sm items-center gap-1 rounded-md px-2.5 text-xs font-semibold',
        applied ? 'bg-surface-sunken text-content' : 'border border-border text-content-muted',
      )}
    >
      <span className={applied ? 'text-content-subtle' : undefined}>Sort</span>

      {sort.map((term, index) => (
        <span key={term.key} className="inline-flex items-center gap-1">
          {/* 📁 **The design's own word.** ⛔ Not a second arrow to decode. */}
          {index > 0 ? <span className="font-normal text-content-subtle">then</span> : null}
          <select
            aria-label={index === 0 ? 'Sort by' : 'Then sort by'}
            value={term.key}
            onChange={(event) => setTerm(index, event.target.value === '' ? null : event.target.value)}
            className="cursor-pointer border-0 bg-transparent p-0 pr-1 text-xs font-semibold text-content outline-none"
          >
            <option value="">None</option>
            {remaining(index).map((option) => (
              <option key={option.key} value={option.key}>
                {option.label}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => flip(index)}
            aria-label={`Sort ${
              SORTABLE.find((option) => option.key === term.key)?.label ?? term.key
            } ${term.direction === 'asc' ? 'descending' : 'ascending'}`}
            className="rounded px-0.5 text-content hover:bg-surface focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent"
          >
            {term.direction === 'asc' ? '↑' : '↓'}
          </button>
        </span>
      ))}

      {/* ⚡ **The next key's chooser** — the first when nothing is sorted, the
          tie-break when one is, and absent once the design's limit is met. */}
      {sort.length < MAX_SORT_KEYS ? (
        <select
          aria-label={applied ? 'Then sort by' : 'Sort by'}
          value=""
          onChange={(event) =>
            event.target.value === ''
              ? undefined
              : onSort([...sort, { key: event.target.value as SortKey, direction: 'asc' }])
          }
          className={cn(
            'cursor-pointer border-0 bg-transparent p-0 pr-1 text-xs font-semibold outline-none',
            applied ? 'text-content-subtle' : 'text-content-muted',
          )}
        >
          <option value="">{applied ? 'then…' : 'None'}</option>
          {remaining(-1).map((option) => (
            <option key={option.key} value={option.key}>
              {option.label}
            </option>
          ))}
        </select>
      ) : null}

      {applied ? (
        <button
          type="button"
          onClick={() => onSort([])}
          aria-label="Remove the sort"
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

  const grouped = group === null ? null : GROUPABLE.find((g) => g.key === group);
  const conditions = conditionsOf(filters);

  /**
   * 🔴 **The one state transition in this toolbar** — 📁 §20, *"Filter strip
   * collapses to one **Scope** button with a count."*
   *
   * ⚠️ **Measured at 390 × 844 before this**: `Group`, `Sort`, `Density` and
   * `Columns` each became a full-width row, so the arrangement controls
   * occupied more of the phone than the table did. ⛔ **That is a desktop row
   * wrapping**, which the design replaces rather than reflows.
   */
  const band = useBand();
  const scoped = band === 'phone';

  const rows = (
    <>
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
      <div
        /**
         * 📁 **Three behaviours, and the design names each of them.**
         *
         * | Band | 📁 |
         * |---|---|
         * | ≥1280 | the strip, wrapping |
         * | 1024–1279 | *"Filter strip stays; **chips scroll horizontally**."* |
         * | <1024 | *"Filter strip collapses to one **Scope** button with a count."* |
         *
         * ⛔ **The middle one is CSS, not a breakpoint in JavaScript** — it is
         * a change of overflow, not a change of controls. ⚡ **Only the third
         * is a state transition**, because it replaces the controls with a
         * different one, and that is the single thing `useBand` is read for.
         */
        className={cn(
          'flex items-center gap-2',
          // 📁 1024–1279 — chips scroll rather than wrap.
          'flex-nowrap overflow-x-auto',
          // 📁 ≥1280 — the reference strip wraps as before.
          'laptop:flex-wrap laptop:overflow-x-visible',
        )}
        role="group"
        aria-label="Filters"
      >
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

        {/* 📁 **The design's sort control** — *"Sort: Score ↑, then ACV ↓"*.

            ⚡ **Up to two keys, and the sentence is the state.** 📁 The
            mechanic is explicit that it is *"stated in words in the toolbar
            rather than as arrows to decode"* — ⛔ **so the second key reads
            *"then"* rather than being a second arrow a reader has to rank.**

            ⚠️ **The second select appears only once a first key is chosen**,
            because a tie-break with nothing to tie is a control that cannot
            do anything ([B-255](../../../../docs/BUGS.md)). */}
        <SortChip sort={sort} onSort={onSort} />

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
    </>
  );

  return (
    <div
      data-testid="accounts-toolbar"
      className={cn('mb-4 flex flex-col gap-3 border-b border-border-soft pb-4')}
    >
      {scoped ? (
        /**
         * ⚡ **One control, and the controls it holds are the SAME instances** —
         * ⛔ **not a second copy rendered beside a hidden desktop row**: two
         * copies of one control are two things a screen reader announces and
         * two places a value can be set.
         *
         * ♿ **44px** — 📁 `2.5.8`: *"32px target with 8px separation; **44px on
         * touch**."* ⛔ And `<details>` rather than a state flag: the surface
         * opens with no JavaScript and closes with Escape for free.
         */
        <details data-testid="scope-control" className="w-full">
          <summary
            className={cn(
              'flex h-11 w-full cursor-pointer list-none items-center justify-between gap-2',
              'rounded-md border border-border px-3 text-sm font-semibold text-content',
              'hover:bg-surface-sunken focus-visible:outline focus-visible:outline-2',
              'focus-visible:outline-offset-2 focus-visible:outline-accent',
              '[&::-webkit-details-marker]:hidden',
            )}
          >
            <span>Scope</span>
            {/* ⛔ **The count is the number of CONDITIONS, and it is absent at
                zero.** 📁 A `0` badge is a count nobody acts on wearing the
                shape of one they would — the same rule the bell keeps. */}
            {conditions.length > 0 ? (
              <span
                data-testid="scope-count"
                aria-label={`${conditions.length} condition${conditions.length === 1 ? '' : 's'} applied`}
                className="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-surface-sunken px-1.5 text-2xs font-semibold tabular-nums text-content"
              >
                {conditions.length}
              </span>
            ) : null}
          </summary>
          <div className="mt-3 flex flex-col gap-3">{rows}</div>
        </details>
      ) : (
        rows
      )}
    </div>
  );
}
